"""Integration tests for utility methods."""

import os
import tempfile

import pytest


@pytest.mark.integration
class TestUtilityOperations:
    """Test utility methods that don't require Odoo RPC."""

    def test_get_picture_valid_file(self, connection):
        """get_picture should encode a valid image file as BASE64."""
        # Create a minimal PNG file
        png_data = bytes(
            [
                0x89,
                0x50,
                0x4E,
                0x47,
                0x0D,
                0x0A,
                0x1A,
                0x0A,
                0x00,
                0x00,
                0x00,
                0x0D,
                0x49,
                0x48,
                0x44,
                0x52,
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x08,
                0x02,
                0x00,
                0x00,
                0x00,
                0x90,
                0x77,
                0x53,
                0xDE,
                0x00,
                0x00,
                0x00,
                0x0C,
                0x49,
                0x44,
                0x41,
                0x54,
                0x08,
                0xD7,
                0x63,
                0xF8,
                0xFF,
                0xFF,
                0x3F,
                0x00,
                0x05,
                0xFE,
                0x02,
                0xFE,
                0xDC,
                0xCC,
                0x59,
                0xE7,
                0x00,
                0x00,
                0x00,
                0x00,
                0x49,
                0x45,
                0x4E,
                0x44,
                0xAE,
                0x42,
                0x60,
                0x82,
            ]
        )
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as f:
            f.write(png_data)
            f.flush()
            tmp_path = f.name

        try:
            result = connection.get_picture(tmp_path)
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    def test_get_picture_nonexistent_file(self, connection):
        """get_picture should return None for non-existent file."""
        result = connection.get_picture("/tmp/nonexistent_file_xyz_99999.png")
        assert result is None

    def test_get_picture_size_limit(self, connection):
        """get_picture should reject files exceeding the size limit."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            # Create a file slightly over 1MB
            f.write(b"x" * (1024 * 1024 + 1))
            f.flush()
            tmp_path = f.name

        try:
            with pytest.raises(ValueError, match="exceeds"):
                connection.get_picture(tmp_path, max_size_mb=1)
        finally:
            os.unlink(tmp_path)

    def test_extract_street_address_simple(self, connection):
        """Extract street and house number from simple address."""
        street, house_no = connection.extract_street_address_part("Hauptstrasse 42")
        assert street == "Hauptstrasse"
        assert house_no == "42"

    def test_extract_street_address_multi_word(self, connection):
        """Extract address with multi-word street name."""
        street, house_no = connection.extract_street_address_part("Am Alten Rathaus 12")
        assert street == "Am Alten Rathaus"
        assert house_no == "12"

    def test_extract_street_address_no_number(self, connection):
        """Address without house number."""
        street, house_no = connection.extract_street_address_part("Hauptstrasse")
        assert street == "Hauptstrasse"
        assert house_no == ""

    def test_extract_street_address_empty(self, connection):
        """Empty address string."""
        street, house_no = connection.extract_street_address_part("")
        assert street == ""
        assert house_no == ""

    def test_string_contains_numbers_true(self, connection):
        """String with numbers should return True."""
        assert connection.string_contains_numbers("Street 42") is True
        assert connection.string_contains_numbers("12a") is True

    def test_string_contains_numbers_false(self, connection):
        """String without numbers should return False."""
        assert connection.string_contains_numbers("Hauptstrasse") is False
        assert connection.string_contains_numbers("") is False
