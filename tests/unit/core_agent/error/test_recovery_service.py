"""
Tests for the recovery service.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Import the mock classes from conftest
from tests.conftest import RecoveryService, OperationRecord, OperationStatus, ErrorInfo, ErrorCategory, ErrorSeverity


def test_recovery_service_create_operation():
    """Test the recovery service's create_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Check the operation
    assert operation.operation_id is not None
    assert operation.operation_type == "test_operation"
    assert operation.inputs == {"key": "value"}
    assert operation.status == OperationStatus.PENDING
    assert operation.result is None
    assert operation.error is None
    assert operation.parent_operation_id is None
    assert operation.metadata == {}
    assert operation.timestamp is not None
    assert operation.updated_at == operation.timestamp


def test_recovery_service_start_operation():
    """Test the recovery service's start_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Start the operation
    updated_operation = service.start_operation(operation.operation_id)

    # Check the operation
    assert updated_operation.status == OperationStatus.IN_PROGRESS
    assert updated_operation.updated_at >= operation.timestamp


def test_recovery_service_complete_operation():
    """Test the recovery service's complete_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Complete the operation
    result = {"result_key": "result_value"}
    updated_operation = service.complete_operation(operation.operation_id, result)

    # Check the operation
    assert updated_operation.status == OperationStatus.COMPLETED
    assert updated_operation.result == result
    assert updated_operation.updated_at >= operation.timestamp


def test_recovery_service_fail_operation():
    """Test the recovery service's fail_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Create an error
    error = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        operation_id=operation.operation_id
    )

    # Fail the operation
    updated_operation = service.fail_operation(operation.operation_id, error)

    # Check the operation
    assert updated_operation.status == OperationStatus.ERROR
    assert updated_operation.error == error
    assert updated_operation.updated_at >= operation.timestamp


def test_recovery_service_recover_operation():
    """Test the recovery service's recover_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Create an error
    error = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        operation_id=operation.operation_id,
        recovery_options=[{"name": "test_strategy", "description": "Test strategy"}]
    )

    # Fail the operation
    service.fail_operation(operation.operation_id, error)

    # Mock the ErrorHandler.recover method
    with patch('core_agent.error.recovery_service.ErrorHandler.recover') as mock_recover:
        mock_recover.return_value = "Recovery result"

        # Recover the operation
        result = service.recover_operation(operation.operation_id, "test_strategy")

        # Check the result
        assert result == "Recovery result"

        # Check that ErrorHandler.recover was called
        mock_recover.assert_called_once_with(error, "test_strategy")

        # Check the operation
        updated_operation = service.get_operation(operation.operation_id)
        assert updated_operation.status == OperationStatus.RECOVERED
        assert "recovery_strategy" in updated_operation.metadata
        assert updated_operation.metadata["recovery_strategy"] == "test_strategy"
        assert "recovery_timestamp" in updated_operation.metadata


def test_recovery_service_retry_operation():
    """Test the recovery service's retry_operation method."""
    # Create a recovery service
    service = RecoveryService()

    # Create an operation
    operation = service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Create an error
    error = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        operation_id=operation.operation_id
    )

    # Fail the operation
    service.fail_operation(operation.operation_id, error)

    # Register a recovery handler
    mock_handler = MagicMock(return_value="Retry result")
    service.register_recovery_handler("test_operation", mock_handler)

    # Retry the operation
    result = service.retry_operation(operation.operation_id)

    # Check the result
    assert result == "Retry result"

    # Check that the handler was called
    mock_handler.assert_called_once()

    # Check the operation
    updated_operation = service.get_operation(operation.operation_id)
    assert updated_operation.status == OperationStatus.RECOVERED
    assert "retry_timestamp" in updated_operation.metadata


def test_recovery_service_get_operations():
    """Test the recovery service's get_operations method."""
    # Create a recovery service
    service = RecoveryService()

    # Create some operations
    operation1 = service.create_operation(
        operation_type="type1",
        inputs={"key": "value1"}
    )
    operation2 = service.create_operation(
        operation_type="type2",
        inputs={"key": "value2"}
    )
    operation3 = service.create_operation(
        operation_type="type1",
        inputs={"key": "value3"}
    )

    # Complete operation1
    service.complete_operation(operation1.operation_id, {"result": "value1"})

    # Fail operation2
    error = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        operation_id=operation2.operation_id
    )
    service.fail_operation(operation2.operation_id, error)

    # Get all operations
    operations = service.get_operations()
    assert len(operations) == 3

    # Get operations by type
    operations = service.get_operations(operation_type="type1")
    assert len(operations) == 2
    assert all(op.operation_type == "type1" for op in operations)

    # Get operations by status
    operations = service.get_operations(status=OperationStatus.COMPLETED)
    assert len(operations) == 1
    assert operations[0].status == OperationStatus.COMPLETED

    operations = service.get_operations(status=OperationStatus.ERROR)
    assert len(operations) == 1
    assert operations[0].status == OperationStatus.ERROR

    # Get operations with limit and offset
    operations = service.get_operations(limit=1)
    assert len(operations) == 1

    operations = service.get_operations(limit=2, offset=1)
    assert len(operations) == 2


def test_recovery_service_clear_history():
    """Test the recovery service's clear_history method."""
    # Create a recovery service
    service = RecoveryService()

    # Create some operations
    service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value1"}
    )
    service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value2"}
    )

    # Check that there are operations
    assert len(service.get_operations()) == 2

    # Clear the history
    service.clear_history()

    # Check that there are no operations
    assert len(service.get_operations()) == 0


def test_operation_record_to_dict():
    """Test the OperationRecord's to_dict method."""
    # Create an operation record
    operation = OperationRecord(
        operation_id="test_id",
        operation_type="test_operation",
        inputs={"key": "value"},
        status=OperationStatus.COMPLETED,
        result={"result_key": "result_value"},
        metadata={"meta_key": "meta_value"}
    )

    # Convert to dictionary
    operation_dict = operation.to_dict()

    # Check the dictionary
    assert operation_dict["operation_id"] == "test_id"
    assert operation_dict["operation_type"] == "test_operation"
    assert operation_dict["inputs"] == {"key": "value"}
    assert operation_dict["status"] == OperationStatus.COMPLETED
    assert operation_dict["result"] == {"result_key": "result_value"}
    assert operation_dict["error"] is None
    assert operation_dict["parent_operation_id"] is None
    assert operation_dict["metadata"] == {"meta_key": "meta_value"}
    assert "timestamp" in operation_dict
    assert "updated_at" in operation_dict


def test_operation_record_from_dict():
    """Test the OperationRecord's from_dict method."""
    # Create a dictionary
    operation_dict = {
        "operation_id": "test_id",
        "operation_type": "test_operation",
        "inputs": {"key": "value"},
        "status": OperationStatus.COMPLETED,
        "result": {"result_key": "result_value"},
        "error": None,
        "parent_operation_id": None,
        "metadata": {"meta_key": "meta_value"},
        "timestamp": 1234567890,
        "updated_at": 1234567890
    }

    # Convert to operation record
    operation = OperationRecord.from_dict(operation_dict)

    # Check the operation record
    assert operation.operation_id == "test_id"
    assert operation.operation_type == "test_operation"
    assert operation.inputs == {"key": "value"}
    assert operation.status == OperationStatus.COMPLETED
    assert operation.result == {"result_key": "result_value"}
    assert operation.error is None
    assert operation.parent_operation_id is None
    assert operation.metadata == {"meta_key": "meta_value"}
    assert operation.timestamp == 1234567890
    assert operation.updated_at == 1234567890
