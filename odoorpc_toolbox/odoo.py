"""Main ODOO class - entry point for managing an Odoo server.

This is the internalized equivalent of odoorpc.ODOO, providing the same
API for connection, authentication, and RPC execution.

Supports both legacy JSON-RPC (/jsonrpc, Odoo <= 18) and
JSON-2 API (/json/2/, Odoo >= 19).

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from odoorpc_toolbox import exceptions, session
from odoorpc_toolbox.db import DB
from odoorpc_toolbox.environment import Environment
from odoorpc_toolbox.report import Report
from odoorpc_toolbox.rpc import PROTOCOLS
from odoorpc_toolbox.rpc import errors as rpc_errors
from odoorpc_toolbox.tools import Config, v

logger = logging.getLogger(__name__)


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
        if not self._env or not self._password or not self._login:
            raise exceptions.InternalError("Login required")

    @property
    def _use_json2(self) -> bool:
        """Return True if the server supports JSON-2 API (Odoo >= 19)."""
        return v(self.version)[0] >= 19

    def _json2_call(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None) -> Any:
        """Execute a JSON-2 API call (Odoo 19+).

        Sends a plain JSON POST to /json/2/<model>/<method> without the
        JSON-RPC 2.0 envelope. Authentication is handled via session cookie
        (set during /web/session/authenticate login).

        Args:
            model: The Odoo model name.
            method: The method name.
            args: Positional arguments list.
            kwargs: Keyword arguments dictionary.

        Returns:
            The result of the method call.

        Raises:
            RPCError: If the response contains an error.
        """
        url = f"/json/2/{model}/{method}"
        payload: dict[str, Any] = {}
        if args:
            payload["args"] = args
        if kwargs:
            payload["kwargs"] = kwargs

        response = self._connector.proxy_http(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        result = json.loads(response.body.decode("utf-8"))
        if isinstance(result, dict) and result.get("error"):
            error_data = result["error"]
            message = error_data.get("message", str(error_data))
            raise exceptions.RPCError(message, error_data)
        return result

    def login(self, db: str, login: str = "admin", password: str = "admin") -> None:
        """Log in to the Odoo server.

        For Odoo >= 19, uses /web/session/authenticate to avoid the
        deprecated /jsonrpc endpoint. For Odoo 10-18, uses the legacy
        /jsonrpc service dispatch. For Odoo < 10, uses /web/session/authenticate.

        Args:
            db: Database name.
            login: Username (default: 'admin').
            password: Password (default: 'admin').

        Raises:
            RPCError: If login fails.
        """
        if self._use_json2:
            # Odoo 19+: use /web/session/authenticate (avoids deprecated /jsonrpc)
            data = self.json(
                "/web/session/authenticate",
                {"db": db, "login": login, "password": password},
            )
            uid = data["result"]["uid"]
            if uid:
                context = data["result"].get("user_context", {})
                context["uid"] = uid
            else:
                raise exceptions.RPCError("Wrong login ID or password")
        elif v(self.version)[0] >= 10:
            # Odoo 10-18: legacy /jsonrpc service dispatch
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
            args_to_send = [db, uid, password, "res.users", "context_get"]
            context = self.json(
                "/jsonrpc",
                {
                    "service": "object",
                    "method": "execute",
                    "args": args_to_send,
                },
            )["result"]
            context["uid"] = uid
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
                "Connected to Odoo %s using JSON-2 API. "
                "Note: DB and Report services still use legacy /jsonrpc endpoint.",
                self.version,
            )

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
            return self._json2_call(model, method, args=list(args))
        args_to_send = [
            self.env.db,
            self.env.uid,
            self._password,
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
            return self._json2_call(model, method, args=args, kwargs=kwargs)
        args_to_send = [
            self.env.db,
            self.env.uid,
            self._password,
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
            "user": self._login,
            "passwd": self._password,
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
