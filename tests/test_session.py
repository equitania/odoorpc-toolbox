"""Tests for session persistence module."""

import os
import tempfile

import pytest

from odoorpc_toolbox.session import get, get_all, remove, save


@pytest.fixture
def temp_rc_file():
    """Create a temporary RC file."""
    fd, path = tempfile.mkstemp(suffix=".odoorpcrc")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_session_data():
    """Return sample session configuration data."""
    return {
        "type": "ODOO",
        "host": "localhost",
        "protocol": "jsonrpc",
        "port": 8069,
        "timeout": 120.0,
        "user": "admin",
        "passwd": "admin",
        "database": "testdb",
    }


class TestSessionSaveAndGet:
    """Tests for session save and get."""

    def test_save_and_get(self, temp_rc_file, sample_session_data):
        save("test_session", sample_session_data, rc_file=temp_rc_file)
        result = get("test_session", rc_file=temp_rc_file)

        assert result["type"] == "ODOO"
        assert result["host"] == "localhost"
        assert result["port"] == 8069
        assert result["timeout"] == 120.0
        assert result["database"] == "testdb"

    def test_save_multiple_sessions(self, temp_rc_file, sample_session_data):
        save("session1", sample_session_data, rc_file=temp_rc_file)

        session2_data = sample_session_data.copy()
        session2_data["host"] = "remote.server.com"
        session2_data["database"] = "proddb"
        save("session2", session2_data, rc_file=temp_rc_file)

        all_sessions = get_all(rc_file=temp_rc_file)
        assert len(all_sessions) == 2
        assert "session1" in all_sessions
        assert "session2" in all_sessions
        assert all_sessions["session2"]["host"] == "remote.server.com"

    def test_get_nonexistent_session(self, temp_rc_file):
        with pytest.raises(ValueError, match="does not exist"):
            get("nonexistent", rc_file=temp_rc_file)

    def test_get_all_empty(self, temp_rc_file):
        result = get_all(rc_file=temp_rc_file)
        assert result == {}


class TestSessionRemove:
    """Tests for session removal."""

    def test_remove_session(self, temp_rc_file, sample_session_data):
        save("test_session", sample_session_data, rc_file=temp_rc_file)
        result = remove("test_session", rc_file=temp_rc_file)
        assert result is True

        with pytest.raises(ValueError):
            get("test_session", rc_file=temp_rc_file)

    def test_remove_nonexistent_session(self, temp_rc_file):
        with pytest.raises(ValueError, match="does not exist"):
            remove("nonexistent", rc_file=temp_rc_file)

    def test_save_overwrites_existing(self, temp_rc_file, sample_session_data):
        save("test_session", sample_session_data, rc_file=temp_rc_file)

        updated_data = sample_session_data.copy()
        updated_data["host"] = "new.host.com"
        save("test_session", updated_data, rc_file=temp_rc_file)

        result = get("test_session", rc_file=temp_rc_file)
        assert result["host"] == "new.host.com"
