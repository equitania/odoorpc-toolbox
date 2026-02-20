"""Integration tests for search_read operations."""

import pytest


@pytest.mark.integration
class TestSearchReadOperations:
    """Test search_read with various parameters against live Odoo."""

    def test_basic_search_read(self, connection):
        """Basic search_read with domain and fields."""
        result = connection.search_read(
            "res.partner",
            [("is_company", "=", True)],
            ["name", "email"],
            limit=5,
        )
        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "name" in result[0]
            assert "id" in result[0]

    def test_search_read_with_limit(self, connection):
        """search_read respects the limit parameter."""
        result = connection.search_read("res.partner", [], ["name"], limit=3)
        assert len(result) <= 3

    def test_search_read_with_offset(self, connection):
        """search_read respects offset for pagination."""
        page1 = connection.search_read("res.partner", [], ["name"], limit=5, offset=0)
        page2 = connection.search_read("res.partner", [], ["name"], limit=5, offset=5)

        if len(page1) == 5 and len(page2) > 0:
            # Pages should contain different records
            ids1 = {r["id"] for r in page1}
            ids2 = {r["id"] for r in page2}
            assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_search_read_with_order(self, connection):
        """search_read respects order parameter."""
        result = connection.search_read(
            "res.partner",
            [],
            ["name"],
            limit=10,
            order="name asc",
        )
        if len(result) >= 2:
            names = [r["name"] for r in result if r["name"]]
            assert names == sorted(names), "Results should be sorted by name ascending"

    def test_search_read_empty_domain(self, connection):
        """search_read with empty domain returns all records (up to limit)."""
        result = connection.search_read("res.partner", [], ["name"], limit=1)
        assert len(result) >= 1

    def test_search_read_no_results(self, connection):
        """search_read with impossible domain returns empty list."""
        result = connection.search_read(
            "res.partner",
            [("name", "=", "NonExistentPartner_XYZ_99999_Unique")],
            ["name"],
        )
        assert result == []

    def test_search_read_multiple_fields(self, connection):
        """search_read returns all requested fields."""
        fields = ["name", "email", "phone", "city", "country_id"]
        result = connection.search_read(
            "res.partner",
            [("is_company", "=", True)],
            fields,
            limit=1,
        )
        if result:
            for field in fields:
                assert field in result[0], f"Field '{field}' missing from result"

    def test_search_read_default_fields(self, connection):
        """search_read with default fields returns id and name."""
        result = connection.search_read("res.partner", [], limit=1)
        if result:
            assert "id" in result[0]
            assert "name" in result[0]

    def test_search_read_complex_domain(self, connection):
        """search_read with complex domain (AND conditions)."""
        result = connection.search_read(
            "res.partner",
            [
                ("is_company", "=", True),
                ("country_id", "!=", False),
            ],
            ["name", "country_id"],
            limit=5,
        )
        for record in result:
            assert record.get("country_id") is not False
