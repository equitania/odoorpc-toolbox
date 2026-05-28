# Testing Patterns

**Analysis Date:** 2026-05-28

## Test Framework

**Runner:**
- pytest >= 7.0.0
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`
- Coverage: pytest-cov >= 4.0.0

**Assertion Library:**
- pytest's built-in `assert` statements (no unittest.assert style)

**Run Commands:**
```bash
# Unit tests only (no Odoo required — 227 tests)
pytest tests/ -m "not integration"

# All unit tests (default testpath)
pytest tests/

# Integration tests (live Odoo required — 60 tests)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest tests/integration/ -v

# Benchmarks (live Odoo required — 16 scenarios)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -v

# Quick benchmarks (skip bulk scaling tests)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -m "benchmark and not slow" -v

# Coverage
pytest tests/ -m "not integration" --cov=odoorpc_toolbox

# Quality checks
ruff check . && black --check .
```

## Test File Organization

**Location:** Three tiers in separate directories, all separate from source:

```
odoorpc-toolbox/
├── tests/                           # Unit tests (no Odoo required)
│   ├── conftest.py                  # Shared fixtures (temp files, mock data)
│   ├── __init__.py
│   ├── test_batch.py
│   ├── test_cache.py
│   ├── test_config_generator.py
│   ├── test_connection.py
│   ├── test_exceptions.py
│   ├── test_helpers.py
│   ├── test_introspection.py
│   ├── test_metrics.py
│   ├── test_odoo.py
│   ├── test_rpc.py
│   ├── test_session.py
│   ├── test_tools.py
│   ├── test_transport.py
│   ├── test_version.py
│   └── integration/                 # Integration tests (live Odoo required)
│       ├── conftest.py              # Connection, TestDataManager, fresh_cache fixtures
│       ├── __init__.py
│       ├── test_int_batch_write.py
│       ├── test_int_cache.py
│       ├── test_int_execute_method.py
│       ├── test_int_location.py
│       ├── test_int_partner.py
│       ├── test_int_product.py
│       ├── test_int_search_read.py
│       ├── test_int_sequence.py
│       └── test_int_utilities.py
└── benchmarks/                      # Performance benchmarks (live Odoo required)
    ├── conftest.py                  # Connection, RPCMetrics, report generation fixtures
    ├── __init__.py
    ├── baselines.py                 # v0.5.1 behavior simulation functions
    ├── reporter.py                  # Benchmark report generator (tabulate)
    ├── rpc_counter.py               # Monkey-patch RPC counter context managers
    ├── test_bench_batch_write.py
    ├── test_bench_bulk.py           # @pytest.mark.slow — bulk scaling tests
    ├── test_bench_cache.py
    ├── test_bench_search_read.py
    └── test_bench_sequence.py
```

**Naming:**
- Unit test files: `test_<module>.py` matching the source module name
- Integration test files: `test_int_<feature>.py`
- Benchmark files: `test_bench_<feature>.py`
- Test classes: `Test<Feature>` (e.g., `TestTTLCache`, `TestSearchReadBenchmark`)
- Test methods: `test_<what_is_verified>` with descriptive names

## Test Markers

Defined in `pyproject.toml` under `[tool.pytest.ini_options].markers`:

| Marker | Purpose | Location |
|--------|---------|----------|
| `integration` | Tests requiring a live Odoo instance | `tests/integration/` |
| `benchmark` | Performance benchmark tests | `benchmarks/` |
| `slow` | Slow tests — bulk operations, large datasets | `benchmarks/test_bench_bulk.py` |

**Usage pattern:**
```python
@pytest.mark.integration
class TestPartnerOperations:
    ...

@pytest.mark.benchmark
@pytest.mark.slow                         # combine for bulk tests
class TestBulkBenchmark:
    ...
