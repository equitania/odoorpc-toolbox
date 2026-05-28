# Technology Stack

**Analysis Date:** 2026-05-28

## Languages

**Primary:**
- Python 3.10+ - All package source code, tests, benchmarks, examples

**Supported Python Versions:**
- 3.10, 3.11, 3.12, 3.13 (all declared in `pyproject.toml` classifiers)
- Development venv runs Python 3.13 (`.venv/pyvenv.cfg`)

## Runtime

**Environment:**
- CPython 3.13 (local dev venv)
- No Node.js, no Rust, pure Python package

**Package Manager:**
- UV (mandatory — never pip directly)
- Lockfile: `uv.lock` (present, committed)

## Frameworks

**Core:**
- No web framework — pure library package

**Testing:**
- `pytest>=7.0.0` — test runner
- `pytest-cov>=4.0.0` — coverage reporting
- Config: `[tool.pytest.ini_options]` in `pyproject.toml`

**Type Checking:**
- `mypy>=1.0.0` — static type analysis
- Config: `[tool.mypy]` in `pyproject.toml`, target Python 3.10

**Build/Dev:**
- `setuptools>=68.0` — build backend (`pyproject.toml` build-system)
- `ruff>=0.8.0` — linting and import sorting (`[tool.ruff]`)
- `black>=23.0.0` — code formatting (`[tool.black]`)
- `tabulate>=0.9.0` — benchmark result table rendering (optional extra `[benchmark]`)

## Key Dependencies

**Critical (runtime):**
- `PyYAML>=6.0` — YAML configuration file parsing (`odoo_connection.py:17`)
  - Used to load connection config from `*.yaml` files
  - Single mandatory runtime dependency

**Optional (runtime extras):**
- `httpx[http2]>=0.25.0` — HTTP/2-capable transport backend
  - Declared under `[project.optional-dependencies] httpx`
  - Also included in `dev` extras for testing
  - Import-guarded in `odoorpc_toolbox/rpc/transport.py:159` — graceful fallback to urllib

**Standard Library (no extra install needed):**
- `urllib.request` — default HTTP transport (`UrllibTransport`)
- `http.cookiejar` — cookie-based session management
- `json` — JSON-RPC 2.0 serialization/deserialization
- `threading` — `TTLCache` thread-safety (`cache.py`), `RequestMetrics` thread-safety (`rpc/metrics.py`)
- `dataclasses` — `TransportResponse`, `RetryConfig`, `RequestMetrics`
- `contextlib` — `batch_write` context manager (`batch.py`)
- `functools` — `cached_lookup` decorator (`cache.py`)
- `inspect`, `typing` — MCP introspection (`introspection.py`)

## Configuration

**Environment:**
- No `.env` file — all configuration via YAML files
- YAML config path is passed at instantiation: `OdooConnection('path/to/config.yaml')`
- Integration tests require `ODOO_TEST_CONFIG=yaml_examples/test_config.yaml` env var

**YAML Config Structure:**
```yaml
Server:           # Required
  url, port, user, password, database, protocol

transport:        # Optional
  backend, http2, pool_connections

retry:            # Optional
  max_attempts, backoff_factor, retry_on

timeout:          # Optional
  connect, read

cache:            # Optional
  maxsize, ttl
```

**Example configs:** `yaml_examples/config_full.yaml`, `yaml_examples/config.yaml`

**Build:**
- `pyproject.toml` — single source of truth for all project metadata, dependencies, tool configs
- `setup.py` — minimal shim (exists for editable install compatibility)
- Version source: `odoorpc_toolbox/_version.py` → `__version__ = "0.7.2"`
- Dynamic version attribute: `[tool.setuptools.dynamic] version = { attr = "odoorpc_toolbox._version.__version__" }`

## Linting and Formatting Configuration

**ruff** (`[tool.ruff]`):
- `line-length = 120`
- `target-version = "py310"`
- Enabled rule sets: E (pycodestyle errors), W (warnings), F (pyflakes), I (isort), B (bugbear), UP (pyupgrade)
- Ignored: E203, E266
- First-party import group: `odoorpc_toolbox`

**black** (`[tool.black]`):
- `line-length = 120`
- `target-version = ["py310"]`

**mypy** (`[tool.mypy]`):
- `python_version = "3.10"`
- `warn_return_any = true`
- `warn_unused_configs = true`
- `ignore_missing_imports = true`

## Test Markers

Defined in `[tool.pytest.ini_options]`:
- `integration` — requires a live Odoo instance
- `benchmark` — performance benchmark tests
- `slow` — bulk operations, large datasets

## Platform Requirements

**Development:**
- Python 3.10 or newer
- UV package manager
- Optional: `httpx[http2]` for HTTP/2 transport

**Production (as installed library):**
- Python 3.10+
- PyYAML (mandatory)
- httpx optional — falls back to stdlib urllib automatically
- No operating system restrictions (OS Independent classifier)

**Published to:**
- PyPI as `odoorpc-toolbox`
- GitHub: `https://github.com/equitania/odoorpc-toolbox`

---

*Stack analysis: 2026-05-28*
