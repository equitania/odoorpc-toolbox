"""Unit tests for the DB service (db.py) version routing."""

import io
from unittest.mock import MagicMock, patch

import pytest

from odoorpc_toolbox.exceptions import RPCError
from odoorpc_toolbox.odoo import ODOO
from odoorpc_toolbox.rpc.transport import TransportResponse


def _make_odoo(mock_protocols, version="18.0"):
    mock_connector = MagicMock()
    mock_connector.version = version
    mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))
    return ODOO("localhost", version=version), mock_connector


class TestDBList:
    """db.list() routes by version."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_list_uses_jsonrpc_on_v18(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.return_value = {"result": ["db1"]}
        assert odoo.db.list() == ["db1"]
        call_args = mock_connector.proxy_json.call_args
        assert call_args[0][0] == "/jsonrpc"
        assert call_args[0][1]["service"] == "db"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_list_uses_web_controller_on_v19(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": ["db1", "db2"]}
        assert odoo.db.list() == ["db1", "db2"]
        call_args = mock_connector.proxy_json.call_args
        assert call_args[0][0] == "/web/database/list"


class TestDBDump:
    """db.dump() routes by version."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_dump_uses_jsonrpc_base64_on_v18(self, mock_protocols):
        import base64

        odoo, mock_connector = _make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.return_value = {"result": base64.standard_b64encode(b"ZIPDATA").decode()}
        result = odoo.db.dump("masterpw", "my_db")
        assert isinstance(result, io.BytesIO)
        assert result.read() == b"ZIPDATA"
        assert mock_connector.proxy_json.call_args[0][0] == "/jsonrpc"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_dump_uses_backup_controller_on_v19(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={"Content-Type": "application/octet-stream; charset=binary"},
            body=b"RAWZIPDATA",
        )
        result = odoo.db.dump("masterpw", "my_db")
        assert isinstance(result, io.BytesIO)
        assert result.read() == b"RAWZIPDATA"

        call_args = mock_connector.proxy_http.call_args
        assert call_args[0][0] == "/web/database/backup"
        assert "master_pwd=masterpw" in call_args[0][1]
        assert "backup_format=zip" in call_args[0][1]
        assert call_args[0][2]["Content-Type"] == "application/x-www-form-urlencoded"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_dump_v19_html_error_page_raises(self, mock_protocols):
        """The backup controller renders errors as HTTP 200 HTML pages."""
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={"Content-Type": "text/html; charset=utf-8"},
            body=b"<html><div>Database backup error: Access Denied</div></html>",
        )
        with pytest.raises(RPCError, match="Database backup error: Access Denied"):
            odoo.db.dump("wrongpw", "my_db")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_dump_v19_http_error_raises(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=500,
            headers={},
            body=b"boom",
        )
        with pytest.raises(RPCError, match="HTTP 500"):
            odoo.db.dump("masterpw", "my_db")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_dump_v19_lowercase_content_type_header(self, mock_protocols):
        """httpx delivers lower-cased header names - lookup must be case-insensitive."""
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_http.return_value = TransportResponse(
            status_code=200,
            headers={"content-type": "application/octet-stream"},
            body=b"DATA",
        )
        assert odoo.db.dump("masterpw", "my_db").read() == b"DATA"


class TestDBLegacyOpsDeprecation:
    """Legacy-only operations emit DeprecationWarning on Odoo 19+."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_drop_warns_on_v19(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": True}
        with pytest.warns(DeprecationWarning, match="Odoo 22"):
            odoo.db.drop("masterpw", "old_db")
        assert mock_connector.proxy_json.call_args[0][0] == "/jsonrpc"

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_create_warns_on_v19(self, mock_protocols):
        odoo, mock_connector = _make_odoo(mock_protocols, "19.0")
        mock_connector.proxy_json.return_value = {"result": True}
        with pytest.warns(DeprecationWarning, match="Odoo 22"):
            odoo.db.create("masterpw", "new_db")

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_drop_does_not_warn_on_v18(self, mock_protocols):
        import warnings

        odoo, mock_connector = _make_odoo(mock_protocols, "18.0")
        mock_connector.proxy_json.return_value = {"result": True}
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            odoo.db.drop("masterpw", "old_db")


class TestExtractDatabaseError:
    """HTML error page parsing."""

    def test_extracts_backup_error(self):
        from odoorpc_toolbox.db import _extract_database_error

        body = b'<div class="alert">Database backup error: Wrong master password</div>'
        assert _extract_database_error(body) == "Database backup error: Wrong master password"

    def test_returns_none_without_error(self):
        from odoorpc_toolbox.db import _extract_database_error

        assert _extract_database_error(b"<html>all fine</html>") is None
