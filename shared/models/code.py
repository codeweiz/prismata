"""
Code models.

This module defines models related to code analysis and generation.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Set

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


class DependencyType(str, Enum):
    """Enum for dependency types."""
    IMPORT = "import"  # 导入依赖
    INHERITANCE = "inheritance"  # 继承依赖
    USAGE = "usage"  # 使用依赖（如函数调用、变量引用）
    IMPLEMENTATION = "implementation"  # 接口实现
    REFERENCE = "reference"  # 一般引用


class Dependency(BaseModel):
    """Model for a dependency between symbols or files."""
    source_file: str
    target_file: str
    source_symbol: Optional[str] = None
    target_symbol: Optional[str] = None
    dependency_type: DependencyType
    description: Optional[str] = None


class CrossFileAnalysisResult(BaseModel):
    """Model for cross-file analysis results."""
    files: List[str]  # 分析的文件列表
    dependencies: List[Dependency]  # 文件间的依赖关系
    symbols_by_file: Dict[str, List[Symbol]] = Field(default_factory=dict)  # 每个文件的符号列表
    imports_by_file: Dict[str, List[str]] = Field(default_factory=dict)  # 每个文件的导入语句
    errors: Optional[List[Dict]] = None  # 分析过程中的错误


class CodeRefactoringRequest(BaseModel):
    """Model for code refactoring requests."""
    refactoring_type: str  # 重构类型，如 "rename", "extract_method", "move_method" 等
    file_paths: List[str]  # 需要重构的文件路径
    target_symbol: Optional[str] = None  # 目标符号名称
    new_name: Optional[str] = None  # 新名称（用于重命名）
    selection: Optional[Dict[str, Range]] = None  # 选中的代码范围（按文件路径索引）
    options: Optional[Dict] = None  # 其他选项


class CodeRefactoringResult(BaseModel):
    """Model for code refactoring results."""
    changes: Dict[str, str]  # 文件路径 -> 新内容的映射
    description: str  # 重构描述
    affected_files: List[str]  # 受影响的文件列表
    preview: Optional[Dict[str, Dict[str, str]]] = None  # 预览（文件路径 -> {原内容, 新内容}）
    errors: Optional[List[Dict]] = None  # 重构过程中的错误


class CodeCompletionRequest(BaseModel):
    """Model for code completion requests."""
    file_path: str
    position: Position
    prefix: Optional[str] = None  # 光标前的文本前缀
    context: Optional[str] = None  # 上下文代码
    options: Optional[Dict] = None  # 其他选项


class CompletionItem(BaseModel):
    """Model for a completion item."""
    label: str  # 显示的标签
    insert_text: str  # 插入的文本
    kind: Optional[int] = None  # 补全项类型
    detail: Optional[str] = None  # 详细信息
    documentation: Optional[str] = None  # 文档
    sort_text: Optional[str] = None  # 排序文本


class CodeCompletionResult(BaseModel):
    """Model for code completion results."""
    items: List[CompletionItem]  # 补全项列表
    is_incomplete: bool = False  # 结果是否不完整
