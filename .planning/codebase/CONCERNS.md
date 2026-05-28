# Codebase Concerns

**Analysis Date:** 2026-05-28

---

## Tech Debt

**Disabled JSON-2 API code paths (Odoo 19+):**
- Issue: `_use_json2` property is hardcoded to return `False` (`odoorpc_toolbox/odoo.py:216`). The `_json2_call()` method (`odoo.py:218-254`) and all routing branches in `login()`, `execute()`, `execute_kw()` that check `self._use_json2` are dead code. The `db.py` module explicitly acknowledges it will not support JSON-2 for DB management (Phase 4/v0.9.0).
- Files: `odoorpc_toolbox/odoo.py:195-254`, `odoorpc_toolbox/db.py:1-12`
- Impact: Odoo v19 is served via the deprecated `/jsonrpc` endpoint, which is scheduled for removal in Odoo v20. If Odoo v20 drops the legacy endpoint, all v20+ connections will break.
- Fix approach: Implement Bearer token auth as described in `odoo.py:198-213`. Requires API key storage in YAML config, `Authorization: bearer <API_KEY>` header injection into the transport layer, `X-Odoo-Database` header for multi-DB, and conversion of positional args to named params for JSON-2 calls. Phase 4 placeholder mentioned at `db.py:9-12`.

**TODO marker for JSON-2 Bearer token auth:**
- Files: `odoorpc_toolbox/odoo.py:214`
- Comment: `# TODO: Implement Bearer token auth for JSON-2 API (Phase 4)`
- The commented-out activation line is: `# return v(self.version)[0] >= 19`
- Impact: No active development is tracked for this; it is only in code comments.

**Report download broken for all currently-relevant Odoo versions (>=14):**
- Issue: `Report.download()` raises `NotImplementedError("Report download requires CSRF token for Odoo >= 14")` for all Odoo versions 14 and above (`odoorpc_toolbox/report.py:88`). Since Odoo 14 was released in 2020, and all actively-supported versions (16, 17, 18, 19) exceed this threshold, the `download()` method is effectively non-functional.
- Files: `odoorpc_toolbox/report.py:84-93`
- Impact: The `odoo.report.download()` public API silently advertises a feature that raises on all modern Odoo versions.
- Fix approach: Obtain CSRF token from session cookies after `/web/session/authenticate`, then pass it in the `X-CSRF-Token` header when calling the Odoo report URL (e.g., `/report/pdf/<report_name>/<ids>`).

**NOTE marker in db.py — DB service legacy endpoint:**
- Files: `odoorpc_toolbox/db.py:8-12`
- Comment: `NOTE: DB service still uses the legacy /jsonrpc endpoint even on Odoo 19+`
- The note defers resolution to "Phase 4 (v0.9.0) when Odoo documents the replacement for DB service operations."

---

## Known Bugs

**Double `_get_proxies()` call on SSL connections:**
- Symptoms: Every SSL connection (protocol `jsonrpc+ssl`) triggers two HTTP requests to `/web/webclient/version_info` during `ODOO.__init__`. The first call (from `ConnectorJSONRPC.__init__` line 82) and the second call (from `ConnectorJSONRPCSSL.__init__` line 148) both use `ssl=True` (Python MRO ensures the subclass property is active for both). Net result: one redundant unauthenticated HTTP round-trip per connection.
- Files: `odoorpc_toolbox/rpc/__init__.py:82`, `odoorpc_toolbox/rpc/__init__.py:147-148`
- Trigger: Any `ODOO()` instantiation with `protocol='jsonrpc+ssl'` or any `OdooConnection` using an `https://` URL.
- Workaround: Pass an explicit `version` parameter to `ODOO()` to skip version detection.

