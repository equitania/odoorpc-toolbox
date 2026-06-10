"""Tests for RPC connector and JSON-RPC protocol modules."""

import pytest

from odoorpc_toolbox.rpc import PROTOCOLS, Connector, ConnectorJSONRPC, ConnectorJSONRPCSSL
from odoorpc_toolbox.rpc.errors import ConnectorError
from odoorpc_toolbox.rpc.jsonrpc import (
    ProxyHTTP,
    URLBuilder,
    encode_data,
    get_http_log_data,
    get_http_log_result,
    get_json_log_data,
)
from odoorpc_toolbox.rpc.transport import TransportResponse


class TestEncodeDecodeData:
    """Tests for encode/decode helpers."""

    def test_encode_data_string(self):
        result = encode_data("hello")
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_encode_data_unicode(self):
        result = encode_data("Stra\u00dfe")
        assert result == "Straße".encode()

    def test_encode_data_empty(self):
        result = encode_data("")
        assert result == b""


class TestGetJsonLogData:
    """Tests for sensitive data hiding in logs."""

    def test_no_sensitive_params(self):
        data = {"jsonrpc": "2.0", "params": {"db": "test"}}
        result = get_json_log_data(data)
        assert result["params"]["db"] == "test"

    def test_hides_password(self):
        data = {"jsonrpc": "2.0", "params": {"password": "secret123"}}
        result = get_json_log_data(data)
        assert result["params"]["password"] == "**********"
        # Original should not be modified
        assert data["params"]["password"] == "secret123"

    def test_no_params_key(self):
        data = {"jsonrpc": "2.0"}
        result = get_json_log_data(data)
        assert result == data

    def test_hides_password_in_common_login_args(self):
        # /jsonrpc service=common method=login uses args[2] = password.
        # Regression guard: ensure positional credentials are masked.
        data = {
            "jsonrpc": "2.0",
            "params": {
                "service": "common",
                "method": "login",
                "args": ["mydb", "admin", "SUPER_SECRET"],
            },
        }
        result = get_json_log_data(data)
        assert result["params"]["args"] == ["mydb", "admin", "**********"]
        assert data["params"]["args"][2] == "SUPER_SECRET"

    def test_hides_password_in_object_execute_kw_args(self):
        data = {
            "jsonrpc": "2.0",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": ["mydb", 2, "SUPER_SECRET", "res.partner", "search_read", [[]]],
            },
        }
        result = get_json_log_data(data)
        assert result["params"]["args"][2] == "**********"
        assert result["params"]["args"][0] == "mydb"
        assert result["params"]["args"][3] == "res.partner"
        assert data["params"]["args"][2] == "SUPER_SECRET"

    def test_hides_master_password_in_db_dump(self):
        data = {
            "jsonrpc": "2.0",
            "params": {"service": "db", "method": "dump", "args": ["MASTER_PW", "mydb", "zip"]},
        }
        result = get_json_log_data(data)
        assert result["params"]["args"] == ["**********", "mydb", "zip"]

    def test_hides_both_passwords_in_db_change_admin_password(self):
        data = {
            "jsonrpc": "2.0",
            "params": {
                "service": "db",
                "method": "change_admin_password",
                "args": ["OLD_PW", "NEW_PW"],
            },
        }
        result = get_json_log_data(data)
        assert result["params"]["args"] == ["**********", "**********"]

    def test_hides_master_and_admin_in_db_create_database(self):
        data = {
            "jsonrpc": "2.0",
            "params": {
                "service": "db",
                "method": "create_database",
                "args": ["MASTER_PW", "newdb", False, "en_US", "ADMIN_PW"],
            },
        }
        result = get_json_log_data(data)
        assert result["params"]["args"][0] == "**********"
        assert result["params"]["args"][4] == "**********"
        assert result["params"]["args"][1] == "newdb"
        assert result["params"]["args"][3] == "en_US"

    def test_db_unknown_method_defaults_to_masking_args0(self):
        # Wildcard fallback for db service: any unlisted db method still hides
        # args[0] (always the master password per Odoo's db service contract).
        data = {
            "jsonrpc": "2.0",
            "params": {"service": "db", "method": "future_method_xyz", "args": ["MASTER_PW", "data"]},
        }
        result = get_json_log_data(data)
        assert result["params"]["args"][0] == "**********"
        assert result["params"]["args"][1] == "data"

    def test_unknown_service_does_not_mask_args(self):
        data = {
            "jsonrpc": "2.0",
            "params": {"service": "report", "method": "render", "args": ["doc_id", 42]},
        }
        result = get_json_log_data(data)
        assert result["params"]["args"] == ["doc_id", 42]

    def test_no_args_no_modification(self):
        data = {"jsonrpc": "2.0", "params": {"service": "common", "method": "version", "args": []}}
        result = get_json_log_data(data)
        assert result == data

    def test_named_password_and_positional_args_both_masked(self):
        # Defensive combo: dict-level password + nested args list.
        data = {
            "jsonrpc": "2.0",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "password": "OUTER_PW",
                "args": ["mydb", 2, "INNER_PW", "res.partner", "read", [[1]]],
            },
        }
        result = get_json_log_data(data)
        assert result["params"]["password"] == "**********"
        assert result["params"]["args"][2] == "**********"


