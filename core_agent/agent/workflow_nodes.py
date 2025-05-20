"""
Workflow nodes for the LangGraph agent.

This module implements the nodes used in the LangGraph workflow.
"""

import traceback
from typing import Any, List

from langchain.llms.base import BaseLLM

from core_agent.agent.state_models import AgentState
from core_agent.error.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from core_agent.error.exceptions import ToolException, WorkflowException
from core_agent.error.recovery_service import RecoveryService
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)


def understand_request(state: AgentState, llm: BaseLLM) -> AgentState:
    """
    Understand the user's request.

    Args:
        state: The current state.
        llm: The LLM to use.

    Returns:
        The updated state.
    """
    logger.info(f"Understanding request for task {state.task_id}")

    # Extract the task type and inputs
    task_type = state.task_type
    inputs = state.inputs

    # Log the task details
    logger.debug(f"Task type: {task_type}")
    logger.debug(f"Inputs: {inputs}")

    # Update the state with the understood request
    state.status = "understanding_request"

    # For now, just pass through the inputs
    # In a real implementation, this would use the LLM to understand the request

    return state


def analyze_context(state: AgentState, llm: BaseLLM) -> AgentState:
    """
    Analyze the context for the task.

    Args:
        state: The current state.
        llm: The LLM to use.

    Returns:
        The updated state.
    """
    logger.info(f"Analyzing context for task {state.task_id}")

    # Extract the task type and inputs
    task_type = state.task_type
    inputs = state.inputs
    context = state.context

    # Update the state with the analyzed context
    state.status = "analyzing_context"

    # For now, just pass through the context
    # In a real implementation, this would use the LLM to analyze the context

    return state


def plan_changes(state: AgentState, llm: BaseLLM) -> AgentState:
    """
    Plan the changes to make.

    Args:
        state: The current state.
        llm: The LLM to use.

    Returns:
        The updated state.
    """
    logger.info(f"Planning changes for task {state.task_id}")

    # Extract the task type and inputs
    task_type = state.task_type
    inputs = state.inputs

    # Update the state with the planned changes
    state.status = "planning_changes"

    # For now, just create a simple plan
    # In a real implementation, this would use the LLM to plan the changes

    if task_type == "generate_code":
        state.changes = {
            "type": "code_generation",
            "prompt": inputs.get("prompt", ""),
            "language": inputs.get("language", "python"),
            "context": inputs.get("context"),
            "file_path": inputs.get("file_path"),
            "use_project_context": inputs.get("use_project_context", True),
            "max_context_files": inputs.get("max_context_files", 3),
            "options": inputs.get("options", {})
        }
    elif task_type == "analyze_code":
        state.changes = {
            "type": "code_analysis",
            "file_path": inputs.get("file_path", ""),
            "content": inputs.get("content", ""),
            "language": inputs.get("language", "python")
        }
    elif task_type == "analyze_cross_file_dependencies":
        state.changes = {
            "type": "cross_file_analysis",
            "file_paths": inputs.get("file_paths", []),
            "content_map": inputs.get("content_map"),
            "options": inputs.get("options", {})
        }
    elif task_type == "refactor_code":
        state.changes = {
            "type": "code_refactoring",
            "refactoring_type": inputs.get("refactoring_type", ""),
            "file_paths": inputs.get("file_paths", []),
            "target_symbol": inputs.get("target_symbol"),
            "new_name": inputs.get("new_name"),
            "selection": inputs.get("selection"),
            "options": inputs.get("options", {})
        }
    elif task_type == "complete_code":
        state.changes = {
            "type": "code_completion",
            "file_path": inputs.get("file_path", ""),
            "position": inputs.get("position", {"line": 0, "character": 0}),
            "prefix": inputs.get("prefix"),
            "context": inputs.get("context"),
            "options": inputs.get("options", {})
        }
    elif task_type == "write_file":
        state.changes = {
            "type": "file_write",
            "file_path": inputs.get("file_path", ""),
            "content": inputs.get("content", ""),
            "encoding": inputs.get("encoding", "utf-8"),
            "requires_confirmation": True
        }

    return state


# Initialize recovery service
recovery_service = RecoveryService(history_file=".prismata/operation_history.json")


