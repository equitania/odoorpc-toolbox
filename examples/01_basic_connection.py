#!/usr/bin/env python3
"""Basic connection example for odoorpc-toolbox.

This example demonstrates how to establish a connection to an Odoo server
and handle potential errors.

Usage:
    python 01_basic_connection.py
"""

from odoorpc_toolbox import (
    EqOdooConnection,
    OdooAuthError,
    OdooConfigError,
    OdooConnectionError,
)


def main():
    """Demonstrate basic connection to Odoo server."""

    # Path to your YAML configuration file
    config_path = "odoo_config.yaml"

    try:
        # Establish connection
        print(f"Connecting to Odoo using config: {config_path}")
        conn = EqOdooConnection(config_path)

        # Connection successful
        print(f"Successfully connected to Odoo version {conn.odoo_version}")
        print(f"Database: {conn.db}")
        print(f"User: {conn.user}")

        # Test the connection by getting database list
        # (This won't work if list_db is disabled on the server)
        try:
            databases = conn.odoo.db.list()
            print(f"Available databases: {databases}")
        except Exception:
            print("Database listing not available (list_db may be disabled)")

    except OdooConfigError as e:
        print(f"Configuration error: {e}")
        print("Please check your YAML configuration file.")

    except OdooAuthError as e:
        print(f"Authentication error: {e}")
        print("Please check your username and password.")

    except OdooConnectionError as e:
        print(f"Connection error: {e}")
        print("Please check the server URL and port.")


if __name__ == "__main__":
    main()
