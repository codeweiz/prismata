"""
Code completion tool.

This module provides a tool for generating code completion suggestions.
"""

import os
from typing import Dict, Any, Optional

from langchain.tools import BaseTool

from core_agent.llm.llm_service import LLMService
from core_agent.tools.context_collection_tool import ContextCollectionTool
from shared.models.code import CodeCompletionRequest, CodeCompletionResult, CompletionItem, Position
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CodeCompletionTool(BaseTool):
    """Tool for generating code completion suggestions."""

    name = "code_completion"
    description = """
    Generate code completion suggestions.
    
    This tool generates code completion suggestions based on the current context.
    
    Args:
        file_path: The path to the file being edited.
        position: The position in the file where completion is requested.
        prefix: Optional prefix text before the cursor.
        context: Optional additional context.
        options: Optional additional options.
        
    Returns:
        A dictionary with completion suggestions.
    """

    def __init__(self, llm_service: LLMService):
        """Initialize the tool with an LLM service."""
        super().__init__()
        self.llm_service = llm_service
        self.context_tool = ContextCollectionTool()
        logger.info("Initialized CodeCompletionTool")

    def _run(
            self,
            file_path: str,
            position: Dict[str, int],
            prefix: Optional[str] = None,
            context: Optional[str] = None,
            options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the tool to generate code completion suggestions.

        Args:
            file_path: The path to the file being edited.
            position: The position in the file where completion is requested.
            prefix: Optional prefix text before the cursor.
            context: Optional additional context.
            options: Optional additional options.

        Returns:
            A dictionary with completion suggestions.
        """
        logger.info(f"Generating code completion for file: {file_path}")
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Extract language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)

            # If no context is provided, extract it from the file
            if not context:
                context = self._extract_context(file_content, position)

            # If no prefix is provided, extract it from the context
            if not prefix:
                prefix = self._extract_prefix(context)

            # Collect project context if requested
            project_context = None
            if options and options.get("use_project_context", False):
                logger.info(f"Collecting project context for file: {file_path}")
                try:
                    project_context = self.context_tool._run(
                        file_path=file_path,
                        max_files=options.get("max_context_files", 3),
                        include_imports=True,
                        include_siblings=True
                    )
                    logger.debug(
                        f"Collected context with {len(project_context.get('related_files', []))} related files")
                except Exception as e:
                    logger.warning(f"Error collecting project context: {str(e)}")

            # Create completion request
            request = CodeCompletionRequest(
                file_path=file_path,
                position=Position(line=position.get("line", 0), character=position.get("character", 0)),
                prefix=prefix,
                context=context,
                options=options or {}
            )

            # This is a synchronous wrapper around the async method
            import asyncio
            result = asyncio.run(self.llm_service.complete_code(
                request=request,
                file_content=file_content,
                language=language,
                project_context=project_context
            ))

            # Convert to CodeCompletionResult
            completion_result = CodeCompletionResult(
                items=[
                    CompletionItem(
                        label=item.get("label", ""),
                        insert_text=item.get("insert_text", ""),
                        kind=item.get("kind"),
                        detail=item.get("detail"),
                        documentation=item.get("documentation"),
                        sort_text=item.get("sort_text")
                    )
                    for item in result.get("items", [])
                ],
                is_incomplete=result.get("is_incomplete", False)
            )

            return completion_result.model_dump()
        except Exception as e:
            logger.error(f"Error generating code completion: {str(e)}")
            raise

    async def _arun(
            self,
            file_path: str,
            position: Dict[str, int],
            prefix: Optional[str] = None,
            context: Optional[str] = None,
            options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Generating code completion for file: {file_path}")
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Extract language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)

            # If no context is provided, extract it from the file
            if not context:
                context = self._extract_context(file_content, position)

            # If no prefix is provided, extract it from the context
            if not prefix:
                prefix = self._extract_prefix(context)

            # Collect project context if requested
            project_context = None
            if options and options.get("use_project_context", False):
                logger.info(f"Collecting project context for file: {file_path}")
                try:
                    project_context = await self.context_tool._arun(
                        file_path=file_path,
                        max_files=options.get("max_context_files", 3),
                        include_imports=True,
                        include_siblings=True
                    )
                    logger.debug(
                        f"Collected context with {len(project_context.get('related_files', []))} related files")
                except Exception as e:
                    logger.warning(f"Error collecting project context: {str(e)}")

            # Create completion request
            request = CodeCompletionRequest(
                file_path=file_path,
                position=Position(line=position.get("line", 0), character=position.get("character", 0)),
                prefix=prefix,
                context=context,
                options=options or {}
            )

            result = await self.llm_service.complete_code(
                request=request,
                file_content=file_content,
                language=language,
                project_context=project_context
            )

            # Convert to CodeCompletionResult
            completion_result = CodeCompletionResult(
                items=[
                    CompletionItem(
                        label=item.get("label", ""),
                        insert_text=item.get("insert_text", ""),
                        kind=item.get("kind"),
                        detail=item.get("detail"),
                        documentation=item.get("documentation"),
                        sort_text=item.get("sort_text")
                    )
                    for item in result.get("items", [])
                ],
                is_incomplete=result.get("is_incomplete", False)
            )

            return completion_result.model_dump()
        except Exception as e:
            logger.error(f"Error generating code completion: {str(e)}")
            raise

    def _extract_context(self, file_content: str, position: Dict[str, int], context_lines: int = 10) -> str:
        """
        Extract context around the cursor position.
        
        Args:
            file_content: The content of the file.
            position: The cursor position.
            context_lines: Number of lines to include before and after the cursor.
            
        Returns:
            The extracted context.
        """
        lines = file_content.split('\n')
        line_num = position.get("line", 0)

        # Determine the range of lines to include
        start_line = max(0, line_num - context_lines)
        end_line = min(len(lines), line_num + context_lines + 1)

        # Extract the context
        context_lines = lines[start_line:end_line]

        # Mark the cursor position
        if 0 <= line_num < len(lines):
            char_pos = position.get("character", 0)
            cursor_line = lines[line_num]
            if char_pos <= len(cursor_line):
                # Insert a cursor marker
                context_lines[line_num - start_line] = cursor_line[:char_pos] + "█" + cursor_line[char_pos:]

        return '\n'.join(context_lines)

    def _extract_prefix(self, context: str) -> str:
        """
        Extract the prefix before the cursor.
        
        Args:
            context: The context string with a cursor marker.
            
        Returns:
            The extracted prefix.
        """
        # Find the cursor marker
        cursor_pos = context.find('█')
        if cursor_pos == -1:
            return ""

        # Extract the text before the cursor on the same line
        line_start = context.rfind('\n', 0, cursor_pos)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1  # Skip the newline character

        return context[line_start:cursor_pos]

    def _get_language_from_extension(self, ext: str) -> str:
        """
        Get language name from file extension.
        
        Args:
            ext: The file extension.
            
        Returns:
            The language name.
        """
        ext = ext.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".rs": "rust",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sh": "shell",
            ".bat": "batch",
            ".ps1": "powershell",
            ".sql": "sql",
            ".r": "r",
            ".m": "matlab",
            ".scala": "scala",
            ".pl": "perl",
            ".lua": "lua",
            ".dart": "dart",
            ".ex": "elixir",
            ".exs": "elixir",
            ".hs": "haskell",
            ".fs": "fsharp",
            ".clj": "clojure",
            ".groovy": "groovy",
            ".jl": "julia",
        }
        return language_map.get(ext, "plaintext")
