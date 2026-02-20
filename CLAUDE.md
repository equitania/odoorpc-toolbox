# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**odoorpc-toolbox** is a Python package providing helper functions and a fully internalized OdooRPC implementation for Odoo server operations. JSON-RPC 2.0 protocol, TTL cache, batch writes, native search_read, MCP-compatible introspection.

- **Author**: Equitania Software GmbH
- **License**: GNU Affero General Public License v3
- **Python**: >= 3.10
- **Current Version**: 0.6.0

## Development Commands

```bash
# Create and activate virtual environment (UV preferred)
uv venv && source .venv/bin/activate.fish  # Fish shell
# Or with aliases: venv+

# Install package in editable mode with all dependencies
uv pip install -e ".[dev,benchmark]"

# Build package for PyPI
uv build

# Verify installation
python -c "from odoorpc_toolbox import EqOdooConnection; print('OK')"
```

## Testing

### Three-Tier Test Architecture

```bash
# Unit tests (no Odoo required) - 145 tests
pytest tests/ -m "not integration"

# Integration tests (live Odoo required) - 60 tests
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest tests/integration/ -v

# Benchmarks (live Odoo required) - 16 scenarios
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -v

# Quick benchmarks (skip bulk scaling)
ODOO_TEST_CONFIG=yaml_examples/test_config.yaml pytest benchmarks/ -m "benchmark and not slow" -v

# Quality checks
ruff check . && black --check .
```

### Integration Test Setup

1. Copy `yaml_examples/test_config.yaml.example` to `yaml_examples/test_config.yaml`
2. Adjust URL, port, credentials, database name
3. Requires: Odoo 18 Community with demo data, modules: base, product, sale, contacts
4. Test data is automatically cleaned up via `TestDataManager`

### Benchmark Approach (Option B: Baseline Simulation)

Benchmarks compare v0.6.0 optimized code against simulated v0.5.1 behavior (`benchmarks/baselines.py`). All baselines use direct `execute_kw` calls to reproduce the old multi-RPC patterns.

**Important**: First model access triggers implicit `fields_get` RPC. Always warmup before measurement.

## Architecture

```
odoorpc_toolbox/
├── odoo_connection.py   # Base OdooConnection - YAML config, auth, HTTPS detection
├── base_helper.py       # EqOdooConnection - 20+ helper methods with cache
├── cache.py             # TTLCache - thread-safe LRU+TTL cache for lookups
├── batch.py             # batch_write - context manager for batched field writes
├── odoo.py              # ODOO class - internalized OdooRPC (JSON-RPC 2.0)
├── environment.py       # Environment + Model registry
├── model.py             # Model proxy + Recordset (MetaModel metaclass)
├── fields.py            # 14 field type descriptors
├── introspection.py     # MCP-compatible method discovery (JSON Schema)
├── exceptions.py        # Unified exception hierarchy
└── rpc/                 # JSON-RPC 2.0 protocol layer
```

### Key Monkey-Patch Targets (for benchmarks)

| Target | Location | Purpose |
|--------|----------|---------|
| `ODOO.json()` | `odoo.py:138` | Single choke-point for ALL RPC calls |
| `TTLCache.get()` | `cache.py:48` | Cache hit/miss tracking |

## Configuration

```yaml
Server:
  url: https://odoo.com       # http:// or https:// (auto-detected)
  port: 443                   # 443 for SSL, 8069 for local
  user: admin
  password: pw
  database: db
  protocol: jsonrpc            # jsonrpc or jsonrpc+ssl
```

## Version-Specific Logic

- `get_product_uom_id()`: Uses `product.uom` for v10-12, `uom.uom` for v13+
- `odoo.py login()`: Uses `/jsonrpc` for Odoo 10+
- Report download: Odoo 14+ requires CSRF token (NotImplementedError)

## Git Commit Conventions

- `[ADD]` - New features or extensions
- `[CHG]` - Modifications to existing code
- `[FIX]` - Bug fixes
