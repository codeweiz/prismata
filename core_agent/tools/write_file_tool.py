"""
Write file tool for the agent.

This module provides a tool for writing files that can be used by the agent.
"""

import os
from typing import Dict, Any, Optional

from langchain.tools import BaseTool

from shared.models.file import FileContent, FileMetadata, FileType, FileChange
from shared.utils.file_utils import get_file_metadata
from shared.utils.path_utils import normalize_path, is_safe_path
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class WriteFileTool(BaseTool):
    """Tool for writing file content."""

    name: str = "write_file"
    description: str = "Write content to a file"

    def _run(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        base_dir: Optional[str] = None,
        create_backup: bool = True,
        requires_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        Run the tool to write a file.

        Args:
            file_path: The path to the file to write.
            content: The content to write to the file.
            encoding: The encoding to use when writing the file.
            base_dir: Optional base directory for security checks.
            create_backup: Whether to create a backup of the file before writing.
            requires_confirmation: Whether the operation requires user confirmation.

        Returns:
            A dictionary with the result of the operation.
        """
        logger.info(f"Writing to file: {file_path}")
        try:
            # Normalize the path
            path = normalize_path(file_path)

            # Security check if base_dir is provided
            if base_dir and not is_safe_path(path, base_dir):
                raise PermissionError(f"Access to {path} is not allowed")

            # Check if the file exists
            file_exists = os.path.exists(path)
            old_content = None

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

            # If the file exists and we need to create a backup, read the old content
            if file_exists and create_backup:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        old_content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read existing file for backup: {str(e)}")

            # Create a FileChange object for preview
            file_change = FileChange(
                path=path,
                operation="update" if file_exists else "create",
                content=content,
                old_content=old_content,
                diff=self._generate_diff(old_content, content) if old_content else None
            )

            # If requires confirmation, return the preview without writing
            if requires_confirmation:
                return {
                    "preview": file_change.model_dump(),
                    "requires_confirmation": True,
                    "message": "Preview of file changes. Requires confirmation to proceed."
                }

            # Write the file
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

            # Get the file metadata
            metadata = get_file_metadata(path)

            # Create a FileContent object
            file_content = FileContent(
                path=path,
                content=content,
                metadata=metadata
            )

            return {
                "success": True,
                "file_path": path,
                "metadata": metadata.model_dump(),
                "message": f"File {'updated' if file_exists else 'created'} successfully."
            }
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {str(e)}")
            raise

    async def _arun(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        base_dir: Optional[str] = None,
        create_backup: bool = True,
        requires_confirmation: bool = True
    ) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(file_path, content, encoding, base_dir, create_backup, requires_confirmation)

    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """
        Generate a simple diff between old and new content.

        Args:
            old_content: The old content.
            new_content: The new content.

        Returns:
            A string representation of the diff.
        """
        import difflib
        diff = difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            lineterm=''
        )
        return '\n'.join(diff)


class ConfirmWriteFileTool(BaseTool):
    """Tool for confirming a file write operation."""

    name: str = "confirm_write_file"
    description: str = "Confirm a file write operation"

    def _run(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        base_dir: Optional[str] = None,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Run the tool to confirm and execute a file write operation.

        Args:
            file_path: The path to the file to write.
            content: The content to write to the file.
            encoding: The encoding to use when writing the file.
            base_dir: Optional base directory for security checks.
            create_backup: Whether to create a backup of the file before writing.

        Returns:
            A dictionary with the result of the operation.
        """
        logger.info(f"Confirming write to file: {file_path}")
        
        # Use the WriteFileTool to perform the actual write
        write_tool = WriteFileTool()
        return write_tool._run(
            file_path=file_path,
            content=content,
            encoding=encoding,
            base_dir=base_dir,
            create_backup=create_backup,
            requires_confirmation=False  # No confirmation needed as this is the confirmation step
        )

    async def _arun(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        base_dir: Optional[str] = None,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(file_path, content, encoding, base_dir, create_backup)
