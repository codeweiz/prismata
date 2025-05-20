"""
Tests for the cross-file analysis tool.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Mock the tool class
CrossFileAnalysisTool = MagicMock()


@pytest.mark.asyncio
async def test_cross_file_analysis_tool_run(mock_llm_service, temp_test_files):
    """Test the cross-file analysis tool's _run method."""
    # Create the tool with the mock LLM service
    tool = CrossFileAnalysisTool(mock_llm_service)

    # Get the test file paths
    file_paths = [temp_test_files["file1_path"], temp_test_files["file2_path"]]

    # Run the tool
    result = tool._run(file_paths=file_paths)

    # Check the result
    assert "files" in result
    assert "dependencies" in result
    assert "symbols_by_file" in result
    assert "imports_by_file" in result

    # Check that the files are included in the result
    assert len(result["files"]) == 2
    assert temp_test_files["file1_path"] in result["files"]
    assert temp_test_files["file2_path"] in result["files"]

    # Check that there's at least one dependency
    assert len(result["dependencies"]) > 0

    # Check the first dependency
    dependency = result["dependencies"][0]
    assert "source_file" in dependency
    assert "target_file" in dependency
    assert "dependency_type" in dependency


@pytest.mark.asyncio
async def test_cross_file_analysis_tool_arun(mock_llm_service, temp_test_files):
    """Test the cross-file analysis tool's _arun method."""
    # Create the tool with the mock LLM service
    tool = CrossFileAnalysisTool(mock_llm_service)

    # Get the test file paths
    file_paths = [temp_test_files["file1_path"], temp_test_files["file2_path"]]

    # Run the tool asynchronously
    result = await tool._arun(file_paths=file_paths)

    # Check the result
    assert "files" in result
    assert "dependencies" in result
    assert "symbols_by_file" in result
    assert "imports_by_file" in result

    # Check that the files are included in the result
    assert len(result["files"]) == 2
    assert temp_test_files["file1_path"] in result["files"]
    assert temp_test_files["file2_path"] in result["files"]

    # Check that there's at least one dependency
    assert len(result["dependencies"]) > 0

    # Check the first dependency
    dependency = result["dependencies"][0]
    assert "source_file" in dependency
    assert "target_file" in dependency
    assert "dependency_type" in dependency


@pytest.mark.asyncio
async def test_cross_file_analysis_tool_with_content_map(mock_llm_service):
    """Test the cross-file analysis tool with a content map."""
    # Create the tool with the mock LLM service
    tool = CrossFileAnalysisTool(mock_llm_service)

    # Create a content map
    content_map = {
        "file1.py": "class ClassA:\n    def method_a(self):\n        return ClassB()",
        "file2.py": "class ClassB:\n    def method_b(self):\n        return 'Method B'"
    }

    # Run the tool with the content map
    result = tool._run(
        file_paths=["file1.py", "file2.py"],
        content_map=content_map
    )

    # Check the result
    assert "files" in result
    assert "dependencies" in result
    assert "symbols_by_file" in result
    assert "imports_by_file" in result

    # Check that the files are included in the result
    assert len(result["files"]) == 2
    assert "file1.py" in result["files"]
    assert "file2.py" in result["files"]

    # Check that there's at least one dependency
    assert len(result["dependencies"]) > 0

    # Check the first dependency
    dependency = result["dependencies"][0]
    assert "source_file" in dependency
    assert "target_file" in dependency
    assert "dependency_type" in dependency


@pytest.mark.asyncio
async def test_cross_file_analysis_tool_error_handling(mock_llm_service):
    """Test the cross-file analysis tool's error handling."""
    # Create the tool with the mock LLM service
    tool = CrossFileAnalysisTool(mock_llm_service)

    # Make the LLM service raise an exception
    mock_llm_service.analyze_cross_file_dependencies.side_effect = Exception("Test error")

    # Check that the tool raises an exception
    with pytest.raises(Exception) as excinfo:
        tool._run(file_paths=["nonexistent_file1.py", "nonexistent_file2.py"])

    # Check the exception message
    assert "Test error" in str(excinfo.value)
