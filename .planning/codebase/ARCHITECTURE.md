<!-- refreshed: 2026-05-28 -->
# Architecture

**Analysis Date:** 2026-05-28

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         User Entry Points                            │
│                                                                      │
│   EqOdooConnection('config.yaml')     ODOO('host', port=8069)       │
│   `odoorpc_toolbox/base_helper.py`    `odoorpc_toolbox/odoo.py`     │
│                                                                      │
│   odoorpc-init-config CLI                                            │
│   `odoorpc_toolbox/config_generator.py`                              │
└────────────┬──────────────────────┬────────────────────────────────┘
             │                      │
             ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Helper Layer                                  │
│   EqOdooConnection  (inherits OdooConnection)                       │
│   20+ helper methods: get_state_id, get_res_partner_id, ...        │
│   TTLCache via @cached_lookup decorator                              │
│   `odoorpc_toolbox/base_helper.py`                                  │
└────────────┬────────────────────────────────────────────────────────┘
             │  (inherits)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Connection Layer                               │
│   OdooConnection - YAML config parsing, HTTPS detection,            │
│   transport construction, auto_commit/context defaults              │
│   `odoorpc_toolbox/odoo_connection.py`                              │
└────────────┬────────────────────────────────────────────────────────┘
             │  (owns)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ODOO Class Layer                            │
│   ODOO - main JSON-RPC entry point (internalized OdooRPC fork)      │
│   login(), execute(), execute_kw(), json(), http()                  │
│   Environment + Model registry, DB service, Report service          │
│   `odoorpc_toolbox/odoo.py`                                         │
│   `odoorpc_toolbox/environment.py`                                  │
│   `odoorpc_toolbox/model.py`                                        │
│   `odoorpc_toolbox/fields.py`  (14 field descriptors)              │
└────────────┬────────────────────────────────────────────────────────┘
             │  (delegates to)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RPC Protocol Layer                           │
│   ConnectorJSONRPC / ConnectorJSONRPCSSL                             │
│   ProxyJSON + ProxyHTTP + URLBuilder                                 │
│   `odoorpc_toolbox/rpc/__init__.py`                                 │
│   `odoorpc_toolbox/rpc/jsonrpc.py`                                  │
└────────────┬────────────────────────────────────────────────────────┘
             │  (uses)
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Transport Layer                               │
│   Transport (Protocol)                                               │
│   UrllibTransport (default, no extra deps)                          │
│   HttpxTransport  (optional, httpx[http2] extra)                    │
│   MetricsTransport (decorator wrapping any Transport)               │
│   RetryConfig + exponential backoff                                  │
│   create_transport() factory                                         │
│   `odoorpc_toolbox/rpc/transport.py`                                │
│   `odoorpc_toolbox/rpc/metrics.py`                                  │
└────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `EqOdooConnection` | 20+ domain helper methods, caching via TTLCache | `odoorpc_toolbox/base_helper.py` |
| `OdooConnection` | YAML config parse, HTTPS detection, transport build, `ODOO` init | `odoorpc_toolbox/odoo_connection.py` |
| `ODOO` | JSON-RPC 2.0 entry point, login, execute, execute_kw, version routing | `odoorpc_toolbox/odoo.py` |
| `Environment` | Model registry, user context, dirty-record tracking, commit/batch_commit | `odoorpc_toolbox/environment.py` |
| `Model` / `MetaModel` | Dynamic model proxy via metaclass; RPC delegation for any method call | `odoorpc_toolbox/model.py` |
| `fields.py` | 14 field type descriptors (Char, Integer, Many2one, One2many, etc.) | `odoorpc_toolbox/fields.py` |
| `TTLCache` | Thread-safe LRU+TTL cache for lookup results | `odoorpc_toolbox/cache.py` |
| `batch_write` | Context manager: disables auto_commit, groups field writes, bulk-commits | `odoorpc_toolbox/batch.py` |
| `ConnectorJSONRPC` | Builds ProxyJSON + ProxyHTTP from shared Transport; detects server version | `odoorpc_toolbox/rpc/__init__.py` |
| `ProxyJSON` / `ProxyHTTP` | Serialize/deserialize JSON-RPC 2.0 envelopes, delegate to Transport | `odoorpc_toolbox/rpc/jsonrpc.py` |
| `Transport` (Protocol) | Pluggable HTTP backend interface: `request()` + `close()` | `odoorpc_toolbox/rpc/transport.py` |
| `UrllibTransport` | stdlib urllib backend; default, no extra dependencies | `odoorpc_toolbox/rpc/transport.py` |
| `HttpxTransport` | Optional httpx backend; HTTP/2, connection pooling, retry | `odoorpc_toolbox/rpc/transport.py` |
| `MetricsTransport` | Decorator transport; records timing and error counts thread-safely | `odoorpc_toolbox/rpc/metrics.py` |
| `introspection.py` | MCP-compatible JSON Schema discovery for `EqOdooConnection` methods | `odoorpc_toolbox/introspection.py` |
| `config_generator.py` | CLI `odoorpc-init-config`; generates YAML config templates | `odoorpc_toolbox/config_generator.py` |
| `exceptions.py` | Unified exception hierarchy: `RPCError`, `OdooAuthError`, `OdooConfigError` | `odoorpc_toolbox/exceptions.py` |
| `db.py` | Database service proxy (list, create, drop databases) | `odoorpc_toolbox/db.py` |
| `report.py` | Report download service (Odoo 14+ CSRF note: NotImplementedError) | `odoorpc_toolbox/report.py` |
| `session.py` | Session-related utilities | `odoorpc_toolbox/session.py` |
| `tools.py` | `Config` dict, `v()` version parser | `odoorpc_toolbox/tools.py` |

