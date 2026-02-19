"""Tests for tools module (Config, version parsing, encodings)."""

from unittest.mock import MagicMock

import pytest

from odoorpc_toolbox.exceptions import InternalError
from odoorpc_toolbox.tools import Config, clean_version, get_encodings, v


class TestCleanVersion:
    """Tests for clean_version function."""

    def test_simple_version(self):
        assert clean_version("16.0") == "16.0"

    def test_version_with_alpha(self):
        assert clean_version("7.0alpha-20121206-000102") == "7.0"

    def test_version_with_suffix(self):
        assert clean_version("14.0-20210101") == "14.0"

    def test_version_with_saas(self):
        assert clean_version("saas~14.1") == "14.1"

    def test_version_three_parts(self):
        assert clean_version("16.0.1") == "16.0.1"


class TestVersionComparison:
    """Tests for v() version comparison function."""

    def test_simple_version(self):
        assert v("16.0") == [16, 0]

    def test_version_comparison(self):
        assert v("16.0") > v("15.0")
        assert v("7.0") > v("6.1")
        assert v("14.0") < v("16.0")

    def test_version_equality(self):
        assert v("16.0") == v("16.0")

    def test_version_with_suffix(self):
        assert v("14.0-20210101") == [14, 0]


class TestConfig:
    """Tests for Config class."""

    def test_getitem(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"auto_commit": True, "timeout": 120})
        assert config["auto_commit"] is True
        assert config["timeout"] == 120

    def test_setitem(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"auto_commit": True})
        config["auto_commit"] = False
        assert config["auto_commit"] is False

    def test_setitem_timeout_updates_connector(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"timeout": 120})
        config["timeout"] = 300
        assert config["timeout"] == 300
        assert mock_odoo._connector.timeout == 300

    def test_delitem_raises(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"auto_commit": True})
        with pytest.raises(InternalError):
            del config["auto_commit"]

    def test_len(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"a": 1, "b": 2, "c": 3})
        assert len(config) == 3

    def test_iter(self):
        mock_odoo = MagicMock()
        config = Config(mock_odoo, {"auto_commit": True, "timeout": 120})
        keys = list(config)
        assert "auto_commit" in keys
        assert "timeout" in keys


class TestGetEncodings:
    """Tests for get_encodings function."""

    def test_default_hint(self):
        encodings = list(get_encodings())
        assert encodings[0] == "utf-8"

    def test_custom_hint(self):
        encodings = list(get_encodings("latin1"))
        assert encodings[0] == "latin1"
        # Fallback for latin1 should be latin9
        assert "latin9" in encodings

    def test_contains_fallback_encodings(self):
        encodings = list(get_encodings())
        assert "latin1" in encodings
        assert "ascii" in encodings
