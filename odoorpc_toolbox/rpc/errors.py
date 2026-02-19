"""RPC-specific exceptions for connector errors.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""


class ConnectorError(Exception):
    """Exception raised by the RPC connector layer."""

    def __init__(self, message: str, odoo_traceback: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.odoo_traceback = odoo_traceback
