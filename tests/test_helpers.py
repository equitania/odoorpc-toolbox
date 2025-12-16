"""Tests for helper functions in base_helper.py."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64


class TestStringContainsNumbers:
    """Tests for string_contains_numbers method."""

    @pytest.fixture
    def helper(self):
        """Create a mock helper instance."""
        with patch('odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__',
                   return_value=None):
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
        with patch('odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__',
                   return_value=None):
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
        with patch('odoorpc_toolbox.base_helper.odoo_connection.OdooConnection.__init__',
                   return_value=None):
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
