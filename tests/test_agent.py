"""
Tests for the Agent implementation.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from core_agent.agent.base_agent import AgentRequest, AgentResponse
from core_agent.agent.langgraph_agent import LangGraphAgent


class TestLangGraphAgent(unittest.TestCase):
    """Tests for the LangGraphAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = LangGraphAgent()
    
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
    async def test_execute(self, mock_uuid):
        """Test agent execution."""
        # Arrange
        mock_uuid.return_value = "test-task-id"
        request = AgentRequest(
            task_type="test_task",
            inputs={"test_input": "test_value"},
            context={"test_context": "test_value"}
        )
        
        # Mock the workflow
        self.agent.workflow = MagicMock()
        self.agent.workflow.ainvoke = MagicMock()
        self.agent.workflow.ainvoke.return_value = {
            "status": "completed",
            "results": {"test_result": "test_value"}
        }
        
        # Act
        response = await self.agent.execute(request)
        
        # Assert
        self.assertIsInstance(response, AgentResponse)
        self.assertEqual(response.task_id, "test-task-id")
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.results, {"test_result": "test_value"})
        self.agent.workflow.ainvoke.assert_called_once()
    
    async def test_cancel(self):
        """Test task cancellation."""
        # Arrange
        task_id = "test-task-id"
        self.agent.active_tasks = {
            task_id: {"cancelled": False, "state": {}}
        }
        
        # Act
        result = await self.agent.cancel(task_id)
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(self.agent.active_tasks[task_id]["cancelled"])
    
    async def test_cancel_nonexistent_task(self):
        """Test cancellation of a nonexistent task."""
        # Act
        result = await self.agent.cancel("nonexistent-task-id")
        
        # Assert
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
