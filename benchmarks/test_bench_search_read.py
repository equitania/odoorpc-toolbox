"""Benchmark: search_read (1 RPC) vs search+read (2 RPCs)."""

import pytest

from benchmarks.baselines import search_then_read
from benchmarks.rpc_counter import counting


@pytest.mark.benchmark
class TestSearchReadBenchmark:
    """Compare native search_read vs old search+read pattern."""

    def test_single_record(self, connection, odoo, benchmark_results):
        """search_read for 1 record: expect 1 RPC (v0.6.0) vs 2 RPCs (v0.5.1)."""
        domain = [("is_company", "=", True)]
        fields = ["name", "email", "phone"]

        # Baseline: search + read = 2 RPCs
        with counting(odoo, "search_read (1 record) - baseline") as baseline:
            search_then_read(odoo, "res.partner", domain, fields, limit=1)

        # Optimized: native search_read = 1 RPC
        with counting(odoo, "search_read (1 record) - v0.6.0") as optimized:
            connection.search_read("res.partner", domain, fields, limit=1)

        benchmark_results.append((baseline, optimized))

        assert (
            optimized.rpc_calls < baseline.rpc_calls
        ), f"Expected fewer RPCs: v0.6.0={optimized.rpc_calls} vs v0.5.1={baseline.rpc_calls}"

    def test_multiple_records(self, connection, odoo, benchmark_results):
        """search_read for 50 records: expect 1 RPC (v0.6.0) vs 2 RPCs (v0.5.1)."""
        domain = []
        fields = ["name", "email", "city"]

        # Baseline: search + read = 2 RPCs
        with counting(odoo, "search_read (50 records) - baseline") as baseline:
            search_then_read(odoo, "res.partner", domain, fields, limit=50)

        # Optimized: native search_read = 1 RPC
        with counting(odoo, "search_read (50 records) - v0.6.0") as optimized:
            connection.search_read("res.partner", domain, fields, limit=50)

        benchmark_results.append((baseline, optimized))

        assert optimized.rpc_calls < baseline.rpc_calls

    def test_with_order_and_offset(self, connection, odoo, benchmark_results):
        """search_read with order and offset parameters."""
        domain = []
        fields = ["name", "email"]

        # Baseline
        with counting(odoo, "search_read (order+offset) - baseline") as baseline:
            search_then_read(odoo, "res.partner", domain, fields, limit=10)

        # Optimized
        with counting(odoo, "search_read (order+offset) - v0.6.0") as optimized:
            connection.search_read("res.partner", domain, fields, limit=10, offset=5, order="name asc")

        benchmark_results.append((baseline, optimized))

        assert optimized.rpc_calls <= baseline.rpc_calls