## Pattern Overview

**Overall:** Layered architecture with an internalized OdooRPC fork. No external `odoorpc` dependency — the full JSON-RPC protocol stack is owned by this package.

**Key Characteristics:**
- **Pluggable transport**: `Transport` is a `typing.Protocol`; backends are swapped via `create_transport()` factory or YAML config
- **Decorator pattern for metrics**: `MetricsTransport` wraps any `Transport` without modifying it
- **Metaclass-based model proxy**: `MetaModel` dynamically generates model classes from `fields_get` RPC response; any attribute access that is not a reserved name becomes an RPC call
- **Config-driven construction**: All connection and transport parameters come from YAML; `OdooConnection.__init__` never takes explicit host/port arguments
- **Inheritance chain**: `EqOdooConnection → OdooConnection → (owns) ODOO → (owns) Environment/Model`

## Layers

**Transport Layer:**
- Purpose: HTTP communication; session cookies; retry; metrics
- Location: `odoorpc_toolbox/rpc/transport.py`, `odoorpc_toolbox/rpc/metrics.py`
- Contains: `Transport` protocol, `UrllibTransport`, `HttpxTransport`, `MetricsTransport`, `RetryConfig`, `TransportResponse`
- Depends on: stdlib `urllib`, optional `httpx`
- Used by: `ConnectorJSONRPC` (via `ProxyJSON`/`ProxyHTTP`)

**RPC Protocol Layer:**
- Purpose: JSON-RPC 2.0 envelope construction and URL building
- Location: `odoorpc_toolbox/rpc/__init__.py`, `odoorpc_toolbox/rpc/jsonrpc.py`
- Contains: `ConnectorJSONRPC`, `ConnectorJSONRPCSSL`, `ProxyJSON`, `ProxyHTTP`, `URLBuilder`
- Depends on: Transport layer
- Used by: `ODOO` class via `self._connector`

