"""
Custom exceptions module.

This module defines custom exceptions used by the agent.
"""

from typing import Dict, Any, Optional


class AgentException(Exception):
    """Base exception for all agent exceptions."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent exception.
        
        Args:
            message: Exception message.
            details: Additional exception details.
        """
        super().__init__(message)
        self.details = details or {}


class NetworkException(AgentException):
    """Exception for network-related errors."""
    pass


class FileSystemException(AgentException):
    """Exception for file system-related errors."""
    pass


class PermissionException(AgentException):
    """Exception for permission-related errors."""
    pass


class ValidationException(AgentException):
    """Exception for validation errors."""
    pass


class LLMException(AgentException):
    """Exception for LLM-related errors."""
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        prompt: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize LLM exception.
        
        Args:
            message: Exception message.
            model: LLM model name.
            prompt: LLM prompt.
            details: Additional exception details.
        """
        details = details or {}
        if model:
            details["model"] = model
        if prompt:
            details["prompt"] = prompt
        
        super().__init__(message, details)


class ToolException(AgentException):
    """Exception for tool execution errors."""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tool exception.
        
        Args:
            message: Exception message.
            tool_name: Tool name.
            tool_args: Tool arguments.
            details: Additional exception details.
        """
        details = details or {}
        if tool_name:
            details["tool_name"] = tool_name
        if tool_args:
            details["tool_args"] = tool_args
        
        super().__init__(message, details)


class WorkflowException(AgentException):
    """Exception for workflow errors."""
    
    def __init__(
        self,
        message: str,
        node_name: Optional[str] = None,
        node_inputs: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize workflow exception.
        
        Args:
            message: Exception message.
            node_name: Workflow node name.
            node_inputs: Workflow node inputs.
            details: Additional exception details.
        """
        details = details or {}
        if node_name:
            details["node_name"] = node_name
        if node_inputs:
            details["node_inputs"] = node_inputs
        
        super().__init__(message, details)


class UserCancelledException(AgentException):
    """Exception for user-cancelled operations."""
    pass
