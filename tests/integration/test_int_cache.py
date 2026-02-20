"""Integration tests for TTL cache behavior."""

import pytest


@pytest.mark.integration
class TestCacheOperations:
    """Test cache persistence, clearing, and key isolation."""

    def test_cache_persists_across_calls(self, connection, fresh_cache):
        """Cache should return same result without additional RPC."""
        de_id_1 = connection.get_country_id_by_code("DE")
        if de_id_1 is None:
            pytest.skip("Germany not found in database")

        de_id_2 = connection.get_country_id_by_code("DE")
        assert de_id_1 == de_id_2

    def test_clear_cache(self, connection):
        """clear_cache should force fresh RPC calls."""
        de_id_1 = connection.get_country_id_by_code("DE")
        if de_id_1 is None:
            pytest.skip("Germany not found in database")

        connection.clear_cache()

        # After clear, should still return same value (just via RPC)
        de_id_2 = connection.get_country_id_by_code("DE")
        assert de_id_1 == de_id_2

    def test_different_keys_cached_separately(self, connection, fresh_cache):
        """Different lookup keys should be cached independently."""
        de_id = connection.get_country_id_by_code("DE")
        us_id = connection.get_country_id_by_code("US")

        if de_id is None or us_id is None:
            pytest.skip("DE or US not found in database")

        assert de_id != us_id

        # Both should be cached now
        assert connection.get_country_id_by_code("DE") == de_id
        assert connection.get_country_id_by_code("US") == us_id

    def test_cache_different_methods(self, connection, fresh_cache):
        """Cache should be isolated per method."""
        # These use different methods, so cache keys should not collide
        country_id = connection.get_country_id_by_code("DE")
        if country_id is None:
            pytest.skip("Germany not found in database")

        uom_id = connection.get_product_uom_id("Units")

        # Both should be independently cached
        assert connection.get_country_id_by_code("DE") == country_id
        assert connection.get_product_uom_id("Units") == uom_id

    def test_cache_state_with_multiple_args(self, connection, fresh_cache):
        """Cache should handle multi-argument keys correctly."""
        states = connection.odoo.execute_kw(
            "res.country.state",
            "search_read",
            [[]],
            {"fields": ["name", "country_id"], "limit": 2},
        )
        if len(states) < 2:
            pytest.skip("Need at least 2 states for this test")

        s1 = states[0]
        s2 = states[1]

        id1 = connection.get_state_id(s1["country_id"][0], s1["name"])
        id2 = connection.get_state_id(s2["country_id"][0], s2["name"])

        # Cache should return same values
        assert connection.get_state_id(s1["country_id"][0], s1["name"]) == id1
        assert connection.get_state_id(s2["country_id"][0], s2["name"]) == id2

    def test_cache_len(self, connection, fresh_cache):
        """Cache length should reflect number of cached entries."""
        initial_len = len(connection._lookup_cache)
        assert initial_len == 0

        connection.get_country_id_by_code("DE")
        assert len(connection._lookup_cache) >= 1

        connection.get_country_id_by_code("US")
        assert len(connection._lookup_cache) >= 2
