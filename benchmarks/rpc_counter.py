"""RPC call counter via monkey-patching ODOO.json().

Provides context managers to count JSON-RPC calls and measure timing
during benchmark scenarios. Thread-safe via threading.Lock().
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

    from odoorpc_toolbox.base_helper import EqOdooConnection
    from odoorpc_toolbox.odoo import ODOO


@dataclass
class RPCMetrics:
    """Collected metrics for a benchmark scenario.

    Attributes:
        scenario: Name of the benchmark scenario.
        rpc_calls: Total number of RPC calls made.
        rpc_calls_by_method: Breakdown of RPC calls by service method.
        total_time_ms: Total wall-clock time in milliseconds.
        call_times_ms: Individual call durations in milliseconds.
        cache_hits: Number of cache hits (when tracking cache).
        cache_misses: Number of cache misses (when tracking cache).
    """

    scenario: str = ""
    rpc_calls: int = 0
    rpc_calls_by_method: dict[str, int] = field(default_factory=dict)
    total_time_ms: float = 0.0
    call_times_ms: list[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def avg_call_time_ms(self) -> float:
        """Average time per RPC call in milliseconds."""
        if not self.call_times_ms:
            return 0.0
        return sum(self.call_times_ms) / len(self.call_times_ms)

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as a percentage (0-100)."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100


@contextmanager
def counting(odoo: ODOO, scenario: str = "") -> Generator[RPCMetrics, None, None]:
    """Context manager that counts RPC calls on an ODOO instance.

    Monkey-patches ``ODOO.json()`` to intercept and count all JSON-RPC calls.

    Args:
        odoo: The ODOO instance to monitor.
        scenario: Name for this benchmark scenario.

    Yields:
        RPCMetrics: Metrics object that gets populated during the block.

    Example:
        >>> with counting(connection.odoo, "search_read") as metrics:
        ...     result = connection.search_read("res.partner", [], ["name"])
        >>> print(f"RPC calls: {metrics.rpc_calls}")
    """
    metrics = RPCMetrics(scenario=scenario)
    lock = threading.Lock()
    original_json = odoo.json

    def patched_json(url: str, params: dict) -> dict:
        call_start = time.perf_counter()
        result = original_json(url, params)
        call_end = time.perf_counter()

        call_ms = (call_end - call_start) * 1000

        # Extract service method for breakdown
        method_key = params.get("method", "unknown")
        service = params.get("service", "")
        if service:
            # For execute/execute_kw, include the model method
            args = params.get("args", [])
            if method_key in ("execute", "execute_kw") and len(args) >= 5:
                model = args[3]
                model_method = args[4]
                method_key = f"{service}/{method_key}:{model}.{model_method}"
            else:
                method_key = f"{service}/{method_key}"

        with lock:
            metrics.rpc_calls += 1
            metrics.call_times_ms.append(call_ms)
            metrics.rpc_calls_by_method[method_key] = metrics.rpc_calls_by_method.get(method_key, 0) + 1

        return result

    odoo.json = patched_json
    start_time = time.perf_counter()
    try:
        yield metrics
    finally:
        end_time = time.perf_counter()
        metrics.total_time_ms = (end_time - start_time) * 1000
        odoo.json = original_json


@contextmanager
def counting_with_cache(connection: EqOdooConnection, scenario: str = "") -> Generator[RPCMetrics, None, None]:
    """Context manager that counts both RPC calls and cache hits/misses.

    Monkey-patches both ``ODOO.json()`` and ``TTLCache.get()`` to track
    RPC calls and cache effectiveness.

    Args:
        connection: The EqOdooConnection instance to monitor.
        scenario: Name for this benchmark scenario.

    Yields:
        RPCMetrics: Metrics object with RPC and cache data.

    Example:
        >>> with counting_with_cache(connection, "cached_lookup") as metrics:
        ...     for _ in range(10):
        ...         connection.get_state_id(1, "California")
        >>> print(f"Cache hit rate: {metrics.cache_hit_rate:.0f}%")
    """
    metrics = RPCMetrics(scenario=scenario)
    lock = threading.Lock()
    odoo = connection.odoo
    cache = connection._lookup_cache

    original_json = odoo.json
    original_cache_get = cache.get

    def patched_json(url: str, params: dict) -> dict:
        call_start = time.perf_counter()
        result = original_json(url, params)
        call_end = time.perf_counter()

        call_ms = (call_end - call_start) * 1000

        method_key = params.get("method", "unknown")
        service = params.get("service", "")
        if service:
            args = params.get("args", [])
            if method_key in ("execute", "execute_kw") and len(args) >= 5:
                model = args[3]
                model_method = args[4]
                method_key = f"{service}/{method_key}:{model}.{model_method}"
            else:
                method_key = f"{service}/{method_key}"

        with lock:
            metrics.rpc_calls += 1
            metrics.call_times_ms.append(call_ms)
            metrics.rpc_calls_by_method[method_key] = metrics.rpc_calls_by_method.get(method_key, 0) + 1

        return result

    def patched_cache_get(key: str):
        result = original_cache_get(key)
        with lock:
            if result is not None:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1
        return result

    odoo.json = patched_json
    cache.get = patched_cache_get
    start_time = time.perf_counter()
    try:
        yield metrics
    finally:
        end_time = time.perf_counter()
        metrics.total_time_ms = (end_time - start_time) * 1000
        odoo.json = original_json
        cache.get = original_cache_get
