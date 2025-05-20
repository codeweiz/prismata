"""
Error handling module.

This module provides error handling and recovery mechanisms for the agent.
"""

import sys
import traceback
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Type

from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Enum for error severity levels."""
    INFO = "info"           # Informational message, not an error
    WARNING = "warning"     # Warning, operation can continue
    ERROR = "error"         # Error, operation failed but system can continue
    CRITICAL = "critical"   # Critical error, system may need to restart


class ErrorCategory(Enum):
    """Enum for error categories."""
    NETWORK = "network"         # Network-related errors
    FILE_SYSTEM = "file_system" # File system errors
    PERMISSION = "permission"   # Permission errors
    VALIDATION = "validation"   # Input validation errors
    LLM = "llm"                 # LLM-related errors
    TOOL = "tool"               # Tool execution errors
    WORKFLOW = "workflow"       # Workflow errors
    UNKNOWN = "unknown"         # Unknown errors


class ErrorInfo:
    """Class for storing error information."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        exception: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        recovery_options: Optional[List[Dict[str, Any]]] = None,
        operation_id: Optional[str] = None
    ):
        """
        Initialize error information.
        
        Args:
            message: Error message.
            category: Error category.
            severity: Error severity.
            exception: Original exception.
            details: Additional error details.
            recovery_options: Available recovery options.
            operation_id: ID of the operation that caused the error.
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.exception = exception
        self.details = details or {}
        self.recovery_options = recovery_options or []
        self.operation_id = operation_id
        self.timestamp = self._get_timestamp()
        self.stack_trace = self._get_stack_trace() if exception else None
    
    def _get_timestamp(self) -> int:
        """Get current timestamp."""
        import time
        return int(time.time() * 1000)
    
    def _get_stack_trace(self) -> str:
        """Get stack trace from exception."""
        if self.exception:
            return ''.join(traceback.format_exception(
                type(self.exception),
                self.exception,
                self.exception.__traceback__
            ))
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error info to dictionary."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recovery_options": self.recovery_options,
            "operation_id": self.operation_id,
            "timestamp": self.timestamp,
            "stack_trace": self.stack_trace
        }
    
    def __str__(self) -> str:
        """String representation of error info."""
        return f"{self.severity.value.upper()}: {self.message} ({self.category.value})"


class ErrorHandler:
    """Class for handling errors and providing recovery options."""
    
    # Mapping of exception types to error categories
    _exception_category_map: Dict[Type[Exception], ErrorCategory] = {
        ConnectionError: ErrorCategory.NETWORK,
        TimeoutError: ErrorCategory.NETWORK,
        FileNotFoundError: ErrorCategory.FILE_SYSTEM,
        PermissionError: ErrorCategory.PERMISSION,
        ValueError: ErrorCategory.VALIDATION,
        TypeError: ErrorCategory.VALIDATION
    }
    
    # Mapping of exception types to error severities
    _exception_severity_map: Dict[Type[Exception], ErrorSeverity] = {
        ConnectionError: ErrorSeverity.ERROR,
        TimeoutError: ErrorSeverity.ERROR,
        FileNotFoundError: ErrorSeverity.ERROR,
        PermissionError: ErrorSeverity.ERROR,
        ValueError: ErrorSeverity.WARNING,
        TypeError: ErrorSeverity.WARNING
    }
    
    # Registry of error handlers by category
    _error_handlers: Dict[ErrorCategory, List[Callable[[ErrorInfo], None]]] = {
        category: [] for category in ErrorCategory
    }
    
    # Registry of recovery strategies by category
    _recovery_strategies: Dict[ErrorCategory, Dict[str, Callable[[ErrorInfo], Any]]] = {
        category: {} for category in ErrorCategory
    }
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        message: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None
    ) -> ErrorInfo:
        """
        Handle an exception and return error information.
        
        Args:
            exception: The exception to handle.
            message: Custom error message. If None, uses exception message.
            category: Error category. If None, determined from exception type.
            severity: Error severity. If None, determined from exception type.
            details: Additional error details.
            operation_id: ID of the operation that caused the error.
            
        Returns:
            Error information.
        """
        # Determine message
        if message is None:
            message = str(exception)
        
        # Determine category
        if category is None:
            category = cls._get_category_for_exception(exception)
        
        # Determine severity
        if severity is None:
            severity = cls._get_severity_for_exception(exception)
        
        # Create error info
        error_info = ErrorInfo(
            message=message,
            category=category,
            severity=severity,
            exception=exception,
            details=details,
            operation_id=operation_id
        )
        
        # Add recovery options
        error_info.recovery_options = cls._get_recovery_options(error_info)
        
        # Log the error
        cls._log_error(error_info)
        
        # Call registered handlers
        cls._call_handlers(error_info)
        
        return error_info
    
    @classmethod
    def create_error(
        cls,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        details: Optional[Dict[str, Any]] = None,
        operation_id: Optional[str] = None
    ) -> ErrorInfo:
        """
        Create an error without an exception.
        
        Args:
            message: Error message.
            category: Error category.
            severity: Error severity.
            details: Additional error details.
            operation_id: ID of the operation that caused the error.
            
        Returns:
            Error information.
        """
        # Create error info
        error_info = ErrorInfo(
            message=message,
            category=category,
            severity=severity,
            details=details,
            operation_id=operation_id
        )
        
        # Add recovery options
        error_info.recovery_options = cls._get_recovery_options(error_info)
        
        # Log the error
        cls._log_error(error_info)
        
        # Call registered handlers
        cls._call_handlers(error_info)
        
        return error_info
    
    @classmethod
    def register_handler(cls, category: ErrorCategory, handler: Callable[[ErrorInfo], None]) -> None:
        """
        Register an error handler for a specific category.
        
        Args:
            category: Error category.
            handler: Error handler function.
        """
        cls._error_handlers[category].append(handler)
    
    @classmethod
    def register_recovery_strategy(
        cls,
        category: ErrorCategory,
        name: str,
        strategy: Callable[[ErrorInfo], Any],
        description: str
    ) -> None:
        """
        Register a recovery strategy for a specific category.
        
        Args:
            category: Error category.
            name: Strategy name.
            strategy: Recovery strategy function.
            description: Strategy description.
        """
        cls._recovery_strategies[category][name] = strategy
        
        # Store the description in the strategy function
        strategy.__description__ = description
    
    @classmethod
    def recover(cls, error_info: ErrorInfo, strategy_name: str) -> Any:
        """
        Apply a recovery strategy to an error.
        
        Args:
            error_info: Error information.
            strategy_name: Name of the recovery strategy to apply.
            
        Returns:
            Result of the recovery strategy.
            
        Raises:
            ValueError: If the strategy is not found.
        """
        category = error_info.category
        
        if strategy_name not in cls._recovery_strategies[category]:
            raise ValueError(f"Recovery strategy '{strategy_name}' not found for category {category.value}")
        
        strategy = cls._recovery_strategies[category][strategy_name]
        
        logger.info(f"Applying recovery strategy '{strategy_name}' for error: {error_info}")
        
        return strategy(error_info)
    
    @classmethod
    def _get_category_for_exception(cls, exception: Exception) -> ErrorCategory:
        """Get error category for an exception type."""
        for exc_type, category in cls._exception_category_map.items():
            if isinstance(exception, exc_type):
                return category
        return ErrorCategory.UNKNOWN
    
    @classmethod
    def _get_severity_for_exception(cls, exception: Exception) -> ErrorSeverity:
        """Get error severity for an exception type."""
        for exc_type, severity in cls._exception_severity_map.items():
            if isinstance(exception, exc_type):
                return severity
        return ErrorSeverity.ERROR
    
    @classmethod
    def _get_recovery_options(cls, error_info: ErrorInfo) -> List[Dict[str, Any]]:
        """Get recovery options for an error."""
        category = error_info.category
        options = []
        
        for name, strategy in cls._recovery_strategies[category].items():
            description = getattr(strategy, "__description__", "No description")
            options.append({
                "name": name,
                "description": description
            })
        
        return options
    
    @classmethod
    def _log_error(cls, error_info: ErrorInfo) -> None:
        """Log an error."""
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(str(error_info), exc_info=error_info.exception)
        elif error_info.severity == ErrorSeverity.ERROR:
            logger.error(str(error_info), exc_info=error_info.exception)
        elif error_info.severity == ErrorSeverity.WARNING:
            logger.warning(str(error_info), exc_info=error_info.exception)
        else:
            logger.info(str(error_info))
    
    @classmethod
    def _call_handlers(cls, error_info: ErrorInfo) -> None:
        """Call registered handlers for an error."""
        category = error_info.category
        
        for handler in cls._error_handlers[category]:
            try:
                handler(error_info)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")


# Register default recovery strategies

def _retry_network_operation(error_info: ErrorInfo) -> Any:
    """Retry a network operation."""
    # This is a placeholder. In a real implementation, this would retry the operation.
    logger.info(f"Retrying network operation for error: {error_info}")
    return None

ErrorHandler.register_recovery_strategy(
    ErrorCategory.NETWORK,
    "retry",
    _retry_network_operation,
    "Retry the network operation"
)

def _skip_file(error_info: ErrorInfo) -> Any:
    """Skip a file that caused an error."""
    # This is a placeholder. In a real implementation, this would skip the file.
    logger.info(f"Skipping file for error: {error_info}")
    return None

ErrorHandler.register_recovery_strategy(
    ErrorCategory.FILE_SYSTEM,
    "skip_file",
    _skip_file,
    "Skip the file that caused the error"
)

def _create_file(error_info: ErrorInfo) -> Any:
    """Create a missing file."""
    # This is a placeholder. In a real implementation, this would create the file.
    logger.info(f"Creating missing file for error: {error_info}")
    return None

ErrorHandler.register_recovery_strategy(
    ErrorCategory.FILE_SYSTEM,
    "create_file",
    _create_file,
    "Create the missing file"
)
