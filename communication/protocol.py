"""
Communication protocol definition.

This module defines the JSON-RPC protocol used for communication between
IDE plugins and the Agent service.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MethodType(str, Enum):
    """Enum for supported method types."""
    # File operations
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    GET_FILE_METADATA = "get_file_metadata"
    
    # Code analysis
    ANALYZE_CODE = "analyze_code"
    EXTRACT_DEPENDENCIES = "extract_dependencies"
    QUERY_SYMBOLS = "query_symbols"
    
    # Code generation
    GENERATE_CODE = "generate_code"
    COMPLETE_CODE = "complete_code"
    REFACTOR_CODE = "refactor_code"
    
    # Multi-step tasks
    GENERATE_TESTS = "generate_tests"
    GENERATE_DOCUMENTATION = "generate_documentation"
    COMPLEX_REFACTORING = "complex_refactoring"


class JsonRpcRequest(BaseModel):
    """JSON-RPC request model."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Dict[str, Any]


class JsonRpcResponse(BaseModel):
    """JSON-RPC response model."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class JsonRpcError(BaseModel):
    """JSON-RPC error model."""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorCode(int, Enum):
    """Standard error codes for the protocol."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom error codes
    FILE_NOT_FOUND = -32000
    PERMISSION_DENIED = -32001
    ENCODING_ERROR = -32002
    INVALID_PROMPT = -32010
    UNSUPPORTED_LANGUAGE = -32011
    GENERATION_FAILED = -32012


# Method parameter and result definitions
class ReadFileParams(BaseModel):
    """Parameters for read_file method."""
    file_path: str
    encoding: Optional[str] = "utf-8"


class ReadFileResult(BaseModel):
    """Result for read_file method."""
    content: str
    metadata: Dict[str, Any]


class WriteFileParams(BaseModel):
    """Parameters for write_file method."""
    file_path: str
    content: str
    encoding: Optional[str] = "utf-8"


class WriteFileResult(BaseModel):
    """Result for write_file method."""
    success: bool
    file_path: str


class GenerateCodeParams(BaseModel):
    """Parameters for generate_code method."""
    prompt: str
    context: Optional[str] = None
    language: str
    options: Optional[Dict[str, Any]] = None


class GenerateCodeResult(BaseModel):
    """Result for generate_code method."""
    code: str
    explanation: Optional[str] = None
    alternatives: Optional[List[str]] = None
