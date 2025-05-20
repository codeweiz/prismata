"""
Code tools for the agent.

This module provides tools for code generation and analysis.
"""

from typing import Dict, Any, Optional, List

from langchain.tools import BaseTool

from core_agent.llm.llm_service import LLMService
from shared.models.code import CodeGenerationResult, CodeAnalysisResult, Symbol, Position, Range
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class GenerateCodeTool(BaseTool):
    """Tool for generating code."""

    name: str = "generate_code"
    description: str = "Generate code based on a prompt"
    llm_service: LLMService = None

    def __init__(self, llm_service: LLMService):
        """
        Initialize the tool.

        Args:
            llm_service: The LLM service to use for code generation.
        """
        super().__init__()
        self.llm_service = llm_service
        logger.info("Initialized GenerateCodeTool")

    def _run(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        file_path: Optional[str] = None,
        position: Optional[Dict[str, int]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the tool to generate code.

        Args:
            prompt: The prompt describing the code to generate.
            language: The programming language to use.
            context: Optional context for the code generation.
            file_path: Optional file path where the code will be used.
            position: Optional position in the file where the code will be inserted.
            options: Optional additional options.

        Returns:
            A dictionary with the generated code and explanation.
        """
        logger.info(f"Generating code for prompt: {prompt}")
        try:
            # This is a synchronous wrapper around the async method
            # In a real implementation, you would use asyncio.run() or similar
            import asyncio
            result = asyncio.run(self.llm_service.generate_code(
                prompt=prompt,
                language=language,
                context=context,
                options=options
            ))

            # Convert to CodeGenerationResult
            code_result = CodeGenerationResult(
                code=result.get("code", ""),
                explanation=result.get("explanation"),
                alternatives=result.get("alternatives"),
                file_path=file_path,
                position=Position(**position) if position else None
            )

            return code_result.model_dump()
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    async def _arun(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        file_path: Optional[str] = None,
        position: Optional[Dict[str, int]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Generating code for prompt: {prompt}")
        try:
            result = await self.llm_service.generate_code(
                prompt=prompt,
                language=language,
                context=context,
                options=options
            )

            # Convert to CodeGenerationResult
            code_result = CodeGenerationResult(
                code=result.get("code", ""),
                explanation=result.get("explanation"),
                alternatives=result.get("alternatives"),
                file_path=file_path,
                position=Position(**position) if position else None
            )

            return code_result.model_dump()
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise


class AnalyzeCodeTool(BaseTool):
    """Tool for analyzing code."""

    name: str = "analyze_code"
    description: str = "Analyze code structure and functionality"
    llm_service: LLMService = None

    def __init__(self, llm_service: LLMService):
        """
        Initialize the tool.

        Args:
            llm_service: The LLM service to use for code analysis.
        """
        super().__init__()
        self.llm_service = llm_service
        logger.info("Initialized AnalyzeCodeTool")

    def _run(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the tool to analyze code.

        Args:
            code: The code to analyze.
            language: The programming language of the code.
            file_path: Optional file path for context.
            options: Optional additional options.

        Returns:
            A dictionary with the analysis results.
        """
        logger.info(f"Analyzing code for file: {file_path or 'unknown'}")
        try:
            # This is a synchronous wrapper around the async method
            import asyncio
            result = asyncio.run(self.llm_service.analyze_code(
                code=code,
                language=language,
                file_path=file_path,
                options=options
            ))

            # Convert the result to a CodeAnalysisResult
            symbols = []
            for symbol_data in result.get("symbols", []):
                # Create Range objects for the symbol
                range_data = symbol_data.get("range", {})
                start_data = range_data.get("start", {"line": 0, "character": 0})
                end_data = range_data.get("end", {"line": 0, "character": 0})

                symbol_range = Range(
                    start=Position(line=start_data["line"], character=start_data["character"]),
                    end=Position(line=end_data["line"], character=end_data["character"])
                )

                # Create the Symbol
                symbol = Symbol(
                    name=symbol_data.get("name", ""),
                    kind=symbol_data.get("kind", 0),
                    range=symbol_range,
                    selection_range=symbol_range,  # Use the same range for selection_range
                    detail=symbol_data.get("detail", "")
                )
                symbols.append(symbol)

            # Create the CodeAnalysisResult
            analysis_result = CodeAnalysisResult(
                file_path=file_path or "unknown",
                symbols=symbols,
                imports=result.get("imports", []),
                dependencies=result.get("dependencies", []),
                language=language,
                errors=result.get("issues", [])
            )

            return analysis_result.model_dump()
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            raise

    async def _arun(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Analyzing code for file: {file_path or 'unknown'}")
        try:
            result = await self.llm_service.analyze_code(
                code=code,
                language=language,
                file_path=file_path,
                options=options
            )

            # Convert the result to a CodeAnalysisResult
            symbols = []
            for symbol_data in result.get("symbols", []):
                # Create Range objects for the symbol
                range_data = symbol_data.get("range", {})
                start_data = range_data.get("start", {"line": 0, "character": 0})
                end_data = range_data.get("end", {"line": 0, "character": 0})

                symbol_range = Range(
                    start=Position(line=start_data["line"], character=start_data["character"]),
                    end=Position(line=end_data["line"], character=end_data["character"])
                )

                # Create the Symbol
                symbol = Symbol(
                    name=symbol_data.get("name", ""),
                    kind=symbol_data.get("kind", 0),
                    range=symbol_range,
                    detail=symbol_data.get("detail", "")
                )
                symbols.append(symbol)

            # Create the CodeAnalysisResult
            analysis_result = CodeAnalysisResult(
                file_path=file_path or "unknown",
                symbols=symbols,
                imports=result.get("imports", []),
                dependencies=result.get("dependencies", []),
                language=language,
                errors=result.get("issues", [])
            )

            return analysis_result.model_dump()
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            raise
