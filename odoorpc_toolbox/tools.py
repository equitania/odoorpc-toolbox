"""Utility classes and functions for odoorpc-toolbox.

Provides the Config class for managing ODOO instance configuration,
version parsing utilities, and encoding helpers.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

import re
from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any

from odoorpc_toolbox.exceptions import InternalError

if TYPE_CHECKING:
    from odoorpc_toolbox.odoo import ODOO

MATCH_VERSION = re.compile(r"[^\d.]")


class Config(MutableMapping):
    """Manages the configuration of an ODOO instance.

    Available options:
        - auto_commit: If True (default), each time a value is set on a record
          field, a RPC request is sent to update the record.
        - auto_context: If True (default), the user context will be sent
          automatically to every model method call.
        - timeout: Maximum timeout in seconds for a RPC request (default: 120).
    """

    def __init__(self, odoo: "ODOO", options: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._odoo = odoo
        self._options: dict[str, Any] = options or {}

    def __getitem__(self, key: str) -> Any:
        return self._options[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Handle timeout option to set the timeout on the connector."""
        if key == "timeout":
            self._odoo._connector.timeout = value
        self._options[key] = value

    def __delitem__(self, key: str) -> None:
        raise InternalError("Operation not allowed")

    def __iter__(self):
        return self._options.__iter__()

    def __len__(self) -> int:
        return len(self._options)

    def __str__(self) -> str:
        return self._options.__str__()

    def __repr__(self) -> str:
        return self._options.__repr__()


def clean_version(version: str) -> str:
    """Clean a version string.

    Example:
        >>> clean_version('7.0alpha-20121206-000102')
        '7.0'

    Returns:
        A cleaner version string containing only digits and dots.
    """
    version = MATCH_VERSION.sub("", version.split("-")[0])
    return version


def v(version: str) -> list[int]:
    """Convert a version string to a list of integers for comparison.

    Example:
        >>> v('7.0')
        [7, 0]
        >>> v('6.1')
        [6, 1]
        >>> v('7.0') > v('6.1')
        True

    Returns:
        The version as a list of integers.
    """
    return [int(x) for x in clean_version(version).split(".")]


def get_encodings(hint_encoding: str = "utf-8"):
    """Yield encoding names to try, starting with the hint encoding.

    Used to try different encodings when decoding server responses.
    Originally from Odoo 11.0 (odoo.loglevels.get_encodings), LGPL-v3.
    """
    fallbacks = {
        "latin1": "latin9",
        "iso-8859-1": "iso8859-15",
        "cp1252": "1252",
    }
    if hint_encoding:
        yield hint_encoding
        if hint_encoding.lower() in fallbacks:
            yield fallbacks[hint_encoding.lower()]

    for charset in ["utf8", "latin1", "ascii"]:
        if not hint_encoding or (charset.lower() != hint_encoding.lower()):
            yield charset

    from locale import getpreferredencoding

    prefenc = getpreferredencoding()
    if prefenc and prefenc.lower() != "utf-8":
        yield prefenc
        prefenc = fallbacks.get(prefenc.lower())
        if prefenc:
            yield prefenc
