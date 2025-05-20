"""
Tests for Workflow Nodes.

This module contains tests for the Workflow Nodes.
"""

import unittest
from unittest.mock import MagicMock, patch

from core_agent.agent.workflow_nodes import (
    understand_request,
    analyze_context,
    plan_changes,
    execute_changes,
    verify_results
)
from core_agent.agent.state_models import AgentState


class TestWorkflowNodes(unittest.TestCase):
    """Tests for the workflow nodes."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock LLM
        self.mock_llm = MagicMock()

        # Create a test state
        self.state = AgentState(
            task_id="test-task",
            task_type="generate_code",
            inputs={
                "prompt": "Create a hello world function",
                "language": "python"
            },
            status="started"
        )

        # Create mock tools
        self.mock_generate_code_tool = MagicMock()
        self.mock_generate_code_tool.name = "generate_code"
        self.mock_generate_code_tool._run.return_value = {
            "code": "def hello_world():\n    print('Hello, World!')",
            "explanation": "This is a simple hello world function."
        }

        self.mock_analyze_code_tool = MagicMock()
        self.mock_analyze_code_tool.name = "analyze_code"
        self.mock_analyze_code_tool._run.return_value = {
            "symbols": [
                {
                    "name": "hello_world",
                    "kind": 12,
                    "range": {
                        "start": {"line": 0, "character": 0},
                        "end": {"line": 1, "character": 27}
                    },
                    "detail": "A simple hello world function"
                }
            ],
            "imports": [],
            "dependencies": []
        }

        self.mock_write_file_tool = MagicMock()
        self.mock_write_file_tool.name = "write_file"
        self.mock_write_file_tool._run.return_value = {
            "requires_confirmation": True,
            "preview": {
                "path": "test.py",
                "content": "def hello_world():\n    print('Hello, World!')",
                "operation": "create"
            }
        }

        self.mock_tools = [
            self.mock_generate_code_tool,
            self.mock_analyze_code_tool,
            self.mock_write_file_tool
        ]

    def test_understand_request(self):
        """Test the understand_request node."""
        # Act
        result = understand_request(self.state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "understanding_request")
        self.assertEqual(result.task_type, "generate_code")
        self.assertEqual(result.inputs["prompt"], "Create a hello world function")

    def test_analyze_context(self):
        """Test the analyze_context node."""
        # Act
        result = analyze_context(self.state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "analyzing_context")
        self.assertEqual(result.task_type, "generate_code")
        self.assertEqual(result.inputs["prompt"], "Create a hello world function")

    def test_plan_changes_for_generate_code(self):
        """Test the plan_changes node for generate_code task."""
        # Act
        result = plan_changes(self.state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "planning_changes")
        self.assertIsNotNone(result.changes)
        self.assertEqual(result.changes["type"], "code_generation")
        self.assertEqual(result.changes["prompt"], "Create a hello world function")
        self.assertEqual(result.changes["language"], "python")

    def test_plan_changes_for_analyze_code(self):
        """Test the plan_changes node for analyze_code task."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="analyze_code",
            inputs={
                "content": "def hello_world():\n    print('Hello, World!')",
                "language": "python",
                "file_path": "test.py"
            },
            status="started"
        )

        # Act
        result = plan_changes(state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "planning_changes")
        self.assertIsNotNone(result.changes)
        self.assertEqual(result.changes["type"], "code_analysis")
        self.assertEqual(result.changes["content"], "def hello_world():\n    print('Hello, World!')")
        self.assertEqual(result.changes["language"], "python")
        self.assertEqual(result.changes["file_path"], "test.py")

    def test_plan_changes_for_write_file(self):
        """Test the plan_changes node for write_file task."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="write_file",
            inputs={
                "file_path": "test.py",
                "content": "def hello_world():\n    print('Hello, World!')",
                "encoding": "utf-8"
            },
            status="started"
        )

        # Act
        result = plan_changes(state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "planning_changes")
        self.assertIsNotNone(result.changes)
        self.assertEqual(result.changes["type"], "file_write")
        self.assertEqual(result.changes["file_path"], "test.py")
        self.assertEqual(result.changes["content"], "def hello_world():\n    print('Hello, World!')")
        self.assertEqual(result.changes["encoding"], "utf-8")
        self.assertTrue(result.changes["requires_confirmation"])

    def test_execute_changes_for_generate_code(self):
        """Test the execute_changes node for generate_code task."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="generate_code",
            inputs={
                "prompt": "Create a hello world function",
                "language": "python"
            },
            status="planning_changes",
            changes={
                "type": "code_generation",
                "prompt": "Create a hello world function",
                "language": "python"
            }
        )

        # Act
        result = execute_changes(state, self.mock_tools)

        # Assert
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.results)
        self.assertEqual(result.results["code"], "def hello_world():\n    print('Hello, World!')")
        self.assertEqual(result.results["explanation"], "This is a simple hello world function.")
        self.mock_generate_code_tool._run.assert_called_once_with(
            prompt="Create a hello world function",
            language="python",
            context=None
        )

    def test_execute_changes_for_analyze_code(self):
        """Test the execute_changes node for analyze_code task."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="analyze_code",
            inputs={
                "content": "def hello_world():\n    print('Hello, World!')",
                "language": "python",
                "file_path": "test.py"
            },
            status="planning_changes",
            changes={
                "type": "code_analysis",
                "content": "def hello_world():\n    print('Hello, World!')",
                "language": "python",
                "file_path": "test.py"
            }
        )

        # Act
        result = execute_changes(state, self.mock_tools)

        # Assert
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.results)
        self.assertIn("symbols", result.results)
        self.assertEqual(len(result.results["symbols"]), 1)
        self.assertEqual(result.results["symbols"][0]["name"], "hello_world")
        self.mock_analyze_code_tool._run.assert_called_once_with(
            code="def hello_world():\n    print('Hello, World!')",
            language="python",
            file_path="test.py"
        )

    def test_execute_changes_for_write_file(self):
        """Test the execute_changes node for write_file task."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="write_file",
            inputs={
                "file_path": "test.py",
                "content": "def hello_world():\n    print('Hello, World!')",
                "encoding": "utf-8"
            },
            status="planning_changes",
            changes={
                "type": "file_write",
                "file_path": "test.py",
                "content": "def hello_world():\n    print('Hello, World!')",
                "encoding": "utf-8",
                "requires_confirmation": True
            }
        )

        # Act
        result = execute_changes(state, self.mock_tools)

        # Assert
        self.assertEqual(result.status, "awaiting_confirmation")
        self.assertTrue(result.requires_confirmation)
        self.assertIsNotNone(result.preview)
        self.assertEqual(result.preview["path"], "test.py")
        self.assertEqual(result.preview["content"], "def hello_world():\n    print('Hello, World!')")
        self.assertEqual(result.preview["operation"], "create")
        self.mock_write_file_tool._run.assert_called_once_with(
            file_path="test.py",
            content="def hello_world():\n    print('Hello, World!')",
            encoding="utf-8",
            requires_confirmation=True
        )

    def test_execute_changes_with_no_changes(self):
        """Test the execute_changes node with no changes."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="generate_code",
            inputs={
                "prompt": "Create a hello world function",
                "language": "python"
            },
            status="planning_changes",
            changes=None
        )

        # Act
        result = execute_changes(state, self.mock_tools)

        # Assert
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.results)
        self.assertEqual(result.results["message"], "No changes to execute")

    def test_execute_changes_with_unknown_type(self):
        """Test the execute_changes node with an unknown change type."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="unknown",
            inputs={},
            status="planning_changes",
            changes={
                "type": "unknown"
            }
        )

        # Act
        result = execute_changes(state, self.mock_tools)

        # Assert
        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error)
        self.assertIn("Unknown change type", result.error)

    def test_verify_results(self):
        """Test the verify_results node."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="generate_code",
            inputs={
                "prompt": "Create a hello world function",
                "language": "python"
            },
            status="executing_changes",
            results={
                "code": "def hello_world():\n    print('Hello, World!')",
                "explanation": "This is a simple hello world function."
            }
        )

        # Act
        result = verify_results(state, self.mock_llm)

        # Assert
        self.assertEqual(result.status, "verifying_results")
        self.assertTrue(result.verification_passed)

    def test_verify_results_with_no_results(self):
        """Test the verify_results node with no results."""
        # Arrange
        state = AgentState(
            task_id="test-task",
            task_type="generate_code",
            inputs={
                "prompt": "Create a hello world function",
                "language": "python"
            },
            status="executing_changes",
            results=None
        )

        # Act
        result = verify_results(state, self.mock_llm)

        # Assert
        # The status remains unchanged in the current implementation
        self.assertEqual(result.status, "executing_changes")
        self.assertFalse(result.verification_passed)


if __name__ == "__main__":
    unittest.main()
