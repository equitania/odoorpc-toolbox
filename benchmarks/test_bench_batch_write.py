"""Benchmark: batch_write vs individual field writes."""

import pytest

from benchmarks.baselines import write_fields_individually
from benchmarks.rpc_counter import counting
from odoorpc_toolbox import batch_write


@pytest.mark.benchmark
class TestBatchWriteBenchmark:
    """Compare batch_write (1 RPC) vs individual writes (N RPCs)."""

    def _get_test_partner(self, connection):
        """Find or create a test partner for write benchmarks."""
        partners = connection.search_read(
            "res.partner",
            [("is_company", "=", True)],
            ["name", "phone", "website", "street", "city"],
            limit=1,
        )
        if not partners:
            pytest.skip("No company partner found for write benchmark")
        return partners[0]

    def test_batch_write_5_fields(self, connection, odoo, benchmark_results):
        """5 field updates: expect 1 RPC (batch) vs 5 RPCs (individual)."""
        partner = self._get_test_partner(connection)
        partner_id = partner["id"]

        # Save original values for restoration
        original_values = {
            "phone": partner.get("phone", ""),
            "website": partner.get("website", ""),
            "street": partner.get("street", ""),
            "city": partner.get("city", ""),
            "comment": "",
        }

        test_values = {
            "phone": "+49 711 12345678",
            "website": "https://benchmark-test.example.com",
            "street": "Benchmark Street 42",
            "city": "Benchmark City",
            "comment": "Benchmark test comment",
        }

        try:
            # Baseline: 5 individual write calls = 5 RPCs
            with counting(odoo, "batch_write (5 fields) - baseline") as baseline:
                write_fields_individually(odoo, "res.partner", [partner_id], test_values)

            # Optimized: single batch write = 1 RPC
            with counting(odoo, "batch_write (5 fields) - v0.6.0") as optimized:
                odoo.execute_kw("res.partner", "write", [[partner_id], test_values])

            benchmark_results.append((baseline, optimized))

            assert (
                optimized.rpc_calls < baseline.rpc_calls
            ), f"Expected fewer RPCs: v0.6.0={optimized.rpc_calls} vs v0.5.1={baseline.rpc_calls}"
        finally:
            # Restore original values
            odoo.execute_kw("res.partner", "write", [[partner_id], original_values])

    def test_batch_write_context_manager(self, connection, odoo, benchmark_results):
        """Verify batch_write context manager reduces RPC calls."""
        partner = self._get_test_partner(connection)
        partner_id = partner["id"]

        original_values = {
            "phone": partner.get("phone", ""),
            "website": partner.get("website", ""),
        }

        try:
            # Using batch_write context manager
            Partner = odoo.env["res.partner"]
            record = Partner.browse(partner_id)

            with counting(odoo, "batch_write context manager") as metrics:
                with batch_write(odoo):
                    record.phone = "+49 711 99999999"
                    record.website = "https://batch-test.example.com"

            # batch_write should result in fewer RPCs than 2 individual writes
            assert metrics.rpc_calls <= 2, f"batch_write should consolidate writes, got {metrics.rpc_calls} RPCs"
        finally:
            odoo.execute_kw("res.partner", "write", [[partner_id], original_values])
