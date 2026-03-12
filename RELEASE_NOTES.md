# Release Notes

## Version 0.7.0 (12.03.2026)

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
