"""OdooRPC Toolbox - Helper functions for Odoo server operations.

This package provides utilities for working with Odoo servers,
including connection management, RPC communication, and common operation helpers.
OdooRPC functionality is fully internalized - no external OdooRPC dependency needed.

Example:
    from odoorpc_toolbox import EqOdooConnection

    connection = EqOdooConnection('config.yaml')
    partner_id = connection.get_res_partner_id(customerno="CUST001")

Direct ODOO usage:
    from odoorpc_toolbox import ODOO

    odoo = ODOO('localhost', port=8069)
    odoo.login('mydb', 'admin', 'admin')

MCP Discovery:
    from odoorpc_toolbox import get_available_methods

    # Get all methods as MCP-compatible JSON schema
    schema = get_available_methods()
"""

from ._version import __version__
from .base_helper import EqOdooConnection
from .batch import batch_write
from .cache import TTLCache
from .exceptions import (
    Error,
    InternalError,
    OdooAuthError,
    OdooConfigError,
    OdooConnectionError,
    RPCError,
)
from .introspection import (
    get_available_methods,
    get_method_schema,
    print_available_methods,
)
from .odoo import ODOO
from .odoo_connection import OdooConnection

__all__ = [
    "__version__",
    "ODOO",
    "OdooConnection",
    "EqOdooConnection",
    "TTLCache",
    "batch_write",
    "Error",
    "RPCError",
    "InternalError",
    "OdooConnectionError",
    "OdooConfigError",
    "OdooAuthError",
    "get_available_methods",
    "get_method_schema",
    "print_available_methods",
]
__author__ = "Equitania Software GmbH"
