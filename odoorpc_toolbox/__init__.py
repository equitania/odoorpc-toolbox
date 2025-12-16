"""OdooRPC Toolbox - Helper functions for OdooRPC operations.

This package provides utilities for working with Odoo servers via OdooRPC,
including connection management and common operation helpers.

Example:
    from odoorpc_toolbox import EqOdooConnection

    connection = EqOdooConnection('config.yaml')
    partner_id = connection.get_res_partner_id(customerno="CUST001")

MCP Discovery:
    from odoorpc_toolbox import get_available_methods

    # Get all methods as MCP-compatible JSON schema
    schema = get_available_methods()
"""

from ._version import __version__
from .odoo_connection import (
    OdooConnection,
    OdooConnectionError,
    OdooConfigError,
    OdooAuthError,
)
from .base_helper import EqOdooConnection
from .introspection import (
    get_available_methods,
    get_method_schema,
    print_available_methods,
)

__all__ = [
    '__version__',
    'OdooConnection',
    'EqOdooConnection',
    'OdooConnectionError',
    'OdooConfigError',
    'OdooAuthError',
    'get_available_methods',
    'get_method_schema',
    'print_available_methods',
]
__author__ = 'Equitania Software GmbH'
