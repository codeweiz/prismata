"""
Path utilities.

This module provides utility functions for working with file paths.
"""

import os
import pathlib
from typing import List, Optional, Tuple, Union

PathLike = Union[str, os.PathLike]


def normalize_path(path: PathLike) -> str:
    """
    Normalize a path to a standard format.
    
    Args:
        path: The path to normalize.
        
    Returns:
        The normalized path as a string.
    """
    return os.path.normpath(str(path))


def is_subpath(path: PathLike, parent: PathLike) -> bool:
    """
    Check if a path is a subpath of another path.
    
    Args:
        path: The path to check.
        parent: The potential parent path.
        
    Returns:
        True if path is a subpath of parent, False otherwise.
    """
    path_abs = os.path.abspath(str(path))
    parent_abs = os.path.abspath(str(parent))
    
    return path_abs.startswith(parent_abs)


def is_safe_path(path: PathLike, base_dir: PathLike) -> bool:
    """
    Check if a path is safe to access (within the base directory).
    
    Args:
        path: The path to check.
        base_dir: The base directory that should contain the path.
        
    Returns:
        True if the path is safe to access, False otherwise.
    """
    # Resolve to absolute paths
    path_abs = os.path.abspath(str(path))
    base_dir_abs = os.path.abspath(str(base_dir))
    
    # Check if path is within base_dir
    return is_subpath(path_abs, base_dir_abs)


def get_relative_path(path: PathLike, base_dir: PathLike) -> str:
    """
    Get the relative path from a base directory.
    
    Args:
        path: The path to convert.
        base_dir: The base directory.
        
    Returns:
        The relative path as a string.
    """
    path_abs = os.path.abspath(str(path))
    base_dir_abs = os.path.abspath(str(base_dir))
    
    return os.path.relpath(path_abs, base_dir_abs)


def split_path(path: PathLike) -> Tuple[str, str]:
    """
    Split a path into directory and filename.
    
    Args:
        path: The path to split.
        
    Returns:
        A tuple of (directory, filename).
    """
    path_norm = normalize_path(path)
    return os.path.split(path_norm)


def get_file_extension(path: PathLike) -> str:
    """
    Get the file extension from a path.
    
    Args:
        path: The path to get the extension from.
        
    Returns:
        The file extension (including the dot) or an empty string if there is no extension.
    """
    _, ext = os.path.splitext(str(path))
    return ext


def list_files(directory: PathLike, pattern: Optional[str] = None) -> List[str]:
    """
    List files in a directory, optionally matching a pattern.
    
    Args:
        directory: The directory to list files from.
        pattern: An optional glob pattern to match files against.
        
    Returns:
        A list of file paths.
    """
    directory_path = pathlib.Path(directory)
    
    if pattern:
        return [str(p) for p in directory_path.glob(pattern) if p.is_file()]
    else:
        return [str(p) for p in directory_path.iterdir() if p.is_file()]
