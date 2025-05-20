"""
Recovery service module.

This module provides operation history tracking and recovery mechanisms.
"""

import json
import os
import time
import uuid
from typing import Dict, Any, Optional, List, Callable

from core_agent.error.error_handler import ErrorHandler, ErrorInfo, ErrorCategory, ErrorSeverity
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class OperationStatus:
    """Operation status constants."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    RECOVERED = "recovered"


class OperationRecord:
    """Class for storing operation records."""
    
    def __init__(
        self,
        operation_id: str,
        operation_type: str,
        inputs: Dict[str, Any],
        status: str = OperationStatus.PENDING,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[ErrorInfo] = None,
        parent_operation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize operation record.
        
        Args:
            operation_id: Unique operation ID.
            operation_type: Type of operation.
            inputs: Operation inputs.
            status: Operation status.
            result: Operation result.
            error: Error information if operation failed.
            parent_operation_id: ID of parent operation.
            metadata: Additional metadata.
        """
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.inputs = inputs
        self.status = status
        self.result = result
        self.error = error
        self.parent_operation_id = parent_operation_id
        self.metadata = metadata or {}
        self.timestamp = int(time.time() * 1000)
        self.updated_at = self.timestamp
    
    def update_status(self, status: str) -> None:
        """Update operation status."""
        self.status = status
        self.updated_at = int(time.time() * 1000)
    
    def set_result(self, result: Dict[str, Any]) -> None:
        """Set operation result."""
        self.result = result
        self.status = OperationStatus.COMPLETED
        self.updated_at = int(time.time() * 1000)
    
    def set_error(self, error: ErrorInfo) -> None:
        """Set operation error."""
        self.error = error
        self.status = OperationStatus.ERROR
        self.updated_at = int(time.time() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert operation record to dictionary."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "inputs": self.inputs,
            "status": self.status,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "parent_operation_id": self.parent_operation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OperationRecord':
        """Create operation record from dictionary."""
        error = None
        if data.get("error"):
            error = ErrorInfo(
                message=data["error"]["message"],
                category=ErrorCategory(data["error"]["category"]),
                severity=ErrorSeverity(data["error"]["severity"]),
                details=data["error"].get("details"),
                recovery_options=data["error"].get("recovery_options"),
                operation_id=data["error"].get("operation_id")
            )
        
        return cls(
            operation_id=data["operation_id"],
            operation_type=data["operation_type"],
            inputs=data["inputs"],
            status=data["status"],
            result=data.get("result"),
            error=error,
            parent_operation_id=data.get("parent_operation_id"),
            metadata=data.get("metadata", {})
        )


class RecoveryService:
    """Service for tracking operation history and providing recovery mechanisms."""
    
    def __init__(self, history_file: Optional[str] = None):
        """
        Initialize recovery service.
        
        Args:
            history_file: Path to history file. If None, history is not persisted.
        """
        self.history_file = history_file
        self.operations: Dict[str, OperationRecord] = {}
        self.recovery_handlers: Dict[str, Callable[[OperationRecord], Any]] = {}
        
        # Load history from file if available
        if history_file and os.path.exists(history_file):
            self._load_history()
    
    def create_operation(
        self,
        operation_type: str,
        inputs: Dict[str, Any],
        parent_operation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationRecord:
        """
        Create a new operation record.
        
        Args:
            operation_type: Type of operation.
            inputs: Operation inputs.
            parent_operation_id: ID of parent operation.
            metadata: Additional metadata.
            
        Returns:
            Operation record.
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationRecord(
            operation_id=operation_id,
            operation_type=operation_type,
            inputs=inputs,
            status=OperationStatus.PENDING,
            parent_operation_id=parent_operation_id,
            metadata=metadata
        )
        
        self.operations[operation_id] = operation
        self._save_history()
        
        return operation
    
    def start_operation(self, operation_id: str) -> OperationRecord:
        """
        Mark an operation as in progress.
        
        Args:
            operation_id: Operation ID.
            
        Returns:
            Updated operation record.
            
        Raises:
            ValueError: If operation is not found.
        """
        operation = self._get_operation(operation_id)
        operation.update_status(OperationStatus.IN_PROGRESS)
        self._save_history()
        
        return operation
    
    def complete_operation(self, operation_id: str, result: Dict[str, Any]) -> OperationRecord:
        """
        Mark an operation as completed.
        
        Args:
            operation_id: Operation ID.
            result: Operation result.
            
        Returns:
            Updated operation record.
            
        Raises:
            ValueError: If operation is not found.
        """
        operation = self._get_operation(operation_id)
        operation.set_result(result)
        self._save_history()
        
        return operation
    
    def fail_operation(
        self,
        operation_id: str,
        error: ErrorInfo
    ) -> OperationRecord:
        """
        Mark an operation as failed.
        
        Args:
            operation_id: Operation ID.
            error: Error information.
            
        Returns:
            Updated operation record.
            
        Raises:
            ValueError: If operation is not found.
        """
        operation = self._get_operation(operation_id)
        operation.set_error(error)
        self._save_history()
        
        return operation
    
    def recover_operation(
        self,
        operation_id: str,
        strategy_name: str
    ) -> Any:
        """
        Recover a failed operation.
        
        Args:
            operation_id: Operation ID.
            strategy_name: Name of the recovery strategy to apply.
            
        Returns:
            Result of the recovery strategy.
            
        Raises:
            ValueError: If operation is not found or not in error state.
        """
        operation = self._get_operation(operation_id)
        
        if operation.status != OperationStatus.ERROR:
            raise ValueError(f"Operation {operation_id} is not in error state")
        
        if not operation.error:
            raise ValueError(f"Operation {operation_id} has no error information")
        
        # Apply recovery strategy
        result = ErrorHandler.recover(operation.error, strategy_name)
        
        # Update operation status
        operation.update_status(OperationStatus.RECOVERED)
        operation.metadata["recovery_strategy"] = strategy_name
        operation.metadata["recovery_timestamp"] = int(time.time() * 1000)
        
        self._save_history()
        
        return result
    
    def retry_operation(self, operation_id: str) -> Any:
        """
        Retry a failed operation.
        
        Args:
            operation_id: Operation ID.
            
        Returns:
            Result of the retry.
            
        Raises:
            ValueError: If operation is not found or not in error state.
        """
        operation = self._get_operation(operation_id)
        
        if operation.status != OperationStatus.ERROR:
            raise ValueError(f"Operation {operation_id} is not in error state")
        
        # Get the operation type and inputs
        operation_type = operation.operation_type
        inputs = operation.inputs
        
        # Check if we have a recovery handler for this operation type
        if operation_type not in self.recovery_handlers:
            raise ValueError(f"No recovery handler registered for operation type {operation_type}")
        
        # Call the recovery handler
        handler = self.recovery_handlers[operation_type]
        result = handler(operation)
        
        # Update operation status
        operation.update_status(OperationStatus.RECOVERED)
        operation.metadata["retry_timestamp"] = int(time.time() * 1000)
        
        self._save_history()
        
        return result
    
    def register_recovery_handler(
        self,
        operation_type: str,
        handler: Callable[[OperationRecord], Any]
    ) -> None:
        """
        Register a recovery handler for an operation type.
        
        Args:
            operation_type: Operation type.
            handler: Recovery handler function.
        """
        self.recovery_handlers[operation_type] = handler
    
    def get_operation(self, operation_id: str) -> OperationRecord:
        """
        Get an operation record.
        
        Args:
            operation_id: Operation ID.
            
        Returns:
            Operation record.
            
        Raises:
            ValueError: If operation is not found.
        """
        return self._get_operation(operation_id)
    
    def get_operations(
        self,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[OperationRecord]:
        """
        Get operation records.
        
        Args:
            operation_type: Filter by operation type.
            status: Filter by status.
            limit: Maximum number of records to return.
            offset: Offset for pagination.
            
        Returns:
            List of operation records.
        """
        operations = list(self.operations.values())
        
        # Apply filters
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        if status:
            operations = [op for op in operations if op.status == status]
        
        # Sort by timestamp (newest first)
        operations.sort(key=lambda op: op.timestamp, reverse=True)
        
        # Apply pagination
        operations = operations[offset:offset + limit]
        
        return operations
    
    def clear_history(self) -> None:
        """Clear operation history."""
        self.operations = {}
        self._save_history()
    
    def _get_operation(self, operation_id: str) -> OperationRecord:
        """Get an operation record by ID."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")
        
        return self.operations[operation_id]
    
    def _save_history(self) -> None:
        """Save operation history to file."""
        if not self.history_file:
            return
        
        try:
            # Convert operations to dictionaries
            operations_dict = {
                op_id: op.to_dict() for op_id, op in self.operations.items()
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            # Write to file
            with open(self.history_file, 'w') as f:
                json.dump(operations_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving operation history: {e}")
    
    def _load_history(self) -> None:
        """Load operation history from file."""
        if not self.history_file or not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r') as f:
                operations_dict = json.load(f)
            
            # Convert dictionaries to operation records
            self.operations = {
                op_id: OperationRecord.from_dict(op_data)
                for op_id, op_data in operations_dict.items()
            }
        except Exception as e:
            logger.error(f"Error loading operation history: {e}")
            self.operations = {}