**`cached_lookup` decorator silently bypasses cache for `None` results:**
- Symptoms: If a lookup method returns `None` (i.e., the record was not found in Odoo), the result is never written to the cache (`cache.py:137-141`). Every subsequent call with the same arguments makes a live RPC call. Methods affected include `get_state_id()`, `get_res_partner_title_id()`, `get_country_id_by_code()`, and others decorated with `@cached_lookup()`.
- Files: `odoorpc_toolbox/cache.py:137-141`, `odoorpc_toolbox/base_helper.py:44-57, 79-96, 119-131, 217-232, 315-327`
- Trigger: Any lookup for a value that does not exist in the target Odoo database (e.g., a missing country code, an unknown UoM name). In import pipelines with bad data, this degrades performance significantly.
- Fix approach: Use a sentinel value (e.g., `_CACHE_MISS = object()`) to distinguish "not in cache" from "cached None". Cache the `None` result under the sentinel, return `None` on hit.

**`get_country_id()` not cached despite being a lookup method:**
- Symptoms: `get_country_id()` in `base_helper.py:299-313` is not decorated with `@cached_lookup()`, unlike similar methods (`get_country_id_by_code` is cached, `get_state_id` is cached). Repeated lookups for the same country name each make an RPC call.
- Files: `odoorpc_toolbox/base_helper.py:299-313`
- Fix approach: Add `@cached_lookup()` decorator, consistent with the rest of the lookup API.

---

## Security Considerations

**Credentials stored in memory as plain strings:**
- Risk: `ODOO._password` (`odoo.py:81`) holds the cleartext password for the lifetime of the session. Similarly, `OdooConnection.pw` (`odoo_connection.py:89`) holds the password loaded from YAML. The password is also included inside `args_to_send` lists passed to `execute_kw` at `odoo.py:366-378`, `odoo.py:406-421`.
- Files: `odoorpc_toolbox/odoo.py:81, 296, 366-378, 406-421`, `odoorpc_toolbox/odoo_connection.py:89`
- Current mitigation: `get_json_log_data()` in `jsonrpc.py:44-52` masks `password` only when it appears at the top-level `params` dict key. The password sent in `args_to_send` lists (for `execute`, `execute_kw`) is NOT masked in debug logs.
- Recommendations: Mask password in all positions in debug log output; consider using a `SecretStr`-like wrapper to prevent accidental logging; document that debug logging should not be enabled in production.

**YAML config files store credentials in plaintext:**
- Risk: `yaml_examples/config.yaml`, `yaml_examples/config_full.yaml`, and any user-created config files contain `user:` and `password:` fields. The `OdooConnection.__init__` reads them directly (`odoo_connection.py:88-89`).
- Files: `odoorpc_toolbox/odoo_connection.py:83-91`, `yaml_examples/`
- Current mitigation: `yaml_examples/test_config.yaml` is `.gitignore`-listed (via `.gitignore`).
- Recommendations: Document that production configs should not be committed; consider supporting environment variable substitution (e.g., `password: ${ODOO_PASSWORD}`) in the config loader.

**Session RC file stores plaintext password:**
- Risk: `ODOO.save()` writes the plaintext password to `~/.odoorpcrc` (`session.py:82-86`). File permissions are set to owner read/write only (`stat.S_IREAD | stat.S_IWRITE`), but the password is stored as plain INI text.
- Files: `odoorpc_toolbox/session.py:69-87`
- Current mitigation: File mode 0o600 reduces exposure.
- Recommendations: Document the security model clearly; consider base64 obfuscation at minimum, or keyring integration as an alternative.

**`HttpxTransport` accepts `verify=False` to disable TLS verification:**
- Risk: `create_transport()` passes `verify` through to `httpx.Client(verify=verify)` (`transport.py:156, 173`). The YAML config parser does not expose this as a named option (not present in `config_generator.py`), but it can be passed via `**kwargs` to `create_transport`. If a user passes `verify=False`, TLS is silently disabled with no warning.
- Files: `odoorpc_toolbox/rpc/transport.py:156, 173, 295`
- Current mitigation: Default is `verify=True`.
- Recommendations: Log a warning when `verify=False` is used; consider rejecting it in production mode.

**`UrllibTransport` has no SSL certificate verification control:**
- Risk: The default urllib-based transport provides no way to configure CA bundle or disable/enable verification. Self-signed certificates on Odoo servers will cause connection failures with no documented workaround other than switching to `httpx` backend.
- Files: `odoorpc_toolbox/rpc/transport.py:71-130`

