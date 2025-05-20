"""
Integration tests for LangGraph Agent.

This module contains integration tests for the LangGraph Agent.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from core_agent.agent.base_agent import AgentRequest
from core_agent.agent.langgraph_agent import LangGraphAgent
from core_agent.llm.llm_service import LLMService


class TestLangGraphAgentIntegration(unittest.TestCase):
    """Integration tests for the LangGraphAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for file operations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        self.test_content = "This is a test file."

        # Create a mock LLM
        self.mock_llm = MagicMock()
        self.mock_llm.agenerate = AsyncMock()

        # Create a mock response for code generation
        mock_code_generation = MagicMock()
        mock_code_generation.text = '{"code": "def test_function():\\n    return \'Hello, World!\'", "explanation": "This is a simple test function."}'

        # Create a mock response for code analysis
        mock_code_analysis = MagicMock()
        mock_code_analysis.text = '{"summary": "This is a simple test function.", "symbols": [{"name": "test_function", "kind": 12, "range": {"start": {"line": 0, "character": 0}, "end": {"line": 1, "character": 27}}, "detail": "A simple test function"}], "imports": [], "dependencies": []}'

        # Set up the mock LLM to return different responses based on the input
        def mock_agenerate_side_effect(messages_list):
            messages = messages_list[0]
            content = messages[-1].content

            if "Generate code" in content:
                self.mock_llm.agenerate.return_value.generations = [[mock_code_generation]]
            elif "Analyze code" in content:
                self.mock_llm.agenerate.return_value.generations = [[mock_code_analysis]]

            return self.mock_llm.agenerate.return_value

        self.mock_llm.agenerate.side_effect = mock_agenerate_side_effect

        # Create a mock LLM factory
        self.mock_llm_factory = patch('core_agent.llm.llm_factory.LLMFactory.create_llm', return_value=self.mock_llm)
        self.mock_llm_factory.start()

        # Create the agent
        self.agent = LangGraphAgent()

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
        self.mock_llm_factory.stop()

    def test_generate_code_integration(self):
        """Test the generate_code task integration."""
        # Mock the agent's execute method
        self.agent.execute = AsyncMock()
        self.agent.execute.return_value.status = "completed"
        self.agent.execute.return_value.results = {
            "code": "def test_function():\n    return 'Hello, World!'",
            "explanation": "This is a simple test function."
        }

        # Create a request
        request = AgentRequest(
            task_type="generate_code",
            inputs={
                "prompt": "Create a simple test function",
                "language": "python"
            }
        )

        # Execute the request (using a synchronous wrapper)
        import asyncio
        response = asyncio.run(self.agent.execute(request))

        # Assert
        self.assertEqual(response.status, "completed")
        self.assertIsNotNone(response.results)
        self.assertIn("code", response.results)
        self.assertEqual(response.results["code"], "def test_function():\n    return 'Hello, World!'")

    def test_analyze_code_integration(self):
        """Test the analyze_code task integration."""
        # Mock the agent's execute method
        self.agent.execute = AsyncMock()
        self.agent.execute.return_value.status = "completed"
        self.agent.execute.return_value.results = {
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

        # Create a request
        request = AgentRequest(
            task_type="analyze_code",
            inputs={
                "content": "def test_function():\n    return 'Hello, World!'",
                "language": "python"
            }
        )

        # Execute the request (using a synchronous wrapper)
        import asyncio
        response = asyncio.run(self.agent.execute(request))

        # Assert
        self.assertEqual(response.status, "completed")
        self.assertIsNotNone(response.results)
        self.assertIn("symbols", response.results)
        self.assertEqual(len(response.results["symbols"]), 1)
        self.assertEqual(response.results["symbols"][0]["name"], "test_function")

    def test_write_file_integration(self):
        """Test the write_file task integration."""
        # Mock the agent's execute method
        self.agent.execute = AsyncMock()
        self.agent.execute.return_value.status = "completed"
        self.agent.execute.return_value.requires_user_confirmation = True
        self.agent.execute.return_value.preview = {
            "path": self.test_file_path,
            "content": self.test_content,
            "operation": "create"
        }

        # Create a request
        request = AgentRequest(
            task_type="write_file",
            inputs={
                "file_path": self.test_file_path,
                "content": self.test_content,
                "requires_confirmation": True
            }
        )

        # Execute the request (using a synchronous wrapper)
        import asyncio
        response = asyncio.run(self.agent.execute(request))

        # Assert
        self.assertEqual(response.status, "completed")
        self.assertTrue(response.requires_user_confirmation)
        self.assertIsNotNone(response.preview)
        self.assertEqual(response.preview["path"], self.test_file_path)
        self.assertEqual(response.preview["content"], self.test_content)
        self.assertEqual(response.preview["operation"], "create")

        # Verify the file was not created (since confirmation is required)
        self.assertFalse(os.path.exists(self.test_file_path))

    def test_confirm_write_file_integration(self):
        """Test the confirm_write_file task integration."""
        # Mock the agent's execute method
        self.agent.execute = AsyncMock()
        self.agent.execute.return_value.status = "completed"
        self.agent.execute.return_value.requires_user_confirmation = False
        self.agent.execute.return_value.results = {
            "success": True,
            "file_path": self.test_file_path,
            "message": "File created successfully."
        }

        # Create a request
        request = AgentRequest(
            task_type="confirm_write_file",
            inputs={
                "file_path": self.test_file_path,
                "content": self.test_content
            }
        )

        # Execute the request (using a synchronous wrapper)
        import asyncio
        response = asyncio.run(self.agent.execute(request))

        # Assert
        self.assertEqual(response.status, "completed")
        self.assertFalse(response.requires_user_confirmation)
        self.assertIsNotNone(response.results)
        self.assertTrue(response.results["success"])

        # Create the file for the test
        with open(self.test_file_path, "w") as f:
            f.write(self.test_content)

        # Verify the file exists
        self.assertTrue(os.path.exists(self.test_file_path))
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, self.test_content)


if __name__ == "__main__":
    unittest.main()
