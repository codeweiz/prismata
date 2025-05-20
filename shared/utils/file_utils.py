"""
File utilities.

This module provides utility functions for working with files.
"""

import datetime
import mimetypes
import os
from typing import Optional

from shared.models.file import FileMetadata, FileContent, FileType
from shared.utils.path_utils import normalize_path, get_file_extension, is_safe_path


def is_text_file(file_path: str) -> bool:
    """
    Check if a file is a text file.

    Args:
        file_path: The path to the file.

    Returns:
        True if the file is a text file, False otherwise.
    """
    # Normalize the path
    path = normalize_path(file_path)

    # Check if the file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found")

    # Read the first few KB of the file to check for binary content
    try:
        with open(path, 'rb') as f:
            chunk = f.read(8192)  # Read 8KB

        # Check for null bytes and other binary characters
        # This is a common heuristic for detecting binary files
        text_characters = bytes(range(32, 127)) + b'\n\r\t\b'

        # If more than 30% non-text characters, consider it binary
        binary_chars = sum(1 for byte in chunk if byte not in text_characters)
        if not chunk:
            return True  # Empty files are considered text
        if binary_chars / len(chunk) > 0.3:
            return False

        # Try to decode as UTF-8 as a final check
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False

    except Exception:
        # If we can't read the file, assume it's not text
        return False


def get_file_metadata(file_path: str, base_dir: Optional[str] = None) -> FileMetadata:
    """
    Get metadata for a file.

    Args:
        file_path: The path to the file.
        base_dir: Optional base directory for security checks.

    Returns:
        A FileMetadata object with information about the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file is not accessible or outside the base directory.
    """
    # Normalize the path
    path = normalize_path(file_path)

    # Security check if base_dir is provided
    if base_dir and not is_safe_path(path, base_dir):
        raise PermissionError(f"Access to {path} is not allowed")

    # Check if the file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found")

    # Get file stats
    stats = os.stat(path)

    # Determine file type
    file_type = FileType.UNKNOWN
    if os.path.isdir(path):
        file_type = FileType.DIRECTORY
    elif os.path.islink(path):
        file_type = FileType.SYMLINK
    elif os.path.isfile(path):
        # Check if it's a text or binary file
        if is_text_file(path):
            file_type = FileType.TEXT
        else:
            file_type = FileType.BINARY

    # Get file name and extension
    name = os.path.basename(path)
    extension = get_file_extension(path)

    # Determine mime type
    mime_type, encoding = mimetypes.guess_type(path)

    # Create and return the metadata
    return FileMetadata(
        path=path,
        name=name,
        type=file_type,
        size=stats.st_size,
        created_at=datetime.datetime.fromtimestamp(stats.st_ctime),
        modified_at=datetime.datetime.fromtimestamp(stats.st_mtime),
        is_readonly=not os.access(path, os.W_OK),
        mime_type=mime_type,
        encoding=encoding,
        extension=extension
    )


def read_file(file_path: str, encoding: str = 'utf-8', base_dir: Optional[str] = None) -> FileContent:
    """
    Read a file and return its content with metadata.

    Args:
        file_path: The path to the file.
        encoding: The encoding to use when reading the file.
        base_dir: Optional base directory for security checks.

    Returns:
        A FileContent object with the file content and metadata.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file is not accessible or outside the base directory.
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding.
    """
    # Get file metadata
    metadata = get_file_metadata(file_path, base_dir)

    # Check if it's a regular file
    if metadata.type not in [FileType.TEXT, FileType.BINARY]:
        raise ValueError(f"Cannot read {metadata.type} file: {file_path}")

    # Read the file content
    try:
        with open(metadata.path, 'r', encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Cannot decode file {file_path} with encoding {encoding}")

    # Create and return the file content
    return FileContent(
        path=metadata.path,
        content=content,
        metadata=metadata
    )
