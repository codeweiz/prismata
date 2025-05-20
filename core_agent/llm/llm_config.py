"""
LLM configuration.

This module defines the configuration for LLM models.
"""

from enum import Enum
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, Field


class LLMType(str, Enum):
    """Enum for LLM types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


class LLMConfig(BaseModel):
    """Configuration for LLM models."""
    
    model_type: LLMType = Field(
        description="Type of LLM model to use"
    )
    model_name: str = Field(
        description="Name of the model to use"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the model provider"
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Base URL for the API"
    )
    temperature: float = Field(
        default=0.7,
        description="Temperature for sampling"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum number of tokens to generate"
    )
    additional_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for the model"
    )


class CodeGenerationPromptConfig(BaseModel):
    """Configuration for code generation prompts."""
    
    system_message: str = Field(
        description="System message for the LLM"
    )
    user_message_template: str = Field(
        description="Template for user messages"
    )
    examples: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Examples for few-shot learning"
    )


class CodeAnalysisPromptConfig(BaseModel):
    """Configuration for code analysis prompts."""
    
    system_message: str = Field(
        description="System message for the LLM"
    )
    user_message_template: str = Field(
        description="Template for user messages"
    )
    examples: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Examples for few-shot learning"
    )


class PromptConfig(BaseModel):
    """Configuration for prompts."""
    
    code_generation: CodeGenerationPromptConfig
    code_analysis: CodeAnalysisPromptConfig


class LLMServiceConfig(BaseModel):
    """Configuration for the LLM service."""
    
    llm: LLMConfig
    prompts: PromptConfig
    cache_enabled: bool = Field(
        default=True,
        description="Whether to enable caching of LLM responses"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Time-to-live for cached responses in seconds"
    )
