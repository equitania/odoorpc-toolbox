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
    """Tests for the JSON-2 API (Odoo 19+): Bearer auth, routing, error mapping.

    JSON-2 is active for Odoo >= 19. Login bootstraps the user context via
    res.users/context_get; execute/execute_kw route through /json/2/ with
    named parameters and fall back to legacy /jsonrpc when positional
    arguments cannot be mapped.
    """

    def _make_odoo(self, mock_protocols, version="19.0"):
        """Helper to create an ODOO instance with a mock connector."""
        mock_connector = MagicMock()
        mock_connector.version = version
        mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))
        return ODOO("localhost", version=version), mock_connector

    def _login_v19(self, odoo, mock_connector, api_key="test_api_key", uid=2):
        """Perform a JSON-2 login against the mocked connector."""
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps({"lang": "en_US", "tz": "UTC", "uid": uid}).encode("utf-8"),
        )
        odoo.login("testdb", "admin", "admin", api_key=api_key)

    def _set_json2_response(self, mock_connector, result):
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={},
            body=json.dumps(result).encode("utf-8"),
        )

    # ---- Feature flag ----

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_false_before_login_v19(self, mock_protocols):
        """JSON-2 routing requires an API key - inactive before login."""
        odoo, _ = self._make_odoo(mock_protocols, "19.0")
        assert odoo._use_json2 is False

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_enabled_after_api_key_login_v19(self, mock_protocols):
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)
        assert odoo._use_json2 is True

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_enabled_after_api_key_login_v20(self, mock_protocols):
        odoo, mock_connector = self._make_odoo(mock_protocols, "20.0")
        self._login_v19(odoo, mock_connector)
        assert odoo._use_json2 is True

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_false_for_v18(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "18.0")
        assert odoo._use_json2 is False

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_use_json2_false_for_v16(self, mock_protocols):
        odoo, _ = self._make_odoo(mock_protocols, "16.0")
        assert odoo._use_json2 is False

    # ---- Login (JSON-2 bootstrap) ----

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_uses_json2_bootstrap(self, mock_protocols):
        """Odoo 19+ login bootstraps via /json/2/res.users/context_get."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        mock_connector.proxy_json.assert_not_called()
        http_call = mock_connector.proxy_http.call_args
        assert http_call[0][0] == "/json/2/res.users/context_get"
        assert odoo.env.uid == 2

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_sends_bearer_and_database_headers(self, mock_protocols):
        """Bootstrap call carries lowercase bearer scheme and X-Odoo-Database."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector, api_key="secret_key")

        headers = mock_connector.proxy_http.call_args[1]["headers"]
        assert headers["Authorization"] == "bearer secret_key"
        assert headers["X-Odoo-Database"] == "testdb"
        assert headers["Content-Type"].startswith("application/json")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_uid_fallback_via_search(self, mock_protocols):
        """When context_get exposes no uid, login resolves it via res.users search."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.side_effect = [
            TransportResponse(status_code=200, headers={}, body=json.dumps({"lang": "en_US"}).encode("utf-8")),
            TransportResponse(status_code=200, headers={}, body=json.dumps([7]).encode("utf-8")),
        ]
        odoo.login("testdb", "bot_user", api_key="bot_key")

        assert odoo.env.uid == 7
        search_call = mock_connector.proxy_http.call_args_list[1]
        assert search_call[0][0] == "/json/2/res.users/search"
        payload = json.loads(search_call[1]["data"])
        assert payload["domain"] == [["login", "=", "bot_user"]]

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_invalid_key_raises(self, mock_protocols):
        """HTTP 401 from the bootstrap call raises RPCError with the server message."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=401,
            headers={},
            body=json.dumps(
                {
                    "name": "werkzeug.exceptions.Unauthorized",
                    "message": "Invalid apikey",
                    "arguments": ["Invalid apikey", 401],
                    "context": {},
                }
            ).encode("utf-8"),
        )
        with pytest.raises(RPCError, match="Invalid apikey"):
            odoo.login("testdb", "admin", api_key="bad_key")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_password_used_as_api_key(self, mock_protocols):
        """Without api_key, the password is used as Bearer token (backward compat)."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._set_json2_response(mock_connector, {"lang": "en_US", "uid": 2})
        odoo.login("testdb", "admin", "key_in_password_field")

        headers = mock_connector.proxy_http.call_args[1]["headers"]
        assert headers["Authorization"] == "bearer key_in_password_field"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_api_key_takes_precedence(self, mock_protocols):
        """api_key wins over password for the Bearer token."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._set_json2_response(mock_connector, {"lang": "en_US", "uid": 2})
        odoo.login("testdb", "admin", password="some_password", api_key="real_key")

        headers = mock_connector.proxy_http.call_args[1]["headers"]
        assert headers["Authorization"] == "bearer real_key"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_real_password_falls_back_to_jsonrpc(self, mock_protocols):
        """A real password (rejected as Bearer token with 401) falls back to legacy login.

        Regression test: before this fallback, password users who worked on
        v19 via /jsonrpc were broken by the JSON-2 activation.
        """
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        # JSON-2 bootstrap rejects the password as API key
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=401,
            headers={},
            body=json.dumps({"name": "x", "message": "Invalid apikey", "arguments": []}).encode("utf-8"),
        )
        # Legacy /jsonrpc login succeeds
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "admin")

        assert odoo.env.uid == 2
        assert odoo._api_key is None
        assert odoo._use_json2 is False
        first_legacy = mock_connector.proxy_json.call_args_list[0]
        assert first_legacy[0][0] == "/jsonrpc"
        assert first_legacy[0][1]["service"] == "common"

        # Subsequent execute_kw stays on legacy /jsonrpc with the password
        mock_connector.proxy_json.side_effect = None
        mock_connector.proxy_json.return_value = {"result": [1]}
        assert odoo.execute_kw("res.partner", "search", [[]]) == [1]
        last_call = mock_connector.proxy_json.call_args
        assert last_call[0][0] == "/jsonrpc"
        assert last_call[0][1]["args"][2] == "admin"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v19_explicit_bad_api_key_does_not_fall_back(self, mock_protocols):
        """An explicitly given invalid api_key raises - no silent password fallback."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=401,
            headers={},
            body=json.dumps({"name": "x", "message": "Invalid apikey", "arguments": []}).encode("utf-8"),
        )
        with pytest.raises(RPCError, match="Invalid apikey"):
            odoo.login("testdb", "admin", "admin", api_key="explicit_bad_key")
        mock_connector.proxy_json.assert_not_called()

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v18_uses_jsonrpc(self, mock_protocols):
        """Odoo 18 login must use /jsonrpc service dispatch."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "admin")
        first_call = mock_connector.proxy_json.call_args_list[0]
        assert first_call[0][0] == "/jsonrpc"
        assert first_call[0][1]["service"] == "common"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_login_v18_api_key_used_as_password_substitute(self, mock_protocols):
        """On Odoo 10-18 an explicit api_key is sent in the password slot."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "ignored_password", api_key="v18_key")

        first_call = mock_connector.proxy_json.call_args_list[0]
        assert first_call[0][1]["args"] == ["testdb", "admin", "v18_key"]
        assert odoo._use_json2 is False  # version < 19 regardless of key

        # Subsequent execute_kw also uses the api_key in the password slot
        mock_connector.proxy_json.side_effect = None
        mock_connector.proxy_json.return_value = {"result": [1]}
        odoo.execute_kw("res.partner", "search", [[]])
        assert mock_connector.proxy_json.call_args[0][1]["args"][2] == "v18_key"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_logout_resets_api_key(self, mock_protocols):
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)
        assert odoo._api_key == "test_api_key"
        odoo.logout()
        assert odoo._api_key is None

    # ---- execute / execute_kw routing ----

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_kw_v19_uses_json2(self, mock_protocols):
        """Odoo 19+ execute_kw routes through /json/2/ with named parameters."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        self._set_json2_response(mock_connector, [1, 2, 3])
        result = odoo.execute_kw("res.partner", "search", [[]])
        assert result == [1, 2, 3]

        http_call = mock_connector.proxy_http.call_args
        assert http_call[0][0] == "/json/2/res.partner/search"
        payload = json.loads(http_call[1]["data"])
        assert payload == {"domain": []}

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_kw_v18_uses_jsonrpc(self, mock_protocols):
        """Odoo 18 execute_kw must use legacy /jsonrpc."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.side_effect = [
            {"result": 2},
            {"result": {"lang": "en_US"}},
        ]
        odoo.login("testdb", "admin", "admin")

        mock_connector.proxy_json.side_effect = None
        mock_connector.proxy_json.return_value = {"result": [1, 2, 3]}
        result = odoo.execute_kw("res.partner", "search", [[]])
        assert result == [1, 2, 3]

        last_call = mock_connector.proxy_json.call_args
        assert last_call[0][0] == "/jsonrpc"
        assert last_call[0][1]["service"] == "object"
        assert last_call[0][1]["method"] == "execute_kw"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_v19_maps_positional_args(self, mock_protocols):
        """execute() on v19 maps known ORM method args to JSON-2 named params."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        self._set_json2_response(mock_connector, [{"id": 1, "name": "Test"}])
        result = odoo.execute("res.partner", "read", [1], ["name"])
        assert result == [{"id": 1, "name": "Test"}]

        http_call = mock_connector.proxy_http.call_args
        assert http_call[0][0] == "/json/2/res.partner/read"
        payload = json.loads(http_call[1]["data"])
        assert payload == {"ids": [1], "fields": ["name"]}

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_execute_kw_v19_unmappable_falls_back_to_jsonrpc(self, mock_protocols):
        """Unknown method with positional args falls back to legacy /jsonrpc."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector, api_key="fallback_key")

        mock_connector.proxy_json.return_value = {"result": True}
        with pytest.warns(DeprecationWarning, match="Odoo 22"):
            result = odoo.execute_kw("res.partner", "custom_method", [1, 2, 3])
        assert result is True

        last_call = mock_connector.proxy_json.call_args
        assert last_call[0][0] == "/jsonrpc"
        # The API key is used in the password slot of the legacy call
        assert last_call[0][1]["args"][2] == "fallback_key"

    # ---- _json2_call ----

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_format(self, mock_protocols):
        """_json2_call must send a flat JSON body without any envelope."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        self._set_json2_response(mock_connector, [42])
        odoo._json2_call("res.partner", "search", kwargs={"domain": [("name", "=", "Test")], "limit": 1})

        http_call = mock_connector.proxy_http.call_args
        payload = json.loads(http_call[1]["data"])
        # Must NOT have JSON-RPC 2.0 envelope fields or args/kwargs wrappers
        assert "jsonrpc" not in payload
        assert "method" not in payload
        assert "id" not in payload
        assert "args" not in payload
        assert "kwargs" not in payload
        # Named parameters live at the top level of the body
        assert payload["domain"] == [["name", "=", "Test"]]
        assert payload["limit"] == 1
        assert http_call[1]["headers"]["Content-Type"].startswith("application/json")
        assert http_call[1]["headers"]["Authorization"].startswith("bearer ")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_http_error_mapping(self, mock_protocols):
        """HTTP 4xx/5xx responses raise RPCError with status_code in info."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        for status, message in [(401, "Invalid apikey"), (403, "Forbidden"), (500, "Server Error")]:
            mock_connector.proxy_http.return_value = TransportResponse(
                status_code=status,
                headers={},
                body=json.dumps({"name": "x", "message": message, "arguments": [message]}).encode("utf-8"),
            )
            with pytest.raises(RPCError, match=message) as exc_info:
                odoo._json2_call("res.partner", "search", kwargs={"domain": []})
            assert exc_info.value.info["status_code"] == status

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_non_json_error_body(self, mock_protocols):
        """Non-JSON error bodies (e.g. HTML proxy pages) are surfaced as text."""
        from odoorpc_toolbox.exceptions import RPCError

        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=502,
            headers={},
            body=b"<html>Bad Gateway</html>",
        )
        with pytest.raises(RPCError, match="Bad Gateway"):
            odoo._json2_call("res.partner", "search", kwargs={})

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_empty_payload(self, mock_protocols):
        """_json2_call with no kwargs sends an empty JSON object."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        self._set_json2_response(mock_connector, [])
        odoo._json2_call("res.partner", "search")

        http_call = mock_connector.proxy_http.call_args
        payload = json.loads(http_call[1]["data"])
        assert payload == {}

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_without_api_key_raises(self, mock_protocols):
        """_json2_call without a configured API key raises InternalError."""
        from odoorpc_toolbox.exceptions import InternalError

        odoo, _ = self._make_odoo(mock_protocols, "19.0")
        with pytest.raises(InternalError, match="API key"):
            odoo._json2_call("res.partner", "search", kwargs={})

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_json2_call_returns_direct_result(self, mock_protocols):
        """JSON-2 returns the direct value - no {"result": ...} unwrapping."""
        odoo, mock_connector = self._make_odoo(mock_protocols, "19.0")
        self._login_v19(odoo, mock_connector)

        # A method may legitimately return a dict containing an "error" key
        self._set_json2_response(mock_connector, {"error": "this is data, not an error"})
        result = odoo._json2_call("res.partner", "some_method", kwargs={})
        assert result == {"error": "this is data, not an error"}


