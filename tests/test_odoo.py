"""Tests for the main ODOO class."""

from unittest.mock import MagicMock, patch

import pytest

from odoorpc_toolbox.odoo import ODOO


class TestODOOInit:
    """Tests for ODOO class initialization."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_init_default_params(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.host == "localhost"
        assert odoo.port == 8069
        assert odoo.protocol == "jsonrpc"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_init_custom_params(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("example.com", protocol="jsonrpc+ssl", port=443, version="16.0")
        assert odoo.host == "example.com"
        assert odoo.port == 443
        assert odoo.protocol == "jsonrpc+ssl"

    def test_invalid_protocol(self):
        with pytest.raises(ValueError, match="not supported"):
            ODOO("localhost", protocol="invalid")

    def test_invalid_port(self):
        with pytest.raises(ValueError, match="integer"):
            ODOO("localhost", port="not_a_number")

    def test_invalid_timeout(self):
        with pytest.raises(ValueError, match="float"):
            ODOO("localhost", timeout="not_a_float")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_version_property(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.version == "16.0"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_config_property(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.config is not None
        assert odoo.config["auto_commit"] is True
        assert odoo.config["auto_context"] is True


class TestODOOLoginLogout:
    """Tests for login and logout methods."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_env_requires_login(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        from odoorpc_toolbox.exceptions import InternalError

        odoo = ODOO("localhost", version="16.0")
        with pytest.raises(InternalError, match="Login required"):
            _ = odoo.env

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_logout_without_login(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.logout() is False

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_close_alias(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.close() is False


class TestODOOJson:
    """Tests for json method."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json_raises_on_error(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_connector.proxy_json.return_value = {"error": {"data": {"message": "Server Error"}}}
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        from odoorpc_toolbox.exceptions import RPCError

        odoo = ODOO("localhost", version="16.0")
        with pytest.raises(RPCError, match="Server Error"):
            odoo.json("/jsonrpc", {"service": "db", "method": "list", "args": []})

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json_returns_data(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_connector.proxy_json.return_value = {"result": ["db1", "db2"]}
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        result = odoo.json("/jsonrpc", {"service": "db", "method": "list", "args": []})
        assert result["result"] == ["db1", "db2"]
