"""Integration tests for country and state lookups."""

import pytest


@pytest.mark.integration
class TestLocationOperations:
    """Test country and state lookup operations against live Odoo."""

    def test_get_country_id_by_name(self, connection):
        """Look up Germany by name."""
        country_id = connection.get_country_id("Germany")
        if country_id is None:
            # Try German name
            country_id = connection.get_country_id("Deutschland")
        assert country_id is not None and country_id > 0

    def test_get_country_id_by_code(self, connection):
        """Look up countries by ISO code."""
        de_id = connection.get_country_id_by_code("DE")
        assert de_id is not None and de_id > 0

        us_id = connection.get_country_id_by_code("US")
        assert us_id is not None and us_id > 0

        # Different countries should have different IDs
        assert de_id != us_id

    def test_get_country_id_by_code_lowercase(self, connection):
        """Country code lookup should be case-insensitive."""
        id_upper = connection.get_country_id_by_code("DE")
        connection.clear_cache()
        id_lower = connection.get_country_id_by_code("de")
        assert id_upper == id_lower

    def test_get_country_id_not_found(self, connection):
        """Non-existent country returns None."""
        result = connection.get_country_id("NonExistentCountryXYZ")
        assert result is None

    def test_get_country_id_by_code_not_found(self, connection):
        """Non-existent country code returns None."""
        result = connection.get_country_id_by_code("ZZ")
        assert result is None

    def test_get_state_id(self, connection):
        """Look up a state by country and name."""
        # First find a country with states
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

        state_id = connection.get_state_id(country_id, state_name)
        assert state_id is not None and state_id > 0

    def test_get_state_id_cached(self, connection, fresh_cache):
        """Second state lookup should be served from cache."""
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

        # First call populates cache
        id1 = connection.get_state_id(country_id, state_name)
        # Second call should return same result (from cache)
        id2 = connection.get_state_id(country_id, state_name)
        assert id1 == id2

    def test_get_state_id_not_found(self, connection):
        """Non-existent state returns None."""
        # Use a valid country but invalid state
        de_id = connection.get_country_id_by_code("DE")
        if de_id is None:
            pytest.skip("Germany not found in database")

        connection.clear_cache()
        result = connection.get_state_id(de_id, "NonExistentStateXYZ12345")
        assert result is None
