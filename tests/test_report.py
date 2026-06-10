"""Unit tests for the Report service (report.py)."""

from unittest.mock import MagicMock, patch

import pytest

from odoorpc_toolbox.odoo import ODOO


def _make_logged_in_odoo(mock_protocols, version="19.0"):
    mock_connector = MagicMock()
    mock_connector.version = version
    mock_protocols.__getitem__ = MagicMock(return_value=MagicMock(return_value=mock_connector))
    odoo = ODOO("localhost", version=version)
    odoo._env = MagicMock()
    odoo._env.context = {}
    odoo._login = "admin"
    odoo._password = "admin"
    return odoo, mock_connector


class TestReportDownloadV14Plus:
    """report.download() raises an actionable NotImplementedError for Odoo >= 14."""

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_raises_not_implemented_on_v14(self, mock_protocols):
        odoo, _ = _make_logged_in_odoo(mock_protocols, "14.0")
        odoo._env.__getitem__.return_value.search.return_value = [5]
        with pytest.raises(NotImplementedError) as exc_info:
            odoo.report.download("sale.report_saleorder", [1])
        assert "14.0" in str(exc_info.value)

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_message_mentions_workarounds_on_v19(self, mock_protocols):
        odoo, _ = _make_logged_in_odoo(mock_protocols, "19.0")
        odoo._env.__getitem__.return_value.search.return_value = [5]
        with pytest.raises(NotImplementedError) as exc_info:
            odoo.report.download("sale.report_saleorder", [1])
        message = str(exc_info.value)
        assert "19.0" in message
        assert "Workarounds" in message
        assert "CSRF" in message
        assert "ir.attachment" in message or "headless" in message

    @patch("odoorpc_toolbox.odoo.PROTOCOLS")
    def test_unknown_report_raises_value_error(self, mock_protocols):
        odoo, _ = _make_logged_in_odoo(mock_protocols, "19.0")
        odoo._env.__getitem__.return_value.search.return_value = []
        with pytest.raises(ValueError, match="does not exist"):
            odoo.report.download("nonexistent.report", [1])
