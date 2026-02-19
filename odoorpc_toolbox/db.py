"""Database management service for Odoo.

Provides functionalities such as list, create, drop, dump,
duplicate and restore databases.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

from odoorpc_toolbox import exceptions
from odoorpc_toolbox.tools import v

if TYPE_CHECKING:
    from odoorpc_toolbox.odoo import ODOO


class DB:
    """Database management service.

    Access via odoo.db property.

    Example:
        >>> odoo.db.list()
        ['prod', 'test']
    """

    def __init__(self, odoo: ODOO) -> None:
        self._odoo = odoo

    def dump(self, password: str, db: str, format_: str = "zip") -> io.BytesIO:
        """Backup the database. Returns the dump as a binary ZIP file.

        Args:
            password: Super administrator password.
            db: Database name.
            format_: Backup format (default: 'zip').

        Returns:
            BytesIO object containing the database backup.
        """
        args = [password, db]
        if v(self._odoo.version)[0] >= 9:
            args.append(format_)
        data = self._odoo.json("/jsonrpc", {"service": "db", "method": "dump", "args": args})
        result = bytes(data["result"], "ascii")
        content = base64.standard_b64decode(result)
        return io.BytesIO(content)

    def change_password(self, password: str, new_password: str) -> None:
        """Change the administrator password.

        Args:
            password: Current super administrator password.
            new_password: New super administrator password.
        """
        self._odoo.json(
            "/jsonrpc",
            {
                "service": "db",
                "method": "change_admin_password",
                "args": [password, new_password],
            },
        )

    def create(
        self,
        password: str,
        db: str,
        demo: bool = False,
        lang: str = "en_US",
        admin_password: str = "admin",
    ) -> None:
        """Create a new database.

        Args:
            password: Super administrator password.
            db: Name for the new database.
            demo: Whether to insert demonstration data.
            lang: Localization language code.
            admin_password: Admin password for the new database.
        """
        self._odoo.json(
            "/jsonrpc",
            {
                "service": "db",
                "method": "create_database",
                "args": [password, db, demo, lang, admin_password],
            },
        )

    def drop(self, password: str, db: str) -> bool:
        """Drop a database.

        Args:
            password: Super administrator password.
            db: Database name to drop.

        Returns:
            True if the database was removed, False otherwise.
        """
        if self._odoo._env and self._odoo._env.db == db:
            self._odoo.logout()
        data = self._odoo.json(
            "/jsonrpc",
            {"service": "db", "method": "drop", "args": [password, db]},
        )
        return data["result"]

    def duplicate(self, password: str, db: str, new_db: str) -> None:
        """Duplicate a database.

        Args:
            password: Super administrator password.
            db: Source database name.
            new_db: Name for the duplicate database.
        """
        self._odoo.json(
            "/jsonrpc",
            {
                "service": "db",
                "method": "duplicate_database",
                "args": [password, db, new_db],
            },
        )

    def list(self) -> list[str]:
        """Return the list of databases on the server.

        Returns:
            List of database names.
        """
        data = self._odoo.json("/jsonrpc", {"service": "db", "method": "list", "args": []})
        return data.get("result", [])

    def restore(self, password: str, db: str, dump: io.BytesIO, copy: bool = False) -> None:
        """Restore a database from a dump file.

        Args:
            password: Super administrator password.
            db: Name for the restored database.
            dump: BytesIO dump file (from the dump method).
            copy: If True, the restored database will have a new UUID.

        Raises:
            InternalError: If the dump file is closed.
        """
        if dump.closed:
            raise exceptions.InternalError("Dump file closed")
        b64_data = base64.standard_b64encode(dump.read()).decode()
        self._odoo.json(
            "/jsonrpc",
            {
                "service": "db",
                "method": "restore",
                "args": [password, db, b64_data, copy],
            },
        )
