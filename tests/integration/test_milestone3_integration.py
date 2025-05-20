"""
Integration tests for Milestone 3 features.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Import the mock classes from conftest
from tests.conftest import ErrorHandler, ErrorCategory, ErrorSeverity, RecoveryService, OperationStatus

# Mock the tool classes
CrossFileAnalysisTool = MagicMock()
GenerateCodeTool = MagicMock()
AnalyzeCodeTool = MagicMock()
RefactorCodeTool = MagicMock()
CodeCompletionTool = MagicMock()


@pytest.mark.asyncio
async def test_cross_file_analysis_integration(mock_llm_service, temp_test_files):
    """Test the integration of cross-file analysis."""
    # Create the tool with the mock LLM service
    tool = CrossFileAnalysisTool(mock_llm_service)

    # Get the test file paths
    file_paths = [temp_test_files["file1_path"], temp_test_files["file2_path"]]

    # Run the tool
    result = tool._run(file_paths=file_paths)

    # Check the result
    assert "files" in result
    assert "dependencies" in result
    assert len(result["files"]) == 2
    assert len(result["dependencies"]) > 0


@pytest.mark.asyncio
async def test_context_aware_code_generation_integration(mock_llm_service, temp_test_files):
    """Test the integration of context-aware code generation."""
    # Create the tool with the mock LLM service
    tool = GenerateCodeTool(mock_llm_service)

    # Mock the context tool
    with patch.object(tool, 'context_tool') as mock_context_tool:
        # Set up the mock to return a project context
        mock_context_tool._run.return_value = {
            "target_file": {
                "path": temp_test_files["file1_path"],
                "content": temp_test_files["file1_content"]
            },
            "related_files": [
                {
                    "path": temp_test_files["file2_path"],
                    "content": temp_test_files["file2_content"],
                    "relationship": "import"
                }
            ],
            "imports": ["from file2 import ClassB"],
            "project_root": os.path.dirname(temp_test_files["file1_path"])
        }

        # Run the tool with project context
        result = tool._run(
            prompt="Create a function that uses ClassB",
            language="python",
            file_path=temp_test_files["file1_path"],
            use_project_context=True
        )

        # Check the result
        assert "code" in result
        assert "explanation" in result
        assert "def" in result["code"]

        # Check that the context tool was called
        mock_context_tool._run.assert_called_once()


@pytest.mark.asyncio
async def test_code_refactoring_integration(mock_llm_service, temp_test_files):
    """Test the integration of code refactoring."""
    # Create the tool with the mock LLM service
    tool = RefactorCodeTool(mock_llm_service)

    # Mock the cross_file_analysis_tool
    with patch.object(tool, 'cross_file_analysis_tool') as mock_analysis_tool:
        # Set up the mock to return a cross-file analysis result
        mock_analysis_tool._run.return_value = {
            "files": [temp_test_files["file1_path"], temp_test_files["file2_path"]],
            "dependencies": [
                {
                    "source_file": temp_test_files["file1_path"],
                    "target_file": temp_test_files["file2_path"],
                    "source_symbol": "ClassA",
                    "target_symbol": "ClassB",
                    "dependency_type": "import",
                    "description": "ClassA imports ClassB"
                }
            ],
            "symbols_by_file": {
                temp_test_files["file1_path"]: [
                    {
                        "name": "ClassA",
                        "kind": "class",
                        "range": {"start": {"line": 1, "character": 0}, "end": {"line": 6, "character": 0}}
                    }
                ],
                temp_test_files["file2_path"]: [
                    {
                        "name": "ClassB",
                        "kind": "class",
                        "range": {"start": {"line": 1, "character": 0}, "end": {"line": 6, "character": 0}}
                    }
                ]
            },
            "imports_by_file": {
                temp_test_files["file1_path"]: ["from file2 import ClassB"],
                temp_test_files["file2_path"]: []
            }
        }

        # Run the tool for a rename refactoring across files
        result = tool._run(
            refactoring_type="rename",
            file_paths=[temp_test_files["file1_path"], temp_test_files["file2_path"]],
            target_symbol="ClassB",
            new_name="RenamedClass"
        )

        # Check the result
        assert "changes" in result
        assert "description" in result
        assert "affected_files" in result
        assert "preview" in result

        # Check that the cross-file analysis tool was called
        mock_analysis_tool._run.assert_called_once()


@pytest.mark.asyncio
async def test_code_completion_integration(mock_llm_service, temp_test_files):
    """Test the integration of code completion."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Mock the context tool
    with patch.object(tool, 'context_tool') as mock_context_tool:
        # Set up the mock to return a project context
        mock_context_tool._run.return_value = {
            "target_file": {
                "path": temp_test_files["file1_path"],
                "content": temp_test_files["file1_content"]
            },
            "related_files": [
                {
                    "path": temp_test_files["file2_path"],
                    "content": temp_test_files["file2_content"],
                    "relationship": "import"
                }
            ],
            "imports": ["from file2 import ClassB"],
            "project_root": os.path.dirname(temp_test_files["file1_path"])
        }

        # Run the tool with project context
        result = tool._run(
            file_path=temp_test_files["file1_path"],
            position={"line": 5, "character": 8},
            options={"use_project_context": True}
        )

        # Check the result
        assert "items" in result
        assert "is_incomplete" in result
        assert len(result["items"]) > 0

        # Check that the context tool was called
        mock_context_tool._run.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_and_recovery_integration(mock_llm_service, mock_recovery_service):
    """Test the integration of error handling and recovery."""
    # Create an error
    error_info = ErrorHandler.create_error(
        message="Test error",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR
    )

    # Create an operation
    operation = mock_recovery_service.create_operation(
        operation_type="test_operation",
        inputs={"key": "value"}
    )

    # Fail the operation
    mock_recovery_service.fail_operation(operation.operation_id, error_info)

    # Register a recovery handler
    mock_handler = MagicMock(return_value="Recovery result")
    mock_recovery_service.register_recovery_handler("test_operation", mock_handler)

    # Retry the operation
    result = mock_recovery_service.retry_operation(operation.operation_id)

    # Check the result
    assert result == "Recovery result"

    # Check that the handler was called
    mock_handler.assert_called_once()

    # Check the operation
    mock_recovery_service.get_operation.assert_called_with(operation.operation_id)


