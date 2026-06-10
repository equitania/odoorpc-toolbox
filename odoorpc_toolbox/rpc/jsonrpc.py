"""JSON-RPC 2.0 protocol implementation for Odoo communication.

Provides ProxyJSON for JSON-RPC requests and ProxyHTTP for raw HTTP requests.
Uses Transport abstraction for pluggable HTTP backends (urllib, httpx).

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

import copy
import io
import json
import logging
import random

from odoorpc_toolbox.rpc.transport import TransportResponse, UrllibTransport

LOG_HIDDEN_JSON_PARAMS = ["password"]
# Positional `args` indices containing credentials for known (service, method)
# pairs sent via the legacy /jsonrpc service dispatch. Use "*" as method to
# apply the masking to every method of a service (default-deny for db service).
LOG_HIDDEN_ARG_INDICES: dict[tuple[str, str], tuple[int, ...]] = {
    ("common", "login"): (2,),
    ("common", "authenticate"): (2,),
    ("object", "execute"): (2,),
    ("object", "execute_kw"): (2,),
    ("db", "dump"): (0,),
    ("db", "change_admin_password"): (0, 1),
    ("db", "create_database"): (0, 4),
    ("db", "drop"): (0,),
    ("db", "duplicate_database"): (0,),
    ("db", "restore"): (0,),
    ("db", "*"): (0,),
}
LOG_REDACTED = "**********"
LOG_JSON_SEND_MSG = "(JSON,send) %(url)s %(data)s"
LOG_JSON_RECV_MSG = "(JSON,recv) %(url)s %(data)s => %(result)s"
LOG_HTTP_SEND_MSG = "(HTTP,send) %(url)s%(data)s"
LOG_HTTP_RECV_MSG = "(HTTP,recv) %(url)s%(data)s => %(result)s"

logger = logging.getLogger(__name__)


def encode_data(data: str) -> bytes:
    """Encode string data to bytes for HTTP transmission."""
    try:
        return bytes(data, "utf-8")
    except TypeError:
        return bytes(data)


def decode_data(data) -> io.StringIO:
    """Decode HTTP response data to a StringIO object.

    Accepts either a urllib response (with .read()) or a TransportResponse.
    """
    if isinstance(data, TransportResponse):
        return io.StringIO(data.body.decode("utf-8"))
    return io.StringIO(data.read().decode("utf-8"))


def get_json_log_data(data: dict) -> dict:
    """Return a copy of `data` with sensitive params hidden for logging.

    Masks two shapes of credentials:
    - Named params listed in LOG_HIDDEN_JSON_PARAMS (e.g. ``password`` in
      ``/web/session/authenticate`` calls).
    - Positional ``args`` entries for known ``(service, method)`` pairs sent
      via the legacy ``/jsonrpc`` dispatch (see LOG_HIDDEN_ARG_INDICES). This
      covers ``service=common method=login`` (args[2] = password),
      ``service=object`` execute/execute_kw (args[2] = password), and
      ``service=db`` management calls (args[0] = master password).
    """
    log_data: dict | None = None  # lazily deep-copied when first redaction is needed

    def _ensure_copy() -> dict:
        nonlocal log_data
        if log_data is None:
            log_data = copy.deepcopy(data)
        return log_data

    params = data.get("params")

    if isinstance(params, dict):
        for param in LOG_HIDDEN_JSON_PARAMS:
            if param in params:
                _ensure_copy()["params"][param] = LOG_REDACTED

        args = params.get("args")
        if isinstance(args, list):
            service = params.get("service")
            method = params.get("method")
            indices = LOG_HIDDEN_ARG_INDICES.get((service, method))
            if indices is None and service is not None:
                indices = LOG_HIDDEN_ARG_INDICES.get((service, "*"))
            if indices:
                masked_args = _ensure_copy()["params"]["args"]
                for idx in indices:
                    if 0 <= idx < len(masked_args) and masked_args[idx] is not None:
                        masked_args[idx] = LOG_REDACTED

    return log_data if log_data is not None else data


def get_http_log_data(data: str | None) -> str:
    """Return a safe log representation of a raw HTTP request body.

    Raw HTTP bodies (e.g. JSON-2 payloads or session authentication data)
    may contain credentials in arbitrary shapes that cannot be reliably
    redacted, so only the body size is logged - never the content.
    """
    if not data:
        return ""
    return f" (<{len(data)} bytes>)"


def get_http_log_result(response) -> str:
    """Return a safe log representation of an HTTP response.

    Response bodies may contain session tokens or sensitive business data,
    so only the status code and body size are logged.
    """
    status = getattr(response, "status_code", "?")
    body = getattr(response, "body", b"")
    return f"<status {status}, {len(body)} bytes>"


class Proxy:
    """Base class to implement a proxy to perform requests.

    Accepts either a Transport instance or a legacy urllib opener.
    If neither is provided, creates a default UrllibTransport.
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 120,
        ssl: bool = False,
        opener=None,
        transport=None,
    ) -> None:
        self._root_url = "{http}{host}:{port}".format(http=("https://" if ssl else "http://"), host=host, port=port)
        self._timeout = timeout
        self._builder = URLBuilder(self)

        if transport is not None:
            self._transport = transport
        elif opener is not None:
            self._transport = UrllibTransport(opener=opener)
        else:
            self._transport = UrllibTransport()

    @property
    def _opener(self):
        """Backward-compatible access to the underlying urllib opener.

        Returns the opener if the transport is UrllibTransport-based,
        otherwise returns None.
        """
        return getattr(self._transport, "opener", None)

    def __getattr__(self, name: str):
        return getattr(self._builder, name)

    def __getitem__(self, url: str):
        return self._builder[url]

    def _get_full_url(self, url: str) -> str:
        return "/".join([self._root_url, url])


