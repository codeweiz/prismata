"""
Tests for code tools.

This module contains tests for the code generation and analysis tools.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from core_agent.tools.code_tools import GenerateCodeTool, AnalyzeCodeTool
from core_agent.llm.llm_service import LLMService


class TestGenerateCodeTool(unittest.TestCase):
    """Tests for the GenerateCodeTool class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock LLM service
        self.mock_llm_service = MagicMock(spec=LLMService)
        self.mock_llm_service.generate_code = AsyncMock()
        self.mock_llm_service.generate_code.return_value = {
            "code": "def test_function():\n    return 'Hello, World!'",
            "explanation": "This is a simple test function."
        }

        # Create the tool
        self.tool = GenerateCodeTool(self.mock_llm_service)

    @patch('asyncio.run')
    def test_run(self, mock_asyncio_run):
        """Test the _run method."""
        # Arrange
        mock_asyncio_run.return_value = {
            "code": "def test_function():\n    return 'Hello, World!'",
            "explanation": "This is a simple test function."
        }

        # Act
        result = self.tool._run(
            prompt="Create a simple test function",
            language="python"
        )

        # Assert
        self.assertIn("code", result)
        self.assertIn("explanation", result)
        self.assertEqual(result["code"], "def test_function():\n    return 'Hello, World!'")
        mock_asyncio_run.assert_called_once()

    def test_arun(self):
        """Test the _arun method."""
        # Arrange
        self.mock_llm_service.generate_code.return_value = {
            "code": "def test_function():\n    return 'Hello, World!'",
            "explanation": "This is a simple test function."
        }

        # Create a coroutine mock
        async def mock_coro():
            return {
                "code": "def test_function():\n    return 'Hello, World!'",
                "explanation": "This is a simple test function."
            }

        # Mock the _arun method
        self.tool._arun = mock_coro

        # Act
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("code", result)
        self.assertIn("explanation", result)
        self.assertEqual(result["code"], "def test_function():\n    return 'Hello, World!'")


class TestAnalyzeCodeTool(unittest.TestCase):
    """Tests for the AnalyzeCodeTool class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock LLM service
        self.mock_llm_service = MagicMock(spec=LLMService)
        self.mock_llm_service.analyze_code = AsyncMock()
        self.mock_llm_service.analyze_code.return_value = {
            "summary": "This is a simple test function.",
            "symbols": [
                {
                    "name": "test_function",
                    "kind": 12,  # Function
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 27}
                    },
                    "detail": "A simple test function"
                }
            ],
            "imports": [],
            "dependencies": []
        }

        # Create the tool
        self.tool = AnalyzeCodeTool(self.mock_llm_service)

    @patch('asyncio.run')
    def test_run(self, mock_asyncio_run):
        """Test the _run method."""
        # Arrange
        mock_asyncio_run.return_value = {
            "summary": "This is a simple test function.",
            "symbols": [
                {
                    "name": "test_function",
                    "kind": 12,  # Function
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 27}
                    },
                    "detail": "A simple test function"
                }
            ],
            "imports": [],
            "dependencies": []
        }

        # Act
        result = self.tool._run(
            code="def test_function():\n    return 'Hello, World!'",
            language="python"
        )

        # Assert
        self.assertIn("symbols", result)
        self.assertEqual(len(result["symbols"]), 1)
        self.assertEqual(result["symbols"][0]["name"], "test_function")
        mock_asyncio_run.assert_called_once()

    def test_arun(self):
        """Test the _arun method."""
        # Arrange
        self.mock_llm_service.analyze_code.return_value = {
            "summary": "This is a simple test function.",
            "symbols": [
                {
                    "name": "test_function",
                    "kind": 12,  # Function
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 27}
                    },
                    "detail": "A simple test function"
                }
            ],
            "imports": [],
            "dependencies": []
        }

        # Create a coroutine mock
        async def mock_coro():
            return {
                "symbols": [
                    {
                        "name": "test_function",
                        "kind": 12,
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 1, "character": 27}
                        },
                        "selection_range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 1, "character": 27}
                        },
                        "detail": "A simple test function"
                    }
                ],
                "imports": [],
                "dependencies": []
            }

        # Mock the _arun method
        self.tool._arun = mock_coro

        # Act
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("symbols", result)
        self.assertEqual(len(result["symbols"]), 1)
        self.assertEqual(result["symbols"][0]["name"], "test_function")


if __name__ == "__main__":
    unittest.main()
