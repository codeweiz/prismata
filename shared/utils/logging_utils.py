"""
Logging utilities.

This module provides utility functions for logging.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any


def setup_logger(
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        propagate: bool = False
) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name: The name of the logger.
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.
        log_format: Optional log format string.
        propagate: Whether to propagate logs to parent loggers.
        
    Returns:
        A configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    logger.propagate = propagate

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Default format if not provided
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_file is provided
    if log_file:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name. If the logger doesn't exist, it will be created with default settings.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A logger instance.
    """
    logger = logging.getLogger(name)

    # If the logger has no handlers, set up a basic configuration
    if not logger.handlers and not logging.root.handlers:
        setup_logger(name)

    return logger


class LogContext:
    """Context manager for adding context to log messages."""

    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """
        Initialize the log context.
        
        Args:
            logger: The logger to use.
            context: The context dictionary to add to log messages.
        """
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self):
        """Enter the context manager."""
        old_factory = self.old_factory
        context = self.context

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        logging.setLogRecordFactory(self.old_factory)
