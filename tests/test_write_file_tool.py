"""
Tests for write file tool.

This module contains tests for the write file tool.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from core_agent.tools.write_file_tool import WriteFileTool, ConfirmWriteFileTool


class TestWriteFileTool(unittest.TestCase):
    """Tests for the WriteFileTool class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = WriteFileTool()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        self.test_content = "This is a test file."

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def test_run_with_confirmation(self):
        """Test the _run method with confirmation required."""
        # Act
        result = self.tool._run(
            file_path=self.test_file_path,
            content=self.test_content,
            requires_confirmation=True
        )
        
        # Assert
        self.assertTrue(result["requires_confirmation"])
        self.assertIn("preview", result)
        self.assertEqual(result["preview"]["path"], self.test_file_path)
        self.assertEqual(result["preview"]["content"], self.test_content)
        self.assertEqual(result["preview"]["operation"], "create")
        
        # Verify the file was not actually created
        self.assertFalse(os.path.exists(self.test_file_path))

    def test_run_without_confirmation(self):
        """Test the _run method without confirmation required."""
        # Act
        result = self.tool._run(
            file_path=self.test_file_path,
            content=self.test_content,
            requires_confirmation=False
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["file_path"], self.test_file_path)
        self.assertIn("metadata", result)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(self.test_file_path))
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, self.test_content)

    def test_run_with_existing_file(self):
        """Test the _run method with an existing file."""
        # Arrange
        with open(self.test_file_path, "w") as f:
            f.write("Original content")
        
        # Act
        result = self.tool._run(
            file_path=self.test_file_path,
            content=self.test_content,
            requires_confirmation=True,
            create_backup=True
        )
        
        # Assert
        self.assertTrue(result["requires_confirmation"])
        self.assertIn("preview", result)
        self.assertEqual(result["preview"]["path"], self.test_file_path)
        self.assertEqual(result["preview"]["content"], self.test_content)
        self.assertEqual(result["preview"]["operation"], "update")
        self.assertEqual(result["preview"]["old_content"], "Original content")
        self.assertIn("diff", result["preview"])
        
        # Verify the file was not modified
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "Original content")

    def test_run_with_invalid_path(self):
        """Test the _run method with an invalid path."""
        # Act and Assert
        with self.assertRaises(Exception):
            self.tool._run(
                file_path="/invalid/path/that/should/not/exist/test_file.txt",
                content=self.test_content,
                requires_confirmation=False,
                base_dir=self.temp_dir.name  # Restrict to temp dir for safety
            )


class TestConfirmWriteFileTool(unittest.TestCase):
    """Tests for the ConfirmWriteFileTool class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = ConfirmWriteFileTool()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        self.test_content = "This is a test file."

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    @patch('core_agent.tools.write_file_tool.WriteFileTool._run')
    def test_run(self, mock_write_tool_run):
        """Test the _run method."""
        # Arrange
        mock_write_tool_run.return_value = {
            "success": True,
            "file_path": self.test_file_path,
            "message": "File created successfully."
        }
        
        # Act
        result = self.tool._run(
            file_path=self.test_file_path,
            content=self.test_content
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["file_path"], self.test_file_path)
        mock_write_tool_run.assert_called_once_with(
            file_path=self.test_file_path,
            content=self.test_content,
            encoding="utf-8",
            base_dir=None,
            create_backup=True,
            requires_confirmation=False
        )


if __name__ == "__main__":
    unittest.main()
