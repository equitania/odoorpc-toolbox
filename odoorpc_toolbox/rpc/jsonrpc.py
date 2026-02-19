"""JSON-RPC 2.0 protocol implementation for Odoo communication.

Provides ProxyJSON for JSON-RPC requests and ProxyHTTP for raw HTTP requests.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

import copy
import io
import json
import logging
import random
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener

LOG_HIDDEN_JSON_PARAMS = ["password"]
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
    """Decode HTTP response data to a StringIO object."""
    return io.StringIO(data.read().decode("utf-8"))


def get_json_log_data(data: dict) -> dict:
    """Return a copy of `data` with sensitive params hidden for logging."""
    log_data = data
    for param in LOG_HIDDEN_JSON_PARAMS:
        if param in data.get("params", {}):
            if log_data is data:
                log_data = copy.deepcopy(data)
            log_data["params"][param] = "**********"
    return log_data


class Proxy:
    """Base class to implement a proxy to perform requests."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 120,
        ssl: bool = False,
        opener=None,
    ) -> None:
        self._root_url = "{http}{host}:{port}".format(http=("https://" if ssl else "http://"), host=host, port=port)
        self._timeout = timeout
        self._builder = URLBuilder(self)
        self._opener = opener
        if not opener:
            cookie_jar = CookieJar()
            self._opener = build_opener(HTTPCookieProcessor(cookie_jar))

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
    ) -> None:
        super().__init__(host, port, timeout, ssl, opener)
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
        request = Request(url=full_url, data=encode_data(data_json))
        request.add_header("Content-Type", "application/json")
        response = self._opener.open(request, timeout=self._timeout)
        if not self._deserialize:
            return response
        result = json.load(decode_data(response))
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
        logger.debug(
            LOG_HTTP_SEND_MSG,
            {"url": full_url, "data": f" ({data})" if data else ""},
        )
        kwargs: dict = {"url": full_url}
        if data:
            kwargs["data"] = encode_data(data)
        request = Request(**kwargs)
        if headers:
            for hkey, hvalue in headers.items():
                request.add_header(hkey, hvalue)
        response = self._opener.open(request, timeout=self._timeout)
        logger.debug(
            LOG_HTTP_RECV_MSG,
            {
                "url": full_url,
                "data": f" ({data})" if data else "",
                "result": response,
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
