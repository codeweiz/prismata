"""
History models.

This module defines models related to operation history.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Enum for operation types."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    GENERATE_CODE = "generate_code"
    ANALYZE_CODE = "analyze_code"
    CUSTOM = "custom"


class OperationStatus(str, Enum):
    """Enum for operation statuses."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    CANCELLED = "cancelled"


class OperationRecord(BaseModel):
    """Model for an operation record."""
    id: str
    type: OperationType
    timestamp: datetime
    status: OperationStatus
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileOperationRecord(OperationRecord):
    """Model for a file operation record."""
    file_path: str
    operation: str  # "read", "write", "delete", etc.
    content_preview: Optional[str] = None
    diff: Optional[str] = None


class CodeOperationRecord(OperationRecord):
    """Model for a code operation record."""
    language: str
    code_preview: Optional[str] = None
    file_path: Optional[str] = None


class HistoryEntry(BaseModel):
    """Model for a history entry."""
    id: str
    timestamp: datetime
    operation: Union[OperationRecord, FileOperationRecord, CodeOperationRecord]
    description: str
    can_undo: bool = False
    undo_operation: Optional[Dict[str, Any]] = None


class HistoryManager(BaseModel):
    """Model for managing operation history."""
    entries: List[HistoryEntry] = Field(default_factory=list)
    max_entries: int = 100

    def add_entry(self, entry: HistoryEntry) -> None:
        """
        Add an entry to the history.
        
        Args:
            entry: The history entry to add.
        """
        self.entries.append(entry)
        
        # Trim the history if it exceeds the maximum number of entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_entries(
        self,
        limit: Optional[int] = None,
        operation_type: Optional[OperationType] = None,
        status: Optional[OperationStatus] = None
    ) -> List[HistoryEntry]:
        """
        Get history entries with optional filtering.
        
        Args:
            limit: Optional limit on the number of entries to return.
            operation_type: Optional filter by operation type.
            status: Optional filter by operation status.
            
        Returns:
            A list of history entries.
        """
        filtered_entries = self.entries
        
        # Filter by operation type if specified
        if operation_type:
            filtered_entries = [
                entry for entry in filtered_entries
                if entry.operation.type == operation_type
            ]
        
        # Filter by status if specified
        if status:
            filtered_entries = [
                entry for entry in filtered_entries
                if entry.operation.status == status
            ]
        
        # Apply limit if specified
        if limit is not None:
            filtered_entries = filtered_entries[-limit:]
        
        return filtered_entries

    def clear_history(self) -> None:
        """Clear the history."""
        self.entries = []

    def get_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        """
        Get a specific history entry by ID.
        
        Args:
            entry_id: The ID of the entry to get.
            
        Returns:
            The history entry if found, None otherwise.
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
