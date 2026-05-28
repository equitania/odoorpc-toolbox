# External Integrations

**Analysis Date:** 2026-05-28

## APIs & External Services

**Odoo Server (primary integration target):**
- Odoo 10–19 via JSON-RPC 2.0 over HTTP/HTTPS
  - SDK/Client: Internalized — no external OdooRPC package. All RPC logic lives in `odoorpc_toolbox/odoo.py`, `odoorpc_toolbox/rpc/jsonrpc.py`, and `odoorpc_toolbox/rpc/transport.py`
  - Auth: YAML config keys `Server.user`, `Server.password`, `Server.database`
  - Connection config: `Server.url`, `Server.port`, `Server.protocol`

## Protocol Details

**JSON-RPC 2.0 (primary):**
- Endpoint: `POST /jsonrpc`
- Request envelope: `{ "service": ..., "method": ..., "args": [...] }`
- Response envelope: `{ "result": ..., "error": ... }`
- Used for: all model operations (`execute`, `execute_kw`), DB management, reports
- Implementation: `odoorpc_toolbox/rpc/jsonrpc.py` (`ProxyJSON` class)

**Web session endpoint:**
- Endpoint: `POST /web/session/authenticate`
- Used for login in Odoo < 10 and Odoo >= 19 (when JSON-2 is enabled)
- Returns: `uid`, `user_context`

**JSON-2 API (Odoo 19+, currently disabled):**
- Endpoint: `POST /json/2/<model>/<method>`
- Plain JSON POST without JSON-RPC envelope
- Requires Bearer token auth (`Authorization: bearer <API_KEY>`)
- Currently disabled — returns `False` from `ODOO._use_json2` in `odoorpc_toolbox/odoo.py:216`
- TODO: Implement Bearer token auth (Phase 4, see comment at `odoo.py:214`)
- Legacy `/jsonrpc` endpoint is deprecated in Odoo v19 but still functional

**Raw HTTP endpoint:**
- Used for report downloads via `ODOO.http()` → `odoorpc_toolbox/report.py`
- Odoo 14+ report download requires CSRF token (raises `NotImplementedError`)

## Authentication Flow

**Odoo 10–18 (active path):**
1. `POST /jsonrpc` with `service=common`, `method=login`, `args=[db, user, password]`
2. Returns `uid` (integer)
3. `POST /jsonrpc` with `service=object`, `method=execute`, to call `res.users.context_get`
4. Returns `user_context` dict
5. Session stored in `ODOO._env` (`odoorpc_toolbox/environment.py`)
6. All subsequent calls send `[db, uid, password, model, method, ...]` in `args`

**Odoo < 10:**
1. `POST /web/session/authenticate` with `{db, login, password}`
2. Returns `uid` + `user_context` directly

**Session persistence:**
- Session cookie managed by `http.cookiejar.CookieJar` (urllib backend)
- Sessions can be saved/loaded from `~/.odoorpcrc` INI file via `ODOO.save()`/`ODOO.load()`
- `odoorpc_toolbox/session.py` — RC file read/write

## Transport Backends

**UrllibTransport (default, no extra deps):**
- Uses Python stdlib `urllib.request` with `CookieJar`
- No connection pooling, no HTTP/2
- Implementation: `odoorpc_toolbox/rpc/transport.py:71`
- Activated when: httpx not installed, or `transport.backend = "urllib"` in YAML config

**HttpxTransport (optional, requires `httpx[http2]>=0.25.0`):**
- Uses `httpx.Client` with configurable connection pooling and HTTP/2
- Supports retry with exponential backoff + jitter
- Implementation: `odoorpc_toolbox/rpc/transport.py:133`
- Activated when: httpx installed and `transport.backend = "httpx"` or `"auto"` in YAML config

**Transport factory:**
- `create_transport(backend="auto", ...)` in `odoorpc_toolbox/rpc/transport.py:269`
- `"auto"` mode: tries httpx first, silently falls back to urllib on `ImportError`

**Transport protocol (structural typing):**
- `Transport` Protocol class in `odoorpc_toolbox/rpc/transport.py:41`
- Required methods: `request(url, data, headers, timeout) → TransportResponse`, `close()`
- Custom transports can be injected into `ODOO(transport=my_transport)`

