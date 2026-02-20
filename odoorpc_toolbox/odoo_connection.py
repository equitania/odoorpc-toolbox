"""OdooRPC Connection Module.

This module provides a base connection class for interacting with Odoo servers
using the internal ODOO class (previously OdooRPC). It handles connection setup,
authentication, and basic server communication.

Supports extended YAML configuration for transport, retry, timeout, and cache settings.

Typical usage example:
    connection = OdooConnection('path/to/config.yaml')
    connection.odoo_connect()
"""

import logging
import urllib.error

import yaml

from odoorpc_toolbox.exceptions import (
    OdooAuthError,
    OdooConfigError,
    OdooConnectionError,
    RPCError,
)
from odoorpc_toolbox.odoo import ODOO
from odoorpc_toolbox.rpc.transport import RetryConfig, create_transport

logger = logging.getLogger(__name__)

# Default values for extended configuration sections
_TRANSPORT_DEFAULTS = {
    "backend": "auto",
    "http2": True,
    "pool_connections": 10,
}

_RETRY_DEFAULTS = {
    "max_attempts": 3,
    "backoff_factor": 0.5,
    "retry_on": [502, 503, 504],
}

_TIMEOUT_DEFAULTS = {
    "connect": 30,
    "read": 120,
}

_CACHE_DEFAULTS = {
    "maxsize": 256,
    "ttl": 3600,
}


class OdooConnection:
    """Base class for establishing and managing Odoo server connections.

    Attributes:
        odoo_address: Server URL address.
        odoo_port: Server port number.
        user: Username for authentication.
        pw: Password for authentication.
        db: Database name.
        protocol: Connection protocol (jsonrpc or jsonrpc+ssl).
        odoo_version: Odoo server version.
        odoo: ODOO connection instance.
        transport_config: Parsed transport configuration dict.
        retry_config: Parsed retry configuration dict.
        timeout_config: Parsed timeout configuration dict.
        cache_config: Parsed cache configuration dict.
    """

    def __init__(self, eq_yaml_path: str) -> None:
        """Initializes the connection using configuration from a YAML file.

        Args:
            eq_yaml_path: Path to the YAML configuration file.

        Raises:
            OdooConfigError: If the YAML configuration file is not found or malformed.
            OdooConnectionError: If the connection to the server fails.
        """
        try:
            with open(eq_yaml_path, encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
            connection_data = data["Server"]
            self.odoo_address = connection_data.get("url", "0.0.0.0")
            self.odoo_port = connection_data.get("port", 8069)
            self.user = connection_data.get("user", "admin")
            self.pw = connection_data.get("password", "dbpassword")
            self.db = connection_data.get("database", "dbname")
            self.protocol = connection_data.get("protocol", "jsonrpc")
            self.odoo_version = 0

            # Parse extended configuration sections (optional)
            self.transport_config = {**_TRANSPORT_DEFAULTS, **(data.get("transport") or {})}
            self.retry_config = {**_RETRY_DEFAULTS, **(data.get("retry") or {})}
            self.timeout_config = {**_TIMEOUT_DEFAULTS, **(data.get("timeout") or {})}
            self.cache_config = {**_CACHE_DEFAULTS, **(data.get("cache") or {})}

            # Build connection
            self.odoo = self.odoo_connect()
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {eq_yaml_path}")
            raise OdooConfigError(f"Configuration file not found: {eq_yaml_path}") from e
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise OdooConfigError(f"Error parsing YAML configuration: {e}") from e
        except urllib.error.URLError as ex:
            logger.error(f"Connection error: Please check your parameters and connection: {ex}")
            raise OdooConnectionError(f"Connection error: {ex}") from ex

    def _build_transport(self):
        """Build a Transport instance from parsed configuration.

        Returns:
            A Transport instance or None if using defaults.
        """
        backend = self.transport_config.get("backend", "auto")

        # Only build explicit transport for non-default configs
        if backend == "auto" and not any(k in (self.transport_config or {}) for k in ("http2", "pool_connections")):
            # Check if retry is configured - if so, we need transport
            if self.retry_config == _RETRY_DEFAULTS:
                return None

        retry_config = None
        if self.retry_config.get("max_attempts", 1) > 1:
            retry_on = self.retry_config.get("retry_on", _RETRY_DEFAULTS["retry_on"])
            if isinstance(retry_on, list):
                retry_on = tuple(retry_on)
            retry_config = RetryConfig(
                max_attempts=self.retry_config.get("max_attempts", _RETRY_DEFAULTS["max_attempts"]),
                backoff_factor=self.retry_config.get("backoff_factor", _RETRY_DEFAULTS["backoff_factor"]),
                retry_on=retry_on,
            )

        try:
            return create_transport(
                backend=backend,
                http2=self.transport_config.get("http2", True),
                pool_connections=self.transport_config.get("pool_connections", 10),
                retry_config=retry_config,
            )
        except ImportError:
            logger.info("httpx not available, falling back to urllib transport")
            return None

    def odoo_connect(self) -> ODOO:
        """Establishes connection to the Odoo server.

        Returns:
            ODOO: Connected Odoo instance.

        Raises:
            OdooConnectionError: If connection to server fails.
            OdooAuthError: If authentication fails.
        """
        odoo_address = self.odoo_address
        protocol = self.protocol
        odoo_port = self.odoo_port
        if odoo_address.startswith("https"):
            odoo_address = odoo_address.replace("https:", "")
            protocol = "jsonrpc+ssl"
            if odoo_port <= 0:
                odoo_port = 443
        elif odoo_address.startswith("http:"):
            odoo_address = odoo_address.replace("http:", "")
            protocol = "jsonrpc"

        while odoo_address and odoo_address.startswith("/"):
            odoo_address = odoo_address[1:]

        while odoo_address and odoo_address.endswith("/"):
            odoo_address = odoo_address[:-1]

        while odoo_address and odoo_address.endswith("\\"):
            odoo_address = odoo_address[:-1]

        # Build transport from config
        transport = self._build_transport()
        timeout = self.timeout_config.get("read", _TIMEOUT_DEFAULTS["read"])

        try:
            odoo_con = ODOO(odoo_address, port=odoo_port, protocol=protocol, timeout=timeout, transport=transport)
            self.odoo_version = int(odoo_con.version.split(".")[0])
            odoo_con.login(self.db, self.user, self.pw)

            odoo_con.config["auto_commit"] = True  # No need for manual commits
            odoo_con.env.context["active_test"] = False  # Show inactive articles
            odoo_con.env.context["tracking_disable"] = True
            return odoo_con
        except urllib.error.URLError as ex:
            logger.error(f"Connection error: Please check your parameters and connection: {ex}")
            raise OdooConnectionError(f"Connection error: {ex}") from ex
        except RPCError as e:
            logger.error(f"Authentication error: {e}")
            raise OdooAuthError(f"Authentication error: {e}") from e
