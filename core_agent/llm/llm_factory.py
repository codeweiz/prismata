"""
LLM factory.

This module provides a factory for creating LLM instances.
"""

import os
from typing import Dict, Any, Optional

try:
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
except ImportError:
    # For newer versions of LangChain
    from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain.llms.base import BaseLLM
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

from core_agent.llm.llm_config import LLMConfig, LLMType
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """Factory for creating LLM instances."""

    @staticmethod
    def create_llm(config: LLMConfig) -> BaseLLM:
        """
        Create an LLM instance based on the configuration.

        Args:
            config: The LLM configuration.

        Returns:
            An LLM instance.

        Raises:
            ValueError: If the model type is not supported.
        """
        logger.info(f"Creating LLM of type {config.model_type} with model {config.model_name}")

        # Set up caching
        set_llm_cache(InMemoryCache())

        # Create the LLM based on the type
        if config.model_type == LLMType.OPENAI:
            return LLMFactory._create_openai_llm(config)
        elif config.model_type == LLMType.ANTHROPIC:
            return LLMFactory._create_anthropic_llm(config)
        elif config.model_type == LLMType.LOCAL:
            return LLMFactory._create_local_llm(config)
        elif config.model_type == LLMType.CUSTOM:
            return LLMFactory._create_custom_llm(config)
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")

    @staticmethod
    def _create_openai_llm(config: LLMConfig) -> BaseLLM:
        """Create an OpenAI LLM instance."""
        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")

        # Create the LLM
        return ChatOpenAI(
            model_name=config.model_name,
            openai_api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            **(config.additional_params or {})
        )

    @staticmethod
    def _create_anthropic_llm(config: LLMConfig) -> BaseLLM:
        """Create an Anthropic LLM instance."""
        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")

        # Create the LLM
        return ChatAnthropic(
            model_name=config.model_name,
            anthropic_api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            **(config.additional_params or {})
        )

    @staticmethod
    def _create_local_llm(config: LLMConfig) -> BaseLLM:
        """Create a local LLM instance."""
        # This is a placeholder for local LLM integration
        # In a real implementation, this would use a library like llama-cpp-python
        raise NotImplementedError("Local LLM support is not yet implemented")

    @staticmethod
    def _create_custom_llm(config: LLMConfig) -> BaseLLM:
        """Create a custom LLM instance."""
        # This is a placeholder for custom LLM integration
        raise NotImplementedError("Custom LLM support is not yet implemented")