**MetricsTransport (decorator pattern):**
- Wraps any `Transport` instance to record request timing and error rates
- `odoorpc_toolbox/rpc/metrics.py:79`
- `RequestMetrics` dataclass: `total_requests`, `total_errors`, `total_time_ms`, `avg_time_ms`, `error_rate`
- Thread-safe via `threading.Lock`
- Accessed via `odoo.metrics` property

## Retry Configuration

**Via HttpxTransport + RetryConfig:**
- `RetryConfig(max_attempts=3, backoff_factor=0.5, retry_on=(502, 503, 504))`
- `odoorpc_toolbox/rpc/transport.py:57`
- Algorithm: exponential backoff `backoff_factor * 2^attempt` + random jitter (0–10%)
- Retries on: HTTP 502, 503, 504 status codes

**Via YAML config (applied by OdooConnection):**
```yaml
retry:
  max_attempts: 3
  backoff_factor: 0.5
  retry_on: [502, 503, 504]
```
- `odoorpc_toolbox/odoo_connection.py:127` — builds `RetryConfig` from parsed YAML

## Data Storage

**Databases:**
- None — this is a client library. The Odoo server manages its own PostgreSQL database.
- Database name passed as YAML config `Server.database` and forwarded in every RPC call.

**File Storage:**
- Local filesystem only — YAML config files read by `OdooConnection.__init__`
- Session RC file: `~/.odoorpcrc` (INI format, optional)

**Caching:**
- In-process `TTLCache` — `odoorpc_toolbox/cache.py`
- Thread-safe LRU+TTL eviction, no external cache service (no Redis, no Memcached)
- Used in `EqOdooConnection` for Odoo lookup results (countries, states, UoMs, partners, categories)
- Default: `maxsize=256`, `ttl=3600s`

## MCP-Compatible Introspection

**Model Context Protocol (MCP) discovery:**
- `odoorpc_toolbox/introspection.py`
- `get_available_methods()` — returns JSON Schema for all public EqOdooConnection methods
- `get_method_schema(method_name)` — returns schema for a single method
- `print_available_methods()` — prints human-readable listing
- Exported from package `__init__.py` — no external MCP SDK dependency required

## Authentication & Identity

**Auth Provider:**
- Custom — credentials stored in YAML config file, no OAuth, no SAML, no SSO
- Passwords are NOT logged (filtered in `odoorpc_toolbox/rpc/jsonrpc.py:17` `LOG_HIDDEN_JSON_PARAMS`)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, no Datadog)

**Logs:**
- Python stdlib `logging` throughout (`logging.getLogger(__name__)`)
- JSON send/receive logged at DEBUG level in `odoorpc_toolbox/rpc/jsonrpc.py`
- Password masked in log output via `get_json_log_data()`

**Metrics:**
- In-process only via `RequestMetrics` + `MetricsTransport`
- No external metrics export (no Prometheus, no StatsD)

## CI/CD & Deployment

**Hosting:**
- PyPI — published as `odoorpc-toolbox`
- GitHub: `https://github.com/equitania/odoorpc-toolbox`

**CI Pipeline:**
- Not detected in repository (no `.github/workflows/`, no `.gitlab-ci.yml` found at root)

## Environment Configuration

**Required config (YAML file):**
- `Server.url` — Odoo server URL (http:// or https://)
- `Server.port` — Server port (443 for SSL, 8069 for local)
- `Server.user` — Odoo username
- `Server.password` — Odoo password
- `Server.database` — Database name

**Optional env vars:**
- `ODOO_TEST_CONFIG` — path to YAML config for integration tests and benchmarks

**Secrets location:**
- YAML config file on local filesystem — not committed (example: `yaml_examples/test_config.yaml.example`)

## Webhooks & Callbacks

**Incoming:** None — client library only, no HTTP server component

**Outgoing:** None — all communication is request-initiated RPC calls to Odoo

## Version-Specific Routing

All version branching lives in `odoorpc_toolbox/odoo.py`:

| Odoo Version | Login endpoint | execute/execute_kw endpoint |
|---|---|---|
| < 10 | `/web/session/authenticate` | `/jsonrpc` (service=object) |
| 10–18 | `/jsonrpc` (service=common) | `/jsonrpc` (service=object) |
| 19+ | `/web/session/authenticate` | `/jsonrpc` (JSON-2 disabled, TODO) |

UoM model routing in `odoorpc_toolbox/base_helper.py`:
- Odoo 10–12: `product.uom`
- Odoo 13+: `uom.uom`

---

*Integration audit: 2026-05-28*
