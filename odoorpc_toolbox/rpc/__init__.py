"""RPC connector classes for communicating with Odoo servers.

Provides Connector classes using the JSON-RPC protocol (HTTP and HTTPS).
Web controllers of Odoo expose two kinds of methods: json and http.
These methods can be accessed from the connectors of this module.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from odoorpc_toolbox.rpc import errors, jsonrpc
from odoorpc_toolbox.rpc.transport import UrllibTransport


class Connector:
    """Connector base class defining the interface used to interact with a server."""

    def __init__(
        self,
        host: str,
        port: int = 8069,
        timeout: float = 120,
        version: str | None = None,
    ) -> None:
        self.host = host
        try:
            int(port)
        except (ValueError, TypeError) as exc:
            raise errors.ConnectorError(f"The port '{port}' is invalid. An integer is required.") from exc
        self.port = int(port)
        self._timeout = timeout
        self.version = version

    @property
    def ssl(self) -> bool:
        """Return True if SSL is activated."""
        return False

    @property
    def timeout(self) -> float:
        """Return the timeout."""
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: float) -> None:
        """Set the timeout."""
        self._timeout = timeout


class ConnectorJSONRPC(Connector):
    """Connector class using the JSON-RPC protocol.

    Accepts either a Transport instance or a legacy urllib opener.
    Both JSON and HTTP proxies share the same Transport for consistent
    cookie/session state.

    Example:
        >>> cnt = ConnectorJSONRPC('localhost', port=8069)
        >>> cnt.proxy_json.web.session.authenticate(db='mydb', login='admin', password='admin')
    """

    def __init__(
        self,
        host: str,
        port: int = 8069,
        timeout: float = 120,
        version: str | None = None,
        deserialize: bool = True,
        opener=None,
        transport=None,
    ) -> None:
        super().__init__(host, port, timeout, version)
        self.deserialize = deserialize

        # Create or wrap transport - one instance shared between JSON and HTTP proxies
        if transport is not None:
            self._transport = transport
        elif opener is not None:
            self._transport = UrllibTransport(opener=opener)
        else:
            self._transport = UrllibTransport()

        self._proxy_json, self._proxy_http = self._get_proxies()

    def _get_proxies(self) -> tuple[jsonrpc.ProxyJSON, jsonrpc.ProxyHTTP]:
        """Return ProxyJSON and ProxyHTTP instances sharing the same transport."""
        proxy_json = jsonrpc.ProxyJSON(
            self.host,
            self.port,
            self._timeout,
            ssl=self.ssl,
            deserialize=self.deserialize,
            transport=self._transport,
        )
        proxy_http = jsonrpc.ProxyHTTP(
            self.host,
            self.port,
            self._timeout,
            ssl=self.ssl,
            transport=self._transport,
        )
        # Detect the server version
        if self.version is None:
            result = proxy_json("/web/webclient/version_info")["result"]
            if "server_version" in result:
                self.version = result["server_version"]
        return proxy_json, proxy_http

    @property
    def proxy_json(self) -> jsonrpc.ProxyJSON:
        """Return the JSON proxy."""
        return self._proxy_json

    @property
    def proxy_http(self) -> jsonrpc.ProxyHTTP:
        """Return the HTTP proxy."""
        return self._proxy_http

    @property
    def timeout(self) -> float:
        """Return the timeout."""
        return self._proxy_json._timeout

    @timeout.setter
    def timeout(self, timeout: float) -> None:
        """Set the timeout."""
        self._proxy_json._timeout = timeout
        self._proxy_http._timeout = timeout


class ConnectorJSONRPCSSL(ConnectorJSONRPC):
    """Connector class using the JSON-RPC protocol over SSL.

    Example:
        >>> cnt = ConnectorJSONRPCSSL('localhost', port=443)
    """

    def __init__(
        self,
        host: str,
        port: int = 8069,
        timeout: float = 120,
        version: str | None = None,
        deserialize: bool = True,
        opener=None,
        transport=None,
    ) -> None:
        super().__init__(host, port, timeout, version, opener=opener, transport=transport)
        self._proxy_json, self._proxy_http = self._get_proxies()

    @property
    def ssl(self) -> bool:
        return True


PROTOCOLS: dict[str, type[ConnectorJSONRPC]] = {
    "jsonrpc": ConnectorJSONRPC,
    "jsonrpc+ssl": ConnectorJSONRPCSSL,
}