class TestGetHttpLogData:
    """Tests for HTTP body log redaction."""

    def test_empty_data(self):
        assert get_http_log_data(None) == ""
        assert get_http_log_data("") == ""

    def test_body_content_never_logged(self):
        body = '{"args": ["db", "admin", "supersecret"]}'
        result = get_http_log_data(body)
        assert "supersecret" not in result
        assert f"<{len(body)} bytes>" in result

    def test_result_hides_response_body(self):
        response = TransportResponse(status_code=200, body=b'{"session_id": "secret-token"}')
        result = get_http_log_result(response)
        assert "secret-token" not in result
        assert "status 200" in result
        assert "30 bytes" in result


class TestProxyHTTPLogging:
    """Tests that ProxyHTTP debug logs never contain request/response bodies."""

    def test_debug_log_redacts_bodies(self, caplog):
        import logging
        from unittest.mock import MagicMock

        transport = MagicMock()
        transport.request.return_value = TransportResponse(status_code=200, body=b'{"result": "session-token"}')
        proxy = ProxyHTTP("localhost", 8069, transport=transport)

        with caplog.at_level(logging.DEBUG, logger="odoorpc_toolbox.rpc.jsonrpc"):
            proxy("/json/2/res.users/login", data='{"args": ["db", "admin", "supersecret"]}')

        log_text = caplog.text
        assert "supersecret" not in log_text
        assert "session-token" not in log_text
        assert "/json/2/res.users/login" in log_text


class TestConnector:
    """Tests for the Connector base class."""

    def test_basic_connector(self):
        c = Connector("localhost", 8069, timeout=120)
        assert c.host == "localhost"
        assert c.port == 8069
        assert c.timeout == 120
        assert c.ssl is False

    def test_invalid_port_string(self):
        with pytest.raises(ConnectorError, match="invalid"):
            Connector("localhost", "not_a_number")

    def test_port_as_string_number(self):
        c = Connector("localhost", "8069")
        assert c.port == 8069

    def test_timeout_setter(self):
        c = Connector("localhost", 8069)
        c.timeout = 300
        assert c.timeout == 300


class TestProtocols:
    """Tests for PROTOCOLS dict."""

    def test_jsonrpc_protocol(self):
        assert "jsonrpc" in PROTOCOLS
        assert PROTOCOLS["jsonrpc"] is ConnectorJSONRPC

    def test_jsonrpc_ssl_protocol(self):
        assert "jsonrpc+ssl" in PROTOCOLS
        assert PROTOCOLS["jsonrpc+ssl"] is ConnectorJSONRPCSSL

    def test_only_two_protocols(self):
        assert len(PROTOCOLS) == 2


class TestURLBuilder:
    """Tests for URLBuilder dynamic URL construction."""

    def test_single_attribute(self):
        from unittest.mock import MagicMock

        proxy = MagicMock()
        builder = URLBuilder(proxy, "web")
        assert str(builder) == "web"

    def test_chained_attributes(self):
        from unittest.mock import MagicMock

        proxy = MagicMock()
        builder = URLBuilder(proxy)
        child = builder.web
        grandchild = child.session
        assert str(grandchild) == "web/session"

    def test_empty_url(self):
        from unittest.mock import MagicMock

        proxy = MagicMock()
        builder = URLBuilder(proxy)
        assert str(builder) == ""

    def test_getitem_with_slash(self):
        from unittest.mock import MagicMock

        proxy = MagicMock()
        builder = URLBuilder(proxy)
        child = builder["/web/session/"]
        assert str(child) == "web/session"
