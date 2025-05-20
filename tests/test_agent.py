"""
Tests for the Agent implementation.
"""

import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from core_agent.agent.base_agent import AgentRequest, AgentResponse
from core_agent.agent.langgraph_agent import LangGraphAgent


class TestLangGraphAgent(unittest.TestCase):
    """Tests for the LangGraphAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        # We'll patch the LangGraphAgent in each test to avoid workflow compilation issues

    @patch('core_agent.agent.langgraph_agent.StateGraph')
    def test_initialize(self, mock_state_graph):
        """Test agent initialization."""
        # Arrange
        mock_compile = MagicMock()
        mock_state_graph.return_value.compile.return_value = mock_compile

        # Act
        agent = LangGraphAgent()

        # Assert
        self.assertIsNotNone(agent.workflow)
        mock_state_graph.return_value.compile.assert_called_once()

    @patch('core_agent.agent.langgraph_agent.uuid.uuid4')
    @patch('core_agent.agent.langgraph_agent.LangGraphAgent._build_workflow')
    async def test_execute(self, mock_build_workflow, mock_uuid):
        """Test agent execution."""
        # Arrange
        mock_uuid.return_value = "test-task-id"
        request = AgentRequest(
            task_type="test_task",
            inputs={"test_input": "test_value"},
            context={"test_context": "test_value"}
        )

        # Mock the workflow
        mock_workflow = MagicMock()
        mock_workflow.ainvoke = AsyncMock()
        mock_workflow.ainvoke.return_value = {
            "status": "completed",
            "results": {"test_result": "test_value"}
        }
        mock_build_workflow.return_value = mock_workflow

        # Create agent with mocked workflow
        agent = LangGraphAgent()

        # Act
        response = await agent.execute(request)

        # Assert
        self.assertIsInstance(response, AgentResponse)
        self.assertEqual(response.task_id, "test-task-id")
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.results, {"test_result": "test_value"})
        mock_workflow.ainvoke.assert_called_once()

    @patch('core_agent.agent.langgraph_agent.LangGraphAgent._build_workflow')
    async def test_cancel(self, mock_build_workflow):
        """Test task cancellation."""
        # Arrange
        mock_build_workflow.return_value = MagicMock()
        agent = LangGraphAgent()
        task_id = "test-task-id"
        agent.active_tasks = {
            task_id: {"cancelled": False, "state": {}}
        }

        # Act
        result = await agent.cancel(task_id)

        # Assert
        self.assertTrue(result)
        self.assertTrue(agent.active_tasks[task_id]["cancelled"])

    @patch('core_agent.agent.langgraph_agent.LangGraphAgent._build_workflow')
    async def test_cancel_nonexistent_task(self, mock_build_workflow):
        """Test cancellation of a nonexistent task."""
        # Arrange
        mock_build_workflow.return_value = MagicMock()
        agent = LangGraphAgent()

        # Act
        result = await agent.cancel("nonexistent-task-id")

        # Assert
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