---

## Performance Bottlenecks

**Implicit `fields_get` RPC on first model access:**
- Problem: `Environment._create_model_class()` calls `self._odoo.execute(model, "fields_get")` (`environment.py:184`) every time a new model is first accessed via `odoo.env['model.name']`. This call is not cached — it is only skipped if the model class is already in `env._registry`.
- Files: `odoorpc_toolbox/environment.py:158-190`
- Cause: Model classes are created lazily and cached in `_registry`, but the registry is tied to the `Environment` instance. Creating a new `Environment` (e.g., via `env(context=...)`) copies the registry reference but a fresh login recreates the environment from scratch.
- Improvement path: Persist `fields_get` results in the TTL cache keyed by `(model, version)`; pre-warm the registry for commonly used models at connection time.

**Cache warmup required before meaningful benchmark measurements:**
- Problem: `ARCHITECTURE.md` / project README note that the first model access triggers an implicit `fields_get` RPC. Benchmarks in `benchmarks/` must warm up before measurement (`benchmarks/baselines.py:1-170`). In production code, the first call to any model in a new session is always slower than subsequent calls, which may surprise users.
- Files: `odoorpc_toolbox/environment.py:184`, `benchmarks/baselines.py`

**`TTLCache._evict_oldest()` is O(n) on every insert beyond maxsize:**
- Problem: When the cache is full, `_evict_oldest()` scans all entries with `min()` (`cache.py:85`). For the default `maxsize=256`, this is negligible. For users configuring large caches, this adds per-insert overhead.
- Files: `odoorpc_toolbox/cache.py:81-86`
- Improvement path: Replace `_store` with `collections.OrderedDict` and use `popitem(last=False)` for O(1) eviction.

---

## Fragile Areas

**Monkey-patch targets for benchmarks:**
- Files: `odoorpc_toolbox/odoo.py:158-174` (`ODOO.json()`), `odoorpc_toolbox/cache.py:48-65` (`TTLCache.get()`)
- Why fragile: The `benchmarks/rpc_counter.py` patches `ODOO.json` and `TTLCache.get` as choke-points for all RPC call counting. Any refactoring that changes method names, splits `json()` into sub-methods, or changes how the transport is invoked will silently break benchmark measurements without test failures.
- Safe modification: Any rename or signature change to `ODOO.json()` or `TTLCache.get()` must be reflected in `benchmarks/rpc_counter.py`. Ensure benchmarks still pass with `pytest benchmarks/ -m "benchmark and not slow"` after structural changes.

**`MetaModel.__getattr__` on class silently swallows `AttributeError`:**
- Files: `odoorpc_toolbox/model.py:47-57`
- Why fragile: `MetaModel.__getattr__` converts any missing class attribute into an RPC method call. If a typo occurs (e.g., `User.serach(...)` instead of `User.search(...)`), no `AttributeError` is raised — instead, an RPC call to the Odoo server with the typo'd method name is made, which may produce a confusing `RPCError` rather than a clear Python error.
- Test coverage: No unit test covers this silent-failure case.

**`_json2_call()` deserializes response with `json.loads(response.body.decode("utf-8"))`:**
- Files: `odoorpc_toolbox/odoo.py:249`
- Why fragile: If `response.body` is not valid UTF-8 or not valid JSON (e.g., an HTML error page from a proxy), this raises `UnicodeDecodeError` or `json.JSONDecodeError` without any wrapping into the library's own exception hierarchy. This is inconsistent with `ProxyJSON.__call__` which also raises raw `json.JSONDecodeError` but is at least documented.

**`get_res_partner_id()` hardcodes custom field names:**
- Files: `odoorpc_toolbox/base_helper.py:59-77`
- Why fragile: The method searches on `supplier_number` and `customer_number` fields (`base_helper.py:73, 75`). These are not standard Odoo fields — they are custom fields presumably specific to Equitania's Odoo setup. Using this method against a standard Odoo instance will cause an `RPCError` (field not found) with no helpful error message.
- Safe modification: Make the field names configurable parameters, or document that this method requires custom Odoo modules.

---

## Scaling Limits