```

**Excluding slow tests:**
```bash
pytest benchmarks/ -m "benchmark and not slow" -v
```

## Test Structure

**Unit test suite organization:**
```python
class TestTTLCache:
    """Tests for the TTLCache class."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_expiry(self):
        """Test that entries expire after TTL."""
        cache = TTLCache(maxsize=10, ttl=0.1)
        cache.set("key1", "value1")
        time.sleep(0.15)
        assert cache.get("key1") is None
```

**Integration test structure:**
```python
@pytest.mark.integration
class TestPartnerOperations:
    """Test partner CRUD and lookup operations against live Odoo."""

    def test_create_partner_individual(self, connection, data_manager):
        """Create an individual contact and verify it exists."""
        partner_id = data_manager.create("res.partner", {...})
        assert partner_id > 0
        result = connection.search_read("res.partner", [("id", "=", partner_id)], [...])
        assert result[0]["name"] == "Test Individual IntTest"
```

**Benchmark test structure:**
```python
@pytest.mark.benchmark
class TestSearchReadBenchmark:
    """Compare native search_read vs old search+read pattern."""

    def test_single_record(self, connection, odoo, benchmark_results):
        """search_read for 1 record: expect 1 RPC (v0.6.0) vs 2 RPCs (v0.5.1)."""
        # Baseline: old pattern (v0.5.1 simulation)
        with counting(odoo, "search_read (1 record) - baseline") as baseline:
            search_then_read(odoo, "res.partner", domain, fields, limit=1)

        # Optimized: current implementation
        with counting(odoo, "search_read (1 record) - v0.6.0") as optimized:
            connection.search_read("res.partner", domain, fields, limit=1)

        benchmark_results.append((baseline, optimized))

        assert optimized.rpc_calls < baseline.rpc_calls
```

## Mocking

**Framework:** `unittest.mock` — `MagicMock`, `patch`

**Direct import (no pytest-mock):**
```python
from unittest.mock import MagicMock, patch
```

**Module-level mocking with `patch`:**
```python
with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
    from odoorpc_toolbox import EqOdooConnection
    instance = object.__new__(EqOdooConnection)
```

**ODOO instance mocking:**
```python
def _make_mock_odoo(self):
    """Create a mock ODOO instance with config and env."""
    mock_odoo = MagicMock()
    mock_odoo.config = {"auto_commit": True, "auto_context": True, "timeout": 120}
    mock_odoo.env = MagicMock()
    return mock_odoo
```

**What to mock:**
- `OdooConnection.__init__` to avoid actual network connections in unit tests
- `ODOO` instances for testing context managers (e.g., `batch_write`)
- Individual urllib/httpx calls when testing transport layer

**What NOT to mock in integration tests:**
- The live Odoo connection itself — integration tests use real `EqOdooConnection`
- Record operations (`execute_kw`, `search_read`) — these must hit live Odoo

## Fixtures

**Unit test fixtures** (`tests/conftest.py`):
- `valid_config_yaml` — temp file with a minimal valid YAML config (yields path, auto-deletes)
- `extended_config_yaml` — temp file with all config sections (transport, retry, timeout, cache)
- `invalid_config_yaml` — temp file with malformed YAML for error path tests
- `temp_image_file` — temp 1x1 PNG for base64 encoding tests

**All temp-file fixtures** use `tempfile.NamedTemporaryFile` with `yield` + `os.unlink()`:
```python
@pytest.fixture
def valid_config_yaml():
    """Create a temporary valid YAML configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)
```

**Integration test fixtures** (`tests/integration/conftest.py`):

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `odoo_config_path` | session | Resolves YAML config path; skips suite if not found |
| `connection` | session | Session-scoped `EqOdooConnection`; skips if unreachable |
| `odoo` | session | Raw `ODOO` instance from the connection |
| `data_manager` | function | `TestDataManager` with automatic cleanup on test exit |
| `fresh_cache` | function | Clears lookup cache before each test; returns connection |

**Benchmark fixtures** (`benchmarks/conftest.py`):

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `odoo_config_path` | session | Same pattern as integration tests |
| `connection` | session | Session-scoped benchmark connection |
| `odoo` | session | Raw ODOO instance |
| `fresh_cache` | function | Clears cache before each benchmark run |
| `benchmark_results` | session | Accumulates `(baseline, optimized)` metric pairs for report |
| `cache_results` | session | Accumulates cache metric objects for report |

## TestDataManager

Defined in `tests/integration/conftest.py`. Tracks created records and deletes them in **reverse insertion order** (to handle foreign key dependencies):

```python
class TestDataManager:
    """Tracks created records and deletes them on cleanup."""

    def __init__(self, odoo):
        self._odoo = odoo
        self._created: list[tuple[str, int]] = []

    def create(self, model: str, values: dict) -> int:
        """Create a record and track it for cleanup."""
        record_id = self._odoo.execute_kw(model, "create", [values])
        self._created.append((model, record_id))
        return record_id

    def track(self, model: str, record_id: int) -> None:
        """Track an externally created record for cleanup."""
        self._created.append((model, record_id))

    def cleanup(self) -> None:
        """Delete all tracked records in reverse order."""
        for model, record_id in reversed(self._created):
            try:
                self._odoo.execute_kw(model, "unlink", [[record_id]])
            except Exception:
                pass  # Record may already be deleted via cascade
        self._created.clear()
