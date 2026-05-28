# Release Notes

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
