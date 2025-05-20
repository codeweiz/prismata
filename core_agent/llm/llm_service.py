"""
LLM service.

This module provides a service for interacting with LLMs.
"""

import json
import os
from typing import Dict, Any, List, Optional

from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.llms.base import BaseLLM

from core_agent.llm.llm_config import LLMServiceConfig, PromptConfig
from core_agent.llm.llm_factory import LLMFactory
from shared.models.code import CodeGenerationResult, CodeAnalysisResult, Symbol, Position, Range, CodeRefactoringRequest, CodeRefactoringResult
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
        file_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code based on a prompt.

        Args:
            prompt: The prompt describing the code to generate.
            language: The programming language to use.
            context: Optional context for the code generation.
            file_path: Optional file path for additional context.
            options: Optional additional options.

        Returns:
            A dictionary with the generated code and explanation.
        """
        logger.info(f"Generating code for prompt: {prompt}")

        # Prepare the messages
        messages = self._prepare_code_generation_messages(prompt, language, context, file_path, options)

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

    async def analyze_cross_file_dependencies(
        self,
        file_paths: List[str],
        content_map: Optional[Dict[str, str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze dependencies between multiple files.

        Args:
            file_paths: List of file paths to analyze.
            content_map: Optional map of file paths to their content. If not provided, the files will be read from disk.
            options: Optional additional options.

        Returns:
            A dictionary with the analysis results.
        """
        logger.info(f"Analyzing dependencies between {len(file_paths)} files")

        # Read file contents if not provided
        if content_map is None:
            content_map = {}
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_map[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
                    content_map[file_path] = f"# Error reading file: {str(e)}"

        # Prepare the messages
        messages = self._prepare_cross_file_analysis_messages(file_paths, content_map, options)

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
                "files": file_paths,
                "dependencies": [],
                "symbols_by_file": {},
                "imports_by_file": {}
            }

        logger.debug(f"Cross-file analysis result: {result}")
        return result

    async def refactor_code(
        self,
        request: CodeRefactoringRequest,
        content_map: Dict[str, str],
        dependencies: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refactor code based on the specified refactoring type.

        Args:
            request: The refactoring request.
            content_map: Map of file paths to their content.
            dependencies: Optional dependencies information.

        Returns:
            A dictionary with the refactoring results.
        """
        logger.info(f"Refactoring code with type: {request.refactoring_type}")

        # Prepare the messages
        messages = self._prepare_code_refactoring_messages(request, content_map, dependencies)

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
                "description": response_text,
                "changes": {},
                "affected_files": [],
                "errors": ["Failed to parse response as JSON"]
            }

        logger.debug(f"Code refactoring result: {result}")
        return result

    async def complete_code(
        self,
        request: CodeCompletionRequest,
        file_content: str,
        language: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code completion suggestions.

        Args:
            request: The completion request.
            file_content: The content of the file.
            language: The programming language.
            project_context: Optional project context information.

        Returns:
            A dictionary with completion suggestions.
        """
        logger.info(f"Generating code completion for file: {request.file_path}")

        # Prepare the messages
        messages = self._prepare_code_completion_messages(request, file_content, language, project_context)

        # Generate the response
        response = await self.llm.agenerate([messages])
        response_text = response.generations[0][0].text

        # Parse the response
        try:
            # Try to parse as JSON
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If not JSON, create a simple result with the raw text as a single completion item
            result = {
                "items": [
                    {
                        "label": response_text,
                        "insert_text": response_text,
                        "detail": "Generated completion"
                    }
                ],
                "is_incomplete": False
            }

        logger.debug(f"Code completion result: {result}")
        return result

    def _prepare_code_generation_messages(
        self,
        prompt: str,
        language: str,
        context: Optional[str] = None,
        file_path: Optional[str] = None,
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
            file_path=file_path or "No file path provided",
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

    def _prepare_cross_file_analysis_messages(
        self,
        file_paths: List[str],
        content_map: Dict[str, str],
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages for cross-file analysis."""
        # Get the prompt config
        prompt_config = self.prompts.cross_file_analysis

        # Create the system message
        system_message = SystemMessage(content=prompt_config.system_message)

        # Prepare file information
        file_info = []
        for file_path in file_paths:
            # Determine language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)

            # Add file info
            file_info.append({
                "path": file_path,
                "language": language,
                "content": content_map.get(file_path, "# File content not available")
            })

        # Format the user message
        user_message_content = prompt_config.user_message_template.format(
            files=json.dumps(file_info, indent=2),
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

    def _prepare_code_completion_messages(
        self,
        request: CodeCompletionRequest,
        file_content: str,
        language: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages for code completion."""
        # Get the prompt config
        prompt_config = self.prompts.code_completion

        # Create the system message
        system_message = SystemMessage(content=prompt_config.system_message)

        # Extract the relevant context around the cursor position
        position = request.position
        lines = file_content.split('\n')

        # Determine the range of lines to include as context
        context_lines = 10  # Number of lines before and after the cursor
        start_line = max(0, position.line - context_lines)
        end_line = min(len(lines), position.line + context_lines + 1)

        # Extract the context
        context_content = '\n'.join(lines[start_line:end_line])

        # Mark the cursor position
        if 0 <= position.line < len(lines):
            cursor_line = lines[position.line]
            if position.character <= len(cursor_line):
                cursor_line_with_marker = cursor_line[:position.character] + "█" + cursor_line[position.character:]
                context_content = context_content.replace(lines[position.line], cursor_line_with_marker)

        # Prepare project context information if available
        project_context_info = ""
        if project_context:
            # Extract imports and important symbols from related files
            imports = project_context.get("imports", [])
            if imports:
                project_context_info += "\nImports:\n" + "\n".join(imports)

            related_files = project_context.get("related_files", [])
            if related_files:
                project_context_info += "\nRelated Files:\n"
                for related_file in related_files:
                    path = related_file.get("path", "")
                    project_context_info += f"\n{path}:\n"

                    # Extract important parts (imports, class/function definitions)
                    content = related_file.get("content", "")
                    if content:
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
                            project_context_info += "\n".join(important_lines) + "\n"

        # Format the user message
        user_message_content = prompt_config.user_message_template.format(
            file_path=request.file_path,
            position=f"line {position.line}, character {position.character}",
            prefix=request.prefix or "",
            context=context_content,
            language=language,
            project_context=project_context_info,
            options=json.dumps(request.options.model_dump() if request.options else {})
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

    def _prepare_code_refactoring_messages(
        self,
        request: CodeRefactoringRequest,
        content_map: Dict[str, str],
        dependencies: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages for code refactoring."""
        # Get the prompt config
        prompt_config = self.prompts.code_refactoring

        # Create the system message
        system_message = SystemMessage(content=prompt_config.system_message)

        # Prepare file information
        file_info = []
        for file_path in request.file_paths:
            # Determine language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)

            # Add file info
            file_info.append({
                "path": file_path,
                "language": language,
                "content": content_map.get(file_path, "# File content not available")
            })

        # Format the user message
        user_message_content = prompt_config.user_message_template.format(
            refactoring_type=request.refactoring_type,
            files=json.dumps(file_info, indent=2),
            target_symbol=json.dumps(request.target_symbol) if request.target_symbol else "null",
            new_name=json.dumps(request.new_name) if request.new_name else "null",
            selection=json.dumps(request.selection) if request.selection else "null",
            options=json.dumps(request.options) if request.options else "{}",
            dependencies=json.dumps(dependencies) if dependencies else "null"
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

    def _get_language_from_extension(self, ext: str) -> str:
        """Get language name from file extension."""
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