**ODOO Class Layer:**
- Purpose: High-level API for Odoo operations; version-aware login; execute/execute_kw routing
- Location: `odoorpc_toolbox/odoo.py`
- Contains: `ODOO` class with `json()`, `login()`, `execute()`, `execute_kw()`, `logout()`, `metrics` property
- Depends on: RPC Protocol layer, `Environment`, `DB`, `Report`, `tools`, `exceptions`
- Used by: `OdooConnection` (stores as `self.odoo`)

**Environment/Model Layer:**
- Purpose: Model registry; field descriptor system; record browsing; dirty-record tracking
- Location: `odoorpc_toolbox/environment.py`, `odoorpc_toolbox/model.py`, `odoorpc_toolbox/fields.py`
- Contains: `Environment`, `Model`, `MetaModel`, 14 field descriptors
- Depends on: `ODOO` class (circular reference managed via `TYPE_CHECKING` + weakref)
- Used by: `ODOO.env`, `base_helper.py` helper methods

**Connection Layer:**
- Purpose: YAML config parsing; HTTPS/port auto-detection; transport instantiation; Odoo context defaults
- Location: `odoorpc_toolbox/odoo_connection.py`
- Contains: `OdooConnection`, config default dicts (`_TRANSPORT_DEFAULTS`, `_RETRY_DEFAULTS`, etc.)
- Depends on: `ODOO`, `rpc.transport.create_transport`, `exceptions`
- Used by: `EqOdooConnection` (base class)

**Helper Layer:**
- Purpose: Domain-specific Odoo operation helpers with caching
- Location: `odoorpc_toolbox/base_helper.py`
- Contains: `EqOdooConnection`, `@cached_lookup` decorated methods
- Depends on: `OdooConnection`, `TTLCache`, `cached_lookup`
- Used by: End-user application code (primary public API)

**Cross-Cutting Utilities:**
- Cache: `odoorpc_toolbox/cache.py` — `TTLCache`, `cached_lookup` decorator
- Batch writes: `odoorpc_toolbox/batch.py` — `batch_write` context manager
- Introspection: `odoorpc_toolbox/introspection.py` — MCP JSON Schema discovery
- Config generation: `odoorpc_toolbox/config_generator.py` — CLI + library

## Data Flow

### Primary Request Path (EqOdooConnection helper call)

1. `EqOdooConnection.get_state_id(country_id, state_name)` → `@cached_lookup` checks `self._lookup_cache` (`odoorpc_toolbox/cache.py:48`)
2. Cache miss → calls `self.odoo.env["res.country.state"]` → `Environment.__getitem__` (`odoorpc_toolbox/environment.py:152`)
3. First access triggers `_create_model_class` → `ODOO.execute(model, "fields_get")` to build field descriptors (`odoorpc_toolbox/environment.py:184`)
4. `Model.search([...])` → `MetaModel.__getattr__` returns RPC method → `ODOO.execute_kw(model, "search", ...)` (`odoorpc_toolbox/model.py:52-56`)
5. `ODOO.execute_kw` → `ODOO.json(url, params)` → `self._connector.proxy_json(url, params)` (`odoorpc_toolbox/odoo.py:158-174`)
6. `ProxyJSON.__call__` builds JSON-RPC 2.0 envelope, calls `self._transport.request(full_url, data_bytes, headers, timeout)` (`odoorpc_toolbox/rpc/jsonrpc.py:122-149`)
7. If `MetricsTransport` is wrapping: records timing before/after delegating to inner transport (`odoorpc_toolbox/rpc/metrics.py:117-147`)
8. `UrllibTransport.request` or `HttpxTransport.request` executes the HTTP POST (`odoorpc_toolbox/rpc/transport.py:95-126` / `176-227`)
9. Response deserialized, result returned up the call stack
10. `@cached_lookup` stores result in `TTLCache`, returns to caller

### Batch Write Flow

