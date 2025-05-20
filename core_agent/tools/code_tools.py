"""
Code tools for the agent.

This module provides tools for code generation and analysis.
"""

import os
from typing import Dict, Any, Optional

from langchain.tools import BaseTool

from core_agent.llm.llm_service import LLMService
from core_agent.tools.context_collection_tool import ContextCollectionTool
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
        self.context_tool = ContextCollectionTool()
        logger.info("Initialized GenerateCodeTool")

    def _run(
            self,
            prompt: str,
            language: str = "python",
            context: Optional[str] = None,
            file_path: Optional[str] = None,
            position: Optional[Dict[str, int]] = None,
            options: Optional[Dict[str, Any]] = None,
            use_project_context: bool = True,
            max_context_files: int = 3
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
            use_project_context: Whether to use project context for code generation.
            max_context_files: Maximum number of context files to include.

        Returns:
            A dictionary with the generated code and explanation.
        """
        logger.info(f"Generating code for prompt: {prompt}")
        try:
            # Collect project context if requested and file_path is provided
            project_context = None
            if use_project_context and file_path and os.path.exists(file_path):
                logger.info(f"Collecting project context for file: {file_path}")
                try:
                    project_context = self.context_tool._run(
                        file_path=file_path,
                        max_files=max_context_files,
                        include_imports=True,
                        include_siblings=True
                    )
                    logger.debug(
                        f"Collected context with {len(project_context.get('related_files', []))} related files")
                except Exception as e:
                    logger.warning(f"Error collecting project context: {str(e)}")

            # Prepare enhanced context
            enhanced_context = self._prepare_enhanced_context(context, project_context)

            # This is a synchronous wrapper around the async method
            # In a real implementation, you would use asyncio.run() or similar
            import asyncio
            result = asyncio.run(self.llm_service.generate_code(
                prompt=prompt,
                language=language,
                context=enhanced_context,
                file_path=file_path,
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

    def _prepare_enhanced_context(self, user_context: Optional[str], project_context: Optional[Dict[str, Any]]) -> str:
        """
        Prepare enhanced context by combining user-provided context and project context.

        Args:
            user_context: Context provided by the user.
            project_context: Context collected from the project.

        Returns:
            Enhanced context string.
        """
        context_parts = []

        # Add user context if provided
        if user_context:
            context_parts.append("USER PROVIDED CONTEXT:")
            context_parts.append(user_context)

        # Add project context if available
        if project_context:
            # Add target file information
            target_file = project_context.get("target_file", {})
            if target_file:
                context_parts.append("\nTARGET FILE:")
                context_parts.append(f"Path: {target_file.get('path', '')}")
                # We don't include the full content as it might be too large
                # Instead, we'll extract important parts like imports and class/function definitions
                content = target_file.get('content', '')
                if content:
                    imports = project_context.get("imports", [])
                    if imports:
                        context_parts.append("\nIMPORTS:")
                        context_parts.append("\n".join(imports))

            # Add related files information (just the important parts)
            related_files = project_context.get("related_files", [])
            if related_files:
                context_parts.append("\nRELATED FILES:")
                for related_file in related_files:
                    path = related_file.get("path", "")
                    relationship = related_file.get("relationship", "")
                    context_parts.append(f"\n{path} ({relationship}):")

                    # Extract important parts from the content
                    content = related_file.get("content", "")
                    if content:
                        # Extract imports and class/function definitions (simplified)
                        important_lines = []
                        for line in content.split("\n"):
                            line = line.strip()
                            if line.startswith("import ") or line.startswith("from ") or \
                                    line.startswith("class ") or line.startswith("def ") or \
                                    line.startswith("function ") or line.startswith("interface ") or \
                                    line.startswith("type ") or line.startswith("const ") or \
                                    line.startswith("let ") or line.startswith("var "):
                                important_lines.append(line)

                        if important_lines:
                            context_parts.append("\n".join(important_lines))

        return "\n\n".join(context_parts)

    async def _arun(
            self,
            prompt: str,
            language: str = "python",
            context: Optional[str] = None,
            file_path: Optional[str] = None,
            position: Optional[Dict[str, int]] = None,
            options: Optional[Dict[str, Any]] = None,
            use_project_context: bool = True,
            max_context_files: int = 3
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Generating code for prompt: {prompt}")
        try:
            # Collect project context if requested and file_path is provided
            project_context = None
            if use_project_context and file_path and os.path.exists(file_path):
                logger.info(f"Collecting project context for file: {file_path}")
                try:
                    project_context = await self.context_tool._arun(
                        file_path=file_path,
                        max_files=max_context_files,
                        include_imports=True,
                        include_siblings=True
                    )
                    logger.debug(
                        f"Collected context with {len(project_context.get('related_files', []))} related files")
                except Exception as e:
                    logger.warning(f"Error collecting project context: {str(e)}")

            # Prepare enhanced context
            enhanced_context = self._prepare_enhanced_context(context, project_context)

            result = await self.llm_service.generate_code(
                prompt=prompt,
                language=language,
                context=enhanced_context,
                file_path=file_path,
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
