"""Tests for batch_write context manager."""

from unittest.mock import MagicMock

import pytest

from odoorpc_toolbox.batch import batch_write


class TestBatchWrite:
    """Tests for the batch_write() context manager."""

    def _make_mock_odoo(self):
        """Create a mock ODOO instance with config and env."""
        mock_odoo = MagicMock()
        mock_odoo.config = {"auto_commit": True, "auto_context": True, "timeout": 120}
        mock_odoo.env = MagicMock()
        return mock_odoo

    def test_auto_commit_toggled(self):
        """Test that auto_commit is set to False during batch and restored after."""
        mock_odoo = self._make_mock_odoo()

        assert mock_odoo.config["auto_commit"] is True
        with batch_write(mock_odoo):
            assert mock_odoo.config["auto_commit"] is False
        assert mock_odoo.config["auto_commit"] is True

    def test_commit_called_on_success(self):
        """Test that env.commit() is called on successful exit."""
        mock_odoo = self._make_mock_odoo()

        with batch_write(mock_odoo):
            pass

        mock_odoo.env.commit.assert_called_once()

    def test_invalidate_called_on_exception(self):
        """Test that env.invalidate() is called on exception (rollback)."""
        mock_odoo = self._make_mock_odoo()

        with pytest.raises(ValueError):
            with batch_write(mock_odoo):
                raise ValueError("test error")

        mock_odoo.env.invalidate.assert_called_once()
        mock_odoo.env.commit.assert_not_called()

    def test_auto_commit_restored_on_exception(self):
        """Test that auto_commit is restored even after an exception."""
        mock_odoo = self._make_mock_odoo()

        with pytest.raises(ValueError):
            with batch_write(mock_odoo):
                raise ValueError("test error")

        assert mock_odoo.config["auto_commit"] is True

    def test_preserves_previous_auto_commit_false(self):
        """Test that original auto_commit=False is preserved after batch."""
        mock_odoo = self._make_mock_odoo()
        mock_odoo.config["auto_commit"] = False

        with batch_write(mock_odoo):
            assert mock_odoo.config["auto_commit"] is False

        assert mock_odoo.config["auto_commit"] is False

    def test_nested_batch_write(self):
        """Test nested batch_write contexts restore correctly."""
        mock_odoo = self._make_mock_odoo()

        with batch_write(mock_odoo):
            assert mock_odoo.config["auto_commit"] is False
            with batch_write(mock_odoo):
                assert mock_odoo.config["auto_commit"] is False
            # Inner batch restores to False (outer's value)
            assert mock_odoo.config["auto_commit"] is False

        # Outer batch restores to True (original value)
        assert mock_odoo.config["auto_commit"] is True
