"""
File operation tools for the agent.

This module provides tools for file operations that can be used by the agent.
"""

from typing import Dict, Any, Optional

from langchain.tools import BaseTool

from shared.utils.file_utils import read_file, get_file_metadata
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ReadFileTool(BaseTool):
    """Tool for reading file content."""

    name: str = "read_file"
    description: str = "Read the content of a file"

    def _run(self, file_path: str, encoding: str = "utf-8", base_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the tool to read a file.

        Args:
            file_path: The path to the file to read.
            encoding: The encoding to use when reading the file.
            base_dir: Optional base directory for security checks.

        Returns:
            A dictionary with the file content and metadata.
        """
        logger.info(f"Reading file: {file_path}")
        try:
            file_content = read_file(file_path, encoding, base_dir)
            return {
                "content": file_content.content,
                "metadata": file_content.metadata.model_dump()
            }
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    async def _arun(self, file_path: str, encoding: str = "utf-8", base_dir: Optional[str] = None) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(file_path, encoding, base_dir)


class GetFileMetadataTool(BaseTool):
    """Tool for getting file metadata."""

    name: str = "get_file_metadata"
    description: str = "Get metadata for a file"

    def _run(self, file_path: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the tool to get file metadata.

        Args:
            file_path: The path to the file.
            base_dir: Optional base directory for security checks.

        Returns:
            A dictionary with the file metadata.
        """
        logger.info(f"Getting metadata for file: {file_path}")
        try:
            metadata = get_file_metadata(file_path, base_dir)
            return metadata.model_dump()
        except Exception as e:
            logger.error(f"Error getting metadata for file {file_path}: {str(e)}")
            raise

    async def _arun(self, file_path: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(file_path, base_dir)