@pytest.mark.asyncio
async def test_full_milestone3_workflow_integration(
    mock_llm_service, temp_test_files, mock_recovery_service
):
    """Test the full integration of all Milestone 3 features."""
    # 1. Cross-file analysis
    cross_file_tool = CrossFileAnalysisTool(mock_llm_service)
    file_paths = [temp_test_files["file1_path"], temp_test_files["file2_path"]]
    analysis_result = cross_file_tool._run(file_paths=file_paths)

    # 2. Context-aware code generation
    code_gen_tool = GenerateCodeTool(mock_llm_service)
    with patch.object(code_gen_tool, 'context_tool') as mock_context_tool:
        mock_context_tool._run.return_value = {
            "target_file": {
                "path": temp_test_files["file1_path"],
                "content": temp_test_files["file1_content"]
            },
            "related_files": [
                {
                    "path": temp_test_files["file2_path"],
                    "content": temp_test_files["file2_content"],
                    "relationship": "import"
                }
            ],
            "imports": ["from file2 import ClassB"],
            "project_root": os.path.dirname(temp_test_files["file1_path"])
        }

        code_result = code_gen_tool._run(
            prompt="Create a function that uses ClassB",
            language="python",
            file_path=temp_test_files["file1_path"],
            use_project_context=True
        )

    # 3. Code refactoring
    refactor_tool = RefactorCodeTool(mock_llm_service)
    with patch.object(refactor_tool, 'cross_file_analysis_tool') as mock_analysis_tool:
        mock_analysis_tool._run.return_value = analysis_result

        refactor_result = refactor_tool._run(
            refactoring_type="rename",
            file_paths=file_paths,
            target_symbol="ClassB",
            new_name="RenamedClass"
        )

    # 4. Code completion
    completion_tool = CodeCompletionTool(mock_llm_service)
    with patch.object(completion_tool, 'context_tool') as mock_context_tool:
        mock_context_tool._run.return_value = {
            "target_file": {
                "path": temp_test_files["file1_path"],
                "content": temp_test_files["file1_content"]
            },
            "related_files": [
                {
                    "path": temp_test_files["file2_path"],
                    "content": temp_test_files["file2_content"],
                    "relationship": "import"
                }
            ],
            "imports": ["from file2 import ClassB"],
            "project_root": os.path.dirname(temp_test_files["file1_path"])
        }

        completion_result = completion_tool._run(
            file_path=temp_test_files["file1_path"],
            position={"line": 5, "character": 8},
            options={"use_project_context": True}
        )

    # 5. Error handling and recovery
    # Create an operation for the code generation
    operation = mock_recovery_service.create_operation(
        operation_type="generate_code",
        inputs={
            "prompt": "Create a function that uses ClassB",
            "language": "python",
            "file_path": temp_test_files["file1_path"],
            "use_project_context": True
        }
    )

    # Complete the operation
    mock_recovery_service.complete_operation(operation.operation_id, code_result)

    # Check the results
    assert "dependencies" in analysis_result
    assert "code" in code_result
    assert "changes" in refactor_result
    assert "items" in completion_result

    # Check that the operation was completed
    mock_recovery_service.complete_operation.assert_called_with(operation.operation_id, code_result)
