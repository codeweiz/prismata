"""
LangGraph Agent implementation.

This module implements an agent using LangChain and LangGraph for multi-step reasoning.
"""

import uuid
from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from langgraph.graph import StateGraph, START, END

from core_agent.agent.base_agent import AgentRequest, AgentResponse, BaseAgent
from core_agent.agent.state_models import AgentState
from core_agent.tools.file_tools import ReadFileTool, GetFileMetadataTool
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LangGraphAgent(BaseAgent):
    """Agent implementation using LangChain and LangGraph."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LangGraph agent."""
        super().__init__(config)
        logger.info("Initializing LangGraph agent")
        self.tools = self._initialize_tools()
        self.workflow = self._build_workflow()
        self.active_tasks = {}  # Store active tasks for cancellation
        logger.debug(f"Agent initialized with config: {config}")

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize the tools used by the agent."""
        logger.info("Initializing agent tools")
        tools = [
            ReadFileTool(),
            GetFileMetadataTool()
        ]
        logger.debug(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")
        return tools

    def _build_workflow(self) -> StateGraph:
        """Build the agent workflow using LangGraph."""
        # This is a placeholder for the actual workflow implementation
        workflow = StateGraph(state_schema=AgentState)

        # Define nodes (these would be actual functions in a real implementation)
        workflow.add_node("understand_request", lambda x: x)
        workflow.add_node("analyze_context", lambda x: x)
        workflow.add_node("plan_changes", lambda x: x)
        workflow.add_node("execute_changes", lambda x: x)
        workflow.add_node("verify_results", lambda x: x)

        # Define edges
        workflow.add_edge(START, "understand_request")
        workflow.add_edge("understand_request", "analyze_context")
        workflow.add_edge("analyze_context", "plan_changes")
        workflow.add_edge("plan_changes", "execute_changes")
        workflow.add_edge("execute_changes", "verify_results")

        # Add conditional edges (simplified for example)
        workflow.add_conditional_edges(
            "verify_results",
            lambda state: "success" if state.verification_passed else "retry",
            {
                "success": END,
                "retry": "plan_changes"
            }
        )

        return workflow.compile()

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute the agent task using the LangGraph workflow."""
        task_id = str(uuid.uuid4())
        logger.info(f"Executing task {task_id} of type {request.task_type}")

        try:
            # Initialize the state with the request
            initial_state = {
                "task_id": task_id,
                "task_type": request.task_type,
                "inputs": request.inputs,
                "context": request.context or {},
                "status": "in_progress",
                "results": None,
                "changes": None,
                "error": None
            }

            logger.debug(f"Initial state for task {task_id}: {initial_state}")

            # Store the task for potential cancellation
            self.active_tasks[task_id] = {
                "state": initial_state,
                "cancelled": False
            }

            # Execute the workflow
            logger.info(f"Starting workflow execution for task {task_id}")
            final_state = await self.workflow.ainvoke(initial_state)
            logger.debug(f"Final state for task {task_id}: {final_state}")

            # Check if the task was cancelled
            if self.active_tasks[task_id]["cancelled"]:
                logger.info(f"Task {task_id} was cancelled")
                return AgentResponse(
                    task_id=task_id,
                    status="cancelled",
                    error="Task was cancelled"
                )

            # Prepare the response
            response = AgentResponse(
                task_id=task_id,
                status=final_state.get("status", "completed"),
                results=final_state.get("results"),
                requires_user_confirmation=final_state.get("requires_confirmation", False),
                preview=final_state.get("preview"),
                changes=final_state.get("changes"),
                error=final_state.get("error")
            )

            # Clean up
            del self.active_tasks[task_id]

            logger.info(f"Task {task_id} completed with status: {response.status}")
            return response

        except Exception as e:
            # Handle exceptions
            logger.exception(f"Error executing task {task_id}: {str(e)}")
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            return AgentResponse(
                task_id=task_id,
                status="error",
                error=str(e)
            )

    async def cancel(self, task_id: str) -> bool:
        """Cancel an ongoing task."""
        if task_id in self.active_tasks:
            logger.info(f"Cancelling task {task_id}")
            self.active_tasks[task_id]["cancelled"] = True
            return True
        logger.warning(f"Attempted to cancel non-existent task {task_id}")
        return False
