"""Main ODOO class - entry point for managing an Odoo server.

This is the internalized equivalent of odoorpc.ODOO, providing the same
API for connection, authentication, and RPC execution.

Supports JSON-RPC (/jsonrpc) for all Odoo versions and the JSON-2 API
(/json/2/<model>/<method>) with Bearer token authentication for Odoo >= 19.
The legacy /jsonrpc endpoint is deprecated and scheduled for removal in
Odoo 22 (fall 2028).

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import json
import logging
import warnings
from typing import Any

from odoorpc_toolbox import exceptions, session
from odoorpc_toolbox.db import DB
from odoorpc_toolbox.environment import Environment
from odoorpc_toolbox.report import Report
from odoorpc_toolbox.rpc import PROTOCOLS
from odoorpc_toolbox.rpc import errors as rpc_errors
from odoorpc_toolbox.tools import Config, v

logger = logging.getLogger(__name__)

# Positional-argument names of common ORM methods, used to translate legacy
# execute/execute_kw positional calls into JSON-2 named parameters (the JSON-2
# API has no positional calling convention). Record-bound methods start with
# "ids"; the remaining ones are @api.model methods. Source: Odoo 19 ORM
# signatures. Unknown methods fall back to the legacy /jsonrpc endpoint.
_JSON2_METHOD_PARAMS: dict[str, tuple[str, ...]] = {
    "search": ("domain", "offset", "limit", "order"),
    "search_count": ("domain", "limit"),
    "search_read": ("domain", "fields", "offset", "limit", "order"),
    "name_search": ("name", "domain", "operator", "limit"),
    "name_create": ("name",),
    "create": ("vals_list",),
    "default_get": ("fields_list",),
    "fields_get": ("allfields", "attributes"),
    "read": ("ids", "fields", "load"),
    "write": ("ids", "vals"),
    "unlink": ("ids",),
    "copy": ("ids", "default"),
    "exists": ("ids",),
    "name_get": ("ids",),
}


def _normalize_json2_result(method: str, args: list, kwargs: dict, result: Any) -> Any:
    """Restore legacy execute_kw return shapes where JSON-2 differs.

    create(): the legacy /jsonrpc dispatch returns a single id for a dict
    input, but JSON-2 serializes the created recordset as a list of ids.
    Callers (and this package's own helpers) rely on the legacy shape.
    """
    if method == "create" and isinstance(result, list) and len(result) == 1:
        vals = args[0] if args else kwargs.get("vals_list")
        if isinstance(vals, dict):
            return result[0]
    return result


def _map_args_to_json2(method: str, args: list, kwargs: dict) -> dict | None:
    """Translate positional arguments into JSON-2 named parameters.

    Returns the flat parameter dict for the JSON-2 request body, or None
    when the positional arguments cannot be mapped (unknown method, too many
    arguments, or a parameter given both positionally and by name) - in that
    case the caller falls back to the legacy /jsonrpc endpoint.
    """
    if not args:
        return dict(kwargs)
    names = _JSON2_METHOD_PARAMS.get(method)
    if names is None or len(args) > len(names):
        return None
    payload = dict(zip(names, args, strict=False))
    if payload.keys() & kwargs.keys():
        return None
    payload.update(kwargs)
    return payload


def _parse_json2_error(body: bytes) -> tuple[str, dict]:
    """Parse a JSON-2 error response body.

    The JSON-2 API returns errors as HTTP 4xx/5xx with a JSON object body
    of shape {"name", "message", "arguments", "context", "debug"}.

    Returns:
        Tuple of (message, error_dict). Falls back to the raw body text
        when the body is not valid JSON.
    """
    try:
        obj = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body.decode("utf-8", errors="replace"), {}
    if isinstance(obj, dict):
        return obj.get("message", str(obj)), obj
    return str(obj), {}


class ODOO:
    """Main class for connecting to and interacting with an Odoo server.

    Uses JSON-RPC protocol. Supported protocols: 'jsonrpc' and 'jsonrpc+ssl'.

    Example:
        >>> from odoorpc_toolbox.odoo import ODOO
        >>> odoo = ODOO('localhost', protocol='jsonrpc', port=8069)
        >>> odoo.login('mydb', 'admin', 'admin')
        >>> odoo.env.user.name
        'Administrator'

    You can also define a custom URL opener for HTTP basic auth:
        >>> import urllib.request
        >>> pwd_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        >>> pwd_mgr.add_password(None, "http://example.net", "user", "pass")
        >>> auth_handler = urllib.request.HTTPBasicAuthHandler(pwd_mgr)
        >>> opener = urllib.request.build_opener(auth_handler)
        >>> odoo = ODOO('example.net', port=80, opener=opener)
    """

    def __init__(
        self,
        host: str = "localhost",
        protocol: str = "jsonrpc",
        port: int = 8069,
        timeout: float = 120,
        version: str | None = None,
        opener=None,
        transport=None,
    ) -> None:
        if protocol not in ["jsonrpc", "jsonrpc+ssl"]:
            raise ValueError(
                f"The protocol '{protocol}' is not supported. Please choose from: {['jsonrpc', 'jsonrpc+ssl']}"
            )
        if opener is not None and transport is not None:
            raise ValueError("Cannot specify both 'opener' and 'transport'. Use one or the other.")
        try:
            port = int(port)
        except (ValueError, TypeError) as exc:
            raise ValueError("The port must be an integer") from exc
        try:
            if timeout is not None:
                timeout = float(timeout)
        except (ValueError, TypeError) as exc:
            raise ValueError("The timeout must be a float") from exc

        self._host = host
        self._port = port
        self._protocol = protocol
        self._env: Environment | None = None
        self._login: str | None = None
        self._password: str | None = None
        self._api_key: str | None = None
        self._db = DB(self)
        self._report = Report(self)

        # Instantiate the server connector
        try:
            self._connector = PROTOCOLS[protocol](
                self._host, self._port, timeout, version, opener=opener, transport=transport
            )
        except rpc_errors.ConnectorError as exc:
            raise exceptions.InternalError(exc.message) from exc

        # Configuration options
        self._config = Config(
            self,
            {"auto_commit": True, "auto_context": True, "timeout": timeout},
        )

    @property
    def config(self) -> Config:
        """Dictionary of available configuration options.

        Options:
            - auto_commit: Auto-commit record changes (default: True)
            - auto_context: Send user context with model calls (default: True)
            - timeout: RPC request timeout in seconds (default: 120)
        """
        return self._config

    @property
    def metrics(self):
        """Return RequestMetrics if a MetricsTransport is in use, else None."""
        transport = getattr(self._connector, "_transport", None)
        if transport is not None and hasattr(transport, "metrics"):
            return transport.metrics
        return None

    @property
    def version(self) -> str:
        """The version of the server."""
        return self._connector.version

    @property
    def db(self) -> DB:
        """The database management service."""
        return self._db

    @property
    def report(self) -> Report:
        """The report management service."""
        return self._report

    @property
    def host(self) -> str:
        """Hostname or IP address of the server."""
        return self._host

    @property
    def port(self) -> int:
        """The port used."""
        return self._port

    @property
    def protocol(self) -> str:
        """The protocol used."""
        return self._protocol

    @property
    def env(self) -> Environment:
        """The environment wrapping data to manage records.

        Example:
            >>> Partner = odoo.env['res.partner']
        """
        self._check_logged_user()
        return self._env

    def json(self, url: str, params: dict) -> dict:
        """Execute a low-level JSON-RPC query.

        Args:
            url: The endpoint URL.
            params: Dictionary of parameters.

        Returns:
            The JSON response as a dictionary.

        Raises:
            RPCError: If the response contains an error.
        """
        data = self._connector.proxy_json(url, params)
        if data.get("error"):
            raise exceptions.RPCError(data["error"]["data"]["message"], data["error"])
        return data

    def http(self, url: str, data: str | None = None, headers: dict | None = None):
        """Execute a raw HTTP query.

        Args:
            url: The endpoint URL.
            data: POST data string.
            headers: HTTP headers dictionary.

        Returns:
            HTTP response object.
        """
        return self._connector.proxy_http(url, data, headers)

    def _check_logged_user(self) -> None:
        """Check if a user is logged in."""
        if not self._env or not (self._password or self._api_key) or not self._login:
            raise exceptions.InternalError("Login required")

    @property
    def _rpc_credential(self) -> str | None:
        """Credential for the password slot of legacy /jsonrpc calls.

        Odoo accepts API keys in place of passwords for RPC, so the API key
        is preferred when set (e.g. for the legacy fallback on Odoo 19+).
        """
        return self._api_key or self._password

    @property
    def _use_json2(self) -> bool:
        """Return True when JSON-2 routing is active: Odoo >= 19 AND an API key is set.

        The /json/2/<model>/<method> endpoint uses Bearer token
        authentication (Authorization: bearer <API_KEY>) and named
        parameters only. Real passwords are NOT valid Bearer tokens, so
        password-authenticated sessions on Odoo 19+ stay on the deprecated
        /jsonrpc endpoint (scheduled for removal in Odoo 22, fall 2028).

        See: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
        """
        return v(self.version)[0] >= 19 and self._api_key is not None

    def _json2_call(
        self,
        model: str,
        method: str,
        kwargs: dict | None = None,
        *,
        _api_key: str | None = None,
        _db: str | None = None,
    ) -> Any:
        """Execute a JSON-2 API call (Odoo 19+).

        Sends a plain JSON POST to /json/2/<model>/<method> without the
        JSON-RPC 2.0 envelope. Authentication uses the API key as Bearer
        token in the Authorization header.

        Args:
            model: The Odoo model name.
            method: The method name.
            kwargs: Named method parameters (JSON-2 has no positional
                arguments). Record IDs go into the special "ids" key, an
                optional context into the "context" key.
            _api_key: API key override for the login bootstrap (before
                self._api_key is set).
            _db: Database name override for the login bootstrap (before
                self._env is set).

        Returns:
            The JSON-serialized return value of the called method (the
            JSON-2 API returns direct results, no {"result": ...} wrapper).

        Raises:
            RPCError: On HTTP 4xx/5xx, carrying the server's error payload
                plus "status_code" in the info dict.
            InternalError: If no API key is available.
        """
        key = _api_key or self._api_key
        if not key:
            raise exceptions.InternalError("JSON-2 API requires an API key (Bearer token); none is configured")
        url = f"/json/2/{model}/{method}"
        payload: dict[str, Any] = dict(kwargs) if kwargs else {}

        # The headers dict carries the Bearer token - it must never be
        # logged (ProxyHTTP logs bodies as size summaries only, no headers).
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"bearer {key}",  # lowercase scheme per Odoo docs
        }
        db = _db or (self._env.db if self._env else None)
        if db:
            headers["X-Odoo-Database"] = db

        response = self._connector.proxy_http(url, data=json.dumps(payload), headers=headers)
        if response.status_code >= 400:
            message, error_data = _parse_json2_error(response.body)
            raise exceptions.RPCError(message, {**error_data, "status_code": response.status_code})
        return json.loads(response.body.decode("utf-8"))

    def login(
        self,
        db: str,
        login: str = "admin",
        password: str = "admin",
        api_key: str | None = None,
    ) -> None:
        """Log in to the Odoo server.

        For Odoo >= 19, uses the JSON-2 API with Bearer token auth: the API
        key (or the password field, which doubles as API key for backward
        compatibility) is the complete credential - there is no login
        round-trip. The user context and uid are bootstrapped via
        res.users/context_get (the current user is derived server-side from
        the API key). When no explicit ``api_key`` is given and the server
        rejects the password as Bearer token (real passwords are not valid
        API keys), login falls back to the deprecated /jsonrpc dispatch.
        For Odoo 10-18, uses the legacy /jsonrpc service dispatch; an
        explicit ``api_key`` is used as password substitute (valid since
        Odoo 14). For Odoo < 10, uses /web/session/authenticate.

        Args:
            db: Database name.
            login: Username (default: 'admin').
            password: Password (default: 'admin'). On Odoo >= 19 this value
                is tried as API key when ``api_key`` is not given.
            api_key: Odoo API key for Bearer auth (Odoo >= 19). Takes
                precedence over ``password`` for the JSON-2 API.

        Raises:
            RPCError: If login fails.
        """
        self._api_key = None
        if v(self.version)[0] >= 19:
            # Odoo 19+: JSON-2 API, Bearer token auth. Bootstrap the user
            # context via res.users/context_get; validates the key (401 on
            # invalid key) and works for API-only bot accounts too.
            key = api_key or password
            try:
                context = self._json2_call("res.users", "context_get", kwargs={}, _api_key=key, _db=db)
            except exceptions.RPCError as exc:
                status = exc.info.get("status_code") if isinstance(exc.info, dict) else None
                if api_key is None and status in (401, 403):
                    # The password field holds a real password, not an API
                    # key - fall back to the deprecated /jsonrpc login.
                    logger.warning(
                        "Password authentication on Odoo %s uses the deprecated "
                        "/jsonrpc endpoint (removal in Odoo 22, fall 2028). "
                        "Configure an API key (Server.api_key) to use the JSON-2 API.",
                        self.version,
                    )
                    uid, context = self._legacy_jsonrpc_login(db, login, password)
                else:
                    raise
            else:
                if not isinstance(context, dict):
                    raise exceptions.RPCError(f"Unexpected context_get response from JSON-2 API: {context!r}")
                context = dict(context)
                uid = context.get("uid")
                if not uid:
                    # context_get did not expose the uid - resolve via login name
                    ids = self._json2_call(
                        "res.users",
                        "search",
                        kwargs={"domain": [["login", "=", login]], "limit": 1},
                        _api_key=key,
                        _db=db,
                    )
                    uid = ids[0] if ids else None
                if not uid:
                    raise exceptions.RPCError(
                        "Could not determine the user id via the JSON-2 API "
                        "(context_get returned no uid and no user matches the given login)"
                    )
                self._api_key = key
            context["uid"] = uid
        elif v(self.version)[0] >= 10:
            # Odoo 10-18: legacy /jsonrpc service dispatch. API keys are
            # valid password substitutes for RPC since Odoo 14, so an
            # explicit api_key takes precedence here too.
            uid, context = self._legacy_jsonrpc_login(db, login, api_key or password)
            context["uid"] = uid
            self._api_key = api_key
        else:
            # Odoo < 10
            data = self.json(
                "/web/session/authenticate",
                {"db": db, "login": login, "password": password},
            )
            uid = data["result"]["uid"]
            if not uid:
                raise exceptions.RPCError("Wrong login ID or password")
            context = data["result"]["user_context"]

        self._env = Environment(self, db, uid, context=context)
        self._login = login
        self._password = password

        if self._use_json2:
            logger.info(
                "Connected to Odoo %s using the JSON-2 API (Bearer token auth).",
                self.version,
            )

    def _legacy_jsonrpc_login(self, db: str, login: str, password: str) -> tuple[int, dict]:
        """Log in via the legacy /jsonrpc service dispatch (Odoo 10+).

        Also used as fallback on Odoo 19+ when the credential is a real
        password (not a valid Bearer token). Deprecated server-side,
        scheduled for removal in Odoo 22 (fall 2028).

        Returns:
            Tuple of (uid, context).

        Raises:
            RPCError: If login fails.
        """
        data = self.json(
            "/jsonrpc",
            params={
                "service": "common",
                "method": "login",
                "args": [db, login, password],
            },
        )
        uid = data["result"]
        if not uid:
            raise exceptions.RPCError("Wrong login ID or password")
        context = self.json(
            "/jsonrpc",
            {
                "service": "object",
                "method": "execute",
                "args": [db, uid, password, "res.users", "context_get"],
            },
        )["result"]
        return uid, context

    def logout(self) -> bool:
        """Log out the user.

        Returns:
            True if successful, False if no user was logged in.
        """
        if not self._env:
            return False
        if v(self.version)[0] < 10:
            self.json("/web/session/destroy", {})
        self._env = None
        self._login = None
        self._password = None
        self._api_key = None
        return True

    def close(self) -> bool:
        """Same as logout. For compatibility with contextlib.closing."""
        return self.logout()

    # ---- Raw RPC methods ----

    def execute(self, model: str, method: str, *args) -> Any:
        """Execute a method of a model.

        For Odoo >= 19, uses the JSON-2 API endpoint /json/2/<model>/<method>.
        For older versions, uses the legacy /jsonrpc service dispatch.

        Args:
            model: The Odoo model name.
            method: The method name.
            *args: Positional arguments for the method.

        Returns:
            The result of the method call.
        """
        self._check_logged_user()
        if self._use_json2:
            # JSON-2 has no positional calling convention - delegate to
            # execute_kw, which maps known ORM methods to named parameters
            # and falls back to the legacy endpoint otherwise.
            return self.execute_kw(model, method, args=list(args))
        args_to_send = [
            self.env.db,
            self.env.uid,
            self._rpc_credential,
            model,
            method,
        ]
        args_to_send.extend(args)
        data = self.json(
            "/jsonrpc",
            {"service": "object", "method": "execute", "args": args_to_send},
        )
        return data.get("result")

    def execute_kw(
        self,
        model: str,
        method: str,
        args: list | None = None,
        kwargs: dict | None = None,
    ) -> Any:
        """Execute a method of a model with keyword arguments.

        For Odoo >= 19, uses the JSON-2 API endpoint /json/2/<model>/<method>.
        For older versions, uses the legacy /jsonrpc service dispatch.

        Args:
            model: The Odoo model name.
            method: The method name.
            args: Positional arguments list.
            kwargs: Keyword arguments dictionary.

        Returns:
            The result of the method call.
        """
        self._check_logged_user()
        args = args or []
        kwargs = kwargs or {}
        if self._use_json2:
            payload = _map_args_to_json2(method, args, kwargs)
            if payload is not None:
                result = self._json2_call(model, method, kwargs=payload)
                return _normalize_json2_result(method, args, kwargs, result)
            warnings.warn(
                f"Method '{model}.{method}' called with positional arguments that "
                "cannot be mapped to JSON-2 named parameters; falling back to the "
                "deprecated /jsonrpc endpoint (scheduled for removal in Odoo 22, "
                "fall 2028). Pass named parameters (kwargs) instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        args_to_send = [
            self.env.db,
            self.env.uid,
            self._rpc_credential,
            model,
            method,
        ]
        args_to_send.extend([args, kwargs])
        data = self.json(
            "/jsonrpc",
            {
                "service": "object",
                "method": "execute_kw",
                "args": args_to_send,
            },
        )
        return data.get("result")

    # ---- Session methods ----

    def save(self, name: str, rc_file: str = "~/.odoorpcrc") -> None:
        """Save the current session to an RC file.

        Args:
            name: Session identifier.
            rc_file: Path to the RC file (default: ~/.odoorpcrc).
        """
        self._check_logged_user()
        data = {
            "type": self.__class__.__name__,
            "host": self.host,
            "protocol": self.protocol,
            "port": self.port,
            "timeout": self.config["timeout"],
            # API keys round-trip via the passwd slot: ODOO.load() passes it
            # as password, which login() uses as API key on Odoo >= 19.
            "user": self._login,
            "passwd": self._api_key or self._password,
            "database": self.env.db,
        }
        session.save(name, data, rc_file)

    @classmethod
    def load(cls, name: str, rc_file: str = "~/.odoorpcrc") -> ODOO:
        """Load and return a connected ODOO session.

        Args:
            name: Session identifier.
            rc_file: Path to the RC file (default: ~/.odoorpcrc).

        Returns:
            A connected ODOO instance.
        """
        data = session.get(name, rc_file)
        if data.get("type") != cls.__name__:
            raise exceptions.InternalError(f"'{name}' session is not of type '{cls.__name__}'")
        odoo = cls(
            host=data["host"],
            protocol=data["protocol"],
            port=data["port"],
            timeout=data["timeout"],
        )
        odoo.login(db=data["database"], login=data["user"], password=data["passwd"])
        return odoo

    @classmethod
    def list(cls, rc_file: str = "~/.odoorpcrc") -> list[str]:
        """Return a list of all stored session names.

        Args:
            rc_file: Path to the RC file (default: ~/.odoorpcrc).

        Returns:
            List of session names.
        """
        sessions = session.get_all(rc_file)
        return [name for name in sessions if sessions[name].get("type") == cls.__name__]

    @classmethod
    def remove(cls, name: str, rc_file: str = "~/.odoorpcrc") -> bool:
        """Remove a stored session.

        Args:
            name: Session identifier.
            rc_file: Path to the RC file (default: ~/.odoorpcrc).

        Returns:
            True if removed.
        """
        data = session.get(name, rc_file)
        if data.get("type") != cls.__name__:
            raise exceptions.InternalError(f"'{name}' session is not of type '{cls.__name__}'")
        return session.remove(name, rc_file)
