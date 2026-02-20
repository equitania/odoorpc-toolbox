"""Pytest fixtures for integration tests against a live Odoo instance.

Provides session-scoped connection and per-test TestDataManager
for automatic record cleanup.
"""

from __future__ import annotations

import os

import pytest

from odoorpc_toolbox import EqOdooConnection


def _get_config_path() -> str:
    """Resolve the test configuration file path."""
    config_path = os.environ.get("ODOO_TEST_CONFIG")
    if config_path:
        return config_path
    default_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "yaml_examples",
        "test_config.yaml",
    )
    return default_path


@pytest.fixture(scope="session")
def odoo_config_path():
    """Return the path to the Odoo test configuration file."""
    path = _get_config_path()
    if not os.path.exists(path):
        pytest.skip(
            f"Odoo test config not found at {path}. "
            "Set ODOO_TEST_CONFIG env var or create yaml_examples/test_config.yaml"
        )
    return path


@pytest.fixture(scope="session")
def connection(odoo_config_path):
    """Create a session-scoped EqOdooConnection."""
    try:
        conn = EqOdooConnection(odoo_config_path)
    except Exception as e:
        pytest.skip(f"Cannot connect to Odoo: {e}")
    return conn


@pytest.fixture(scope="session")
def odoo(connection):
    """Return the raw ODOO instance."""
    return connection.odoo


class TestDataManager:
    """Tracks created records and deletes them on cleanup.

    Records are deleted in reverse insertion order to handle
    foreign key dependencies correctly.

    Example:
        >>> manager = TestDataManager(odoo)
        >>> partner_id = manager.create("res.partner", {"name": "Test"})
        >>> manager.cleanup()  # Deletes the partner
    """

    def __init__(self, odoo):
        self._odoo = odoo
        self._created: list[tuple[str, int]] = []

    def create(self, model: str, values: dict) -> int:
        """Create a record and track it for cleanup.

        Args:
            model: Odoo model name.
            values: Field values for the new record.

        Returns:
            ID of the created record.
        """
        record_id = self._odoo.execute_kw(model, "create", [values])
        self._created.append((model, record_id))
        return record_id

    def track(self, model: str, record_id: int) -> None:
        """Track an externally created record for cleanup.

        Args:
            model: Odoo model name.
            record_id: ID of the record to track.
        """
        self._created.append((model, record_id))

    def cleanup(self) -> None:
        """Delete all tracked records in reverse order."""
        for model, record_id in reversed(self._created):
            try:
                self._odoo.execute_kw(model, "unlink", [[record_id]])
            except Exception:
                pass  # Record may already be deleted via cascade
        self._created.clear()


@pytest.fixture
def data_manager(odoo):
    """Per-test TestDataManager with automatic cleanup."""
    manager = TestDataManager(odoo)
    yield manager
    manager.cleanup()


@pytest.fixture
def fresh_cache(connection):
    """Clear the lookup cache before each test."""
    connection.clear_cache()
    return connection