1. `with batch_write(connection.odoo):` — sets `odoo.config["auto_commit"] = False` (`odoorpc_toolbox/batch.py:41-43`)
2. Field assignments on records accumulate in `record._values_to_write` (tracked via `env.dirty` WeakSet)
3. On context exit: `odoo.env.commit()` iterates dirty records and calls `record.write(values)` per record (`odoorpc_toolbox/environment.py:67-81`)
4. On exception: `odoo.env.invalidate()` clears dirty set without writing (`odoorpc_toolbox/environment.py:111-113`)

### Login Flow

1. `OdooConnection.odoo_connect()` calls `ODOO(host, port, protocol, timeout, transport)` (`odoorpc_toolbox/odoo_connection.py:184`)
2. `ODOO.__init__` creates `ConnectorJSONRPC` which immediately fetches `/web/webclient/version_info` to detect server version (`odoorpc_toolbox/rpc/__init__.py:101-106`)
3. `odoo_con.login(db, user, pw)` — version-aware routing:
   - Odoo >= 19 (currently disabled): `/web/session/authenticate`
   - Odoo 10-18: `/jsonrpc` service dispatch for `common.login` then `object.execute` for context
   - Odoo < 10: `/web/session/authenticate`
4. `Environment` is created with `(odoo, db, uid, context)` (`odoorpc_toolbox/odoo.py:317`)

**State Management:**
- `ODOO._env`: the active `Environment` instance; `None` until login
- `Environment._registry`: dict mapping model name strings to dynamically generated `Model` subclasses
- `Environment._dirty`: `WeakSet` of records with uncommitted local changes
- `TTLCache._store`: dict of `{key: (value, timestamp)}` tuples, protected by `threading.Lock`

## Key Abstractions

**Transport Protocol:**
- Purpose: Pluggable HTTP backend; decouples JSON-RPC logic from HTTP implementation
- Examples: `odoorpc_toolbox/rpc/transport.py` — `UrllibTransport`, `HttpxTransport`
- Pattern: `typing.Protocol` with `runtime_checkable`; factory `create_transport(backend="auto")` auto-selects httpx or falls back to urllib

**MetaModel (Dynamic Model Proxy):**
- Purpose: Any `odoo.env["res.partner"]` access returns a live Python class whose attribute accesses become RPC calls
- Examples: `odoorpc_toolbox/model.py:42-57`
- Pattern: `MetaModel(type)` overrides `__getattr__` at the class level; `type(cls_name, (Model,), attrs)` generates one class per Odoo model

**@cached_lookup Decorator:**
- Purpose: Transparent cache for any `EqOdooConnection` lookup method
- Examples: `odoorpc_toolbox/cache.py:102-147`
- Pattern: Reads/writes `self._lookup_cache` (a `TTLCache` instance); cache key = `"method_name:arg1:arg2:k=v"`

**MetricsTransport Decorator:**
- Purpose: Wrap any `Transport` to collect timing/error statistics without changing transport behavior
- Examples: `odoorpc_toolbox/rpc/metrics.py:79-151`
- Pattern: Decorator/wrapper; `ODOO.metrics` property exposes the `RequestMetrics` object if active

## Entry Points

**`EqOdooConnection` (primary):**
- Location: `odoorpc_toolbox/base_helper.py:21`
- Triggers: Instantiated with path to YAML config file
- Responsibilities: Loads config, builds transport, authenticates against Odoo, exposes 20+ domain helper methods with caching

**`ODOO` (low-level):**
- Location: `odoorpc_toolbox/odoo.py:29`
- Triggers: Direct instantiation with host/port/protocol
- Responsibilities: Raw JSON-RPC access; requires explicit `login()` call before `env` access

**`odoorpc-init-config` CLI:**
- Location: `odoorpc_toolbox/config_generator.py:main` (registered via `pyproject.toml` `[project.scripts]`)
- Triggers: Shell command `odoorpc-init-config [--minimal] [-o path] [--url ...] [--port ...] [--database ...]`
- Responsibilities: Generates YAML configuration template with all optional sections

