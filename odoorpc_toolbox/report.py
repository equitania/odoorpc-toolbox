"""Report management service for Odoo.

Provides methods to list and download available reports from the server.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING, Any

from odoorpc_toolbox.tools import get_encodings, v

if TYPE_CHECKING:
    from odoorpc_toolbox.odoo import ODOO


def _encode2bytes(data: bytes) -> str:
    """Try different encodings to decode data."""
    for encoding in get_encodings():
        try:
            return data.decode(encoding)
        except Exception:
            pass
    return data


class Report:
    """Report management service.

    Access via odoo.report property.

    Example:
        >>> reports = odoo.report.list()
        >>> report_pdf = odoo.report.download('sale.report_saleorder', [2, 3])
    """

    def __init__(self, odoo: ODOO) -> None:
        self._odoo = odoo

    def download(
        self,
        name: str,
        ids: list[int],
        datas: dict | None = None,
        context: dict | None = None,
    ) -> io.BytesIO:
        """Download a report from the server.

        Note: For Odoo >= 14, this requires a CSRF token and raises NotImplementedError.

        Args:
            name: Report name (e.g., 'sale.report_saleorder').
            ids: List of record IDs to include in the report.
            datas: Additional data for the report.
            context: Context to use for the report.

        Returns:
            BytesIO object containing the report content.

        Raises:
            ValueError: If the report doesn't exist or invalid data received.
            NotImplementedError: For Odoo >= 14 (CSRF token required).
        """
        if context is None:
            context = self._odoo.env.context

        def check_report(name: str) -> int:
            report_model = "ir.actions.report"
            if v(self._odoo.version)[0] < 11:
                report_model = "ir.actions.report.xml"
            IrReport = self._odoo.env[report_model]
            report_ids = IrReport.search([("report_name", "=", name)])
            report_id = report_ids[0] if report_ids else False
            if not report_id:
                raise ValueError(f"The report '{name}' does not exist.")
            return report_id

        report_id = check_report(name)

        # Odoo >= 11.0
        if v(self._odoo.version)[0] >= 11:
            IrReport = self._odoo.env["ir.actions.report"]
            report = IrReport.browse(report_id)
            if v(self._odoo.version)[0] >= 14:
                raise NotImplementedError(
                    f"report.download() is not supported on Odoo {self._odoo.version}. "
                    "The /report/download endpoint requires a browser-session CSRF "
                    "token, and the external API (including the JSON-2 API on Odoo "
                    "19+) exposes no report rendering path: the ir.actions.report "
                    "render methods are private (underscore-prefixed) and not "
                    "RPC-callable.\n"
                    "Workarounds:\n"
                    "  1. Render server-side and fetch the result, e.g. store the "
                    "PDF in an ir.attachment via a custom server action or module, "
                    "then read it over RPC.\n"
                    "  2. Use a headless browser (Playwright/Selenium) with a real "
                    "web session to download from /report/download.\n"
                    "See: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html"
                )
            else:
                response = report.with_context(context).render(ids, data=datas)
            content = response[0]
            result = content.encode("latin1")
            return io.BytesIO(result)
        # Odoo < 11.0
        else:
            args_to_send = [
                self._odoo.env.db,
                self._odoo.env.uid,
                self._odoo._rpc_credential,
                name,
                ids,
                datas,
                context,
            ]
            data = self._odoo.json(
                "/jsonrpc",
                {
                    "service": "report",
                    "method": "render_report",
                    "args": args_to_send,
                },
            )
            if "result" not in data and not data["result"].get("result"):
                raise ValueError("Received invalid data.")
            result = _encode2bytes(data["result"]["result"])
            content = base64.standard_b64decode(result)
            return io.BytesIO(content)

    def list(self) -> dict[str, list[dict[str, Any]]]:
        """List available reports from the server.

        Returns:
            Dictionary with reports classified by data model.
        """
        report_model = "ir.actions.report"
        if v(self._odoo.version)[0] < 11:
            report_model = "ir.actions.report.xml"
        IrReport = self._odoo.env[report_model]
        report_ids = IrReport.search([])
        reports = IrReport.read(report_ids, ["name", "model", "report_name", "report_type"])
        result: dict[str, list[dict[str, Any]]] = {}
        for report in reports:
            model = report.pop("model")
            report.pop("id")
            if model not in result:
                result[model] = []
            result[model].append(report)
        return result