class ProxyJSON(Proxy):
    """Provides dynamic access to all JSON-RPC methods.

    Example usage:
        >>> proxy = ProxyJSON('localhost', 8069)
        >>> proxy.web.session.authenticate(db='mydb', login='admin', password='admin')
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 120,
        ssl: bool = False,
        opener=None,
        deserialize: bool = True,
        transport=None,
    ) -> None:
        super().__init__(host, port, timeout, ssl, opener, transport)
        self._deserialize = deserialize

    def __call__(self, url: str, params: dict | None = None) -> dict:
        if params is None:
            params = {}
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": random.randint(0, 1000000000),
        }
        if url.startswith("/"):
            url = url[1:]
        full_url = self._get_full_url(url)
        log_data = get_json_log_data(data)
        logger.debug(LOG_JSON_SEND_MSG, {"url": full_url, "data": log_data})
        data_json = json.dumps(data)
        data_bytes = encode_data(data_json)
        headers = {"Content-Type": "application/json"}

        response = self._transport.request(full_url, data=data_bytes, headers=headers, timeout=self._timeout)

        if not self._deserialize:
            return response
        result = json.loads(response.body.decode("utf-8"))
        logger.debug(
            LOG_JSON_RECV_MSG,
            {"url": full_url, "data": log_data, "result": result},
        )
        return result


class ProxyHTTP(Proxy):
    """Provides dynamic access to all HTTP methods."""

    def __call__(self, url: str, data: str | None = None, headers: dict | None = None):
        if url.startswith("/"):
            url = url[1:]
        full_url = self._get_full_url(url)
        log_data = get_http_log_data(data)
        logger.debug(
            LOG_HTTP_SEND_MSG,
            {"url": full_url, "data": log_data},
        )
        data_bytes = encode_data(data) if data else None
        response = self._transport.request(full_url, data=data_bytes, headers=headers, timeout=self._timeout)
        logger.debug(
            LOG_HTTP_RECV_MSG,
            {
                "url": full_url,
                "data": log_data,
                "result": get_http_log_result(response),
            },
        )
        return response


class URLBuilder:
    """Auto-builds a URL while getting its attributes.

    Used by ProxyJSON and ProxyHTTP for dynamic URL construction like:
        proxy.web.session.authenticate(...)
    which builds the URL '/web/session/authenticate'.
    """

    def __init__(self, rpc: Proxy, url: str | None = None) -> None:
        self._rpc = rpc
        self._url = url

    def __getattr__(self, path: str) -> "URLBuilder":
        new_url = "/".join([self._url, path]) if self._url else path
        return URLBuilder(self._rpc, new_url)

    def __getitem__(self, path: str) -> "URLBuilder":
        if path and path[0] == "/":
            path = path[1:]
        if path and path[-1] == "/":
            path = path[:-1]
        return getattr(self, path)

    def __call__(self, **kwargs):
        return self._rpc(self._url, kwargs)

    def __str__(self) -> str:
        return self._url or ""