```

**Usage:** Use `data_manager.create()` for records the test creates, use `data_manager.track()` for records created via helpers:
```python
partner_id = connection.create_partner(name="IntTest Helper Partner", ...)
data_manager.track("res.partner", partner_id)
```

## Benchmark Infrastructure

### Baselines (v0.5.1 Simulation)

`benchmarks/baselines.py` simulates the old (pre-optimization) RPC patterns to measure the improvements in v0.6.0. Each function uses direct `execute_kw` calls reproducing the old multi-RPC patterns:

| Baseline function | Old pattern | RPC count |
|-------------------|-------------|-----------|
| `search_then_read()` | `search()` + `read()` | 2 RPCs |
| `get_sequence_old()` | `search()` + `read()` | 2 RPCs |
| `set_sequence_old()` | `search()` + `read()` + `write()` | 3 RPCs |
| `get_state_id_uncached()` | `search()` (no cache) | 1 RPC per call |
| `write_fields_individually()` | one `write()` per field | N RPCs |

### RPC Counter (Monkey-Patching)

`benchmarks/rpc_counter.py` provides two context managers that monkey-patch `ODOO.json()` (the single choke-point for all RPC calls):

**`counting(odoo, scenario)`** — counts RPC calls and timing:
```python
with counting(odoo, "search_read (1 record) - baseline") as metrics:
    search_then_read(odoo, "res.partner", domain, fields, limit=1)
# metrics.rpc_calls, metrics.total_time_ms, metrics.avg_call_time_ms
```

**`counting_with_cache(connection, scenario)`** — counts RPC calls + cache hits/misses (also patches `TTLCache.get()`):
```python
with counting_with_cache(connection, "state_lookup x10 - v0.6.0") as metrics:
    for _ in range(10):
        connection.get_state_id(country_id, state_name)
# metrics.cache_hits, metrics.cache_hit_rate, metrics.rpc_calls
```

**`RPCMetrics` dataclass** stores collected metrics:
```python
@dataclass
class RPCMetrics:
    scenario: str = ""
    rpc_calls: int = 0
    rpc_calls_by_method: dict[str, int] = field(default_factory=dict)
    total_time_ms: float = 0.0
    call_times_ms: list[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
```

### Warmup Pattern

**CRITICAL:** First model access triggers an implicit `fields_get` RPC. Always warmup the model before measuring:
```python
# Warmup: first access triggers fields_get — do this BEFORE entering counting() block
connection.odoo.execute_kw("res.partner", "search_read", [[]], {"fields": ["name"], "limit": 1})

# Now measure cleanly
with counting(odoo, "scenario name") as metrics:
    connection.search_read("res.partner", domain, fields)
```

### Report Generation

`benchmarks/reporter.py` generates a comparison table using `tabulate`. The `pytest_sessionfinish` hook in `benchmarks/conftest.py` writes the report automatically after the benchmark session completes.

## Integration Test Configuration

**Config file resolution** (in order):
1. `ODOO_TEST_CONFIG` environment variable
2. Default: `yaml_examples/test_config.yaml`

**Setup:**
```bash
cp yaml_examples/test_config.yaml.example yaml_examples/test_config.yaml
# Edit url, port, credentials, database
```

**Required Odoo modules:** `base`, `product`, `sale`, `contacts`

**Skip behavior:** If config not found or connection fails, the entire integration suite is skipped via `pytest.skip()` in session-scoped fixtures — not a hard failure:
```python
@pytest.fixture(scope="session")
def connection(odoo_config_path):
    try:
        conn = EqOdooConnection(odoo_config_path)
    except Exception as e:
        pytest.skip(f"Cannot connect to Odoo: {e}")
    return conn
```

**Conditional skips within tests** — used when demo data is optional:
```python
title_id = connection.get_res_partner_title_id("Mister")
if title_id is None:
    pytest.skip("Title 'Mister' not found - demo data may not be installed")
```

## Common Patterns

**Error path testing:**
```python
def test_config_error_inherits(self):
    assert issubclass(OdooConfigError, OdooConnectionError)
    with pytest.raises(OdooConnectionError):
        raise OdooConfigError("bad config")
```

**Thread safety testing** — uses `threading.Thread` with error accumulation:
```python
errors = []
def writer(start, count):
    try:
        for i in range(start, start + count):
            cache.set(f"key_{i}", f"value_{i}")
    except Exception as e:
        errors.append(e)

threads = [threading.Thread(target=writer, args=(i * 100, 100)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()
assert len(errors) == 0
```

**Parametrized scaling tests:**
```python
@pytest.mark.parametrize("record_count", [10, 50, 100])
def test_search_read_scaling(self, connection, odoo, benchmark_results, record_count):
    ...
```

**Mock helper for unit tests that need EqOdooConnection without network:**
```python
@pytest.fixture
def helper(self):
    with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
        from odoorpc_toolbox import EqOdooConnection
        instance = object.__new__(EqOdooConnection)
        return instance
```

---

*Testing analysis: 2026-05-28*
