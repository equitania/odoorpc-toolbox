"""Integration tests for execute_method operations."""

import pytest


@pytest.mark.integration
class TestExecuteMethodOperations:
    """Test the generic execute_method helper."""

    def test_execute_method_name_search(self, connection):
        """Call name_search on res.partner."""
        result = connection.execute_method(
            "res.partner",
            "name_search",
            args=["Admin"],
            kwargs={"limit": 5},
        )
        assert isinstance(result, list)

    def test_execute_method_fields_get(self, connection):
        """Call fields_get to get model field definitions."""
        result = connection.execute_method(
            "res.partner",
            "fields_get",
            kwargs={"attributes": ["string", "type"]},
        )
        assert isinstance(result, dict)
        assert "name" in result
        assert "email" in result

    def test_execute_method_on_records(self, connection, data_manager):
        """Call a method on specific records."""
        partner_id = data_manager.create(
            "res.partner",
            {"name": "IntTest Execute Method Partner", "is_company": True},
        )

        result = connection.execute_method(
            "res.partner",
            "name_get",
            record_ids=[partner_id],
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0][0] == partner_id

    def test_execute_method_private_blocked(self, connection):
        """Private methods (starting with _) should be blocked."""
        with pytest.raises(ValueError, match="Private method"):
            connection.execute_method("res.partner", "_compute_display_name")

    def test_execute_method_dunder_blocked(self, connection):
        """Dunder methods should also be blocked."""
        with pytest.raises(ValueError, match="Private method"):
            connection.execute_method("res.partner", "__init__")

    def test_execute_method_search_count(self, connection):
        """Call search_count on a model."""
        result = connection.execute_method(
            "res.partner",
            "search_count",
            args=[[("is_company", "=", True)]],
        )
        assert isinstance(result, int)
        assert result >= 0
