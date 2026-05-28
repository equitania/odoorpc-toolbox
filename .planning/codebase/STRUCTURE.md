# Codebase Structure

**Analysis Date:** 2026-05-28

## Directory Layout

```
odoorpc-toolbox/
├── odoorpc_toolbox/        # Main package (all production code)
│   ├── __init__.py         # Public API surface (re-exports all public symbols)
│   ├── _version.py         # Single source of version string (__version__)
│   ├── odoo_connection.py  # OdooConnection - YAML config + transport construction
│   ├── base_helper.py      # EqOdooConnection - 20+ helper methods + cache
│   ├── odoo.py             # ODOO class - internalized JSON-RPC 2.0 entry point
│   ├── environment.py      # Environment + model registry
│   ├── model.py            # Model proxy + MetaModel metaclass
│   ├── fields.py           # 14 field type descriptors
│   ├── cache.py            # TTLCache + @cached_lookup decorator
│   ├── batch.py            # batch_write context manager
│   ├── introspection.py    # MCP-compatible JSON Schema method discovery
│   ├── config_generator.py # CLI odoorpc-init-config + generate_config()
│   ├── exceptions.py       # Unified exception hierarchy
│   ├── db.py               # Database management service
│   ├── report.py           # Report download service
│   ├── session.py          # Session utilities
│   ├── tools.py            # Config dict, v() version parser
│   └── rpc/                # JSON-RPC 2.0 protocol layer
│       ├── __init__.py     # Connector classes + PROTOCOLS dict
│       ├── jsonrpc.py      # ProxyJSON, ProxyHTTP, URLBuilder
│       ├── transport.py    # Transport protocol, UrllibTransport, HttpxTransport, create_transport
│       ├── metrics.py      # RequestMetrics + MetricsTransport decorator
│       └── errors.py       # ConnectorError (low-level RPC error)
│
├── tests/                  # Unit tests (no live Odoo required)
│   ├── conftest.py         # Shared fixtures (temp YAML files, mock image)
│   ├── test_batch.py       # batch_write tests
│   ├── test_cache.py       # TTLCache + @cached_lookup tests
│   ├── test_config_generator.py  # CLI and generate_config() tests
│   ├── test_connection.py  # OdooConnection initialization and config parsing
│   ├── test_exceptions.py  # Exception hierarchy tests
│   ├── test_helpers.py     # EqOdooConnection helper method tests (mocked)
│   ├── test_introspection.py     # MCP JSON Schema introspection tests
│   ├── test_metrics.py     # RequestMetrics + MetricsTransport tests
│   ├── test_odoo.py        # ODOO class tests (mocked connector)
│   ├── test_rpc.py         # Connector and proxy tests
│   ├── test_session.py     # Session utility tests
│   ├── test_tools.py       # Config dict and v() parser tests
│   ├── test_transport.py   # UrllibTransport, HttpxTransport, create_transport tests
│   ├── test_version.py     # Version string tests
│   └── integration/        # Integration tests (require live Odoo 18)
│       ├── conftest.py     # Integration fixtures, TestDataManager, live connection setup
│       ├── test_int_batch_write.py    # batch_write against live Odoo
│       ├── test_int_cache.py          # Cache behavior against live Odoo
│       ├── test_int_execute_method.py # execute/execute_kw against live Odoo
│       ├── test_int_location.py       # Country/state lookups against live Odoo
│       ├── test_int_partner.py        # Partner helpers against live Odoo
│       ├── test_int_product.py        # Product/UoM helpers against live Odoo
│       ├── test_int_search_read.py    # search_read optimization tests
│       ├── test_int_sequence.py       # Sequence helpers against live Odoo
│       └── test_int_utilities.py      # Miscellaneous helper tests
│
├── benchmarks/             # Performance benchmarks (require live Odoo)
│   ├── __init__.py
│   ├── conftest.py         # Benchmark fixtures and live connection setup
│   ├── baselines.py        # v0.5.1 behavior simulation (multi-RPC patterns)
│   ├── reporter.py         # Tabular benchmark result formatting
│   ├── rpc_counter.py      # RPC call counting via monkey-patch of ODOO.json()
│   ├── test_bench_batch_write.py   # Batch write vs. per-field write benchmarks
│   ├── test_bench_bulk.py          # Bulk operation scaling benchmarks
│   ├── test_bench_cache.py         # Cache hit/miss performance benchmarks
│   ├── test_bench_search_read.py   # search_read vs. search+browse benchmarks
│   └── test_bench_sequence.py      # Sequence number retrieval benchmarks
│
├── yaml_examples/          # YAML configuration examples and test templates
│   ├── config.yaml         # Full config template (all sections)
│   ├── config_full.yaml    # Minimal config template (Server section only)
│   ├── test_config.yaml    # Active integration test config (git-ignored)
│   └── test_config.yaml.example  # Template for integration test config
│
├── examples/               # Usage examples
├── benchmark_results/      # Stored benchmark output files
├── pyproject.toml          # Single source of truth for deps, build, tool config
├── setup.py                # Minimal shim for editable install compatibility
├── uv.lock                 # UV lockfile
├── CLAUDE.md               # Project-specific Claude guidance
├── README.md               # Package documentation
└── RELEASE_NOTES.md        # Changelog
```

