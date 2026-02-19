"""Unified exception hierarchy for odoorpc-toolbox.

Combines exceptions from OdooRPC (LGPL-3.0) with toolbox-specific exceptions.
All OdooRPC-level and toolbox-level exceptions are defined here.
"""

# ============================================================
# OdooRPC-level exceptions (originally from odoorpc.error)
# ============================================================


class Error(Exception):
    """Base class for all OdooRPC-level exceptions."""

    pass


class RPCError(Error):
    """Exception raised for errors related to RPC queries.

    Error details (like the Odoo server traceback) are available
    through the `info` attribute.

    Example:
        >>> try:
        ...     odoo.execute('res.users', 'wrong_method')
        ... except RPCError as exc:
        ...     print(exc.info)
    """

    def __init__(self, message: str, info: dict | bool = False) -> None:
        super().__init__(message, info)
        self.info = info

    def __str__(self) -> str:
        return self.args[0] if self.args and self.args[0] else ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.args[0]!r})"


class InternalError(Error):
    """Exception raised for errors occurring during an internal operation."""

    pass


# ============================================================
# Toolbox-level exceptions (from odoo_connection.py)
# ============================================================


class OdooConnectionError(Exception):
    """Base exception for Odoo connection errors."""

    pass


class OdooConfigError(OdooConnectionError):
    """Exception raised for configuration file errors."""

    pass


class OdooAuthError(OdooConnectionError):
    """Exception raised for authentication errors."""

    pass
