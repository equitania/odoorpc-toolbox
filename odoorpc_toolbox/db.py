"""Database management service for Odoo.

Provides functionalities such as list, create, drop, dump,
duplicate and restore databases.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.

Endpoint strategy for Odoo >= 19:
- ``list()`` uses the /web/database/list controller (type='jsonrpc').
- ``dump()`` uses the /web/database/backup controller (raw binary stream,
  no base64 round-trip).
- create/drop/duplicate/restore/change_password keep using the deprecated
  /jsonrpc db service: the corresponding /web/database/* form controllers
  return errors as HTTP 200 HTML pages (no machine-readable contract),
  while /jsonrpc returns structured JSON-RPC errors. The /jsonrpc endpoint
  is scheduled for removal in Odoo 22 (fall 2028); these methods emit a
  DeprecationWarning on Odoo 19+.
"""

from __future__ import annotations

import base64
import io
import re
import urllib.parse
import warnings
from typing import TYPE_CHECKING

from odoorpc_toolbox import exceptions
from odoorpc_toolbox.tools import v

if TYPE_CHECKING:
    from odoorpc_toolbox.odoo import ODOO

_FORM_URLENCODED = {"Content-Type": "application/x-www-form-urlencoded"}

_LEGACY_DB_WARNING = (
    "The /jsonrpc db service is deprecated and scheduled for removal in "
    "Odoo 22 (fall 2028). The /web/database/* form controllers provide no "
    "machine-readable error contract, so this method keeps using /jsonrpc "
    "on Odoo 19+."
)


def _extract_database_error(body: bytes) -> str | None:
    """Extract the error message from a database-manager HTML error page.

    The /web/database/* controllers render errors as HTTP 200 HTML pages
    containing messages like "Database backup error: <reason>".
    """
    match = re.search(rb"(?:Database|Master password)[^<>]{0,60}error: [^<]+", body)
    if match:
        return match.group(0).decode("utf-8", errors="replace").strip()
    return None


def _get_header(headers: dict, name: str) -> str:
    """Case-insensitive header lookup (urllib and httpx differ in casing)."""
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


class DB:
    """Database management service.

    Access via odoo.db property.

    Example:
        >>> odoo.db.list()
        ['prod', 'test']
    """

    def __init__(self, odoo: ODOO) -> None:
        self._odoo = odoo

    def _use_web_database_controllers(self) -> bool:
        """Return True for Odoo >= 19 where /web/database/* controllers are used.

        Only operations with a machine-readable response contract are routed
        to the controllers (list, backup); see the module docstring.
        """
        return v(self._odoo.version)[0] >= 19

    def _warn_legacy_db_service(self) -> None:
        """Emit a DeprecationWarning for /jsonrpc db calls on Odoo 19+."""
        if self._use_web_database_controllers():
            warnings.warn(_LEGACY_DB_WARNING, DeprecationWarning, stacklevel=3)

    def dump(self, password: str, db: str, format_: str = "zip") -> io.BytesIO:
        """Backup the database. Returns the dump as a binary ZIP file.

        On Odoo >= 19 uses the /web/database/backup controller (raw binary
        response). On older versions uses the /jsonrpc db service (base64).

        Args:
            password: Super administrator password.
            db: Database name.
            format_: Backup format (default: 'zip').

        Returns:
            BytesIO object containing the database backup.

        Raises:
            RPCError: If the backup fails (e.g. wrong master password).
        """
        if self._use_web_database_controllers():
            body = urllib.parse.urlencode({"master_pwd": password, "name": db, "backup_format": format_})
            response = self._odoo.http("/web/database/backup", data=body, headers=dict(_FORM_URLENCODED))
            content_type = _get_header(response.headers, "Content-Type")
            if response.status_code >= 400 or content_type.startswith("text/html"):
                message = _extract_database_error(response.body)
                raise exceptions.RPCError(
                    message or f"Database backup failed (HTTP {response.status_code})",
                    {"status_code": response.status_code},
                )
            return io.BytesIO(response.body)
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
        self._warn_legacy_db_service()
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
        self._warn_legacy_db_service()
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
        self._warn_legacy_db_service()
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
        self._warn_legacy_db_service()
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

        On Odoo >= 19 uses the /web/database/list controller (type='jsonrpc'),
        on older versions the /jsonrpc db service.

        Returns:
            List of database names.
        """
        if self._use_web_database_controllers():
            data = self._odoo.json("/web/database/list", {})
            return data.get("result", [])
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
        self._warn_legacy_db_service()
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
