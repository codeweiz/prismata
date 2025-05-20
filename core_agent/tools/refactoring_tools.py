"""
Code refactoring tools.

This module provides tools for refactoring code.
"""

import os
from typing import Dict, Any, Optional, List

from langchain.tools import BaseTool

from core_agent.llm.llm_service import LLMService
from core_agent.tools.cross_file_analysis_tool import CrossFileAnalysisTool
from shared.models.code import CodeRefactoringRequest, CodeRefactoringResult, Range
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class RefactorCodeTool(BaseTool):
    """Tool for refactoring code."""

    name = "refactor_code"
    description = """
    Refactor code based on the specified refactoring type.
    
    This tool refactors code based on the specified refactoring type, such as rename, extract method, etc.
    
    Args:
        refactoring_type: The type of refactoring to perform (e.g., "rename", "extract_method", "move_method").
        file_paths: List of file paths to refactor.
        target_symbol: The symbol to refactor (e.g., variable name, function name, class name).
        new_name: The new name for the symbol (for rename refactoring).
        selection: The code selection to refactor (for extract method, etc.).
        options: Additional options for the refactoring.
        
    Returns:
        A dictionary with the refactoring results.
    """

    def __init__(self, llm_service: LLMService):
        """Initialize the tool with an LLM service."""
        super().__init__()
        self.llm_service = llm_service
        self.cross_file_analysis_tool = CrossFileAnalysisTool(llm_service)
        logger.info("Initialized RefactorCodeTool")

    def _run(
        self,
        refactoring_type: str,
        file_paths: List[str],
        target_symbol: Optional[str] = None,
        new_name: Optional[str] = None,
        selection: Optional[Dict[str, Dict[str, int]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the tool to refactor code.

        Args:
            refactoring_type: The type of refactoring to perform.
            file_paths: List of file paths to refactor.
            target_symbol: The symbol to refactor.
            new_name: The new name for the symbol (for rename refactoring).
            selection: The code selection to refactor (for extract method, etc.).
            options: Additional options for the refactoring.

        Returns:
            A dictionary with the refactoring results.
        """
        logger.info(f"Refactoring code with type: {refactoring_type}")
        try:
            # Validate inputs
            if not file_paths:
                raise ValueError("No file paths provided for refactoring")
            
            if refactoring_type == "rename" and (not target_symbol or not new_name):
                raise ValueError("Rename refactoring requires target_symbol and new_name")
            
            if refactoring_type == "extract_method" and not selection:
                raise ValueError("Extract method refactoring requires a selection")
            
            # Read file contents
            content_map = {}
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_map[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
                    raise ValueError(f"Error reading file {file_path}: {str(e)}")
            
            # Analyze dependencies if needed
            if len(file_paths) > 1 or refactoring_type in ["rename", "move_method", "move_class"]:
                logger.info("Analyzing cross-file dependencies for refactoring")
                try:
                    dependencies_result = self.cross_file_analysis_tool._run(
                        file_paths=file_paths,
                        content_map=content_map
                    )
                    logger.debug(f"Dependency analysis result: {dependencies_result}")
                except Exception as e:
                    logger.warning(f"Error analyzing dependencies: {str(e)}")
                    dependencies_result = None
            else:
                dependencies_result = None
            
            # Create refactoring request
            request = CodeRefactoringRequest(
                refactoring_type=refactoring_type,
                file_paths=file_paths,
                target_symbol=target_symbol,
                new_name=new_name,
                selection=selection,
                options=options or {}
            )
            
            # This is a synchronous wrapper around the async method
            import asyncio
            result = asyncio.run(self.llm_service.refactor_code(
                request=request,
                content_map=content_map,
                dependencies=dependencies_result
            ))
            
            # Convert to CodeRefactoringResult
            refactoring_result = CodeRefactoringResult(
                changes=result.get("changes", {}),
                description=result.get("description", ""),
                affected_files=result.get("affected_files", []),
                preview=result.get("preview", {}),
                errors=result.get("errors", [])
            )
            
            return refactoring_result.model_dump()
        except Exception as e:
            logger.error(f"Error refactoring code: {str(e)}")
            raise

    async def _arun(
        self,
        refactoring_type: str,
        file_paths: List[str],
        target_symbol: Optional[str] = None,
        new_name: Optional[str] = None,
        selection: Optional[Dict[str, Dict[str, int]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Refactoring code with type: {refactoring_type}")
        try:
            # Validate inputs
            if not file_paths:
                raise ValueError("No file paths provided for refactoring")
            
            if refactoring_type == "rename" and (not target_symbol or not new_name):
                raise ValueError("Rename refactoring requires target_symbol and new_name")
            
            if refactoring_type == "extract_method" and not selection:
                raise ValueError("Extract method refactoring requires a selection")
            
            # Read file contents
            content_map = {}
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_map[file_path] = f.read()
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
                    raise ValueError(f"Error reading file {file_path}: {str(e)}")
            
            # Analyze dependencies if needed
            if len(file_paths) > 1 or refactoring_type in ["rename", "move_method", "move_class"]:
                logger.info("Analyzing cross-file dependencies for refactoring")
                try:
                    dependencies_result = await self.cross_file_analysis_tool._arun(
                        file_paths=file_paths,
                        content_map=content_map
                    )
                    logger.debug(f"Dependency analysis result: {dependencies_result}")
                except Exception as e:
                    logger.warning(f"Error analyzing dependencies: {str(e)}")
                    dependencies_result = None
            else:
                dependencies_result = None
            
            # Create refactoring request
            request = CodeRefactoringRequest(
                refactoring_type=refactoring_type,
                file_paths=file_paths,
                target_symbol=target_symbol,
                new_name=new_name,
                selection=selection,
                options=options or {}
            )
            
            result = await self.llm_service.refactor_code(
                request=request,
                content_map=content_map,
                dependencies=dependencies_result
            )
            
            # Convert to CodeRefactoringResult
            refactoring_result = CodeRefactoringResult(
                changes=result.get("changes", {}),
                description=result.get("description", ""),
                affected_files=result.get("affected_files", []),
                preview=result.get("preview", {}),
                errors=result.get("errors", [])
            )
            
            return refactoring_result.model_dump()
        except Exception as e:
            logger.error(f"Error refactoring code: {str(e)}")
            raise
