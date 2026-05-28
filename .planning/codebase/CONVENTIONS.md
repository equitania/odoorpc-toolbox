# Coding Conventions

**Analysis Date:** 2026-05-28

## Naming Patterns

**Files:**
- Snake_case for all module files: `odoo_connection.py`, `base_helper.py`, `config_generator.py`
- Test files prefixed with `test_`: `test_cache.py`, `test_connection.py`, `test_transport.py`
- Integration test files prefixed with `test_int_`: `test_int_partner.py`, `test_int_cache.py`
- Benchmark test files prefixed with `test_bench_`: `test_bench_cache.py`, `test_bench_search_read.py`

**Classes:**
- PascalCase: `EqOdooConnection`, `TTLCache`, `TransportResponse`, `RetryConfig`, `RPCMetrics`
- Acronyms capitalized in full: `ODOO`, `TTLCache`, `RPCError`, `RPCMetrics`
- Test classes use `Test` prefix: `TestTTLCache`, `TestPartnerOperations`, `TestBatchWrite`

**Functions and Methods:**
- Snake_case: `get_state_id()`, `search_read()`, `batch_write()`, `create_transport()`
- Private methods with leading underscore: `_evict_oldest()`, `_get_config_path()`, `_make_mock_odoo()`
- Descriptive names that indicate the action and subject: `get_res_partner_category_id()`, `check_if_company_exists()`

**Variables:**
- Snake_case throughout: `config_path`, `record_id`, `cache_key`, `backup_factor`
- Module-level constants use UPPER_SNAKE_CASE: `_TRANSPORT_DEFAULTS`, `_RETRY_DEFAULTS`, `LOG_JSON_SEND_MSG`
- Odoo model references within methods use ALL_CAPS: `RES_COUNTRY_STATE = self.odoo.env["res.country.state"]`

**Type annotations:**
- Modern union syntax (`int | None`, `str | None`) — requires Python 3.10+
- `from __future__ import annotations` used in all source modules where forward references appear

## Code Style

**Formatting:**
- Tool: Black
- Line length: 120 characters
- Target versions: `py310`
- Config: `[tool.black]` in `pyproject.toml`

**Linting:**
- Tool: Ruff
- Line length: 120 characters
- Target version: `py310`
- Enabled rule sets: `E` (pycodestyle errors), `W` (pycodestyle warnings), `F` (pyflakes), `I` (isort), `B` (flake8-bugbear), `UP` (pyupgrade)
- Ignored: `E203` (whitespace before ':'), `E266` (too many leading '#')
- Config: `[tool.ruff]` and `[tool.ruff.lint]` in `pyproject.toml`

**Static typing:**
- Tool: mypy
- `warn_return_any = true`, `warn_unused_configs = true`, `ignore_missing_imports = true`
- Config: `[tool.mypy]` in `pyproject.toml`

**Quality check command:**
```bash
ruff check . && black --check .
```

## Import Organization

Managed by Ruff isort (`I` ruleset). The project's first-party package is `odoorpc_toolbox` (declared in `[tool.ruff.lint.isort]`).

**Order:**
1. Standard library imports (alphabetical): `import base64`, `import os`, `import threading`
2. Third-party imports: `import yaml`
3. First-party imports: `from odoorpc_toolbox import ...`
4. Relative imports: `from . import odoo_connection`, `from .cache import TTLCache`

**`from __future__ import annotations`** appears at the top of all source modules where forward references occur — used in 11 of ~15 source modules.

**TYPE_CHECKING guard** used in `db.py`, `tools.py`, `batch.py`, `model.py`, `environment.py`, `rpc/metrics.py`, `rpc/transport.py` to avoid circular imports:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from odoorpc_toolbox.base_helper import EqOdooConnection
```

## Error Handling

**Exception hierarchy** defined in `odoorpc_toolbox/exceptions.py`:

```
Exception
├── Error                    # Base for all OdooRPC-level exceptions
│   ├── RPCError             # JSON-RPC errors; stores server traceback in .info
│   └── InternalError        # Internal OdooRPC operation errors
└── OdooConnectionError      # Base for all toolbox connection exceptions
    ├── OdooConfigError      # YAML config file missing/malformed
    └── OdooAuthError        # Authentication failure