## Directory Purposes

**`odoorpc_toolbox/`:**
- Purpose: The entire production package; everything here is shipped to PyPI
- Contains: All Python modules — RPC stack, helpers, cache, batch, introspection, config
- Key files: `__init__.py` (public API), `base_helper.py` (primary user-facing class), `odoo.py` (internalized OdooRPC), `rpc/transport.py` (pluggable transport)

**`odoorpc_toolbox/rpc/`:**
- Purpose: Self-contained JSON-RPC 2.0 protocol implementation (internalized from OdooRPC LGPL-3.0)
- Contains: Connector classes, proxy builders, transport abstraction, metrics decorator
- Key files: `__init__.py` (connectors + `PROTOCOLS` dict), `transport.py` (all transport implementations)

**`tests/`:**
- Purpose: Unit tests — run without network or Odoo instance; use mocks and temp files
- Contains: One `test_*.py` per module; shared fixtures in `conftest.py`
- Key files: `conftest.py` (YAML fixtures), `test_odoo.py` (largest, 16KB, mocked ODOO)

**`tests/integration/`:**
- Purpose: Integration tests against a live Odoo 18 Community instance
- Contains: Tests for all `EqOdooConnection` helper categories
- Key files: `conftest.py` (live connection + `TestDataManager` for cleanup)

**`benchmarks/`:**
- Purpose: Performance regression testing; compare v0.6.0 optimized patterns vs. simulated v0.5.1 baselines
- Contains: Benchmark fixtures, RPC counter via monkey-patch, tabular reporter
- Key files: `baselines.py` (simulates old multi-RPC patterns), `rpc_counter.py` (patches `ODOO.json()`)

**`yaml_examples/`:**
- Purpose: Config file templates for users and integration tests
- Contains: Full and minimal YAML templates; `test_config.yaml` (git-ignored, created from `.example`)
- Note: `test_config.yaml` is not committed; copy from `test_config.yaml.example` to run integration tests

## Key File Locations

**Entry Points:**
- `odoorpc_toolbox/base_helper.py`: `EqOdooConnection` — primary user-facing class
- `odoorpc_toolbox/odoo.py`: `ODOO` — low-level JSON-RPC class
- `odoorpc_toolbox/config_generator.py`: `main()` — CLI entry point for `odoorpc-init-config`
- `odoorpc_toolbox/__init__.py`: public `__all__` surface

**Configuration:**
- `pyproject.toml`: dependencies, build settings, ruff/black/mypy/pytest config
- `yaml_examples/config.yaml`: reference YAML with all optional sections documented
- `yaml_examples/test_config.yaml.example`: template for integration test setup

**Core Logic:**
- `odoorpc_toolbox/rpc/transport.py`: `Transport` protocol + all backend implementations
- `odoorpc_toolbox/rpc/jsonrpc.py`: JSON-RPC 2.0 envelope construction
- `odoorpc_toolbox/rpc/__init__.py`: connector classes and `PROTOCOLS` dispatch dict
- `odoorpc_toolbox/environment.py`: model registry + dirty-record tracking
- `odoorpc_toolbox/model.py`: `MetaModel` metaclass + `Model` base class
- `odoorpc_toolbox/cache.py`: `TTLCache` + `@cached_lookup` decorator
- `odoorpc_toolbox/batch.py`: `batch_write` context manager

**Testing:**
- `tests/conftest.py`: shared pytest fixtures (no network required)
- `tests/integration/conftest.py`: live Odoo fixtures with `TestDataManager`
- `benchmarks/rpc_counter.py`: RPC counting via `ODOO.json()` monkey-patch
- `benchmarks/baselines.py`: v0.5.1 behavior simulation for comparison baseline

## Naming Conventions

**Files:**
- Module names are `snake_case.py` (e.g., `odoo_connection.py`, `base_helper.py`, `config_generator.py`)
- Test files: `test_<module_name>.py` for unit tests (e.g., `test_transport.py`)
- Integration tests: `test_int_<domain>.py` (e.g., `test_int_partner.py`, `test_int_cache.py`)
- Benchmark tests: `test_bench_<feature>.py` (e.g., `test_bench_cache.py`)

