"""Session persistence for saving and loading ODOO connections.

Sessions are stored in an RC file (default: ~/.odoorpcrc) using ConfigParser format.

Originally from OdooRPC (LGPL-3.0), modernized for Python 3.10+.
"""

import os
from configparser import ConfigParser
from typing import Any


def get_all(rc_file: str = "~/.odoorpcrc") -> dict[str, dict[str, Any]]:
    """Return all session configurations from the rc_file.

    Args:
        rc_file: Path to the RC file (default: ~/.odoorpcrc).

    Returns:
        Dictionary mapping session names to their configuration data.
    """
    conf = ConfigParser()
    conf.read([os.path.expanduser(rc_file)])
    sessions: dict[str, dict[str, Any]] = {}
    for name in conf.sections():
        sessions[name] = {
            "type": conf.get(name, "type"),
            "host": conf.get(name, "host"),
            "protocol": conf.get(name, "protocol"),
            "port": conf.getint(name, "port"),
            "timeout": conf.getfloat(name, "timeout"),
            "user": conf.get(name, "user"),
            "passwd": conf.get(name, "passwd"),
            "database": conf.get(name, "database"),
        }
    return sessions


def get(name: str, rc_file: str = "~/.odoorpcrc") -> dict[str, Any]:
    """Return the session configuration identified by name.

    Args:
        name: Session name identifier.
        rc_file: Path to the RC file (default: ~/.odoorpcrc).

    Returns:
        Dictionary with session configuration data.

    Raises:
        ValueError: If the session does not exist.
    """
    conf = ConfigParser()
    conf.read([os.path.expanduser(rc_file)])
    if not conf.has_section(name):
        raise ValueError(f"'{name}' session does not exist in {rc_file}")
    return {
        "type": conf.get(name, "type"),
        "host": conf.get(name, "host"),
        "protocol": conf.get(name, "protocol"),
        "port": conf.getint(name, "port"),
        "timeout": conf.getfloat(name, "timeout"),
        "user": conf.get(name, "user"),
        "passwd": conf.get(name, "passwd"),
        "database": conf.get(name, "database"),
    }


def _write_rc_file(conf: ConfigParser, rc_path: str) -> None:
    """Write the RC file with owner-only permissions (0o600).

    The file stores cleartext passwords. The content is written to a
    temporary file created with mode 0o600 and atomically moved into
    place, so the target is never readable by other users - not even
    briefly when it pre-existed with a wider mode.
    """
    tmp_path = rc_path + ".tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as file_:
            conf.write(file_)
        os.replace(tmp_path, rc_path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def save(name: str, data: dict[str, Any], rc_file: str = "~/.odoorpcrc") -> None:
    """Save the data session configuration under the given name.

    Args:
        name: Session name identifier.
        data: Dictionary with session configuration data.
        rc_file: Path to the RC file (default: ~/.odoorpcrc).
    """
    conf = ConfigParser()
    conf.read([os.path.expanduser(rc_file)])
    if not conf.has_section(name):
        conf.add_section(name)
    for key in data:
        value = data[key]
        conf.set(name, key, str(value))
    _write_rc_file(conf, os.path.expanduser(rc_file))


def remove(name: str, rc_file: str = "~/.odoorpcrc") -> bool:
    """Remove the session configuration identified by name.

    Args:
        name: Session name identifier.
        rc_file: Path to the RC file (default: ~/.odoorpcrc).

    Returns:
        True if the session was removed.

    Raises:
        ValueError: If the session does not exist.
    """
    conf = ConfigParser()
    conf.read([os.path.expanduser(rc_file)])
    if not conf.has_section(name):
        raise ValueError(f"'{name}' session does not exist in {rc_file}")
    conf.remove_section(name)
    _write_rc_file(conf, os.path.expanduser(rc_file))
    return True
