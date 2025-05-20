"""
Base Agent implementation.

This module defines the base agent class that all specific agents will inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentRequest(BaseModel):
    """Base model for agent requests."""
    task_type: str
    inputs: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Base model for agent responses."""
    task_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    requires_user_confirmation: bool = False
    preview: Optional[Dict[str, Any]] = None
    changes: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent with optional configuration."""
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute the agent task based on the request.
        
        Args:
            request: The agent request containing task type, inputs, and context.
            
        Returns:
            An agent response with the results or error information.
        """
        pass
    
    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """
        Cancel an ongoing task.
        
        Args:
            task_id: The ID of the task to cancel.
            
        Returns:
            True if the task was successfully canceled, False otherwise.
        """
        pass
