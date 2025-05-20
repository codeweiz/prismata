"""
State models for the LangGraph agent.

This module defines the state models used by the LangGraph agent.
"""

from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Agent state model for LangGraph workflow."""

    # Task information
    task_id: str = Field(description="Unique identifier for the task")
    task_type: str = Field(description="Type of task to perform")

    # Input and context
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input data for the task")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the task")

    # Status and results
    status: str = Field(default="in_progress", description="Current status of the task")
    results: Optional[Dict[str, Any]] = Field(default=None, description="Results of the task")
    changes: Optional[Dict[str, Any]] = Field(default=None, description="Changes made by the task")
    error: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Error information if the task failed")
    recovery_options: Optional[List[Dict[str, Any]]] = Field(default=None, description="Available recovery options")
    operation_id: Optional[str] = Field(default=None, description="ID of the current operation")

    # Additional fields
    requires_confirmation: bool = Field(default=False, description="Whether the task requires user confirmation")
    preview: Optional[str] = Field(default=None, description="Preview of the changes to be made")
    verification_passed: bool = Field(default=True, description="Whether verification passed")