```

**Raising pattern** — always chain exceptions with `from e` or `from ex`:
```python
raise OdooConfigError(f"Configuration file not found: {eq_yaml_path}") from e
raise OdooConnectionError(f"Connection error: {ex}") from ex
raise OdooAuthError(f"Authentication error: {e}") from e
```

**Error messages** include the original cause in f-string format with context.

**Field-level validation** raises standard `ValueError` with descriptive messages:
```python
raise ValueError(f"Length of the '{self.name}' is limited to {self.size}")
```

**Catching exceptions** — broad catches only in connection setup and test infrastructure; production code catches specific exception types.

## Logging

**Framework:** Standard library `logging` module.

**Logger instantiation** — module-level, one per module that needs logging:
```python
logger = logging.getLogger(__name__)
```
Used in `odoorpc_toolbox/odoo_connection.py`, `odoorpc_toolbox/odoo.py`, `odoorpc_toolbox/rpc/jsonrpc.py`.

**Log levels used:**
- `logger.error(...)` — connection failures, config errors, auth errors
- `logger.info(...)` — transport selection, version detection
- `logger.debug(...)` — JSON-RPC request/response details (in `rpc/jsonrpc.py`)

**Pattern:** Log before raising the exception when catching lower-level errors:
```python
logger.error(f"Configuration file not found: {eq_yaml_path}")
raise OdooConfigError(...) from e
```

## Docstrings

**Style:** Google-style docstrings throughout the codebase.

**Module-level docstrings:** Every module begins with a triple-quoted description. Multi-line modules include "Typical usage example:" block.

**Class docstrings:** Include attribute listing under `Attributes:` and `Example:` block using `>>>` syntax.

**Method docstrings:** `Args:`, `Returns:`, `Raises:` sections as applicable:
```python
def create(self, model: str, values: dict) -> int:
    """Create a record and track it for cleanup.

    Args:
        model: Odoo model name.
        values: Field values for the new record.

    Returns:
        ID of the created record.
    """
```

**Short methods:** Single-line docstrings acceptable for simple properties and trivial methods.

## Type Hints

**Coverage:** Comprehensive type hints on all public methods and class attributes.

**Return types:** Always annotated, including `-> None` for void methods.

**Modern syntax** (Python 3.10+):
- Union: `int | None`, `str | None`, `dict | bool`
- Generics: `list[str]`, `dict[str, int]`, `tuple[str, int]`
- `from __future__ import annotations` enables forward references

**Dataclasses** with full type annotations used for transport and metrics: `TransportResponse`, `RetryConfig`, `RPCMetrics`.

**Protocol** for structural subtyping: `Transport` in `odoorpc_toolbox/rpc/transport.py`.

## Comments

**Section dividers** in longer files use comment banners:
```python
# ============================================================
# OdooRPC-level exceptions (originally from odoorpc.error)
# ============================================================
```

**Inline comments** explain non-obvious logic:
```python
# RPC call 1: search
ids = odoo.execute_kw(model, "search", [domain], kwargs)
# RPC call 2: read
records = odoo.execute_kw(model, "read", [ids], {"fields": fields})
```

**Avoid obvious comments** — comments explain "why", not "what" the code does.

## Module Design

**Exports:** `odoorpc_toolbox/__init__.py` defines an explicit `__all__` list — every public symbol must be in `__all__`.

**Relative imports** within the package: `from .cache import TTLCache`, `from . import odoo_connection`.

**Barrel file:** `odoorpc_toolbox/__init__.py` re-exports everything the user needs; consumers only need `from odoorpc_toolbox import EqOdooConnection`.

**Private helpers** prefixed with underscore and defined at module level (e.g., `_TRANSPORT_DEFAULTS`, `_get_config_path()`).

## Version Management

**Version location:** `odoorpc_toolbox/_version.py`, single `__version__` string.

**Dynamic version** resolved at build time via `pyproject.toml`:
```toml
[tool.setuptools.dynamic]
version = { attr = "odoorpc_toolbox._version.__version__" }
```

**Bump process:** Update `__version__` in `odoorpc_toolbox/_version.py` only.

## Git Commit Conventions

**Prefix format:** `[ADD]`, `[CHG]`, `[FIX]` — mandatory prefix in square brackets.

- `[ADD]` — new features or extensions
- `[CHG]` — modifications to existing code
- `[FIX]` — bug fixes

**Examples from git log:**
- `[ADD] Odoo 19+ JSON-2 API support`
- `[CHG] Bump version to 0.7.1`
- `[FIX] Bump to 0.7.2: align tests with disabled JSON-2 API`

---

*Convention analysis: 2026-05-28*
