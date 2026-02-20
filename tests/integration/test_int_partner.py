"""Integration tests for partner operations."""

import pytest


@pytest.mark.integration
class TestPartnerOperations:
    """Test partner CRUD and lookup operations against live Odoo."""

    def test_create_partner_individual(self, connection, data_manager):
        """Create an individual contact and verify it exists."""
        partner_id = data_manager.create(
            "res.partner",
            {
                "name": "Test Individual IntTest",
                "email": "test.individual@inttest.example.com",
                "phone": "+49 711 1111111",
                "is_company": False,
            },
        )
        assert partner_id > 0

        # Verify via search_read
        result = connection.search_read(
            "res.partner",
            [("id", "=", partner_id)],
            ["name", "email", "is_company"],
        )
        assert len(result) == 1
        assert result[0]["name"] == "Test Individual IntTest"
        assert result[0]["is_company"] is False

    def test_create_partner_company(self, connection, data_manager):
        """Create a company and verify via check_if_company_exists."""
        partner_id = data_manager.create(
            "res.partner",
            {
                "name": "IntTest Company GmbH",
                "is_company": True,
                "zip": "70173",
                "city": "Stuttgart",
            },
        )
        assert partner_id > 0

        found_id = connection.check_if_company_exists("IntTest Company GmbH", "70173", "Stuttgart")
        assert found_id == partner_id

    def test_create_partner_via_helper(self, connection, data_manager):
        """Create a partner via the create_partner helper method."""
        partner_id = connection.create_partner(
            name="IntTest Helper Partner",
            is_company=True,
            email="helper@inttest.example.com",
            phone="+49 711 2222222",
            street="Teststrasse 42",
            city="Stuttgart",
            zip_code="70173",
        )
        data_manager.track("res.partner", partner_id)

        assert partner_id > 0

        result = connection.search_read(
            "res.partner",
            [("id", "=", partner_id)],
            ["name", "email", "street", "city"],
        )
        assert len(result) == 1
        assert result[0]["name"] == "IntTest Helper Partner"
        assert result[0]["street"] == "Teststrasse 42"

    def test_get_res_partner_category_id(self, connection, data_manager):
        """Get or create a partner category (tag)."""
        category_name = "IntTest Category Unique 42"
        category_id = connection.get_res_partner_category_id(category_name)
        data_manager.track("res.partner.category", category_id)

        assert category_id > 0

        # Second call should return the same ID (created or cached)
        category_id_2 = connection.get_res_partner_category_id(category_name)
        assert category_id_2 == category_id

    def test_get_res_partner_title_id(self, connection):
        """Look up a partner title (e.g. Mister)."""
        # Demo data should have titles like "Mister", "Miss", "Doctor"
        title_id = connection.get_res_partner_title_id("Mister")
        if title_id is None:
            pytest.skip("Title 'Mister' not found - demo data may not be installed")
        assert title_id > 0

    def test_check_if_company_exists_not_found(self, connection):
        """Check for a non-existent company returns None."""
        result = connection.check_if_company_exists("NonExistent Company XYZ 99999", "00000", "Nowhere")
        assert result is None
