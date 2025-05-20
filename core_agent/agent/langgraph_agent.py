"""
LangGraph Agent implementation.

This module implements an agent using LangChain and LangGraph for multi-step reasoning.
"""

import uuid
import datetime
from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from langchain.llms.base import BaseLLM
from langgraph.graph import StateGraph, START, END

from core_agent.agent.base_agent import AgentRequest, AgentResponse, BaseAgent
from core_agent.agent.state_models import AgentState
from core_agent.agent.workflow_nodes import understand_request, analyze_context, plan_changes, execute_changes, verify_results
from core_agent.tools.file_tools import ReadFileTool, GetFileMetadataTool
from core_agent.tools.code_tools import GenerateCodeTool, AnalyzeCodeTool
from core_agent.tools.write_file_tool import WriteFileTool, ConfirmWriteFileTool
from core_agent.llm.llm_service import LLMService
from core_agent.llm.default_config import DEFAULT_LLM_SERVICE_CONFIG
from shared.models.history import HistoryManager, HistoryEntry, OperationType, OperationStatus, OperationRecord
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LangGraphAgent(BaseAgent):
    """Agent implementation using LangChain and LangGraph."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LangGraph agent."""
        super().__init__(config)
        logger.info("Initializing LangGraph agent")

        # Initialize LLM service
        llm_config = config.get("llm_config") if config else None
        self.llm_service = LLMService(llm_config or DEFAULT_LLM_SERVICE_CONFIG)

        # Initialize tools
        self.tools = self._initialize_tools()

        # Initialize workflow
        self.workflow = self._build_workflow()

        # Initialize history manager
        self.history_manager = HistoryManager(max_entries=100)

        # Store active tasks for cancellation
        self.active_tasks = {}

        logger.debug(f"Agent initialized with config: {config}")

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize the tools used by the agent."""
        logger.info("Initializing agent tools")
        tools = [
            ReadFileTool(),
            GetFileMetadataTool(),
            GenerateCodeTool(self.llm_service),
            AnalyzeCodeTool(self.llm_service),
            WriteFileTool(),
            ConfirmWriteFileTool()
        ]
        logger.debug(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")
        return tools

    def _build_workflow(self) -> StateGraph:
        """Build the agent workflow using LangGraph."""
        workflow = StateGraph(state_schema=AgentState)

        # Get the LLM from the service
        llm = self.llm_service.llm

        # Define nodes with actual implementations
        workflow.add_node("understand_request", lambda state: understand_request(state, llm))
        workflow.add_node("analyze_context", lambda state: analyze_context(state, llm))
        workflow.add_node("plan_changes", lambda state: plan_changes(state, llm))
        workflow.add_node("execute_changes", lambda state: execute_changes(state, self.tools))
        workflow.add_node("verify_results", lambda state: verify_results(state, llm))

        # Define edges
        workflow.add_edge(START, "understand_request")
        workflow.add_edge("understand_request", "analyze_context")
        workflow.add_edge("analyze_context", "plan_changes")
        workflow.add_edge("plan_changes", "execute_changes")
        workflow.add_edge("execute_changes", "verify_results")

        # Add conditional edges
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

            # Record the operation in history
            self._record_operation(task_id, request.task_type, request.inputs, final_state)

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

            # Record the cancellation in history
            self._record_cancellation(task_id)

            return True
        logger.warning(f"Attempted to cancel non-existent task {task_id}")
        return False

    def _record_operation(self, task_id: str, task_type: str, inputs: Dict[str, Any], final_state: Dict[str, Any]) -> None:
        """
        Record an operation in the history.

        Args:
            task_id: The ID of the task.
            task_type: The type of task.
            inputs: The inputs to the task.
            final_state: The final state of the task.
        """
        try:
            # Determine the operation type
            operation_type = OperationType.CUSTOM
            if task_type == "generate_code":
                operation_type = OperationType.GENERATE_CODE
            elif task_type == "analyze_code":
                operation_type = OperationType.ANALYZE_CODE
            elif task_type == "write_file":
                operation_type = OperationType.WRITE_FILE
            elif task_type == "read_file":
                operation_type = OperationType.READ_FILE

            # Determine the operation status
            status = OperationStatus.SUCCESS
            if final_state.get("status") == "error":
                status = OperationStatus.FAILURE
            elif final_state.get("status") == "cancelled":
                status = OperationStatus.CANCELLED

            # Create the operation record
            operation = OperationRecord(
                id=task_id,
                type=operation_type,
                timestamp=datetime.datetime.now(),
                status=status,
                params=inputs,
                result=final_state.get("results"),
                error=final_state.get("error")
            )

            # Create the history entry
            entry = HistoryEntry(
                id=task_id,
                timestamp=datetime.datetime.now(),
                operation=operation,
                description=f"{task_type} operation",
                can_undo=False  # For now, we don't support undo
            )

            # Add the entry to the history
            self.history_manager.add_entry(entry)

        except Exception as e:
            logger.error(f"Error recording operation in history: {str(e)}")

    def _record_cancellation(self, task_id: str) -> None:
        """
        Record a task cancellation in the history.

        Args:
            task_id: The ID of the task.
        """
        try:
            # Get the existing entry if it exists
            entry = self.history_manager.get_entry(task_id)
            if entry:
                # Update the operation status
                entry.operation.status = OperationStatus.CANCELLED

        except Exception as e:
            logger.error(f"Error recording cancellation in history: {str(e)}")
