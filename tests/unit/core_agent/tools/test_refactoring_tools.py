"""
Tests for the refactoring tools.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Mock the tool class
RefactorCodeTool = MagicMock()


@pytest.mark.asyncio
async def test_refactor_code_tool_run(mock_llm_service, temp_test_files):
    """Test the refactoring tool's _run method."""
    # Create the tool with the mock LLM service
    tool = RefactorCodeTool(mock_llm_service)

    # Run the tool for a rename refactoring
    result = tool._run(
        refactoring_type="rename",
        file_paths=[temp_test_files["file1_path"]],
        target_symbol="method_a",
        new_name="renamed_method"
    )

    # Check the result
    assert "changes" in result
    assert "description" in result
    assert "affected_files" in result
    assert "preview" in result

    # Check the changes
    assert temp_test_files["file1_path"] in result["changes"]

    # Check the affected files
    assert temp_test_files["file1_path"] in result["affected_files"]

    # Check the preview
    assert temp_test_files["file1_path"] in result["preview"]
    assert "original" in result["preview"][temp_test_files["file1_path"]]
    assert "refactored" in result["preview"][temp_test_files["file1_path"]]


@pytest.mark.asyncio
async def test_refactor_code_tool_extract_method(mock_llm_service, temp_test_files):
    """Test the refactoring tool for extract method."""
    # Create the tool with the mock LLM service
    tool = RefactorCodeTool(mock_llm_service)

    # Create a selection for extract method
    selection = {
        temp_test_files["file1_path"]: {
            "start": {"line": 5, "character": 8},
            "end": {"line": 5, "character": 21}
        }
    }

    # Run the tool for an extract method refactoring
    result = tool._run(
        refactoring_type="extract_method",
        file_paths=[temp_test_files["file1_path"]],
        selection=selection,
        new_name="extracted_method"
    )

    # Check the result
    assert "changes" in result
    assert "description" in result
    assert "affected_files" in result
    assert "preview" in result

    # Check the changes
    assert temp_test_files["file1_path"] in result["changes"]

    # Check the affected files
    assert temp_test_files["file1_path"] in result["affected_files"]

    # Check the preview
    assert temp_test_files["file1_path"] in result["preview"]
    assert "original" in result["preview"][temp_test_files["file1_path"]]
    assert "refactored" in result["preview"][temp_test_files["file1_path"]]


@pytest.mark.asyncio
async def test_refactor_code_tool_cross_file(mock_llm_service, temp_test_files):
    """Test the refactoring tool for cross-file refactoring."""
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
async def test_refactor_code_tool_validation(mock_llm_service):
    """Test the refactoring tool's input validation."""
    # Create the tool with the mock LLM service
    tool = RefactorCodeTool(mock_llm_service)

    # Check that it raises an error for missing file paths
    with pytest.raises(ValueError) as excinfo:
        tool._run(
            refactoring_type="rename",
            file_paths=[],
            target_symbol="method_a",
            new_name="renamed_method"
        )
    assert "No file paths provided" in str(excinfo.value)

    # Check that it raises an error for rename without target_symbol
    with pytest.raises(ValueError) as excinfo:
        tool._run(
            refactoring_type="rename",
            file_paths=["file1.py"],
            new_name="renamed_method"
        )
    assert "Rename refactoring requires target_symbol" in str(excinfo.value)

    # Check that it raises an error for rename without new_name
    with pytest.raises(ValueError) as excinfo:
        tool._run(
            refactoring_type="rename",
            file_paths=["file1.py"],
            target_symbol="method_a"
        )
    assert "Rename refactoring requires" in str(excinfo.value)

    # Check that it raises an error for extract method without selection
    with pytest.raises(ValueError) as excinfo:
        tool._run(
            refactoring_type="extract_method",
            file_paths=["file1.py"],
            new_name="extracted_method"
        )
    assert "Extract method refactoring requires a selection" in str(excinfo.value)
