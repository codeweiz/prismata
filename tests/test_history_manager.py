"""
Tests for History Manager.

This module contains tests for the History Manager.
"""

import unittest
from datetime import datetime

from shared.models.history import (
    HistoryManager,
    HistoryEntry,
    OperationRecord,
    FileOperationRecord,
    CodeOperationRecord,
    OperationType,
    OperationStatus
)


class TestHistoryManager(unittest.TestCase):
    """Tests for the HistoryManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.history_manager = HistoryManager()
        
        # Create some test entries
        self.file_operation = FileOperationRecord(
            id="file-op-1",
            type=OperationType.READ_FILE,
            timestamp=datetime.now(),
            status=OperationStatus.SUCCESS,
            params={"file_path": "test.py"},
            result={"content": "print('Hello, World!')"},
            file_path="test.py",
            operation="read"
        )
        
        self.code_operation = CodeOperationRecord(
            id="code-op-1",
            type=OperationType.GENERATE_CODE,
            timestamp=datetime.now(),
            status=OperationStatus.SUCCESS,
            params={"prompt": "Create a hello world function"},
            result={"code": "def hello_world():\n    print('Hello, World!')"},
            language="python",
            code_preview="def hello_world():\n    print('Hello, World!')"
        )
        
        self.failed_operation = OperationRecord(
            id="failed-op-1",
            type=OperationType.CUSTOM,
            timestamp=datetime.now(),
            status=OperationStatus.FAILURE,
            params={"action": "test"},
            error="Test error"
        )
        
        # Create history entries
        self.file_entry = HistoryEntry(
            id="entry-1",
            timestamp=datetime.now(),
            operation=self.file_operation,
            description="Read file test.py",
            can_undo=False
        )
        
        self.code_entry = HistoryEntry(
            id="entry-2",
            timestamp=datetime.now(),
            operation=self.code_operation,
            description="Generate hello world function",
            can_undo=False
        )
        
        self.failed_entry = HistoryEntry(
            id="entry-3",
            timestamp=datetime.now(),
            operation=self.failed_operation,
            description="Failed operation",
            can_undo=False
        )

    def test_add_entry(self):
        """Test adding entries to the history."""
        # Act
        self.history_manager.add_entry(self.file_entry)
        self.history_manager.add_entry(self.code_entry)
        self.history_manager.add_entry(self.failed_entry)
        
        # Assert
        self.assertEqual(len(self.history_manager.entries), 3)
        self.assertEqual(self.history_manager.entries[0].id, "entry-1")
        self.assertEqual(self.history_manager.entries[1].id, "entry-2")
        self.assertEqual(self.history_manager.entries[2].id, "entry-3")

    def test_get_entries(self):
        """Test getting entries from the history."""
        # Arrange
        self.history_manager.add_entry(self.file_entry)
        self.history_manager.add_entry(self.code_entry)
        self.history_manager.add_entry(self.failed_entry)
        
        # Act
        all_entries = self.history_manager.get_entries()
        limited_entries = self.history_manager.get_entries(limit=2)
        file_entries = self.history_manager.get_entries(operation_type=OperationType.READ_FILE)
        failed_entries = self.history_manager.get_entries(status=OperationStatus.FAILURE)
        
        # Assert
        self.assertEqual(len(all_entries), 3)
        self.assertEqual(len(limited_entries), 2)
        self.assertEqual(limited_entries[0].id, "entry-2")
        self.assertEqual(limited_entries[1].id, "entry-3")
        self.assertEqual(len(file_entries), 1)
        self.assertEqual(file_entries[0].id, "entry-1")
        self.assertEqual(len(failed_entries), 1)
        self.assertEqual(failed_entries[0].id, "entry-3")

    def test_clear_history(self):
        """Test clearing the history."""
        # Arrange
        self.history_manager.add_entry(self.file_entry)
        self.history_manager.add_entry(self.code_entry)
        
        # Act
        self.history_manager.clear_history()
        
        # Assert
        self.assertEqual(len(self.history_manager.entries), 0)

    def test_get_entry(self):
        """Test getting a specific entry by ID."""
        # Arrange
        self.history_manager.add_entry(self.file_entry)
        self.history_manager.add_entry(self.code_entry)
        
        # Act
        entry = self.history_manager.get_entry("entry-2")
        non_existent_entry = self.history_manager.get_entry("non-existent")
        
        # Assert
        self.assertIsNotNone(entry)
        self.assertEqual(entry.id, "entry-2")
        self.assertIsNone(non_existent_entry)

    def test_max_entries(self):
        """Test that the history manager respects the max_entries limit."""
        # Arrange
        history_manager = HistoryManager(max_entries=2)
        
        # Act
        history_manager.add_entry(self.file_entry)
        history_manager.add_entry(self.code_entry)
        history_manager.add_entry(self.failed_entry)
        
        # Assert
        self.assertEqual(len(history_manager.entries), 2)
        self.assertEqual(history_manager.entries[0].id, "entry-2")
        self.assertEqual(history_manager.entries[1].id, "entry-3")


if __name__ == "__main__":
    unittest.main()
