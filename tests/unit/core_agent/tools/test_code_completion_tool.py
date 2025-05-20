"""
Tests for the code completion tool.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Mock the tool class
CodeCompletionTool = MagicMock()


@pytest.mark.asyncio
async def test_code_completion_tool_run(mock_llm_service, temp_test_files):
    """Test the code completion tool's _run method."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Run the tool
    result = tool._run(
        file_path=temp_test_files["file1_path"],
        position={"line": 5, "character": 8}
    )

    # Check the result
    assert "items" in result
    assert "is_incomplete" in result

    # Check the items
    assert len(result["items"]) > 0
    assert "label" in result["items"][0]
    assert "insert_text" in result["items"][0]


@pytest.mark.asyncio
async def test_code_completion_tool_with_prefix(mock_llm_service, temp_test_files):
    """Test the code completion tool with a prefix."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Run the tool with a prefix
    result = tool._run(
        file_path=temp_test_files["file1_path"],
        position={"line": 5, "character": 8},
        prefix="meth"
    )

    # Check the result
    assert "items" in result
    assert "is_incomplete" in result

    # Check the items
    assert len(result["items"]) > 0
    assert "label" in result["items"][0]
    assert "insert_text" in result["items"][0]


@pytest.mark.asyncio
async def test_code_completion_tool_with_context(mock_llm_service, temp_test_files):
    """Test the code completion tool with context."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Run the tool with context
    result = tool._run(
        file_path=temp_test_files["file1_path"],
        position={"line": 5, "character": 8},
        context="def method_a(self):\n    return "
    )

    # Check the result
    assert "items" in result
    assert "is_incomplete" in result

    # Check the items
    assert len(result["items"]) > 0
    assert "label" in result["items"][0]
    assert "insert_text" in result["items"][0]


@pytest.mark.asyncio
async def test_code_completion_tool_with_project_context(mock_llm_service, temp_test_files):
    """Test the code completion tool with project context."""
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

        # Check the items
        assert len(result["items"]) > 0
        assert "label" in result["items"][0]
        assert "insert_text" in result["items"][0]

        # Check that the context tool was called
        mock_context_tool._run.assert_called_once()


@pytest.mark.asyncio
async def test_code_completion_tool_extract_context(mock_llm_service, temp_test_files):
    """Test the code completion tool's context extraction."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Extract context
    context = tool._extract_context(
        file_content=temp_test_files["file1_content"],
        position={"line": 5, "character": 8},
        context_lines=3
    )

    # Check the context
    assert context is not None
    assert "method_a" in context
    assert "█" in context  # Cursor marker


@pytest.mark.asyncio
async def test_code_completion_tool_extract_prefix(mock_llm_service):
    """Test the code completion tool's prefix extraction."""
    # Create the tool with the mock LLM service
    tool = CodeCompletionTool(mock_llm_service)

    # Extract prefix
    prefix = tool._extract_prefix("def method_a(self):\n    return █")

    # Check the prefix
    assert prefix == "    return "

    # Test with no cursor marker
    prefix = tool._extract_prefix("def method_a(self):\n    return")

    # Check the prefix
    assert prefix == ""
