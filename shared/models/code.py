"""
Code models.

This module defines models related to code analysis and generation.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Model for a position in a file."""
    line: int
    character: int


class Range(BaseModel):
    """Model for a range in a file."""
    start: Position
    end: Position


class SymbolKind(int, Enum):
    """Enum for symbol kinds (based on LSP)."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26


class Symbol(BaseModel):
    """Model for a code symbol."""
    name: str
    kind: SymbolKind
    range: Range
    selection_range: Range
    detail: Optional[str] = None
    children: Optional[List["Symbol"]] = None


class CodeAnalysisResult(BaseModel):
    """Model for code analysis results."""
    file_path: str
    symbols: List[Symbol]
    imports: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    language: Optional[str] = None
    errors: Optional[List[Dict]] = None


class CodeGenerationRequest(BaseModel):
    """Model for code generation requests."""
    prompt: str
    context: Optional[str] = None
    language: str
    file_path: Optional[str] = None
    position: Optional[Position] = None
    options: Optional[Dict] = None


class CodeGenerationResult(BaseModel):
    """Model for code generation results."""
    code: str
    explanation: Optional[str] = None
    alternatives: Optional[List[str]] = None
    file_path: Optional[str] = None
    position: Optional[Position] = None