def execute_changes(state: AgentState, tools: List[Any]) -> AgentState:
    """
    Execute the planned changes.

    Args:
        state: The current state.
        tools: The tools to use.

    Returns:
        The updated state.
    """
    logger.info(f"Executing changes for task {state.task_id}")

    # Extract the changes
    changes = state.changes

    if not changes:
        logger.warning(f"No changes to execute for task {state.task_id}")
        state.status = "completed"
        state.results = {"message": "No changes to execute"}
        return state

    # Update the state
    state.status = "executing_changes"

    # Execute the changes based on the type
    change_type = changes.get("type")

    # Create operation record
    operation = recovery_service.create_operation(
        operation_type=change_type,
        inputs=changes,
        metadata={
            "task_id": state.task_id,
            "task_type": state.task_type
        }
    )

    # Start operation
    recovery_service.start_operation(operation.operation_id)

    try:
        if change_type == "code_generation":
            # Find the generate_code tool
            generate_code_tool = next((tool for tool in tools if tool.name == "generate_code"), None)

            if not generate_code_tool:
                raise ValueError("generate_code tool not found")

            # Execute the tool
            result = generate_code_tool._run(
                prompt=changes.get("prompt", ""),
                language=changes.get("language", "python"),
                context=changes.get("context"),
                file_path=changes.get("file_path"),
                position=changes.get("position"),
                options=changes.get("options", {}),
                use_project_context=changes.get("use_project_context", True),
                max_context_files=changes.get("max_context_files", 3)
            )

            # Update the state with the results
            state.results = result
            state.status = "completed"

        elif change_type == "code_analysis":
            # Find the analyze_code tool
            analyze_code_tool = next((tool for tool in tools if tool.name == "analyze_code"), None)

            if not analyze_code_tool:
                raise ValueError("analyze_code tool not found")

            # Execute the tool
            result = analyze_code_tool._run(
                code=changes.get("content", ""),
                language=changes.get("language", "python"),
                file_path=changes.get("file_path")
            )

            # Update the state with the results
            state.results = result
            state.status = "completed"

        elif change_type == "cross_file_analysis":
            # Find the cross_file_analysis tool
            cross_file_analysis_tool = next((tool for tool in tools if tool.name == "cross_file_analysis"), None)

            if not cross_file_analysis_tool:
                raise ValueError("cross_file_analysis tool not found")

            # Execute the tool
            result = cross_file_analysis_tool._run(
                file_paths=changes.get("file_paths", []),
                content_map=changes.get("content_map"),
                options=changes.get("options", {})
            )

            # Update the state with the results
            state.results = result
            state.status = "completed"

        elif change_type == "code_refactoring":
            # Find the refactor_code tool
            refactor_code_tool = next((tool for tool in tools if tool.name == "refactor_code"), None)

            if not refactor_code_tool:
                raise ValueError("refactor_code tool not found")

            # Execute the tool
            result = refactor_code_tool._run(
                refactoring_type=changes.get("refactoring_type", ""),
                file_paths=changes.get("file_paths", []),
                target_symbol=changes.get("target_symbol"),
                new_name=changes.get("new_name"),
                selection=changes.get("selection"),
                options=changes.get("options", {})
            )

            # Update the state with the results
            state.results = result
            state.status = "completed"

        elif change_type == "code_completion":
            # Find the code_completion tool
            code_completion_tool = next((tool for tool in tools if tool.name == "code_completion"), None)

            if not code_completion_tool:
                raise ValueError("code_completion tool not found")

            # Execute the tool
            result = code_completion_tool._run(
                file_path=changes.get("file_path", ""),
                position=changes.get("position", {"line": 0, "character": 0}),
                prefix=changes.get("prefix"),
                context=changes.get("context"),
                options=changes.get("options", {})
            )

            # Update the state with the results
            state.results = result
            state.status = "completed"

        elif change_type == "file_write":
            # Find the write_file tool
            write_file_tool = next((tool for tool in tools if tool.name == "write_file"), None)

            if not write_file_tool:
                raise ValueError("write_file tool not found")

            # Execute the tool
            result = write_file_tool._run(
                file_path=changes.get("file_path", ""),
                content=changes.get("content", ""),
                encoding=changes.get("encoding", "utf-8"),
                requires_confirmation=changes.get("requires_confirmation", True)
            )

            # Update the state with the results
            state.results = result
            state.status = "completed" if not result.get("requires_confirmation") else "awaiting_confirmation"
            state.requires_confirmation = result.get("requires_confirmation", False)
            state.preview = result.get("preview")

        else:
            logger.warning(f"Unknown change type: {change_type}")
            state.status = "error"
            state.error = f"Unknown change type: {change_type}"

    except Exception as e:
        logger.exception(f"Error executing changes: {str(e)}")

        # Create error info
        if isinstance(e, ToolException):
            error_category = ErrorCategory.TOOL
        elif isinstance(e, WorkflowException):
            error_category = ErrorCategory.WORKFLOW
        elif isinstance(e, ValueError) or isinstance(e, TypeError):
            error_category = ErrorCategory.VALIDATION
        else:
            error_category = ErrorCategory.UNKNOWN

        error_info = ErrorHandler.handle_exception(
            exception=e,
            message=f"Error executing {change_type} operation: {str(e)}",
            category=error_category,
            severity=ErrorSeverity.ERROR,
            details={
                "change_type": change_type,
                "changes": changes,
                "stack_trace": traceback.format_exc()
            },
            operation_id=operation.operation_id
        )

        # Update operation record
        recovery_service.fail_operation(operation.operation_id, error_info)

        # Update state
        state.status = "error"
        state.error = error_info.to_dict()
        return state

    # Complete operation
    recovery_service.complete_operation(operation.operation_id, state.results or {})

    return state


def verify_results(state: AgentState, llm: BaseLLM) -> AgentState:
    """
    Verify the results of the changes.

    Args:
        state: The current state.
        llm: The LLM to use.

    Returns:
        The updated state.
    """
    logger.info(f"Verifying results for task {state.task_id}")

    # Extract the results
    results = state.results

    if not results:
        logger.warning(f"No results to verify for task {state.task_id}")
        state.verification_passed = False
        return state

    # Update the state
    state.status = "verifying_results"

    # For now, just assume verification passes
    # In a real implementation, this would use the LLM to verify the results

    state.verification_passed = True

    return state
