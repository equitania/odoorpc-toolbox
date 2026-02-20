# Tasks - OdooRPC Toolbox

> **Language / Sprache**: [DE](#deutsche-version) | [EN](#english-version)

---

## Deutsche Version

### Kritische Fehler

- [x] **`__init__.py` erstellen** - Package-Import funktioniert nicht ohne diese Datei ✅
- [x] **Boolean-Bug beheben** - `base_helper.py:247`: `'true'` (String) → `True` (Boolean) ✅
- [x] **`sys.exit(1)` entfernen** - Library wirft jetzt `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Code-Qualität

- [x] **Unbenutzte Variable entfernen** - `odoo_connection.py:85`: `ssl = True` wurde entfernt ✅
- [x] **Return-Typen vereinheitlichen** - `get_res_partner_category_id()` gibt jetzt immer `int` zurück ✅
- [x] **Type Hints vervollständigen** - `tuple` → `Tuple[str, str]` für `extract_street_address_part()` ✅
- [x] **Logging-Konfiguration überarbeiten** - `basicConfig()` entfernt, nur `getLogger(__name__)` ✅

### Neue Funktionen

- [x] **`get_country_id(name)`** - Land-ID anhand des Namens abrufen ✅
- [x] **`get_country_id_by_code(code)`** - Land-ID anhand ISO-Code abrufen ✅
- [x] **`create_partner(data)`** - Partner erstellen mit Validierung ✅
- [x] **`get_product_by_ref(ref)`** - Produkt via interne Referenz suchen ✅
- [x] **`get_product_template_by_ref(ref)`** - Produktvorlage via Referenz suchen ✅
- [x] **`execute_method(model, method, args)`** - Generischer RPC-Methodenaufruf ✅
- [x] **`search_read(model, domain, fields)`** - Suchen und Lesen kombiniert ✅
- [x] **Custom Exception-Klassen** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅
- [x] **MCP-Discovery** - `get_available_methods()`, `get_method_schema()` für MCP-Server ✅

### Dokumentation & Tests

- [x] **Unit-Tests erstellen** - 44 pytest-Tests ✅
- [x] **Docstrings überprüfen** - Alle Methoden vollständig dokumentiert ✅
- [x] **Beispiel-Skripte hinzufügen** - 5 Beispiele in `examples/` ✅

---

## English Version

### Critical Bugs

- [x] **Create `__init__.py`** - Package import doesn't work without this file ✅
- [x] **Fix Boolean bug** - `base_helper.py:247`: `'true'` (string) → `True` (boolean) ✅
- [x] **Remove `sys.exit(1)`** - Library now raises `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅

### Code Quality

- [x] **Remove unused variable** - `odoo_connection.py:85`: `ssl = True` removed ✅
- [x] **Unify return types** - `get_res_partner_category_id()` now always returns `int` ✅
- [x] **Complete type hints** - `tuple` → `Tuple[str, str]` for `extract_street_address_part()` ✅
- [x] **Revise logging configuration** - `basicConfig()` removed, only `getLogger(__name__)` ✅

### New Features

- [x] **`get_country_id(name)`** - Get country ID by name ✅
- [x] **`get_country_id_by_code(code)`** - Get country ID by ISO code ✅
- [x] **`create_partner(data)`** - Create partner with validation ✅
- [x] **`get_product_by_ref(ref)`** - Search product by internal reference ✅
- [x] **`get_product_template_by_ref(ref)`** - Search product template by reference ✅
- [x] **`execute_method(model, method, args)`** - Generic RPC method call ✅
- [x] **`search_read(model, domain, fields)`** - Combined search and read ✅
- [x] **Custom exception classes** - `OdooConnectionError`, `OdooConfigError`, `OdooAuthError` ✅
- [x] **MCP Discovery** - `get_available_methods()`, `get_method_schema()` for MCP servers ✅

### Documentation & Tests

- [x] **Create unit tests** - 44 pytest tests ✅
- [x] **Review docstrings** - All methods fully documented ✅
- [x] **Add example scripts** - 5 examples in `examples/` ✅

---

## Priority / Priorität

| Priority | Task | File | Status |
|----------|------|------|--------|
| 🔴 High | Create `__init__.py` | `odoorpc_toolbox/__init__.py` | ✅ Done |
| 🔴 High | Fix Boolean bug | `base_helper.py:247` | ✅ Done |
| 🔴 High | Replace `sys.exit(1)` | `odoo_connection.py` | ✅ Done |
| 🟡 Medium | Fix return types | `base_helper.py` | ✅ Done |
| 🟡 Medium | Remove dead code | `odoo_connection.py:85` | ✅ Done |
| 🟢 Low | Add new helper methods | `base_helper.py` | ✅ Done (7 new methods) |
| 🟢 Low | Create unit tests | `tests/` | ✅ Done (44 tests) |
| 🟢 Low | MCP Discovery | `introspection.py` | ✅ Done |

---

## Performance & Architektur-Roadmap

### Phase 1: Quick Wins → v0.6.0 ✅

- [x] **Native `search_read()`** - 1 RPC Call statt 2 via `execute_kw` ✅
- [x] **Sequence-Methoden optimiert** - `get_ir_sequence_number_next_actual`: 1 Call statt 2-3; `set_ir_sequence_number_next_actual`: 2 Calls statt 3-4 ✅
- [x] **TTL-Cache für statische Lookups** - Thread-safe `TTLCache` mit maxsize + TTL-Eviction, `@cached_lookup` Decorator ✅
- [x] **Cache auf 5 Methoden angewendet** - `get_state_id`, `get_country_id_by_code`, `get_res_partner_title_id`, `get_res_partner_category_id`, `get_product_uom_id` ✅
- [x] **`batch_write()` Context Manager** - Temporär `auto_commit=False`, Commit bei Exit, Rollback bei Exception ✅
- [x] **`batch_commit()` in Environment** - Gruppiert dirty Records nach Model ✅
- [x] **34 neue Tests** - 145 Tests gesamt, alle bestanden ✅
- [x] **Benchmark-Framework** - 16 Szenarien mit RPC-Counter Monkey-Patch, Baseline-Simulation ✅
- [x] **60 Integrationstests** - Live-Odoo Verifizierung aller Optimierungen ✅

### Phase 2: Transport-Modernisierung → v0.7.0 ✅

- [x] **Transport-Abstraktion** - `Transport` Protocol in `rpc/transport.py` mit `UrllibTransport` (Fallback) und `HttpxTransport` (Connection Pooling, HTTP/2) ✅
- [x] **`create_transport()` Factory** - `backend="auto"` versucht httpx, fällt auf urllib zurück ✅
- [x] **Retry mit Exponential Backoff** - In `HttpxTransport` integriert, konfigurierbar: `max_attempts`, `backoff_factor`, `retry_on` (HTTP-Statuscodes) ✅
- [x] **Erweiterte YAML-Konfiguration** - Neue optionale Sections: `transport`, `retry`, `timeout`, `cache` in Server-Config ✅
- [x] **Request-Metriken** - `RequestMetrics` Dataclass: `total_requests`, `total_errors`, `total_time_ms`, `avg_time_ms`, Thread-safe ✅
- [x] **`Proxy` Refactoring** - `ProxyJSON.__call__` und `ProxyHTTP.__call__` nutzen `self._transport.request()` statt `self._opener.open()` ✅
- [x] **httpx als optionale Dependency** - `pip install odoorpc-toolbox[httpx]` für `httpx[http2]>=0.25.0` ✅
- [x] **Backward-Kompatibilität** - `opener`-Parameter wird in `UrllibTransport` gewrappt ✅
- [x] **Tests** - `test_transport.py` (39 Tests), `test_metrics.py` (19 Tests), erweiterte `test_odoo.py` und `test_connection.py` ✅
- [x] **Config-Initialisierung** - `generate_config()` Funktion + `odoorpc-init-config` CLI-Befehl ✅

### Phase 3: Smart ORM → v0.8.0

- [ ] **Prefetch-System für Relationen** - `browse_with_prefetch()` Classmethod + erweiterte `_init_values()` um N+1-Query-Problem zu lösen
- [ ] **`_prefetch_relations()`** - Sammelt alle Relation-IDs, batch-lädt Ziel-Records, reduziert O(N×M) auf O(M) RPC-Calls
- [ ] **Batch-Commit Erweiterung** - Gruppierung nach Model, pro Record alle geänderten Fields in einem `write()`
- [ ] **Deferred Auto-Commit** - Neuer Modus `auto_commit="deferred"`: Field-Writes markieren Record als dirty, Commit aufgeschoben bis zum nächsten Read-RPC-Call oder explizitem `commit()`
- [ ] **Flush-Trigger** - Vor RPC-Calls in `Model.__getattr__` automatisch dirty Records committen
- [ ] **`auto_commit` Validierung** - `tools.py`: Akzeptiert `True`, `False`, `"deferred"`
- [ ] **Tests** - `test_prefetch.py`, erweiterte `test_batch.py`

---

## Performance & Architecture Roadmap (EN)

### Phase 1: Quick Wins → v0.6.0 ✅

- [x] **Native `search_read()`** - 1 RPC call instead of 2 via `execute_kw` ✅
- [x] **Sequence methods optimized** - `get_ir_sequence_number_next_actual`: 1 call instead of 2-3; `set_ir_sequence_number_next_actual`: 2 calls instead of 3-4 ✅
- [x] **TTL cache for static lookups** - Thread-safe `TTLCache` with maxsize + TTL eviction, `@cached_lookup` decorator ✅
- [x] **Cache applied to 5 methods** - `get_state_id`, `get_country_id_by_code`, `get_res_partner_title_id`, `get_res_partner_category_id`, `get_product_uom_id` ✅
- [x] **`batch_write()` context manager** - Temporarily sets `auto_commit=False`, commits on exit, rollback on exception ✅
- [x] **`batch_commit()` in Environment** - Groups dirty records by model ✅
- [x] **34 new tests** - 145 tests total, all passing ✅
- [x] **Benchmark framework** - 16 scenarios with RPC counter monkey-patch, baseline simulation ✅
- [x] **60 integration tests** - Live Odoo verification of all optimizations ✅

### Phase 2: Transport Modernization → v0.7.0 ✅

- [x] **Transport abstraction** - `Transport` protocol in `rpc/transport.py` with `UrllibTransport` (fallback) and `HttpxTransport` (connection pooling, HTTP/2) ✅
- [x] **`create_transport()` factory** - `backend="auto"` tries httpx, falls back to urllib ✅
- [x] **Retry with exponential backoff** - Integrated in `HttpxTransport`, configurable: `max_attempts`, `backoff_factor`, `retry_on` (HTTP status codes) ✅
- [x] **Extended YAML configuration** - New optional sections: `transport`, `retry`, `timeout`, `cache` in Server config ✅
- [x] **Request metrics** - `RequestMetrics` dataclass: `total_requests`, `total_errors`, `total_time_ms`, `avg_time_ms`, thread-safe ✅
- [x] **`Proxy` refactoring** - `ProxyJSON.__call__` and `ProxyHTTP.__call__` use `self._transport.request()` instead of `self._opener.open()` ✅
- [x] **httpx as optional dependency** - `pip install odoorpc-toolbox[httpx]` for `httpx[http2]>=0.25.0` ✅
- [x] **Backward compatibility** - `opener` parameter wrapped in `UrllibTransport` ✅
- [x] **Tests** - `test_transport.py` (39 tests), `test_metrics.py` (19 tests), extended `test_odoo.py` and `test_connection.py` ✅
- [x] **Config initialization** - `generate_config()` function + `odoorpc-init-config` CLI command ✅

### Phase 3: Smart ORM → v0.8.0

- [ ] **Prefetch system for relations** - `browse_with_prefetch()` classmethod + extended `_init_values()` to solve N+1 query problem
- [ ] **`_prefetch_relations()`** - Collects all relation IDs, batch-loads target records, reduces O(N×M) to O(M) RPC calls
- [ ] **Batch commit enhancement** - Grouping by model, per record all changed fields in a single `write()`
- [ ] **Deferred auto-commit** - New mode `auto_commit="deferred"`: field writes mark record as dirty, commit deferred until next read RPC call or explicit `commit()`
- [ ] **Flush trigger** - Before RPC calls in `Model.__getattr__` automatically commit dirty records
- [ ] **`auto_commit` validation** - `tools.py`: Accepts `True`, `False`, `"deferred"`
- [ ] **Tests** - `test_prefetch.py`, extended `test_batch.py`
