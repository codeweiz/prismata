"""
Context collection tool.

This module provides a tool for collecting context information from the project.
"""

import os
import glob
from typing import Dict, Any, Optional, List, Set

from langchain.tools import BaseTool

from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ContextCollectionTool(BaseTool):
    """Tool for collecting context information from the project."""

    name = "collect_context"
    description = """
    Collect context information from the project.
    
    This tool collects relevant context information from the project, such as related files,
    imports, class and function definitions, etc.
    
    Args:
        file_path: The path to the file for which to collect context.
        max_files: Maximum number of related files to include in the context.
        include_imports: Whether to include imported files in the context.
        include_siblings: Whether to include sibling files in the context.
        
    Returns:
        A dictionary with the collected context information.
    """

    def _run(
        self,
        file_path: str,
        max_files: int = 5,
        include_imports: bool = True,
        include_siblings: bool = True,
        project_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the tool to collect context information.

        Args:
            file_path: The path to the file for which to collect context.
            max_files: Maximum number of related files to include in the context.
            include_imports: Whether to include imported files in the context.
            include_siblings: Whether to include sibling files in the context.
            project_root: The root directory of the project. If not provided, it will be inferred.

        Returns:
            A dictionary with the collected context information.
        """
        logger.info(f"Collecting context for file: {file_path}")
        
        try:
            # Determine project root if not provided
            if not project_root:
                project_root = self._infer_project_root(file_path)
                logger.debug(f"Inferred project root: {project_root}")
            
            # Read the target file
            with open(file_path, 'r', encoding='utf-8') as f:
                target_file_content = f.read()
            
            # Collect related files
            related_files = self._collect_related_files(
                file_path=file_path,
                project_root=project_root,
                max_files=max_files,
                include_imports=include_imports,
                include_siblings=include_siblings
            )
            
            # Read related file contents
            related_file_contents = {}
            for related_file in related_files:
                try:
                    with open(related_file, 'r', encoding='utf-8') as f:
                        related_file_contents[related_file] = f.read()
                except Exception as e:
                    logger.warning(f"Error reading related file {related_file}: {str(e)}")
            
            # Extract imports from the target file
            imports = self._extract_imports(target_file_content, os.path.splitext(file_path)[1])
            
            # Prepare the result
            result = {
                "target_file": {
                    "path": file_path,
                    "content": target_file_content
                },
                "related_files": [
                    {
                        "path": path,
                        "content": content,
                        "relationship": self._determine_relationship(file_path, path)
                    }
                    for path, content in related_file_contents.items()
                ],
                "imports": imports,
                "project_root": project_root
            }
            
            return result
        except Exception as e:
            logger.error(f"Error collecting context: {str(e)}")
            raise
    
    async def _arun(
        self,
        file_path: str,
        max_files: int = 5,
        include_imports: bool = True,
        include_siblings: bool = True,
        project_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async version of _run."""
        # For simplicity, we'll just call the synchronous version
        # In a real implementation, this would be properly async
        return self._run(
            file_path=file_path,
            max_files=max_files,
            include_imports=include_imports,
            include_siblings=include_siblings,
            project_root=project_root
        )
    
    def _infer_project_root(self, file_path: str) -> str:
        """
        Infer the project root directory from the file path.
        
        This method looks for common project indicators like .git, pyproject.toml, etc.
        
        Args:
            file_path: The path to the file.
            
        Returns:
            The inferred project root directory.
        """
        directory = os.path.dirname(os.path.abspath(file_path))
        
        # Look for common project indicators
        indicators = ['.git', 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle']
        
        while directory != os.path.dirname(directory):  # Stop at filesystem root
            for indicator in indicators:
                if os.path.exists(os.path.join(directory, indicator)):
                    return directory
            directory = os.path.dirname(directory)
        
        # If no indicator is found, return the directory of the file
        return os.path.dirname(os.path.abspath(file_path))
    
    def _collect_related_files(
        self,
        file_path: str,
        project_root: str,
        max_files: int = 5,
        include_imports: bool = True,
        include_siblings: bool = True
    ) -> List[str]:
        """
        Collect related files for the given file.
        
        Args:
            file_path: The path to the file.
            project_root: The root directory of the project.
            max_files: Maximum number of related files to include.
            include_imports: Whether to include imported files.
            include_siblings: Whether to include sibling files.
            
        Returns:
            A list of paths to related files.
        """
        related_files = set()
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        
        # Include sibling files (files in the same directory)
        if include_siblings:
            directory = os.path.dirname(file_path)
            for sibling in glob.glob(os.path.join(directory, f'*{ext}')):
                if os.path.abspath(sibling) != os.path.abspath(file_path):
                    related_files.add(os.path.abspath(sibling))
        
        # Include imported files (based on simple import statement analysis)
        if include_imports:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = self._extract_imports(content, ext)
            for imp in imports:
                # Try to resolve the import to a file path
                import_path = self._resolve_import_to_file_path(imp, file_path, project_root, ext)
                if import_path and os.path.exists(import_path):
                    related_files.add(import_path)
        
        # Limit the number of related files
        return list(related_files)[:max_files]
    
    def _extract_imports(self, content: str, file_ext: str) -> List[str]:
        """
        Extract import statements from the file content.
        
        Args:
            content: The content of the file.
            file_ext: The file extension.
            
        Returns:
            A list of import statements.
        """
        imports = []
        
        # Handle different file types
        if file_ext.lower() in ['.py', '.pyi']:
            # Python imports
            import_lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(line)
            imports = import_lines
        elif file_ext.lower() in ['.js', '.jsx', '.ts', '.tsx']:
            # JavaScript/TypeScript imports
            import_lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') or line.startswith('require('):
                    import_lines.append(line)
            imports = import_lines
        elif file_ext.lower() in ['.java', '.kt']:
            # Java/Kotlin imports
            import_lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import '):
                    import_lines.append(line)
            imports = import_lines
        
        return imports
    
    def _resolve_import_to_file_path(
        self,
        import_stmt: str,
        file_path: str,
        project_root: str,
        file_ext: str
    ) -> Optional[str]:
        """
        Resolve an import statement to a file path.
        
        This is a simplified implementation and may not work for all cases.
        
        Args:
            import_stmt: The import statement.
            file_path: The path to the file containing the import.
            project_root: The root directory of the project.
            file_ext: The file extension.
            
        Returns:
            The resolved file path, or None if it couldn't be resolved.
        """
        # This is a simplified implementation
        # In a real implementation, this would be more sophisticated
        
        if file_ext.lower() in ['.py', '.pyi']:
            # Python imports
            if import_stmt.startswith('from '):
                parts = import_stmt.split(' import ')
                if len(parts) == 2:
                    module_path = parts[0][5:].replace('.', os.path.sep)
                    possible_paths = [
                        os.path.join(project_root, f"{module_path}.py"),
                        os.path.join(project_root, module_path, "__init__.py"),
                        os.path.join(os.path.dirname(file_path), f"{module_path}.py"),
                        os.path.join(os.path.dirname(file_path), module_path, "__init__.py")
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            return os.path.abspath(path)
            elif import_stmt.startswith('import '):
                module_path = import_stmt[7:].replace('.', os.path.sep)
                possible_paths = [
                    os.path.join(project_root, f"{module_path}.py"),
                    os.path.join(project_root, module_path, "__init__.py"),
                    os.path.join(os.path.dirname(file_path), f"{module_path}.py"),
                    os.path.join(os.path.dirname(file_path), module_path, "__init__.py")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        return os.path.abspath(path)
        
        # For other file types, we would need more sophisticated logic
        
        return None
    
    def _determine_relationship(self, target_file: str, related_file: str) -> str:
        """
        Determine the relationship between the target file and a related file.
        
        Args:
            target_file: The path to the target file.
            related_file: The path to the related file.
            
        Returns:
            A string describing the relationship.
        """
        if os.path.dirname(target_file) == os.path.dirname(related_file):
            return "sibling"
        
        # In a real implementation, we would analyze the content to determine
        # if it's an import, parent, child, etc.
        
        return "related"
