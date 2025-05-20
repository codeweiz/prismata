"""
LLM service.

This module provides a service for interacting with LLMs.
"""

import json
from typing import Dict, Any, List, Optional

from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.llms.base import BaseLLM

from core_agent.llm.llm_config import LLMServiceConfig, PromptConfig
from core_agent.llm.llm_factory import LLMFactory
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with LLMs."""
    
    def __init__(self, config: LLMServiceConfig):
        """
        Initialize the LLM service.
        
        Args:
            config: The LLM service configuration.
        """
        self.config = config
        self.llm = LLMFactory.create_llm(config.llm)
        self.prompts = config.prompts
        logger.info(f"Initialized LLM service with model {config.llm.model_name}")
    
    async def generate_code(
        self,
        prompt: str,
        language: str,
        context: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code based on a prompt.
        
        Args:
            prompt: The prompt describing the code to generate.
            language: The programming language to use.
            context: Optional context for the code generation.
            options: Optional additional options.
            
        Returns:
            A dictionary with the generated code and explanation.
        """
        logger.info(f"Generating code for prompt: {prompt}")
        
        # Prepare the messages
        messages = self._prepare_code_generation_messages(prompt, language, context, options)
        
        # Generate the response
        response = await self.llm.agenerate([messages])
        response_text = response.generations[0][0].text
        
        # Parse the response
        try:
            # Try to parse as JSON first
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If not JSON, use the raw text as code
            result = {
                "code": response_text,
                "explanation": "Generated code based on the prompt."
            }
        
        logger.debug(f"Generated code result: {result}")
        return result
    
    async def analyze_code(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code.
        
        Args:
            code: The code to analyze.
            language: The programming language of the code.
            file_path: Optional file path for context.
            options: Optional additional options.
            
        Returns:
            A dictionary with the analysis results.
        """
        logger.info(f"Analyzing code for file: {file_path or 'unknown'}")
        
        # Prepare the messages
        messages = self._prepare_code_analysis_messages(code, language, file_path, options)
        
        # Generate the response
        response = await self.llm.agenerate([messages])
        response_text = response.generations[0][0].text
        
        # Parse the response
        try:
            # Try to parse as JSON
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If not JSON, create a simple result
            result = {
                "summary": response_text,
                "language": language,
                "file_path": file_path,
                "symbols": []
            }
        
        logger.debug(f"Code analysis result: {result}")
        return result
    
    def _prepare_code_generation_messages(
        self,
        prompt: str,
        language: str,
        context: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages for code generation."""
        # Get the prompt config
        prompt_config = self.prompts.code_generation
        
        # Create the system message
        system_message = SystemMessage(content=prompt_config.system_message)
        
        # Format the user message
        user_message_content = prompt_config.user_message_template.format(
            prompt=prompt,
            language=language,
            context=context or "No context provided",
            options=json.dumps(options or {})
        )
        user_message = HumanMessage(content=user_message_content)
        
        # Add examples if available
        messages = [system_message]
        if prompt_config.examples:
            for example in prompt_config.examples:
                messages.append(HumanMessage(content=example["user"]))
                messages.append(AIMessage(content=example["assistant"]))
        
        messages.append(user_message)
        return messages
    
    def _prepare_code_analysis_messages(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages for code analysis."""
        # Get the prompt config
        prompt_config = self.prompts.code_analysis
        
        # Create the system message
        system_message = SystemMessage(content=prompt_config.system_message)
        
        # Format the user message
        user_message_content = prompt_config.user_message_template.format(
            code=code,
            language=language,
            file_path=file_path or "unknown",
            options=json.dumps(options or {})
        )
        user_message = HumanMessage(content=user_message_content)
        
        # Add examples if available
        messages = [system_message]
        if prompt_config.examples:
            for example in prompt_config.examples:
                messages.append(HumanMessage(content=example["user"]))
                messages.append(AIMessage(content=example["assistant"]))
        
        messages.append(user_message)
        return messages
