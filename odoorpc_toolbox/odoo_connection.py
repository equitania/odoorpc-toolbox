"""OdooRPC Connection Module.

This module provides a base connection class for interacting with Odoo servers
using the internal ODOO class (previously OdooRPC). It handles connection setup,
authentication, and basic server communication.

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

logger = logging.getLogger(__name__)


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

        try:
            odoo_con = ODOO(odoo_address, port=odoo_port, protocol=protocol)
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
