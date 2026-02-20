"""Pytest fixtures for benchmark tests.

Provides session-scoped Odoo connection, RPC counter integration,
and report generation.
"""

from __future__ import annotations

import os

import pytest

from odoorpc_toolbox import EqOdooConnection

from .reporter import generate_report
from .rpc_counter import RPCMetrics


def _get_config_path() -> str:
    """Resolve the test configuration file path."""
    config_path = os.environ.get("ODOO_TEST_CONFIG")
    if config_path:
        return config_path
    default_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
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
    """Create a session-scoped EqOdooConnection for benchmarks."""
    try:
        conn = EqOdooConnection(odoo_config_path)
    except Exception as e:
        pytest.skip(f"Cannot connect to Odoo: {e}")
    return conn


@pytest.fixture(scope="session")
def odoo(connection):
    """Return the raw ODOO instance from the connection."""
    return connection.odoo


@pytest.fixture
def fresh_cache(connection):
    """Clear the lookup cache before each benchmark test."""
    connection.clear_cache()
    return connection


# -- Report collection --

_benchmark_results: list[tuple[RPCMetrics, RPCMetrics]] = []
_cache_results: list[RPCMetrics] = []


@pytest.fixture(scope="session")
def benchmark_results():
    """Session-scoped list to collect (baseline, optimized) metric pairs."""
    return _benchmark_results


@pytest.fixture(scope="session")
def cache_results():
    """Session-scoped list to collect cache benchmark metrics."""
    return _cache_results


def pytest_sessionfinish(session, exitstatus):
    """Generate the benchmark report after all tests complete."""
    if _benchmark_results or _cache_results:
        try:
            report_path = generate_report(_benchmark_results, _cache_results)
            print(f"\n\nBenchmark report written to: {report_path}")
        except Exception as e:
            print(f"\nWarning: Could not generate benchmark report: {e}")
