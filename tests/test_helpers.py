"""Tests for helper functions in base_helper.py."""

import base64
from unittest.mock import MagicMock, patch

import pytest


class TestStringContainsNumbers:
    """Tests for string_contains_numbers method."""

    @pytest.fixture
    def helper(self):
        """Create a mock helper instance."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection

            instance = object.__new__(EqOdooConnection)
            return instance

    def test_string_with_numbers(self, helper):
        """Test that strings with numbers return True."""
        assert helper.string_contains_numbers("abc123") is True
        assert helper.string_contains_numbers("123") is True
        assert helper.string_contains_numbers("a1b") is True

    def test_string_without_numbers(self, helper):
        """Test that strings without numbers return False."""
        assert helper.string_contains_numbers("abc") is False
        assert helper.string_contains_numbers("") is False
        assert helper.string_contains_numbers("hello world") is False

    def test_string_with_special_chars(self, helper):
        """Test strings with special characters."""
        assert helper.string_contains_numbers("test!@#") is False
        assert helper.string_contains_numbers("test1!@#") is True


class TestExtractStreetAddressPart:
    """Tests for extract_street_address_part method."""

    @pytest.fixture
    def helper(self):
        """Create a mock helper instance."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection

            instance = object.__new__(EqOdooConnection)
            return instance

    def test_simple_german_address(self, helper):
        """Test simple German address format: Street Number."""
        street, house_no = helper.extract_street_address_part("Hauptstraße 123")
        assert street == "Hauptstraße"
        assert house_no == "123"

    def test_multi_word_street(self, helper):
        """Test multi-word street names."""
        street, house_no = helper.extract_street_address_part("Am Alten Markt 42")
        assert street == "Am Alten Markt"
        assert house_no == "42"

    def test_address_with_letter_suffix(self, helper):
        """Test address with letter suffix in house number."""
        street, house_no = helper.extract_street_address_part("Bahnhofstraße 12a")
        assert street == "Bahnhofstraße"
        assert house_no == "12a"

    def test_british_address_format(self, helper):
        """Test British address format without number at end."""
        street, house_no = helper.extract_street_address_part("Flat Ashburnham Mansions")
        assert street == "Flat Ashburnham Mansions"
        assert house_no == ""

    def test_empty_string(self, helper):
        """Test empty string input."""
        street, house_no = helper.extract_street_address_part("")
        assert street == ""
        assert house_no == ""

    def test_single_word(self, helper):
        """Test single word input."""
        street, house_no = helper.extract_street_address_part("Hauptstraße")
        assert street == "Hauptstraße"
        assert house_no == ""

    def test_only_number(self, helper):
        """Test input with street and number."""
        street, house_no = helper.extract_street_address_part("Street 5")
        assert street == "Street"
        assert house_no == "5"


class TestGetPicture:
    """Tests for get_picture method."""

    @pytest.fixture
    def helper(self):
        """Create a mock helper instance."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection

            instance = object.__new__(EqOdooConnection)
            return instance

    def test_existing_file(self, helper, temp_image_file):
        """Test loading an existing image file."""
        result = helper.get_picture(temp_image_file)

        assert result is not None
        assert isinstance(result, str)
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_nonexistent_file(self, helper):
        """Test loading a non-existent file."""
        result = helper.get_picture("/nonexistent/path/image.png")
        assert result is None

    def test_empty_path(self, helper):
        """Test with empty path."""
        result = helper.get_picture("")
        assert result is None


class TestOptimizedSearchRead:
    """Tests for the optimized search_read method using native execute_kw."""

    @pytest.fixture
    def connected_helper(self):
        """Create a mock EqOdooConnection with a connected ODOO instance."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection

            instance = object.__new__(EqOdooConnection)
            instance._lookup_cache = MagicMock()
            instance._lookup_cache.get.return_value = None

            mock_odoo = MagicMock()
            instance.odoo = mock_odoo
            return instance

    def test_search_read_uses_execute_kw(self, connected_helper):
        """Test that search_read uses execute_kw with search_read method."""
        connected_helper.odoo.execute_kw.return_value = [
            {"id": 1, "name": "Test Partner"},
        ]

        result = connected_helper.search_read("res.partner", [("is_company", "=", True)], ["id", "name"])

        connected_helper.odoo.execute_kw.assert_called_once_with(
            "res.partner",
            "search_read",
            [[("is_company", "=", True)]],
            {"fields": ["id", "name"], "offset": 0},
        )
        assert len(result) == 1
        assert result[0]["name"] == "Test Partner"

    def test_search_read_with_limit_and_order(self, connected_helper):
        """Test that limit and order are passed correctly."""
        connected_helper.odoo.execute_kw.return_value = []

        connected_helper.search_read("res.partner", limit=10, order="name asc")

        call_kwargs = connected_helper.odoo.execute_kw.call_args[0][3]
        assert call_kwargs["limit"] == 10
        assert call_kwargs["order"] == "name asc"

    def test_search_read_empty_result(self, connected_helper):
        """Test that empty/None result returns empty list."""
        connected_helper.odoo.execute_kw.return_value = None

        result = connected_helper.search_read("res.partner")
        assert result == []

    def test_search_read_default_fields(self, connected_helper):
        """Test that default fields are ['id', 'name']."""
        connected_helper.odoo.execute_kw.return_value = []

        connected_helper.search_read("res.partner")

        call_kwargs = connected_helper.odoo.execute_kw.call_args[0][3]
        assert call_kwargs["fields"] == ["id", "name"]


