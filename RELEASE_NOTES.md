# Release Notes

## Version 0.8.1 (10.06.2026)

### Fixed
- **Regression**: Password-based login on Odoo 19+ was broken in 0.8.0. Real passwords are not valid Bearer tokens, so the JSON-2 bootstrap failed with HTTP 401 "Invalid apikey" - while the same credentials worked before 0.8.0 via the legacy `/jsonrpc` login. Now: when no explicit `api_key` is given and the server rejects the credential with 401/403, `login()` falls back to the legacy `/jsonrpc` dispatch (works until Odoo 22) and logs a warning recommending an API key. An explicitly passed invalid `api_key` still raises (no silent fallback).
- `_use_json2` now requires both Odoo >= 19 AND a stored API key: password-authenticated sessions route `execute`/`execute_kw` over legacy `/jsonrpc` instead of crashing on the missing Bearer token.
- Verified live against Odoo 19: both paths (password fallback with warning, API key via JSON-2) work; new unit tests and integration test cover the fallback.

## Version 0.8.0 (10.06.2026)

**Odoo 19+ JSON-2 API Full Support (Phase 4)**

### Added
- API key authentication for Odoo 19+: `Authorization: bearer <key>` header (lowercase scheme per Odoo docs), new `api_key` parameter on `ODOO.login()` and `api_key` field in the YAML `Server` section (takes precedence over `password`; an API key in the `password` field keeps working)
- JSON-2 login bootstrap via `/json/2/res.users/context_get` - no login round-trip, supports API-only bot accounts; uid fallback via `res.users/search` when the context does not expose it
- `_map_args_to_json2()` mapping table translating positional arguments of known ORM methods (search, search_read, read, write, create, unlink, ...) into JSON-2 named parameters; unmappable positional calls fall back to legacy `/jsonrpc` with a DeprecationWarning
- HTTP status mapping for JSON-2: 4xx/5xx responses raise `RPCError` carrying the server error payload plus `status_code` in `.info`
- `X-Odoo-Database` header on JSON-2 requests (multi-database deployments)
- `/web/version` as primary version detection (plain GET, Odoo 19+), fallback to `/web/webclient/version_info`
- DB service on Odoo 19+: `db.list()` uses `/web/database/list`, `db.dump()` uses `/web/database/backup` (raw binary, no base64 round-trip)
- `counting_json2()` benchmark counter (patches `odoo.json` AND `odoo._json2_call`), `legacy_execute_kw()` baseline, new `benchmarks/test_bench_json2.py`
- Odoo 19 integration test suite `tests/integration/test_int_json2.py` with `ODOO19_TEST_CONFIG` fixtures and `odoo19` marker; `yaml_examples/test_config_v19.yaml.example`
- `odoorpc-init-config --api-key` CLI option and `api_key` parameter in `generate_config()`
- 35 new unit tests (Bearer headers, status mapping, api_key precedence, parameter mapping, DB routing, transport error handling)

### Changed
- `_use_json2` re-enabled: returns True for Odoo >= 19 (was hardcoded False since 0.7.2)
- `_json2_call()` is kwargs-only (JSON-2 has no positional calling convention) and sends a flat parameter body - the previous `{"args": ..., "kwargs": ...}` wrapper was never accepted by the endpoint
- `UrllibTransport` returns HTTP 4xx/5xx as `TransportResponse` instead of raising `urllib.error.HTTPError` (matches HttpxTransport; root cause of the 0.7.2 JSON-2 deactivation)
- Legacy `/jsonrpc` calls use the API key in the password slot when one is configured (Odoo accepts API keys as RPC passwords)
- DB operations without a machine-readable controller contract (create/drop/duplicate/restore/change_password) stay on `/jsonrpc` and emit a DeprecationWarning on Odoo 19+ - the `/web/database/*` form controllers return errors as HTTP 200 HTML pages
- `report.download()` on Odoo >= 14 raises `NotImplementedError` with an actionable message (reason + workarounds) instead of a terse one-liner
- Corrected `/jsonrpc` EOL in all comments and docs: removal is scheduled for Odoo 22 (fall 2028), not Odoo 20
- Roadmap remapped: Phase 4 shipped as v0.8.0, Smart ORM (Phase 3) moves to v0.9.0