class TestMapArgsToJson2:
    """Tests for the positional-to-named parameter mapping."""

    def test_no_args_returns_kwargs(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        assert _map_args_to_json2("anything", [], {"limit": 5}) == {"limit": 5}

    def test_known_model_method(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        result = _map_args_to_json2("search_read", [[("x", "=", 1)], ["name"]], {"limit": 10})
        assert result == {"domain": [("x", "=", 1)], "fields": ["name"], "limit": 10}

    def test_known_recordset_method(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        result = _map_args_to_json2("write", [[1, 2], {"name": "X"}], {})
        assert result == {"ids": [1, 2], "vals": {"name": "X"}}

    def test_unknown_method_returns_none(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        assert _map_args_to_json2("custom_method", [1], {}) is None

    def test_too_many_args_returns_none(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        assert _map_args_to_json2("unlink", [[1], "extra"], {}) is None

    def test_positional_and_named_overlap_returns_none(self):
        from odoorpc_toolbox.odoo import _map_args_to_json2

        assert _map_args_to_json2("search", [[]], {"domain": []}) is None


class TestNormalizeJson2Result:
    """create() return-shape normalization (legacy compat)."""

    def test_create_with_dict_input_returns_single_id(self):
        from odoorpc_toolbox.odoo import _normalize_json2_result

        assert _normalize_json2_result("create", [{"name": "X"}], {}, [42]) == 42

    def test_create_with_list_input_keeps_list(self):
        from odoorpc_toolbox.odoo import _normalize_json2_result

        assert _normalize_json2_result("create", [[{"name": "X"}]], {}, [42]) == [42]

    def test_create_via_kwargs_dict_input(self):
        from odoorpc_toolbox.odoo import _normalize_json2_result

        assert _normalize_json2_result("create", [], {"vals_list": {"name": "X"}}, [42]) == 42

    def test_other_methods_unchanged(self):
        from odoorpc_toolbox.odoo import _normalize_json2_result

        assert _normalize_json2_result("search", [[]], {}, [1, 2]) == [1, 2]