**`get_available_methods()` (MCP):**
- Location: `odoorpc_toolbox/introspection.py`
- Triggers: Called by MCP server or directly
- Responsibilities: Returns JSON Schema for all `EqOdooConnection` public methods; enables external tool discovery

## Architectural Constraints

- **Threading:** No multi-threading in the RPC stack itself. `TTLCache` and `RequestMetrics` are individually thread-safe via `threading.Lock`. The ODOO class and Environment are not thread-safe — one instance per thread.
- **Global state:** No module-level singletons. Each `EqOdooConnection` instance owns its own `ODOO`, `Environment`, and `TTLCache`.
- **Circular imports:** `odoo.py` imports `environment.py`; `environment.py` references `ODOO` only under `TYPE_CHECKING` to avoid runtime circularity.
- **Optional dependency:** `httpx` is optional (`[project.optional-dependencies] httpx`). All transport code is guarded by `try/except ImportError`. Default transport is always `UrllibTransport`.
- **Version-specific routing:** `odoo.py` uses `v(self.version)[0]` comparisons for Odoo version-specific behavior (login endpoints, UoM model names, report CSRF). The JSON-2 API for Odoo 19+ is currently disabled (`_use_json2` always returns `False`).

## Anti-Patterns

### Accessing `odoo.env` before `login()`

**What happens:** Calling `ODOO.env` without first calling `login()` raises `InternalError("Login required")`.
**Why it's wrong:** `self._env` is `None` until `login()` sets it; `_check_logged_user()` is called on every `env` property access.
**Do this instead:** Always use `OdooConnection` or `EqOdooConnection` which calls `odoo_connect()` (including login) in `__init__`.

### Setting field values outside `batch_write` for bulk operations

**What happens:** Each field assignment triggers an immediate `write()` RPC call when `auto_commit=True` (the default).
**Why it's wrong:** N field assignments on M records = N×M RPC calls instead of M.
**Do this instead:** Use `batch_write(connection.odoo)` context manager (`odoorpc_toolbox/batch.py`) to group writes into one `write()` per record.

### Calling `odoo.env["model"]` in a tight loop without caching

**What happens:** First access per model triggers `fields_get` RPC; subsequent accesses within the same session reuse the registry class but re-fetching the model in a new session calls `fields_get` again.
**Why it's wrong:** `fields_get` is an expensive RPC call and model schemas rarely change.
**Do this instead:** Assign the model class to a local variable outside the loop: `Partner = odoo.env["res.partner"]`.

## Error Handling

**Strategy:** Exception hierarchy with two separate roots:
- `Error` (base for OdooRPC-level exceptions) → `RPCError`, `InternalError`
- `OdooConnectionError` (base for toolbox exceptions) → `OdooConfigError`, `OdooAuthError`

**Patterns:**
- `RPCError` carries an `info` dict with the full Odoo server traceback
- `OdooConnection.__init__` translates `FileNotFoundError` → `OdooConfigError`, `yaml.YAMLError` → `OdooConfigError`, `urllib.error.URLError` → `OdooConnectionError`, `RPCError` → `OdooAuthError`
- `batch_write` rolls back (via `env.invalidate()`) on any exception and re-raises

## Cross-Cutting Concerns

**Logging:** stdlib `logging`; each module creates `logger = logging.getLogger(__name__)`. `ProxyJSON` logs send/receive at DEBUG level with password redaction (`odoorpc_toolbox/rpc/jsonrpc.py:18-21`). No structured logging format enforced.

**Validation:** Input validation at `ODOO.__init__` (protocol whitelist, port/timeout type coercion). YAML config validated implicitly via key access; missing `Server` key raises `KeyError` which propagates as-is (not wrapped).

**Authentication:** Session-cookie-based via urllib `CookieJar` / httpx client. The session cookie is stored in the shared `Transport` instance and reused for all subsequent requests within a connection lifetime.

---

*Architecture analysis: 2026-05-28*