**Directories:**
- Package: `odoorpc_toolbox/` (snake_case, matching PyPI name `odoorpc-toolbox`)
- Sub-package: `rpc/` (short, functional name)
- Test directories: `tests/`, `tests/integration/`, `benchmarks/`

**Classes:**
- Public classes: `PascalCase` (e.g., `EqOdooConnection`, `TTLCache`, `MetricsTransport`)
- Metaclass: `MetaModel` (suffix `Model`)
- Connector classes: `ConnectorJSONRPC`, `ConnectorJSONRPCSSL`
- Transport classes: `UrllibTransport`, `HttpxTransport` (suffix `Transport`)

**Functions and methods:**
- All `snake_case`
- Helper methods prefixed by action: `get_`, `set_`, `find_`, `create_`
- Private: leading underscore `_build_transport`, `_check_logged_user`, `_create_model_class`

**Constants:**
- Module-level defaults: `_TRANSPORT_DEFAULTS`, `_RETRY_DEFAULTS` (prefixed underscore, ALL_CAPS suffix `_DEFAULTS`)

## Where to Add New Code

**New EqOdooConnection helper method:**
- Implementation: `odoorpc_toolbox/base_helper.py` — add method to `EqOdooConnection`
- Use `@cached_lookup()` decorator for static lookups (country/state/UoM IDs)
- Unit test: `tests/test_helpers.py` — mock `self.odoo.env` and `execute_kw`
- Integration test: `tests/integration/test_int_<domain>.py` — create new file or add to existing

**New transport backend:**
- Implementation: `odoorpc_toolbox/rpc/transport.py` — add class implementing `Transport` protocol
- Register in `create_transport()` factory function at bottom of same file
- Export from `odoorpc_toolbox/__init__.py` `__all__`
- Tests: `tests/test_transport.py`

**New exception type:**
- Implementation: `odoorpc_toolbox/exceptions.py` — inherit from `Error` (RPC-level) or `OdooConnectionError` (toolbox-level)
- Export from `odoorpc_toolbox/__init__.py` `__all__`

**New configuration YAML section:**
- Add defaults dict to `odoorpc_toolbox/odoo_connection.py` following pattern of `_TRANSPORT_DEFAULTS`
- Parse in `OdooConnection.__init__` with `{**_DEFAULTS, **(data.get("section") or {})}`
- Add section to templates in `odoorpc_toolbox/config_generator.py`
- Update `yaml_examples/config.yaml`

**New utility function (not a helper method):**
- Location: `odoorpc_toolbox/tools.py` if general-purpose; new module if domain-specific
- Export from `odoorpc_toolbox/__init__.py` if public

## Special Directories

**`odoorpc_toolbox/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No (`.gitignore`)

**`benchmarks/`:**
- Purpose: Performance regression tests; not part of the main `pytest tests/` run
- Generated: No
- Committed: Yes
- Note: Requires `ODOO_TEST_CONFIG=yaml_examples/test_config.yaml` env var and live Odoo; run with `pytest benchmarks/ -v`

**`benchmark_results/`:**
- Purpose: Stored tabular output from benchmark runs
- Generated: Yes (by `benchmarks/reporter.py`)
- Committed: Yes (historical reference)

**`dist/`:**
- Purpose: Built wheel and sdist artifacts from `uv build`
- Generated: Yes
- Committed: No (`.gitignore`)

**`.venv/`:**
- Purpose: UV-managed virtual environment
- Generated: Yes
- Committed: No (`.gitignore`)

**`odoorpc_toolbox.egg-info/`:**
- Purpose: Editable install metadata generated by `uv pip install -e .`
- Generated: Yes
- Committed: No (`.gitignore`)

## Test Organization

**Three-tier separation:**

| Tier | Location | Marker | Requires | Count |
|------|----------|--------|----------|-------|
| Unit | `tests/test_*.py` | (none / default) | Nothing (mocks only) | ~227 |
| Integration | `tests/integration/test_int_*.py` | `@pytest.mark.integration` | Live Odoo 18 + `ODOO_TEST_CONFIG` | ~60 |
| Benchmark | `benchmarks/test_bench_*.py` | `@pytest.mark.benchmark` | Live Odoo 18 + `ODOO_TEST_CONFIG` | ~16 |

**Run commands:**
```bash
# Unit tests only (CI-safe)
pytest tests/ -m "not integration"

# Integration tests (live Odoo required)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest tests/integration/ -v

# Benchmarks
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -v

# Quick benchmarks (skip slow bulk scenarios)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -m "benchmark and not slow" -v
```

---

*Structure analysis: 2026-05-28*
