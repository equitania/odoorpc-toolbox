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

### Phase 3: Smart ORM → v0.9.0

- [ ] **Prefetch-System für Relationen** - `browse_with_prefetch()` Classmethod + erweiterte `_init_values()` um N+1-Query-Problem zu lösen
- [ ] **`_prefetch_relations()`** - Sammelt alle Relation-IDs, batch-lädt Ziel-Records, reduziert O(N×M) auf O(M) RPC-Calls
- [ ] **Batch-Commit Erweiterung** - Gruppierung nach Model, pro Record alle geänderten Fields in einem `write()`
- [ ] **Deferred Auto-Commit** - Neuer Modus `auto_commit="deferred"`: Field-Writes markieren Record als dirty, Commit aufgeschoben bis zum nächsten Read-RPC-Call oder explizitem `commit()`
- [ ] **Flush-Trigger** - Vor RPC-Calls in `Model.__getattr__` automatisch dirty Records committen
- [ ] **`auto_commit` Validierung** - `tools.py`: Akzeptiert `True`, `False`, `"deferred"`
- [ ] **Tests** - `test_prefetch.py`, erweiterte `test_batch.py`

### Phase 3.1: Odoo 19+ JSON-2 API Schnelllösung → v0.7.1 ✅

- [x] **Login-Weiche für Odoo 19+** - `/web/session/authenticate` statt deprecated `/jsonrpc` für Login
- [x] **`_json2_call()` Methode** - Plain JSON POST an `/json/2/<model>/<method>` ohne JSON-RPC 2.0 Envelope
- [x] **Version-Weiche `execute_kw()`** - Odoo ≥19 → JSON-2 API, ≤18 → Legacy `/jsonrpc`
- [x] **Version-Weiche `execute()`** - Analog zu `execute_kw()`
- [x] **`_use_json2` Property** - Zentrale Version-Prüfung `v(self.version)[0] >= 19`
- [x] **Deprecation-Logging** - Info-Log nach Login auf Odoo 19+ mit Hinweis auf DB/Report Legacy
- [x] **DB-Service Hinweis** - TODO-Kommentar in `db.py` für Legacy-Endpoint-Nutzung
- [x] **14 neue Unit-Tests** - Version-Weiche, Login-Pfade, JSON-2 Format, Error-Handling, DB-Service

### Phase 4: Odoo 19+ JSON-2 API Vollunterstützung → v0.8.0 ✅

- [x] **API-Key Authentication** - `Authorization: bearer <key>` Header (lowercase per Odoo-Doku), YAML-Config `api_key` Feld, Passwort-Feld als Fallback-API-Key ✅
- [x] **DB-Service Migration** - `list()` → `/web/database/list`, `dump()` → `/web/database/backup` (binär, kein Base64). create/drop/duplicate/restore/change_password bleiben auf `/jsonrpc` (Form-Controller liefern Fehler als HTTP 200 HTML — kein maschinenlesbarer Kontrakt) mit DeprecationWarning ab v19 ✅
- [x] **Report-Service** - Kein externer API-Pfad für Report-Download (Render-Methoden sind underscore-privat); `NotImplementedError` mit handlungsleitender Meldung inkl. Workarounds ✅
- [x] **HTTP Status Code Handling** - 4xx/5xx → `RPCError` mit Server-Payload + `status_code` in `.info`; `UrllibTransport` gibt HTTPError als `TransportResponse` zurück ✅
- [x] **API-Only Users** - Login-Bootstrap via `/json/2/res.users/context_get` (User wird serverseitig aus dem API-Key abgeleitet), uid-Fallback via `res.users/search` ✅
- [x] **`/web/version` Endpoint** - Primäre Version-Detection (GET, plain JSON), Fallback auf `/web/webclient/version_info` ✅
- [x] **Response-Format Anpassung** - JSON-2 liefert direkte Ergebnisse (kein `{"result": ...}` Wrapper) ✅
- [x] **Named Parameters** - `_map_args_to_json2()` Mapping-Tabelle für bekannte ORM-Methoden; unmappbare positionale Calls fallen mit DeprecationWarning auf `/jsonrpc` zurück ✅
- [x] **Integration Tests gegen Odoo 19** - `tests/integration/test_int_json2.py` (ODOO19_TEST_CONFIG), Marker `odoo19` ✅
- [x] **Benchmarks JSON-2 vs Legacy** - `counting_json2()` (patcht `odoo.json` + `odoo._json2_call`), `benchmarks/test_bench_json2.py` ✅
- [ ] **Legacy-Endpoint Entfernung** - `/jsonrpc` Code entfernen wenn Odoo 22 Minimum wird (Entfernung laut Odoo-Doku in Odoo 22, Herbst 2028)

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

