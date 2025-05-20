"""
Cross-file analysis tool.

This module provides a tool for analyzing dependencies between multiple files.
"""

from typing import Dict, Any, Optional, List

from langchain.tools import BaseTool

from core_agent.llm.llm_service import LLMService
from shared.models.code import CrossFileAnalysisResult, Dependency, DependencyType, Symbol, Position, Range
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CrossFileAnalysisTool(BaseTool):
    """Tool for analyzing dependencies between multiple files."""

    name = "cross_file_analysis"
    description = """
    Analyze dependencies between multiple files.
    
    This tool analyzes the dependencies between multiple files in a codebase.
    It identifies imports, inheritance relationships, function calls, and other dependencies.
    
    Args:
        file_paths: List of file paths to analyze.
        content_map: Optional map of file paths to their content. If not provided, the files will be read from disk.
        options: Optional additional options.
        
    Returns:
        A dictionary with the analysis results.
    """

    def __init__(self, llm_service: LLMService):
        """Initialize the tool with an LLM service."""
        super().__init__()
        self.llm_service = llm_service

    def _run(
        self,
        file_paths: List[str],
        content_map: Optional[Dict[str, str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the tool to analyze dependencies between files.

        Args:
            file_paths: List of file paths to analyze.
            content_map: Optional map of file paths to their content. If not provided, the files will be read from disk.
            options: Optional additional options.

        Returns:
            A dictionary with the analysis results.
        """
        logger.info(f"Analyzing dependencies between {len(file_paths)} files")
        try:
            # This is a synchronous wrapper around the async method
            import asyncio
            result = asyncio.run(self.llm_service.analyze_cross_file_dependencies(
                file_paths=file_paths,
                content_map=content_map,
                options=options
            ))

            # Convert to CrossFileAnalysisResult
            analysis_result = CrossFileAnalysisResult(
                files=file_paths,
                dependencies=self._parse_dependencies(result.get("dependencies", [])),
                symbols_by_file=result.get("symbols_by_file", {}),
                imports_by_file=result.get("imports_by_file", {}),
                errors=result.get("errors", [])
            )

            return analysis_result.model_dump()
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {str(e)}")
            raise

    async def _arun(
        self,
        file_paths: List[str],
        content_map: Optional[Dict[str, str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of _run."""
        logger.info(f"Analyzing dependencies between {len(file_paths)} files")
        try:
            result = await self.llm_service.analyze_cross_file_dependencies(
                file_paths=file_paths,
                content_map=content_map,
                options=options
            )

            # Convert to CrossFileAnalysisResult
            analysis_result = CrossFileAnalysisResult(
                files=file_paths,
                dependencies=self._parse_dependencies(result.get("dependencies", [])),
                symbols_by_file=result.get("symbols_by_file", {}),
                imports_by_file=result.get("imports_by_file", {}),
                errors=result.get("errors", [])
            )

            return analysis_result.model_dump()
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {str(e)}")
            raise

    def _parse_dependencies(self, dependencies_data: List[Dict[str, Any]]) -> List[Dependency]:
        """Parse dependencies data into Dependency objects."""
        dependencies = []
        for dep_data in dependencies_data:
            try:
                # Convert dependency type string to enum
                dep_type_str = dep_data.get("dependency_type", "reference").lower()
                if dep_type_str == "import":
                    dep_type = DependencyType.IMPORT
                elif dep_type_str == "inheritance":
                    dep_type = DependencyType.INHERITANCE
                elif dep_type_str == "usage":
                    dep_type = DependencyType.USAGE
                elif dep_type_str == "implementation":
                    dep_type = DependencyType.IMPLEMENTATION
                else:
                    dep_type = DependencyType.REFERENCE

                # Create dependency object
                dependency = Dependency(
                    source_file=dep_data["source_file"],
                    target_file=dep_data["target_file"],
                    source_symbol=dep_data.get("source_symbol"),
                    target_symbol=dep_data.get("target_symbol"),
                    dependency_type=dep_type,
                    description=dep_data.get("description")
                )
                dependencies.append(dependency)
            except KeyError as e:
                logger.warning(f"Missing required field in dependency data: {e}")
                continue
        return dependencies
