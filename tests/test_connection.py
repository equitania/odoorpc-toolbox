"""Tests for OdooConnection class and exceptions."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest


class TestExceptions:
    """Tests for custom exception classes."""

    def test_exception_hierarchy(self):
        """Test that exceptions have correct inheritance."""
        from odoorpc_toolbox import (
            OdooAuthError,
            OdooConfigError,
            OdooConnectionError,
        )

        # OdooConnectionError should be base exception
        assert issubclass(OdooConnectionError, Exception)

        # OdooConfigError and OdooAuthError should inherit from OdooConnectionError
        assert issubclass(OdooConfigError, OdooConnectionError)
        assert issubclass(OdooAuthError, OdooConnectionError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        from odoorpc_toolbox import (
            OdooAuthError,
            OdooConfigError,
            OdooConnectionError,
        )

        exc1 = OdooConnectionError("Connection failed")
        assert str(exc1) == "Connection failed"

        exc2 = OdooConfigError("Config error")
        assert str(exc2) == "Config error"

        exc3 = OdooAuthError("Auth error")
        assert str(exc3) == "Auth error"

    def test_exception_catching(self):
        """Test that exceptions can be caught by parent class."""
        from odoorpc_toolbox import (
            OdooAuthError,
            OdooConfigError,
            OdooConnectionError,
        )

        # OdooConfigError should be catchable as OdooConnectionError
        with pytest.raises(OdooConnectionError):
            raise OdooConfigError("Config error")

        # OdooAuthError should be catchable as OdooConnectionError
        with pytest.raises(OdooConnectionError):
            raise OdooAuthError("Auth error")

    def test_rpc_error_hierarchy(self):
        """Test that RPC exceptions have correct inheritance."""
        from odoorpc_toolbox import Error, InternalError, RPCError

        assert issubclass(RPCError, Error)
        assert issubclass(InternalError, Error)
        assert issubclass(Error, Exception)

    def test_rpc_error_info_attribute(self):
        """Test that RPCError stores error info."""
        from odoorpc_toolbox import RPCError

        error_info = {"message": "Access Denied", "code": 403}
        exc = RPCError("Access Denied", info=error_info)
        assert str(exc) == "Access Denied"
        assert exc.info == error_info


class TestOdooConnectionInit:
    """Tests for OdooConnection initialization."""

    def test_file_not_found(self):
        """Test that missing config file raises OdooConfigError."""
        from odoorpc_toolbox import OdooConfigError, OdooConnection

        with pytest.raises(OdooConfigError) as exc_info:
            OdooConnection("/nonexistent/config.yaml")

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_yaml(self, invalid_config_yaml):
        """Test that invalid YAML raises OdooConfigError."""
        from odoorpc_toolbox import OdooConfigError, OdooConnection

        with pytest.raises(OdooConfigError) as exc_info:
            OdooConnection(invalid_config_yaml)

        assert "yaml" in str(exc_info.value).lower() or "parsing" in str(exc_info.value).lower()

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_successful_connection(self, mock_odoo, valid_config_yaml):
        """Test successful connection with valid config."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)

        assert conn.odoo is not None
        assert conn.odoo_version == 16
        mock_instance.login.assert_called_once()

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_connection_url_error(self, mock_odoo, valid_config_yaml):
        """Test that URL errors raise OdooConnectionError."""
        from odoorpc_toolbox import OdooConnection, OdooConnectionError

        mock_odoo.side_effect = urllib.error.URLError("Connection refused")

        with pytest.raises(OdooConnectionError) as exc_info:
            OdooConnection(valid_config_yaml)

        assert "connection" in str(exc_info.value).lower()

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_auth_error(self, mock_odoo, valid_config_yaml):
        """Test that authentication errors raise OdooAuthError."""
        from odoorpc_toolbox import OdooAuthError, OdooConnection
        from odoorpc_toolbox.exceptions import RPCError

        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.login.side_effect = RPCError("Invalid credentials")
        mock_odoo.return_value = mock_instance

        with pytest.raises(OdooAuthError) as exc_info:
            OdooConnection(valid_config_yaml)

        assert "auth" in str(exc_info.value).lower()


class TestOdooConnectionConfig:
    """Tests for configuration parsing."""

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_https_url_handling(self, mock_odoo, valid_config_yaml):
        """Test that HTTPS URLs are handled correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        OdooConnection(valid_config_yaml)

        # Should have called ODOO with correct parameters
        call_args = mock_odoo.call_args
        assert call_args is not None
        # Protocol should be jsonrpc+ssl for https
        assert call_args[1]["protocol"] == "jsonrpc+ssl"

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_context_settings(self, mock_odoo, valid_config_yaml):
        """Test that context settings are applied correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        OdooConnection(valid_config_yaml)

        # Check that auto_commit is set
        assert mock_instance.config["auto_commit"] is True
        # Check that active_test is False (show inactive records)
        assert mock_instance.env.context["active_test"] is False
        # Check that tracking is disabled
        assert mock_instance.env.context["tracking_disable"] is True


class TestExtendedYAMLConfig:
    """Tests for extended YAML configuration sections (transport, retry, timeout, cache)."""

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_default_transport_config(self, mock_odoo, valid_config_yaml):
        """Test that missing transport section uses defaults."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)
        assert conn.transport_config["backend"] == "auto"
        assert conn.transport_config["http2"] is True
        assert conn.transport_config["pool_connections"] == 10

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_default_retry_config(self, mock_odoo, valid_config_yaml):
        """Test that missing retry section uses defaults."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)
        assert conn.retry_config["max_attempts"] == 3
        assert conn.retry_config["backoff_factor"] == 0.5
        assert conn.retry_config["retry_on"] == [502, 503, 504]

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_default_timeout_config(self, mock_odoo, valid_config_yaml):
        """Test that missing timeout section uses defaults."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)
        assert conn.timeout_config["connect"] == 30
        assert conn.timeout_config["read"] == 120

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_default_cache_config(self, mock_odoo, valid_config_yaml):
        """Test that missing cache section uses defaults."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)
        assert conn.cache_config["maxsize"] == 256
        assert conn.cache_config["ttl"] == 3600

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_custom_transport_config(self, mock_odoo, extended_config_yaml):
        """Test that custom transport section is parsed correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(extended_config_yaml)
        assert conn.transport_config["backend"] == "urllib"
        assert conn.transport_config["http2"] is False
        assert conn.transport_config["pool_connections"] == 5

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_custom_retry_config(self, mock_odoo, extended_config_yaml):
        """Test that custom retry section is parsed correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(extended_config_yaml)
        assert conn.retry_config["max_attempts"] == 5
        assert conn.retry_config["backoff_factor"] == 1.0
        assert conn.retry_config["retry_on"] == [500, 502, 503]

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_custom_timeout_config(self, mock_odoo, extended_config_yaml):
        """Test that custom timeout section is parsed correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(extended_config_yaml)
        assert conn.timeout_config["connect"] == 10
        assert conn.timeout_config["read"] == 60

    @patch("odoorpc_toolbox.odoo_connection.ODOO")
    def test_timeout_passed_to_odoo(self, mock_odoo, extended_config_yaml):
        """Test that read timeout from config is passed to ODOO constructor."""
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        OdooConnection(extended_config_yaml)
        call_args = mock_odoo.call_args
        assert call_args[1]["timeout"] == 60
