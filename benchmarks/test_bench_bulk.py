"""Benchmark: Bulk operations scaling (10/50/100 records)."""

import pytest

from benchmarks.baselines import search_then_read
from benchmarks.rpc_counter import counting


@pytest.mark.benchmark
@pytest.mark.slow
class TestBulkBenchmark:
    """Measure scaling behavior with increasing record counts."""

    @pytest.mark.parametrize("record_count", [10, 50, 100])
    def test_search_read_scaling(self, connection, odoo, benchmark_results, record_count):
        """search_read at different scales: always 1 RPC vs 2 RPCs."""
        domain = []
        fields = ["name", "email", "phone", "city", "country_id"]

        # Baseline: search + read = 2 RPCs regardless of count
        with counting(odoo, f"search_read ({record_count} records) - baseline") as baseline:
            search_then_read(odoo, "res.partner", domain, fields, limit=record_count)

        # Optimized: single search_read = 1 RPC
        with counting(odoo, f"search_read ({record_count} records) - v0.6.0") as optimized:
            connection.search_read("res.partner", domain, fields, limit=record_count)

        benchmark_results.append((baseline, optimized))

        assert optimized.rpc_calls < baseline.rpc_calls

    @pytest.mark.parametrize("lookup_count", [10, 50, 100])
    def test_cached_lookup_scaling(self, connection, odoo, benchmark_results, lookup_count):
        """Cached lookups at scale: 1 RPC + (N-1) cache hits vs N RPCs."""
        # Find a state to lookup
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

        # Baseline: N uncached lookups
        with counting(odoo, f"cached_lookup ({lookup_count}x) - baseline") as baseline:
            for _ in range(lookup_count):
                connection.odoo.execute_kw(
                    "res.country.state",
                    "search",
                    [[("name", "=", state_name), ("country_id", "=", country_id)]],
                )

        # Clear cache before optimized run
        connection.clear_cache()

        # Warm up model metadata (fields_get) outside the measurement
        connection.get_state_id(country_id, state_name)
        connection.clear_cache()

        # Optimized: 1 RPC + (N-1) cache hits
        with counting(odoo, f"cached_lookup ({lookup_count}x) - v0.6.0") as optimized:
            for _ in range(lookup_count):
                connection.get_state_id(country_id, state_name)

        benchmark_results.append((baseline, optimized))

        assert (
            optimized.rpc_calls == 1
        ), f"Expected 1 RPC call for {lookup_count} cached lookups, got {optimized.rpc_calls}"
