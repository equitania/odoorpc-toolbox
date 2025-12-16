"""Tests for version information."""

import re


def test_version_format():
    """Test that version follows semantic versioning."""
    from odoorpc_toolbox import __version__

    # Should match X.Y.Z format
    pattern = r'^\d+\.\d+\.\d+$'
    assert re.match(pattern, __version__), f"Version '{__version__}' does not match X.Y.Z format"


def test_version_importable():
    """Test that version can be imported from package."""
    from odoorpc_toolbox import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_from_module():
    """Test that version can be imported from _version module."""
    from odoorpc_toolbox._version import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)


def test_version_consistency():
    """Test that version is consistent across import methods."""
    from odoorpc_toolbox import __version__ as pkg_version
    from odoorpc_toolbox._version import __version__ as mod_version

    assert pkg_version == mod_version
