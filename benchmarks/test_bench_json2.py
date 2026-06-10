"""Benchmark: JSON-2 (/json/2/) vs legacy (/jsonrpc) on Odoo 19+.

These benchmarks require a live Odoo 19+ instance. On older servers the
whole module is skipped (the JSON-2 path does not exist there).

Run with:
    ODOO_TEST_CONFIG=yaml_examples/test_config_v19.yaml pytest benchmarks/test_bench_json2.py -v
"""

import pytest

from benchmarks.baselines import legacy_execute_kw
from benchmarks.rpc_counter import counting, counting_json2


@pytest.fixture(scope="module", autouse=True)
def _require_odoo19(odoo):
    """Skip the module when the target server is older than Odoo 19."""
    major = int(odoo.version.split(".")[0])
    if major < 19:
        pytest.skip(f"JSON-2 benchmarks require Odoo >= 19, got {odoo.version}")


@pytest.mark.benchmark
class TestJson2VsLegacyBenchmark:
    """Compare /json/2/ vs /jsonrpc latency for equivalent operations."""

    def test_search_read_json2_vs_legacy(self, odoo, benchmark_results):
        """search_read: same RPC count, compare latency."""
        domain = [["is_company", "=", True]]
        fields = ["name"]

        # Warmup both paths
        legacy_execute_kw(odoo, "res.partner", "search_read", [domain], {"fields": fields, "limit": 1})
        odoo.execute_kw("res.partner", "search_read", kwargs={"domain": domain, "fields": fields, "limit": 1})

        with counting(odoo, "search_read - legacy /jsonrpc") as baseline:
            legacy_execute_kw(odoo, "res.partner", "search_read", [domain], {"fields": fields, "limit": 10})

        with counting_json2(odoo, "search_read - JSON-2") as optimized:
            odoo.execute_kw("res.partner", "search_read", kwargs={"domain": domain, "fields": fields, "limit": 10})

        benchmark_results.append((baseline, optimized))
        assert optimized.rpc_calls == baseline.rpc_calls == 1

    def test_search_count_json2_vs_legacy(self, odoo, benchmark_results):
        """search_count: RPC count equivalence between both endpoints."""
        with counting(odoo, "search_count - legacy /jsonrpc") as baseline:
            legacy_execute_kw(odoo, "res.partner", "search_count", [[]])

        with counting_json2(odoo, "search_count - JSON-2") as optimized:
            odoo.execute_kw("res.partner", "search_count", kwargs={"domain": []})

        benchmark_results.append((baseline, optimized))
        assert optimized.rpc_calls == baseline.rpc_calls == 1

    def test_read_json2_vs_legacy(self, odoo, benchmark_results):
        """read: positional-args mapping routes through JSON-2."""
        ids = legacy_execute_kw(odoo, "res.partner", "search", [[]], {"limit": 5})

        with counting(odoo, "read - legacy /jsonrpc") as baseline:
            legacy_execute_kw(odoo, "res.partner", "read", [ids, ["name"]])

        with counting_json2(odoo, "read - JSON-2") as optimized:
            result = odoo.execute_kw("res.partner", "read", args=[ids, ["name"]])

        benchmark_results.append((baseline, optimized))
        assert optimized.rpc_calls == 1
        assert optimized.rpc_calls_by_method.get("json2/res.partner/read") == 1
        assert isinstance(result, list)

    def test_repeated_calls_latency(self, odoo, benchmark_results):
        """10x search_count: aggregate latency comparison legacy vs JSON-2."""
        with counting(odoo, "search_count x10 - legacy /jsonrpc") as baseline:
            for _ in range(10):
                legacy_execute_kw(odoo, "res.partner", "search_count", [[]])

        with counting_json2(odoo, "search_count x10 - JSON-2") as optimized:
            for _ in range(10):
                odoo.execute_kw("res.partner", "search_count", kwargs={"domain": []})

        benchmark_results.append((baseline, optimized))
        assert optimized.rpc_calls == baseline.rpc_calls == 10
