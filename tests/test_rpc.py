"""Tests for RPC connector and JSON-RPC protocol modules."""

import pytest

from odoorpc_toolbox.rpc import PROTOCOLS, Connector, ConnectorJSONRPC, ConnectorJSONRPCSSL
from odoorpc_toolbox.rpc.errors import ConnectorError
from odoorpc_toolbox.rpc.jsonrpc import (
    URLBuilder,
    encode_data,
    get_json_log_data,
)


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