### Phase 3: Smart ORM → v0.9.0

- [ ] **Prefetch system for relations** - `browse_with_prefetch()` classmethod + extended `_init_values()` to solve N+1 query problem
- [ ] **`_prefetch_relations()`** - Collects all relation IDs, batch-loads target records, reduces O(N×M) to O(M) RPC calls
- [ ] **Batch commit enhancement** - Grouping by model, per record all changed fields in a single `write()`
- [ ] **Deferred auto-commit** - New mode `auto_commit="deferred"`: field writes mark record as dirty, commit deferred until next read RPC call or explicit `commit()`
- [ ] **Flush trigger** - Before RPC calls in `Model.__getattr__` automatically commit dirty records
- [ ] **`auto_commit` validation** - `tools.py`: Accepts `True`, `False`, `"deferred"`
- [ ] **Tests** - `test_prefetch.py`, extended `test_batch.py`

### Phase 3.1: Odoo 19+ JSON-2 API Quick Fix → v0.7.1 ✅

- [x] **Login switch for Odoo 19+** - `/web/session/authenticate` instead of deprecated `/jsonrpc` for login
- [x] **`_json2_call()` method** - Plain JSON POST to `/json/2/<model>/<method>` without JSON-RPC 2.0 envelope
- [x] **Version switch `execute_kw()`** - Odoo ≥19 → JSON-2 API, ≤18 → legacy `/jsonrpc`
- [x] **Version switch `execute()`** - Same as `execute_kw()`
- [x] **`_use_json2` property** - Central version check `v(self.version)[0] >= 19`
- [x] **Deprecation logging** - Info log after login on Odoo 19+ noting DB/Report legacy usage
- [x] **DB service note** - TODO comment in `db.py` for legacy endpoint usage
- [x] **14 new unit tests** - Version switch, login paths, JSON-2 format, error handling, DB service

### Phase 4: Odoo 19+ JSON-2 API Full Support → v0.8.0 ✅

- [x] **API key authentication** - `Authorization: bearer <key>` header (lowercase per Odoo docs), YAML config `api_key` field, password field doubles as API key for backward compat ✅
- [x] **DB service migration** - `list()` → `/web/database/list`, `dump()` → `/web/database/backup` (binary, no base64). create/drop/duplicate/restore/change_password stay on `/jsonrpc` (the form controllers return errors as HTTP 200 HTML - no machine-readable contract) with DeprecationWarning on v19+ ✅
- [x] **Report service** - No external API path for report download (render methods are underscore-private); `NotImplementedError` with actionable message including workarounds ✅
- [x] **HTTP status code handling** - 4xx/5xx → `RPCError` carrying the server payload + `status_code` in `.info`; `UrllibTransport` returns HTTPError as `TransportResponse` ✅
- [x] **API-only users** - Login bootstrap via `/json/2/res.users/context_get` (user derived server-side from the API key), uid fallback via `res.users/search` ✅
- [x] **`/web/version` endpoint** - Primary version detection (GET, plain JSON), fallback to `/web/webclient/version_info` ✅
- [x] **Response format adaptation** - JSON-2 returns direct results (no `{"result": ...}` wrapper) ✅
- [x] **Named parameters** - `_map_args_to_json2()` mapping table for known ORM methods; unmappable positional calls fall back to `/jsonrpc` with a DeprecationWarning ✅
- [x] **Integration tests against Odoo 19** - `tests/integration/test_int_json2.py` (ODOO19_TEST_CONFIG), marker `odoo19` ✅
- [x] **Benchmarks JSON-2 vs legacy** - `counting_json2()` (patches `odoo.json` + `odoo._json2_call`), `benchmarks/test_bench_json2.py` ✅
- [ ] **Legacy endpoint removal** - Remove `/jsonrpc` code when Odoo 22 becomes minimum (removal scheduled for Odoo 22, fall 2028 per Odoo docs)
