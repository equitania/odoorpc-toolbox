"""Batch write context manager for grouping Odoo record writes.

Provides batch_write() which temporarily disables auto_commit,
collects all field writes, and commits them in a single operation
upon context exit. Rolls back on exception.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

    from odoorpc_toolbox.odoo import ODOO


@contextmanager
def batch_write(odoo: ODOO) -> Generator[None, None, None]:
    """Context manager that batches record writes into fewer RPC calls.

    Temporarily sets ``auto_commit=False`` on the ODOO instance, so field
    assignments are collected locally. On successful exit the dirty records
    are committed in bulk. On exception the local changes are invalidated
    (rolled back).

    Args:
        odoo: A connected ODOO instance.

    Example:
        >>> with batch_write(connection.odoo):
        ...     record.name = "New Name"
        ...     record.email = "new@example.com"
        ...     record.phone = "+49..."
        ... # -> One write() call instead of 3

    Raises:
        Exception: Re-raises any exception after rolling back changes.
    """
    previous_auto_commit = odoo.config["auto_commit"]
    odoo.config["auto_commit"] = False
    try:
        yield
        odoo.env.commit()
    except Exception:
        odoo.env.invalidate()
        raise
    finally:
        odoo.config["auto_commit"] = previous_auto_commit
