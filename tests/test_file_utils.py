"""
Tests for file utilities.

This module contains tests for the file utilities.
"""

import os
import tempfile
import unittest
from datetime import datetime

from shared.models.file import FileType
from shared.utils.file_utils import get_file_metadata, read_file, is_text_file


class TestFileUtils(unittest.TestCase):
    """Test case for file utilities."""

    def setUp(self):
        """Set up the test case."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a text file
        self.text_file_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(self.text_file_path, "w", encoding="utf-8") as f:
            f.write("This is a test file.\nIt has multiple lines.\n")

        # Create a binary file
        self.binary_file_path = os.path.join(self.temp_dir.name, "test.bin")
        with open(self.binary_file_path, "wb") as f:
            f.write(bytes([0, 1, 2, 3, 4, 5]))

    def tearDown(self):
        """Clean up after the test case."""
        self.temp_dir.cleanup()

    def test_get_file_metadata(self):
        """Test get_file_metadata function."""
        # Test with text file
        metadata = get_file_metadata(self.text_file_path)
        self.assertEqual(metadata.path, self.text_file_path)
        self.assertEqual(metadata.name, "test.txt")
        self.assertEqual(metadata.type, FileType.TEXT)
        self.assertEqual(metadata.extension, ".txt")
        self.assertIsInstance(metadata.created_at, datetime)
        self.assertIsInstance(metadata.modified_at, datetime)

        # Test with binary file
        metadata = get_file_metadata(self.binary_file_path)
        self.assertEqual(metadata.path, self.binary_file_path)
        self.assertEqual(metadata.name, "test.bin")
        self.assertEqual(metadata.type, FileType.BINARY)
        self.assertEqual(metadata.extension, ".bin")

    def test_read_file(self):
        """Test read_file function."""
        # Test with text file
        file_content = read_file(self.text_file_path)
        self.assertEqual(file_content.content, "This is a test file.\nIt has multiple lines.\n")
        self.assertEqual(file_content.metadata.path, self.text_file_path)

        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            read_file("non_existent_file.txt")

    def test_is_text_file(self):
        """Test is_text_file function."""
        # Test with text file
        self.assertTrue(is_text_file(self.text_file_path))

        # Test with binary file
        self.assertFalse(is_text_file(self.binary_file_path))

        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            is_text_file("non_existent_file.txt")


if __name__ == "__main__":
    unittest.main()
