"""Integration tests for product operations."""

import pytest


@pytest.mark.integration
class TestProductOperations:
    """Test product lookup operations against live Odoo."""

    def test_get_product_uom_id(self, connection):
        """Look up a unit of measure by name."""
        # "Units" is always present in Odoo with demo data
        uom_id = connection.get_product_uom_id("Units")
        assert uom_id >= 1  # Default is 1 if not found

    def test_get_product_uom_id_kg(self, connection):
        """Look up the 'kg' unit of measure."""
        connection.clear_cache()
        uom_id = connection.get_product_uom_id("kg")
        assert uom_id >= 1

    def test_get_product_uom_id_not_found(self, connection):
        """Non-existent UoM returns default (1)."""
        connection.clear_cache()
        uom_id = connection.get_product_uom_id("NonExistentUoM_XYZ")
        assert uom_id == 1  # Default fallback

    def test_get_product_by_ref(self, connection):
        """Look up a product by internal reference."""
        # Find any product with a default_code
        products = connection.search_read(
            "product.product",
            [("default_code", "!=", False)],
            ["default_code"],
            limit=1,
        )
        if not products:
            pytest.skip("No products with default_code found")

        ref = products[0]["default_code"]
        product_id = connection.get_product_by_ref(ref)
        assert product_id is not None and product_id > 0

    def test_get_product_by_ref_not_found(self, connection):
        """Non-existent product reference returns None."""
        result = connection.get_product_by_ref("NONEXISTENT_SKU_XYZ_99999")
        assert result is None

    def test_get_product_template_by_ref(self, connection):
        """Look up a product template by internal reference."""
        templates = connection.search_read(
            "product.template",
            [("default_code", "!=", False)],
            ["default_code"],
            limit=1,
        )
        if not templates:
            pytest.skip("No product templates with default_code found")

        ref = templates[0]["default_code"]
        template_id = connection.get_product_template_by_ref(ref)
        assert template_id is not None and template_id > 0

    def test_get_product_template_by_ref_not_found(self, connection):
        """Non-existent product template reference returns None."""
        result = connection.get_product_template_by_ref("NONEXISTENT_TMPL_XYZ_99999")
        assert result is None
