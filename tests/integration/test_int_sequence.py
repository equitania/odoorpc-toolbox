"""Integration tests for sequence operations."""

import pytest

SEQUENCE_CODE = "sale.order"


@pytest.mark.integration
class TestSequenceOperations:
    """Test sequence get/set operations with value restoration."""

    def test_get_ir_sequence_number_next_actual(self, connection):
        """Get the next sequence number."""
        value = connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)
        if value is None:
            pytest.skip(f"Sequence '{SEQUENCE_CODE}' not found - install 'sale' module")
        assert isinstance(value, int)
        assert value > 0

    def test_set_ir_sequence_number_next_actual(self, connection):
        """Set the next sequence number and restore original."""
        original_value = connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)
        if original_value is None:
            pytest.skip(f"Sequence '{SEQUENCE_CODE}' not found - install 'sale' module")

        try:
            test_value = original_value + 1000
            result = connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, test_value)
            assert result is True

            # Verify the value was set
            new_value = connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)
            assert new_value == test_value
        finally:
            # Restore original value
            connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, original_value)

    def test_get_sequence_not_found(self, connection):
        """Non-existent sequence code returns None."""
        result = connection.get_ir_sequence_number_next_actual("nonexistent.sequence.code.xyz")
        assert result is None

    def test_set_sequence_not_found(self, connection):
        """Setting a non-existent sequence returns False."""
        result = connection.set_ir_sequence_number_next_actual("nonexistent.sequence.code.xyz", 42)
        assert result is False

    def test_sequence_roundtrip(self, connection):
        """Full roundtrip: get -> set -> verify -> restore."""
        original = connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE)
        if original is None:
            pytest.skip(f"Sequence '{SEQUENCE_CODE}' not found")

        try:
            # Set to a specific value
            target = 99999
            connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, target)
            assert connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE) == target

            # Set to another value
            target2 = 12345
            connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, target2)
            assert connection.get_ir_sequence_number_next_actual(SEQUENCE_CODE) == target2
        finally:
            connection.set_ir_sequence_number_next_actual(SEQUENCE_CODE, original)
