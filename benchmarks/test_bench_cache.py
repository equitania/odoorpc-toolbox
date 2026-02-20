"""Benchmark: Cache hit/miss measurement for repeated lookups."""

import pytest

from benchmarks.baselines import get_state_id_uncached
from benchmarks.rpc_counter import counting, counting_with_cache


@pytest.mark.benchmark
class TestCacheBenchmark:
    """Measure cache effectiveness for repeated lookups."""

    def test_state_lookup_repeated(self, connection, fresh_cache, odoo, benchmark_results, cache_results):
        """10 identical state lookups: expect 1 RPC + 9 cache hits (v0.6.0) vs 10 RPCs (v0.5.1)."""
        # Find a valid country/state combination first
        states = connection.odoo.execute_kw(
            "res.country.state",
            "search_read",
            [[]],
            {"fields": ["name", "country_id"], "limit": 1},
        )
        if not states:
            pytest.skip("No states found in database")

        state_name = states[0]["name"]
        country_id = states[0]["country_id"][0]

        # Baseline: 10 uncached lookups = 10 RPCs
        with counting(odoo, "state_lookup x10 - baseline") as baseline:
            for _ in range(10):
                get_state_id_uncached(connection, country_id, state_name)

        # Clear cache before optimized run
        connection.clear_cache()

        # Optimized: 1 RPC + 9 cache hits
        with counting_with_cache(connection, "state_lookup x10 - v0.6.0") as optimized:
            for _ in range(10):
                connection.get_state_id(country_id, state_name)

        benchmark_results.append((baseline, optimized))
        cache_results.append(optimized)

        assert (
            optimized.rpc_calls < baseline.rpc_calls
        ), f"Expected fewer RPCs: v0.6.0={optimized.rpc_calls} vs v0.5.1={baseline.rpc_calls}"
        assert optimized.cache_hits >= 9, f"Expected >=9 cache hits, got {optimized.cache_hits}"

    def test_country_code_lookup_repeated(self, connection, fresh_cache, odoo, benchmark_results, cache_results):
        """10 country code lookups with 3 unique codes: expect 3 RPCs + 7 cache hits."""
        codes = ["DE", "US", "FR"]

        # Baseline: 10 uncached lookups = 10 RPCs
        with counting(odoo, "country_code x10 (3 unique) - baseline") as baseline:
            for i in range(10):
                code = codes[i % len(codes)]
                connection.odoo.execute_kw(
                    "res.country",
                    "search",
                    [[("code", "=", code)]],
                )

        # Clear cache for optimized run
        connection.clear_cache()

        # Optimized: 3 RPCs + 7 cache hits
        with counting_with_cache(connection, "country_code x10 (3 unique) - v0.6.0") as optimized:
            for i in range(10):
                code = codes[i % len(codes)]
                connection.get_country_id_by_code(code)

        benchmark_results.append((baseline, optimized))
        cache_results.append(optimized)

        assert optimized.rpc_calls < baseline.rpc_calls
        assert optimized.cache_hits >= 7, f"Expected >=7 cache hits, got {optimized.cache_hits}"

    def test_uom_lookup_repeated(self, connection, fresh_cache, odoo, benchmark_results, cache_results):
        """5 repeated UoM lookups: expect 1 RPC + 4 cache hits."""
        uom_name = "Units"

        # Baseline: 5 uncached lookups
        with counting(odoo, "uom_lookup x5 - baseline") as baseline:
            for _ in range(5):
                connection.odoo.execute_kw(
                    "uom.uom",
                    "search",
                    [[("name", "=", uom_name)]],
                )

        # Clear cache
        connection.clear_cache()

        # Optimized: 1 RPC + 4 cache hits
        with counting_with_cache(connection, "uom_lookup x5 - v0.6.0") as optimized:
            for _ in range(5):
                connection.get_product_uom_id(uom_name)

        benchmark_results.append((baseline, optimized))
        cache_results.append(optimized)

        assert optimized.rpc_calls < baseline.rpc_calls
