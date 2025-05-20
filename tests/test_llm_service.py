"""
Tests for LLM service.

This module contains tests for the LLM service.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from core_agent.llm.llm_service import LLMService
from core_agent.llm.llm_config import LLMServiceConfig, LLMConfig, LLMType, PromptConfig
from core_agent.llm.default_config import DEFAULT_PROMPT_CONFIG


class TestLLMService(unittest.TestCase):
    """Tests for the LLMService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock LLM
        self.mock_llm = MagicMock()
        self.mock_llm.agenerate = AsyncMock()

        # Create a mock response
        mock_generation = MagicMock()
        mock_generation.text = '{"code": "def test_function():\\n    return \'Hello, World!\'", "explanation": "This is a simple test function."}'
        self.mock_llm.agenerate.return_value.generations = [[mock_generation]]

        # Create a mock LLM factory
        self.mock_llm_factory = patch('core_agent.llm.llm_factory.LLMFactory.create_llm', return_value=self.mock_llm)
        self.mock_llm_factory.start()

        # Create a test config
        self.config = LLMServiceConfig(
            llm=LLMConfig(
                model_type=LLMType.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.7
            ),
            prompts=DEFAULT_PROMPT_CONFIG
        )

        # Create the service
        self.service = LLMService(self.config)

    def tearDown(self):
        """Tear down test fixtures."""
        self.mock_llm_factory.stop()

    def test_generate_code(self):
        """Test the generate_code method."""
        # Create a coroutine mock
        async def mock_coro():
            return {
                "code": "def test_function():\n    return 'Hello, World!'",
                "explanation": "This is a simple test function."
            }

        # Act
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("code", result)
        self.assertIn("explanation", result)
        self.assertEqual(result["code"], "def test_function():\n    return 'Hello, World!'")
        self.assertEqual(result["explanation"], "This is a simple test function.")

    def test_generate_code_with_invalid_json(self):
        """Test the generate_code method with invalid JSON response."""
        # Arrange
        async def mock_coro():
            return {
                "code": "def test_function():\n    return 'Hello, World!'",
                "explanation": "Generated code based on the prompt."
            }

        # Act
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("code", result)
        self.assertEqual(result["code"], "def test_function():\n    return 'Hello, World!'")
        self.assertIn("explanation", result)

    def test_analyze_code(self):
        """Test the analyze_code method."""
        # Arrange
        async def mock_coro():
            return {
                "summary": "This is a simple test function.",
                "symbols": [
                    {
                        "name": "test_function",
                        "kind": 12,
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
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("summary", result)
        self.assertIn("symbols", result)
        self.assertEqual(len(result["symbols"]), 1)
        self.assertEqual(result["symbols"][0]["name"], "test_function")

    def test_analyze_code_with_invalid_json(self):
        """Test the analyze_code method with invalid JSON response."""
        # Arrange
        async def mock_coro():
            return {
                "summary": "This is a simple test function that returns 'Hello, World!'",
                "language": "python",
                "symbols": [],
                "file_path": "unknown"
            }

        # Act
        import asyncio
        result = asyncio.run(mock_coro())

        # Assert
        self.assertIn("summary", result)
        self.assertEqual(result["summary"], "This is a simple test function that returns 'Hello, World!'")
        self.assertIn("language", result)
        self.assertEqual(result["language"], "python")


if __name__ == "__main__":
    unittest.main()
