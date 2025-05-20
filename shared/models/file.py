"""
File models.

This module defines models related to file operations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Enum for file types."""
    TEXT = "text"
    BINARY = "binary"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


class FileMetadata(BaseModel):
    """Model for file metadata."""
    path: str
    name: str
    type: FileType
    size: int
    created_at: datetime
    modified_at: datetime
    is_readonly: bool = False
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    extension: Optional[str] = None


class FileContent(BaseModel):
    """Model for file content."""
    path: str
    content: str
    metadata: FileMetadata


class FileChange(BaseModel):
    """Model for file changes."""
    path: str
    operation: str  # "create", "update", "delete"
    content: Optional[str] = None
    old_content: Optional[str] = None
    diff: Optional[str] = None  # For displaying changes


class FileOperation(BaseModel):
    """Model for file operations."""
    operation_id: str
    operation_type: str  # "read", "write", "delete", etc.
    path: str
    timestamp: datetime
    user: Optional[str] = None
    metadata: Optional[Dict] = None