**Single-threaded session cookies (urllib transport):**
- Current capacity: Single connection per `ODOO` instance; `UrllibTransport` uses one `CookieJar` shared across all requests.
- Limit: Not thread-safe for concurrent requests from multiple threads using the same `ODOO` instance (the `TTLCache` is thread-safe, but the urllib opener is not).
- Scaling path: Use `HttpxTransport` with connection pooling for concurrent workloads; document threading model explicitly.

**`batch_write` context manager accumulates all writes in memory:**
- Files: `odoorpc_toolbox/batch.py`
- Limit: For very large import batches (tens of thousands of records), the accumulated `_values_to_write` dict in each `Model` instance and the `env._dirty` WeakSet can consume significant memory before `env.batch_commit()` is called.

---

## Dependencies at Risk

**`/jsonrpc` endpoint deprecated in Odoo 19, scheduled for removal in v20:**
- Risk: The entire library is built on the `/jsonrpc` service dispatch endpoint. Odoo 19 documentation marks it as deprecated. If Odoo 20 removes it, the library becomes non-functional for v20+ without the JSON-2 Bearer token implementation (see Tech Debt section).
- Impact: All `execute()`, `execute_kw()`, `db.*`, `report.*` calls break.
- Migration plan: Implement JSON-2 API support (Phase 4, `odoo.py:214`).

**`httpx[http2]` is optional but silently falls back:**
- Risk: `create_transport(backend='auto')` silently falls back to `UrllibTransport` if `httpx` is not installed (`transport.py:296-300`). Users who configure retry logic in their YAML `retry:` section may not realize their retry config is silently ignored when urllib is the active backend (urllib has no retry).
- Files: `odoorpc_toolbox/rpc/transport.py:269-302`, `odoorpc_toolbox/odoo_connection.py:112-146`
- Impact: Silent degradation — retry config is parsed, `RetryConfig` is created, but only `HttpxTransport` uses it. `UrllibTransport` ignores it entirely.
- Migration plan: Log a warning when retry config is non-default but urllib is active.

---

## Test Coverage Gaps

**JSON-2 code paths have no integration test coverage:**
- What's not tested: The entire `_json2_call()` method, the `login()` branch for `_use_json2=True`, and the `execute()`/`execute_kw()` JSON-2 routing are only tested with mocks in unit tests. No live Odoo 19 integration test exists.
- Files: `odoorpc_toolbox/odoo.py:218-254`, `tests/test_odoo.py:326-380`
- Risk: When JSON-2 support is re-enabled, there is no integration safety net.
- Priority: Medium (currently all paths are disabled; becomes High when Phase 4 begins).

**`Report.download()` has no test coverage for Odoo >= 14:**
- What's not tested: The `NotImplementedError` path at `report.py:88` has no dedicated unit test. There is also no integration test for `Report.list()`.
- Files: `odoorpc_toolbox/report.py:84-93`
- Risk: Changes to the report module could silently break the only functional path (`list()`) without detection.
- Priority: Low (method is non-functional anyway for >=14).

**`cached_lookup` None-bypass bug has no regression test:**
- What's not tested: No test verifies that `@cached_lookup()` bypasses the cache when the result is `None`, nor that repeated calls with the same "not found" arguments each result in an RPC call.
- Files: `odoorpc_toolbox/cache.py:137-141`, `tests/test_cache.py`
- Risk: The bug persists silently; a fix could accidentally break other behavior without test coverage to confirm correctness.
- Priority: High.

**`ConnectorJSONRPCSSL` double `_get_proxies` call has no test:**
- What's not tested: No unit test asserts that version detection runs exactly once for SSL connections.
- Files: `odoorpc_toolbox/rpc/__init__.py:82, 148`, `tests/test_rpc.py`
- Priority: Medium.

**`get_country_id()` missing `@cached_lookup` has no test:**
- What's not tested: No test confirms that `get_country_id()` makes N RPC calls for N identical lookups (proving the missing cache).
- Files: `odoorpc_toolbox/base_helper.py:299-313`
- Priority: Low.

---

*Concerns audit: 2026-05-28*