### Fixed
- JSON-2 calls no longer fail with unhandled `urllib.error.HTTPError` on auth errors
- Example config `config_full.yaml` uses `CHANGE_ME` placeholder instead of `secret`

## Version 0.7.4 (10.06.2026)

### Security
- **MEDIUM**: Harden session RC file permissions (`~/.odoorpcrc`). The file stores cleartext passwords but was created with the process umask and only chmod'ed afterwards (TOCTOU race window where other local users could read it); `remove()` never set permissions at all. The file is now created atomically with mode 0o600 via `os.open`, and existing files with loose permissions are tightened on every write. (`odoorpc_toolbox/session.py`)
- **MEDIUM**: Redact request and response bodies in `ProxyHTTP` DEBUG logs. Raw HTTP bodies (JSON-2 payloads, session authentication data) were logged verbatim, and the `TransportResponse` dataclass repr exposed full response bodies including session tokens. Bodies are now logged as size summaries only (`<N bytes>`, `<status NNN, N bytes>`). Closes the leak path before the JSON-2 API is re-enabled for Odoo 19+. (`odoorpc_toolbox/rpc/jsonrpc.py`)

### Added
- `get_http_log_data()` and `get_http_log_result()` helpers for safe HTTP log representations
- 6 new unit tests: RC file permission checks (creation, tightening, remove) and ProxyHTTP log redaction (request body, response body, end-to-end via caplog)

## Version 0.7.3 (28.05.2026)

### Security
- **HIGH**: Fix plaintext password leak in DEBUG logs for legacy `/jsonrpc` calls. The existing `LOG_HIDDEN_JSON_PARAMS` masking only covered named params (`/web/session/authenticate`); positional `args` lists used by `service=common method=login`, `service=object` execute/execute_kw, and all `service=db` methods passed credentials through to `logger.debug` unredacted. Affects the default code path for Odoo 10–18 logins. (`odoorpc_toolbox/rpc/jsonrpc.py`)

### Added
- `LOG_HIDDEN_ARG_INDICES` mapping for `(service, method) → args indices` redaction in `get_json_log_data()`, with a default-deny wildcard `("db", "*")` so unknown db-service methods still mask `args[0]`
- 9 new unit tests covering login, execute_kw, db dump, db change_admin_password, db create_database, unknown db method fallback, and the combined named+positional case

## Version 0.7.2 (19.03.2026)

### Added
- N/A

### Changed
- N/A

### Fixed
- Disable JSON-2 API (`_use_json2` always returns `False`): `/json/2/` endpoint requires Bearer token auth, not session cookies — caused HTTP 401 on Odoo 19 instances
- Version bump to 0.7.2 so `pip install --upgrade` picks up the fix (0.7.1 was published with JSON-2 enabled)
- Updated 6 unit tests to reflect disabled JSON-2 API (v19/v20 now use legacy `/jsonrpc`)
- Updated module docstring in `odoo.py` to document JSON-2 as disabled

## Version 0.7.1 (12.03.2026)

### Added
- Odoo 19+ JSON-2 API support: version-based routing for `execute()` and `execute_kw()`
- `_json2_call()` method for plain JSON POST to `/json/2/<model>/<method>` (no JSON-RPC 2.0 envelope)
- `_use_json2` property for central version check (Odoo >= 19)
- Login via `/web/session/authenticate` for Odoo 19+ (avoids deprecated `/jsonrpc`)
- Deprecation info logging when connected to Odoo 19+
- 14 new unit tests for JSON-2 API paths
- Phase 4 roadmap in tasks.md for full JSON-2 API support (API keys, DB/Report migration)
- Transport abstraction layer with `UrllibTransport` and `HttpxTransport`
- Retry with exponential backoff in `HttpxTransport`
- Extended YAML configuration (transport, retry, timeout, cache sections)
- Request metrics (`RequestMetrics` dataclass)
- `odoorpc-init-config` CLI command for config file generation

### Changed
- `odoo.py`: Login method restructured with 3-way version switch (v19+, v10-18, <v10)
- `execute()` and `execute_kw()` now route to JSON-2 API on Odoo 19+
- `db.py`: Added note about legacy `/jsonrpc` usage for DB service on Odoo 19+
- `Proxy` classes refactored to use Transport abstraction

### Fixed
- N/A
