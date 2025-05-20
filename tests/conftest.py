"""
Pytest configuration file.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the imports
import sys
from unittest.mock import MagicMock

# Create mock classes for testing
class Position:
    def __init__(self, line=0, character=0):
        self.line = line
        self.character = character

class Range:
    def __init__(self, start=None, end=None):
        self.start = start or Position()
        self.end = end or Position()

class Symbol:
    def __init__(self, name="", kind="", range=None, detail=None, children=None):
        self.name = name
        self.kind = kind
        self.range = range or Range()
        self.detail = detail
        self.children = children or []

class ErrorCategory:
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    VALIDATION = "validation"
    LLM = "llm"
    TOOL = "tool"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"

class ErrorSeverity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class OperationStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    RECOVERED = "recovered"

class ErrorInfo:
    def __init__(self, message="", category=None, severity=None, details=None, recovery_options=None, operation_id=None):
        self.message = message
        self.category = category or ErrorCategory.UNKNOWN
        self.severity = severity or ErrorSeverity.ERROR
        self.details = details or {}
        self.recovery_options = recovery_options or []
        self.operation_id = operation_id
        self.stack_trace = None

    def to_dict(self):
        return {
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "details": self.details,
            "recovery_options": self.recovery_options,
            "operation_id": self.operation_id,
            "stack_trace": self.stack_trace
        }

class OperationRecord:
    def __init__(self, operation_id="", operation_type="", inputs=None, status=OperationStatus.PENDING, result=None, error=None, parent_operation_id=None, metadata=None):
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.inputs = inputs or {}
        self.status = status
        self.result = result
        self.error = error
        self.parent_operation_id = parent_operation_id
        self.metadata = metadata or {}
        self.timestamp = 0
        self.updated_at = 0

    def to_dict(self):
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "inputs": self.inputs,
            "status": self.status,
            "result": self.result,
            "error": self.error.to_dict() if self.error else None,
            "parent_operation_id": self.parent_operation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "updated_at": self.updated_at
        }

# Mock the modules
sys.modules['core_agent.llm.llm_service'] = MagicMock()
sys.modules['core_agent.llm.llm_config'] = MagicMock()
sys.modules['core_agent.error.error_handler'] = MagicMock()
sys.modules['core_agent.error.recovery_service'] = MagicMock()
sys.modules['core_agent.tools.cross_file_analysis_tool'] = MagicMock()
sys.modules['core_agent.tools.code_tools'] = MagicMock()
sys.modules['core_agent.tools.refactoring_tools'] = MagicMock()
sys.modules['core_agent.tools.code_completion_tool'] = MagicMock()
sys.modules['shared.models.code'] = MagicMock()
sys.modules['shared.utils.logging_utils'] = MagicMock()

# Mock the classes
sys.modules['core_agent.error.error_handler'].ErrorHandler = MagicMock()
sys.modules['core_agent.error.error_handler'].ErrorCategory = ErrorCategory
sys.modules['core_agent.error.error_handler'].ErrorSeverity = ErrorSeverity
sys.modules['core_agent.error.error_handler'].ErrorInfo = ErrorInfo
sys.modules['core_agent.error.recovery_service'].RecoveryService = MagicMock()
sys.modules['core_agent.error.recovery_service'].OperationRecord = OperationRecord
sys.modules['core_agent.error.recovery_service'].OperationStatus = OperationStatus

# Export the classes for tests
ErrorHandler = MagicMock()
RecoveryService = MagicMock()


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock_service = MagicMock()

    # Mock the analyze_cross_file_dependencies method
    async def mock_analyze_cross_file_dependencies(*args, **kwargs):
        return {
            "summary": "Mock cross-file analysis result",
            "dependencies": [
                {
                    "source_file": "file1.py",
                    "target_file": "file2.py",
                    "source_symbol": "ClassA",
                    "target_symbol": "ClassB",
                    "dependency_type": "import",
                    "description": "ClassA imports ClassB"
                }
            ],
            "symbols_by_file": {
                "file1.py": [
                    {
                        "name": "ClassA",
                        "kind": "class",
                        "range": {"start": {"line": 1, "character": 0}, "end": {"line": 10, "character": 0}},
                        "detail": "A class that imports ClassB"
                    }
                ],
                "file2.py": [
                    {
                        "name": "ClassB",
                        "kind": "class",
                        "range": {"start": {"line": 1, "character": 0}, "end": {"line": 10, "character": 0}},
                        "detail": "A class that is imported by ClassA"
                    }
                ]
            },
            "imports_by_file": {
                "file1.py": ["from file2 import ClassB"],
                "file2.py": []
            }
        }

    # Mock the generate_code method
    async def mock_generate_code(*args, **kwargs):
        return {
            "code": "def example_function():\n    return 'Hello, World!'",
            "explanation": "This is a simple function that returns a greeting."
        }

    # Mock the refactor_code method
    async def mock_refactor_code(*args, **kwargs):
        return {
            "changes": {
                "file1.py": "def renamed_function():\n    return 'Hello, World!'"
            },
            "description": "Renamed function from example_function to renamed_function",
            "affected_files": ["file1.py"],
            "preview": {
                "file1.py": {
                    "original": "def example_function():\n    return 'Hello, World!'",
                    "refactored": "def renamed_function():\n    return 'Hello, World!'"
                }
            }
        }

    # Mock the complete_code method
    async def mock_complete_code(*args, **kwargs):
        return {
            "items": [
                {
                    "label": "example_function",
                    "insert_text": "example_function()",
                    "kind": 2,
                    "detail": "function",
                    "documentation": "A simple function that returns a greeting."
                }
            ],
            "is_incomplete": False
        }

    # Assign the mock methods
    mock_service.analyze_cross_file_dependencies = mock_analyze_cross_file_dependencies
    mock_service.generate_code = mock_generate_code
    mock_service.refactor_code = mock_refactor_code
    mock_service.complete_code = mock_complete_code

    return mock_service


@pytest.fixture
def mock_recovery_service():
    """Create a mock recovery service."""
    return MagicMock(spec=RecoveryService)


@pytest.fixture
def temp_test_files(tmpdir):
    """Create temporary test files."""
    file1_path = tmpdir.join("file1.py")
    file2_path = tmpdir.join("file2.py")

    file1_content = """
class ClassA:
    def __init__(self):
        self.b = ClassB()

    def method_a(self):
        return "Method A"
"""

    file2_content = """
class ClassB:
    def __init__(self):
        pass

    def method_b(self):
        return "Method B"
"""

    file1_path.write(file1_content)
    file2_path.write(file2_content)

    return {
        "file1_path": str(file1_path),
        "file2_path": str(file2_path),
        "file1_content": file1_content,
        "file2_content": file2_content
    }
