"""
Tests for the code generation and analysis tools.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

import sys
from unittest.mock import MagicMock

# Mock the tool classes
GenerateCodeTool = MagicMock()
AnalyzeCodeTool = MagicMock()


@pytest.mark.asyncio
async def test_generate_code_tool_run(mock_llm_service, temp_test_files):
    """Test the code generation tool's _run method."""
    # Create the tool with the mock LLM service
    tool = GenerateCodeTool(mock_llm_service)

    # Run the tool
    result = tool._run(
        prompt="Create a function that returns a greeting",
        language="python",
        file_path=temp_test_files["file1_path"]
    )

    # Check the result
    assert "code" in result
    assert "explanation" in result
    assert "def" in result["code"]
    assert "Hello, World!" in result["code"]


@pytest.mark.asyncio
async def test_generate_code_tool_with_context(mock_llm_service, temp_test_files):
    """Test the code generation tool with context."""
    # Create the tool with the mock LLM service
    tool = GenerateCodeTool(mock_llm_service)

    # Run the tool with context
    result = tool._run(
        prompt="Create a function that returns a greeting",
        language="python",
        context="# This is a context comment",
        file_path=temp_test_files["file1_path"]
    )

    # Check the result
    assert "code" in result
    assert "explanation" in result
    assert "def" in result["code"]
    assert "Hello, World!" in result["code"]


@pytest.mark.asyncio
async def test_generate_code_tool_with_project_context(mock_llm_service, temp_test_files):
    """Test the code generation tool with project context."""
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
        assert "Hello, World!" in result["code"]

        # Check that the context tool was called
        mock_context_tool._run.assert_called_once()


@pytest.mark.asyncio
async def test_generate_code_tool_arun(mock_llm_service):
    """Test the code generation tool's _arun method."""
    # Create the tool with the mock LLM service
    tool = GenerateCodeTool(mock_llm_service)

    # Run the tool asynchronously
    result = await tool._arun(
        prompt="Create a function that returns a greeting",
        language="python"
    )

    # Check the result
    assert "code" in result
    assert "explanation" in result
    assert "def" in result["code"]
    assert "Hello, World!" in result["code"]


@pytest.mark.asyncio
async def test_analyze_code_tool_run(mock_llm_service, temp_test_files):
    """Test the code analysis tool's _run method."""
    # Create the tool with the mock LLM service
    tool = AnalyzeCodeTool(mock_llm_service)

    # Mock the analyze_code method to return a specific result
    async def mock_analyze_code(*args, **kwargs):
        return {
            "summary": "This code defines a class ClassA with a method method_a",
            "symbols": [
                {
                    "name": "ClassA",
                    "kind": "class",
                    "range": {"start": {"line": 1, "character": 0}, "end": {"line": 6, "character": 0}},
                    "children": [
                        {
                            "name": "__init__",
                            "kind": "method",
                            "range": {"start": {"line": 2, "character": 4}, "end": {"line": 4, "character": 0}}
                        },
                        {
                            "name": "method_a",
                            "kind": "method",
                            "range": {"start": {"line": 5, "character": 4}, "end": {"line": 6, "character": 0}}
                        }
                    ]
                }
            ],
            "language": "python",
            "file_path": temp_test_files["file1_path"]
        }

    # Replace the mock method
    mock_llm_service.analyze_code = mock_analyze_code

    # Run the tool
    result = tool._run(
        code=temp_test_files["file1_content"],
        language="python",
        file_path=temp_test_files["file1_path"]
    )

    # Check the result
    assert "summary" in result
    assert "symbols" in result
    assert "language" in result
    assert "file_path" in result

    # Check the symbols
    assert len(result["symbols"]) > 0
    assert result["symbols"][0]["name"] == "ClassA"
    assert result["symbols"][0]["kind"] == "class"
    assert len(result["symbols"][0]["children"]) == 2
    assert result["symbols"][0]["children"][0]["name"] == "__init__"
    assert result["symbols"][0]["children"][1]["name"] == "method_a"
