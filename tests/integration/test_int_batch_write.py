"""Integration tests for batch_write operations."""

import pytest

from odoorpc_toolbox import batch_write


@pytest.mark.integration
class TestBatchWriteOperations:
    """Test batch_write commit and rollback behavior."""

    def _create_test_partner(self, data_manager):
        """Create a partner for write tests."""
        return data_manager.create(
            "res.partner",
            {
                "name": "IntTest BatchWrite Partner",
                "phone": "+49 711 0000000",
                "website": "https://original.example.com",
                "is_company": True,
            },
        )

    def test_batch_write_commits_on_success(self, connection, odoo, data_manager):
        """batch_write should commit all changes on successful exit."""
        partner_id = self._create_test_partner(data_manager)

        Partner = odoo.env["res.partner"]
        record = Partner.browse(partner_id)

        with batch_write(odoo):
            record.phone = "+49 711 9999999"
            record.website = "https://batch-committed.example.com"

        # Verify changes were committed
        result = connection.search_read(
            "res.partner",
            [("id", "=", partner_id)],
            ["phone", "website"],
        )
        assert result[0]["phone"] == "+49 711 9999999"
        assert result[0]["website"] == "https://batch-committed.example.com"

    def test_batch_write_rollback_on_exception(self, connection, odoo, data_manager):
        """batch_write should rollback changes on exception."""
        partner_id = self._create_test_partner(data_manager)

        Partner = odoo.env["res.partner"]
        record = Partner.browse(partner_id)

        original_phone = "+49 711 0000000"

        with pytest.raises(ValueError, match="test rollback"):
            with batch_write(odoo):
                record.phone = "+49 711 ROLLED_BACK"
                raise ValueError("test rollback")

        # Verify changes were NOT committed
        result = connection.search_read(
            "res.partner",
            [("id", "=", partner_id)],
            ["phone"],
        )
        assert result[0]["phone"] == original_phone

    def test_batch_write_restores_auto_commit(self, odoo, data_manager):
        """batch_write should restore auto_commit setting after exit."""
        assert odoo.config["auto_commit"] is True

        self._create_test_partner(data_manager)

        with batch_write(odoo):
            assert odoo.config["auto_commit"] is False

        assert odoo.config["auto_commit"] is True

    def test_batch_write_restores_on_exception(self, odoo, data_manager):
        """batch_write should restore auto_commit even on exception."""
        assert odoo.config["auto_commit"] is True

        self._create_test_partner(data_manager)

        with pytest.raises(RuntimeError):
            with batch_write(odoo):
                raise RuntimeError("test exception")

        assert odoo.config["auto_commit"] is True
