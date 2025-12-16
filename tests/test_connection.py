"""Tests for OdooConnection class and exceptions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import urllib.error


class TestExceptions:
    """Tests for custom exception classes."""

    def test_exception_hierarchy(self):
        """Test that exceptions have correct inheritance."""
        from odoorpc_toolbox import (
            OdooConnectionError,
            OdooConfigError,
            OdooAuthError,
        )

        # OdooConnectionError should be base exception
        assert issubclass(OdooConnectionError, Exception)

        # OdooConfigError and OdooAuthError should inherit from OdooConnectionError
        assert issubclass(OdooConfigError, OdooConnectionError)
        assert issubclass(OdooAuthError, OdooConnectionError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        from odoorpc_toolbox import (
            OdooConnectionError,
            OdooConfigError,
            OdooAuthError,
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
            OdooConnectionError,
            OdooConfigError,
            OdooAuthError,
        )

        # OdooConfigError should be catchable as OdooConnectionError
        with pytest.raises(OdooConnectionError):
            raise OdooConfigError("Config error")

        # OdooAuthError should be catchable as OdooConnectionError
        with pytest.raises(OdooConnectionError):
            raise OdooAuthError("Auth error")


class TestOdooConnectionInit:
    """Tests for OdooConnection initialization."""

    def test_file_not_found(self):
        """Test that missing config file raises OdooConfigError."""
        from odoorpc_toolbox import OdooConnection, OdooConfigError

        with pytest.raises(OdooConfigError) as exc_info:
            OdooConnection("/nonexistent/config.yaml")

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_yaml(self, invalid_config_yaml):
        """Test that invalid YAML raises OdooConfigError."""
        from odoorpc_toolbox import OdooConnection, OdooConfigError

        with pytest.raises(OdooConfigError) as exc_info:
            OdooConnection(invalid_config_yaml)

        assert "yaml" in str(exc_info.value).lower() or "parsing" in str(exc_info.value).lower()

    @patch('odoorpc_toolbox.odoo_connection.odoorpc.ODOO')
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

    @patch('odoorpc_toolbox.odoo_connection.odoorpc.ODOO')
    def test_connection_url_error(self, mock_odoo, valid_config_yaml):
        """Test that URL errors raise OdooConnectionError."""
        from odoorpc_toolbox import OdooConnection, OdooConnectionError

        mock_odoo.side_effect = urllib.error.URLError("Connection refused")

        with pytest.raises(OdooConnectionError) as exc_info:
            OdooConnection(valid_config_yaml)

        assert "connection" in str(exc_info.value).lower()

    @patch('odoorpc_toolbox.odoo_connection.odoorpc.ODOO')
    def test_auth_error(self, mock_odoo, valid_config_yaml):
        """Test that authentication errors raise OdooAuthError."""
        import odoorpc.error
        from odoorpc_toolbox import OdooConnection, OdooAuthError

        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.login.side_effect = odoorpc.error.RPCError("Invalid credentials")
        mock_odoo.return_value = mock_instance

        with pytest.raises(OdooAuthError) as exc_info:
            OdooConnection(valid_config_yaml)

        assert "auth" in str(exc_info.value).lower()


class TestOdooConnectionConfig:
    """Tests for configuration parsing."""

    @patch('odoorpc_toolbox.odoo_connection.odoorpc.ODOO')
    def test_https_url_handling(self, mock_odoo, valid_config_yaml):
        """Test that HTTPS URLs are handled correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)

        # Should have called ODOO with correct parameters
        call_args = mock_odoo.call_args
        assert call_args is not None
        # Protocol should be jsonrpc+ssl for https
        assert call_args[1]['protocol'] == 'jsonrpc+ssl'

    @patch('odoorpc_toolbox.odoo_connection.odoorpc.ODOO')
    def test_context_settings(self, mock_odoo, valid_config_yaml):
        """Test that context settings are applied correctly."""
        mock_instance = MagicMock()
        mock_instance.version = "16.0"
        mock_instance.config = {}
        mock_instance.env.context = {}
        mock_odoo.return_value = mock_instance

        from odoorpc_toolbox import OdooConnection

        conn = OdooConnection(valid_config_yaml)

        # Check that auto_commit is set
        assert mock_instance.config['auto_commit'] is True
        # Check that active_test is False (show inactive records)
        assert mock_instance.env.context['active_test'] is False
        # Check that tracking is disabled
        assert mock_instance.env.context['tracking_disable'] is True
