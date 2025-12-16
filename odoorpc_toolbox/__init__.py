"""OdooRPC Toolbox - Helper functions for OdooRPC operations.

This package provides utilities for working with Odoo servers via OdooRPC,
including connection management and common operation helpers.

Example:
    from odoorpc_toolbox import EqOdooConnection

    connection = EqOdooConnection('config.yaml')
    partner_id = connection.get_res_partner_id(customerno="CUST001")
"""

from ._version import __version__
from .odoo_connection import (
    OdooConnection,
    OdooConnectionError,
    OdooConfigError,
    OdooAuthError,
)
from .base_helper import EqOdooConnection

__all__ = [
    '__version__',
    'OdooConnection',
    'EqOdooConnection',
    'OdooConnectionError',
    'OdooConfigError',
    'OdooAuthError',
]
__author__ = 'Equitania Software GmbH'