class TestOptimizedSequenceMethods:
    """Tests for optimized sequence methods using fewer RPC calls."""

    @pytest.fixture
    def connected_helper(self):
        """Create a mock EqOdooConnection with a connected ODOO instance."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection

            instance = object.__new__(EqOdooConnection)
            instance._lookup_cache = MagicMock()
            instance._lookup_cache.get.return_value = None

            mock_odoo = MagicMock()
            instance.odoo = mock_odoo
            return instance

    def test_get_sequence_uses_search_read(self, connected_helper):
        """Test that get_ir_sequence_number_next_actual uses a single search_read call."""
        connected_helper.odoo.execute_kw.return_value = [{"id": 1, "number_next_actual": 42}]

        result = connected_helper.get_ir_sequence_number_next_actual("sale.order")

        connected_helper.odoo.execute_kw.assert_called_once_with(
            "ir.sequence",
            "search_read",
            [[("code", "=", "sale.order")]],
            {"fields": ["number_next_actual"], "limit": 1},
        )
        assert result == 42

    def test_get_sequence_not_found(self, connected_helper):
        """Test that get_ir_sequence_number_next_actual returns None when not found."""
        connected_helper.odoo.execute_kw.return_value = []

        result = connected_helper.get_ir_sequence_number_next_actual("nonexistent.code")
        assert result is None

    def test_set_sequence_uses_search_and_write(self, connected_helper):
        """Test that set_ir_sequence_number_next_actual uses search + write (2 calls)."""
        connected_helper.odoo.execute_kw.side_effect = [
            [5],  # search returns ids
            True,  # write returns True
        ]

        result = connected_helper.set_ir_sequence_number_next_actual("sale.order", 100)

        assert result is True
        assert connected_helper.odoo.execute_kw.call_count == 2

        # First call: search
        first_call = connected_helper.odoo.execute_kw.call_args_list[0]
        assert first_call[0][1] == "search"

        # Second call: write
        second_call = connected_helper.odoo.execute_kw.call_args_list[1]
        assert second_call[0][1] == "write"
        assert second_call[0][2] == [[5], {"number_next_actual": 100}]

    def test_set_sequence_not_found(self, connected_helper):
        """Test that set_ir_sequence_number_next_actual returns False when not found."""
        connected_helper.odoo.execute_kw.return_value = []

        result = connected_helper.set_ir_sequence_number_next_actual("nonexistent.code", 100)
        assert result is False


class TestCacheIntegration:
    """Tests for cache integration in EqOdooConnection."""

    @pytest.fixture
    def connected_helper(self):
        """Create a mock EqOdooConnection with a real cache."""
        with patch("odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__", return_value=None):
            from odoorpc_toolbox import EqOdooConnection
            from odoorpc_toolbox.cache import TTLCache

            instance = object.__new__(EqOdooConnection)
            instance._lookup_cache = TTLCache(maxsize=256, ttl=3600)

            mock_odoo = MagicMock()
            instance.odoo = mock_odoo
            instance.odoo_version = 16
            return instance

    def test_get_state_id_cached(self, connected_helper):
        """Test that get_state_id results are cached on repeated calls."""
        mock_model = MagicMock()
        mock_model.search.return_value = [42]
        connected_helper.odoo.env.__getitem__.return_value = mock_model

        result1 = connected_helper.get_state_id(1, "California")
        result2 = connected_helper.get_state_id(1, "California")

        assert result1 == 42
        assert result2 == 42
        # Should only call search once (second call from cache)
        assert mock_model.search.call_count == 1

    def test_clear_cache_forces_fresh_lookup(self, connected_helper):
        """Test that clear_cache() forces fresh RPC calls."""
        mock_model = MagicMock()
        mock_model.search.return_value = [42]
        connected_helper.odoo.env.__getitem__.return_value = mock_model

        connected_helper.get_state_id(1, "California")
        connected_helper.clear_cache()
        connected_helper.get_state_id(1, "California")

        assert mock_model.search.call_count == 2

    def test_get_product_uom_id_cached(self, connected_helper):
        """Test that get_product_uom_id results are cached."""
        mock_model = MagicMock()
        mock_model.search.return_value = [7]
        connected_helper.odoo.env.__getitem__.return_value = mock_model

        result1 = connected_helper.get_product_uom_id("kg")
        result2 = connected_helper.get_product_uom_id("kg")

        assert result1 == 7
        assert result2 == 7
        assert mock_model.search.call_count == 1
