"""Tests for the main ODOO class."""

import json
from unittest.mock import MagicMock, patch

import pytest

from odoorpc_toolbox.odoo import ODOO
from odoorpc_toolbox.rpc.transport import TransportResponse


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


class TestODOOTransport:
    """Tests for transport parameter support."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_transport_parameter_passed(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        mock_transport = MagicMock()
        odoo = ODOO("localhost", version="16.0", transport=mock_transport)
        assert odoo is not None
        # Verify transport was passed to PROTOCOLS constructor
        constructor_call = mock_protocols.__getitem__.return_value.call_args
        assert constructor_call[1]["transport"] is mock_transport

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_opener_parameter_still_works(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        mock_opener = MagicMock()
        odoo = ODOO("localhost", version="16.0", opener=mock_opener)
        assert odoo is not None
        constructor_call = mock_protocols.__getitem__.return_value.call_args
        assert constructor_call[1]["opener"] is mock_opener

    def test_opener_and_transport_raises(self):
        with pytest.raises(ValueError, match="Cannot specify both"):
            ODOO("localhost", opener=MagicMock(), transport=MagicMock())

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_metrics_property_none_without_metrics_transport(self, mock_protocols):
        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        mock_connector._transport = MagicMock(spec=[])  # No metrics attribute
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.metrics is None

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_metrics_property_with_metrics_transport(self, mock_protocols):
        from odoorpc_toolbox.rpc.metrics import RequestMetrics

        mock_connector = MagicMock()
        mock_connector.version = "16.0"
        metrics = RequestMetrics()
        mock_connector._transport.metrics = metrics
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))

        odoo = ODOO("localhost", version="16.0")
        assert odoo.metrics is metrics


class TestODOOJson2API:
    """Tests for Odoo 19+ JSON-2 API support."""

    def _make_odoo(self, mock_protocols, version="19.0"):
        """Helper to create an ODOO instance with a mock connector."""
        mock_connector = MagicMock()
        mock_connector.version = version
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))
        return ODOO("localhost", version=version), mock_connector

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_true_for_v19(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "19.0")
        assert odoo._use_json2 is True

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_true_for_v20(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "20.0")
        assert odoo._use_json2 is True

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_false_for_v18(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "18.0")
        assert odoo._use_json2 is False

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_false_for_v16(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "16.0")
        assert odoo._use_json2 is False

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_uses_web_session(self, mock_protocols):
        """Odoo 19+ login must use /web/session/authenticate, not /jsonrpc."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {
            "result": {
                "uid": 2,
                "user_context": {"lang": "en_US", "tz": "Europe/Berlin"},
            }
        }
        odoo.login("testdb", "admin", "admin")
        # Verify /web/session/authenticate was called (not /jsonrpc)
        call_args = mock_connector.proxy_json.call_args
        assert call_args[0][0] == "/web/session/authenticate"
        assert call_args[0][1] == {"db": "testdb", "login": "admin", "password": "admin"}

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v18_uses_jsonrpc(self, mock_protocols):
        """Odoo 18 login must use /jsonrpc service dispatch."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "18.0")
        # First call: login, second call: context_get
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "admin")
        first_call = mock_connector.proxy_json.call_args_list[0]
        assert first_call[0][0] == "/jsonrpc"
        assert first_call[0][1]["service"] == "common"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_failed_raises(self, mock_protocols):
        """Odoo 19+ login with invalid credentials raises RPCError."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": {"uid": False, "user_context": {}}}
        with pytest.raises(RPCError, match="Wrong login"):
            odoo.login("testdb", "wrong", "wrong")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_kw_v19_uses_json2(self, mock_protocols):
        """Odoo 19+ execute_kw must use JSON-2 API via _json2_call."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        # Login first
        mock_connector.proxy_json.return_value = {"result": {"uid": 2, "user_context": {"lang": "en_US"}}}
        odoo.login("testdb", "admin", "admin")

        # Setup JSON-2 response via proxy_http
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps([1, 2, 3]).encode("utf-8"),
        )

        result = odoo.execute_kw("res.partner", "search", [[]])
        assert result == [1, 2, 3]

        # Verify /json/2/ endpoint was called via proxy_http
        http_call = mock_connector.proxy_http.call_args
        assert http_call[0][0] == "/json/2/res.partner/search"
        payload = json.loads(http_call[1]["data"])
        assert payload["args"] == [[]]

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_kw_v18_uses_jsonrpc(self, mock_protocols):
        """Odoo 18 execute_kw must use legacy /jsonrpc."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "18.0")
        # Login
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "admin")

        # execute_kw call
        mock_connector.proxy_json.side_effect = None
        mock_connector.proxy_json.return_value = {"result": [1, 2, 3]}
        result = odoo.execute_kw("res.partner", "search", [[]])
        assert result == [1, 2, 3]

        # Verify /jsonrpc was called
        last_call = mock_connector.proxy_json.call_args
        assert last_call[0][0] == "/jsonrpc"
        assert last_call[0][1]["service"] == "object"
        assert last_call[0][1]["method"] == "execute_kw"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_v19_uses_json2(self, mock_protocols):
        """Odoo 19+ execute() must use JSON-2 API."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": {"uid": 2, "user_context": {"lang": "en_US"}}}
        odoo.login("testdb", "admin", "admin")

        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps({"name": "Test"}).encode("utf-8"),
        )
        result = odoo.execute("res.partner", "read", [1], ["name"])
        assert result == {"name": "Test"}

        http_call = mock_connector.proxy_http.call_args
        assert http_call[0][0] == "/json/2/res.partner/read"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_format(self, mock_protocols):
        """_json2_call must send plain JSON without JSON-RPC 2.0 envelope."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": {"uid": 2, "user_context": {}}}
        odoo.login("testdb", "admin", "admin")

        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps([42]).encode("utf-8"),
        )
        odoo._json2_call("res.partner", "search", args=[[("name", "=", "Test")]], kwargs={"limit": 1})

        http_call = mock_connector.proxy_http.call_args
        payload = json.loads(http_call[1]["data"])
        # Must NOT have JSON-RPC 2.0 envelope fields
        assert "jsonrpc" not in payload
        assert "method" not in payload
        assert "id" not in payload
        # Must have args and kwargs
        assert payload["args"] == [[["name", "=", "Test"]]]
        assert payload["kwargs"] == {"limit": 1}
        # Content-Type must be application/json
        assert http_call[1]["headers"]["Content-Type"] == "application/json"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_error_handling(self, mock_protocols):
        """_json2_call must raise RPCError on error response."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": {"uid": 2, "user_context": {}}}
        odoo.login("testdb", "admin", "admin")

        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps({"error": {"message": "Access Denied"}}).encode("utf-8"),
        )
        with pytest.raises(RPCError, match="Access Denied"):
            odoo._json2_call("res.partner", "search", args=[[]])

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_empty_payload(self, mock_protocols):
        """_json2_call with no args/kwargs sends empty JSON object."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": {"uid": 2, "user_context": {}}}
        odoo.login("testdb", "admin", "admin")

        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps([]).encode("utf-8"),
        )
        odoo._json2_call("res.partner", "search")

        http_call = mock_connector.proxy_http.call_args
        payload = json.loads(http_call[1]["data"])
        assert payload == {}

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_db_service_uses_jsonrpc_even_on_v19(self, mock_protocols):
        """DB service must still use /jsonrpc even on Odoo 19+."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": ["db1", "db2"]}

        result = odoo.db.list()
        assert result == ["db1", "db2"]

        call_args = mock_connector.proxy_json.call_args
        assert call_args[0][0] == "/jsonrpc"
        assert call_args[0][1]["service"] == "db"
