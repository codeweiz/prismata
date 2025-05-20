"""
Tests for the error handler.
"""

import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Import the mock classes from conftest
from tests.conftest import ErrorHandler, ErrorCategory, ErrorSeverity, ErrorInfo

# Mock exceptions
class NetworkException(Exception):
    pass

class FileSystemException(Exception):
    pass

class ValidationException(Exception):
    pass


def test_error_handler_handle_exception():
    """Test the error handler's handle_exception method."""
    # Create a test exception
    exception = ValueError("Test error")

    # Handle the exception
    error_info = ErrorHandler.handle_exception(exception)

    # Check the error info
    assert error_info.message == "Test error"
    assert error_info.category == ErrorCategory.VALIDATION
    assert error_info.severity == ErrorSeverity.WARNING
    assert error_info.exception == exception
    assert error_info.stack_trace is not None


def test_error_handler_create_error():
    """Test the error handler's create_error method."""
    # Create an error
    error_info = ErrorHandler.create_error(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR
    )

    # Check the error info
    assert error_info.message == "Test error"
    assert error_info.category == ErrorCategory.NETWORK
    assert error_info.severity == ErrorSeverity.ERROR
    assert error_info.exception is None
    assert error_info.stack_trace is None


def test_error_handler_register_handler():
    """Test the error handler's register_handler method."""
    # Create a mock handler
    mock_handler = MagicMock()

    # Register the handler
    ErrorHandler.register_handler(ErrorCategory.NETWORK, mock_handler)

    # Create an error
    error_info = ErrorHandler.create_error(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR
    )

    # Check that the handler was called
    mock_handler.assert_called_once_with(error_info)


def test_error_handler_register_recovery_strategy():
    """Test the error handler's register_recovery_strategy method."""
    # Create a mock strategy
    mock_strategy = MagicMock(return_value="Recovery result")

    # Register the strategy
    ErrorHandler.register_recovery_strategy(
        ErrorCategory.NETWORK,
        "test_strategy",
        mock_strategy,
        "Test strategy description"
    )

    # Create an error
    error_info = ErrorHandler.create_error(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR
    )

    # Check the recovery options
    assert len(error_info.recovery_options) > 0
    assert any(option["name"] == "test_strategy" for option in error_info.recovery_options)

    # Recover using the strategy
    result = ErrorHandler.recover(error_info, "test_strategy")

    # Check the result
    assert result == "Recovery result"

    # Check that the strategy was called
    mock_strategy.assert_called_once_with(error_info)


def test_error_handler_exception_category_mapping():
    """Test the error handler's exception category mapping."""
    # Test various exception types
    assert ErrorHandler._get_category_for_exception(ConnectionError()) == ErrorCategory.NETWORK
    assert ErrorHandler._get_category_for_exception(TimeoutError()) == ErrorCategory.NETWORK
    assert ErrorHandler._get_category_for_exception(FileNotFoundError()) == ErrorCategory.FILE_SYSTEM
    assert ErrorHandler._get_category_for_exception(PermissionError()) == ErrorCategory.PERMISSION
    assert ErrorHandler._get_category_for_exception(ValueError()) == ErrorCategory.VALIDATION
    assert ErrorHandler._get_category_for_exception(TypeError()) == ErrorCategory.VALIDATION
    assert ErrorHandler._get_category_for_exception(Exception()) == ErrorCategory.UNKNOWN


def test_error_handler_exception_severity_mapping():
    """Test the error handler's exception severity mapping."""
    # Test various exception types
    assert ErrorHandler._get_severity_for_exception(ConnectionError()) == ErrorSeverity.ERROR
    assert ErrorHandler._get_severity_for_exception(TimeoutError()) == ErrorSeverity.ERROR
    assert ErrorHandler._get_severity_for_exception(FileNotFoundError()) == ErrorSeverity.ERROR
    assert ErrorHandler._get_severity_for_exception(PermissionError()) == ErrorSeverity.ERROR
    assert ErrorHandler._get_severity_for_exception(ValueError()) == ErrorSeverity.WARNING
    assert ErrorHandler._get_severity_for_exception(TypeError()) == ErrorSeverity.WARNING
    assert ErrorHandler._get_severity_for_exception(Exception()) == ErrorSeverity.ERROR


def test_error_info_to_dict():
    """Test the ErrorInfo's to_dict method."""
    # Create an error info
    error_info = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        details={"key": "value"},
        recovery_options=[{"name": "test_strategy", "description": "Test strategy"}],
        operation_id="test_operation"
    )

    # Convert to dictionary
    error_dict = error_info.to_dict()

    # Check the dictionary
    assert error_dict["message"] == "Test error"
    assert error_dict["category"] == "network"
    assert error_dict["severity"] == "error"
    assert error_dict["details"] == {"key": "value"}
    assert error_dict["recovery_options"] == [{"name": "test_strategy", "description": "Test strategy"}]
    assert error_dict["operation_id"] == "test_operation"
    assert "timestamp" in error_dict
    assert error_dict["stack_trace"] is None


def test_error_info_str():
    """Test the ErrorInfo's __str__ method."""
    # Create an error info
    error_info = ErrorInfo(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR
    )

    # Convert to string
    error_str = str(error_info)

    # Check the string
    assert "ERROR" in error_str
    assert "Test error" in error_str
    assert "network" in error_str
