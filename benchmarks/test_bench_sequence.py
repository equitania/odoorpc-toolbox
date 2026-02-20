"""Benchmark: Sequence get/set optimization."""

import pytest

from benchmarks.baselines import get_sequence_old, set_sequence_old
from benchmarks.rpc_counter import counting

# Default Odoo sequence code (exists with demo data)
SEQUENCE_CODE = "sale.order"


@pytest.mark.benchmark
class TestSequenceBenchmark:
    """Compare optimized vs old sequence operations."""

    def test_get_sequence(self, connection, odoo, benchmark_results):
        """get_sequence: expect 1 RPC (v0.6.0) vs 2 RPCs (v0.5.1)."""
        # Baseline: search + read = 2 RPCs
        with counting(odoo, "get_sequence - baseline") as baseline:
            get_sequence_old(odoo, SEQUENCE_CODE)

        # Optimized: single search_read = 1 RPC
        with counting(odoo, "get_sequence - v0.6.0") as optimized:
            connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)

        benchmark_results.append((baseline, optimized))

        assert (
            optimized.rpc_calls < baseline.rpc_calls
        ), f"Expected fewer RPCs: v0.6.0={optimized.rpc_calls} vs v0.5.1={baseline.rpc_calls}"

    def test_set_sequence(self, connection, odoo, benchmark_results):
        """set_sequence: expect 2 RPCs (v0.6.0) vs 3 RPCs (v0.5.1)."""
        # First, get current value to restore later
        current_value = connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)
        if current_value is None:
            pytest.skip(f"Sequence '{SEQUENCE_CODE}' not found")

        try:
            # Baseline: search + read + write = 3 RPCs
            with counting(odoo, "set_sequence - baseline") as baseline:
                set_sequence_old(odoo, SEQUENCE_CODE, current_value + 100)

            # Optimized: search + write = 2 RPCs
            with counting(odoo, "set_sequence - v0.6.0") as optimized:
                connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, current_value + 200)

            benchmark_results.append((baseline, optimized))

            assert (
                optimized.rpc_calls < baseline.rpc_calls
            ), f"Expected fewer RPCs: v0.6.0={optimized.rpc_calls} vs v0.5.1={baseline.rpc_calls}"
        finally:
            # Restore original value
            connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, current_value)
