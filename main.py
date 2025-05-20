#!/usr/bin/env python3
"""
Prismata Agent Service Entry Point.

This script starts the Prismata Agent service with the specified transport.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any, List

import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_agent.agent.base_agent import AgentRequest
from core_agent.agent.langgraph_agent import LangGraphAgent
from core_agent.error.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from core_agent.error.recovery_service import RecoveryService
from communication.transport.websocket_transport import WebSocketTransport
from shared.utils.logging_utils import setup_logger


async def handle_generate_code(params):
    """Handle generate_code method."""
    prompt = params.get("prompt", "")
    context = params.get("context")
    language = params.get("language", "python")
    file_path = params.get("file_path")
    options = params.get("options", {})

    # Extract context-related options
    use_project_context = options.get("use_project_context", True)
    max_context_files = options.get("max_context_files", 3)

    # Create a request for the agent
    request = AgentRequest(
        task_type="generate_code",
        inputs={
            "prompt": prompt,
            "context": context,
            "language": language,
            "file_path": file_path,
            "use_project_context": use_project_context,
            "max_context_files": max_context_files,
            "options": options
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_analyze_code(params):
    """Handle analyze_code method."""
    file_path = params.get("file_path", "")
    content = params.get("content", "")
    language = params.get("language", "python")

    # Create a request for the agent
    request = AgentRequest(
        task_type="analyze_code",
        inputs={
            "file_path": file_path,
            "content": content,
            "language": language
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_refactor_code(params):
    """Handle refactor_code method."""
    refactoring_type = params.get("refactoring_type", "")
    file_paths = params.get("file_paths", [])
    target_symbol = params.get("target_symbol")
    new_name = params.get("new_name")
    selection = params.get("selection")
    options = params.get("options", {})

    # Create a request for the agent
    request = AgentRequest(
        task_type="refactor_code",
        inputs={
            "refactoring_type": refactoring_type,
            "file_paths": file_paths,
            "target_symbol": target_symbol,
            "new_name": new_name,
            "selection": selection,
            "options": options
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_complete_code(params):
    """Handle complete_code method."""
    file_path = params.get("file_path", "")
    position = params.get("position", {"line": 0, "character": 0})
    prefix = params.get("prefix")
    context = params.get("context")
    options = params.get("options", {})

    # Create a request for the agent
    request = AgentRequest(
        task_type="complete_code",
        inputs={
            "file_path": file_path,
            "position": position,
            "prefix": prefix,
            "context": context,
            "options": options
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_analyze_cross_file_dependencies(params):
    """Handle analyze_cross_file_dependencies method."""
    file_paths = params.get("file_paths", [])
    content_map = params.get("content_map")
    options = params.get("options", {})

    # Create a request for the agent
    request = AgentRequest(
        task_type="analyze_cross_file_dependencies",
        inputs={
            "file_paths": file_paths,
            "content_map": content_map,
            "options": options
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_read_file(params):
    """Handle read_file method."""
    file_path = params.get("file_path", "")
    encoding = params.get("encoding", "utf-8")
    base_dir = params.get("base_dir")

    # Create a request for the agent
    request = AgentRequest(
        task_type="read_file",
        inputs={
            "file_path": file_path,
            "encoding": encoding,
            "base_dir": base_dir
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_get_file_metadata(params):
    """Handle get_file_metadata method."""
    file_path = params.get("file_path", "")
    base_dir = params.get("base_dir")

    # Create a request for the agent
    request = AgentRequest(
        task_type="get_file_metadata",
        inputs={
            "file_path": file_path,
            "base_dir": base_dir
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_write_file(params):
    """Handle write_file method."""
    file_path = params.get("file_path", "")
    content = params.get("content", "")
    encoding = params.get("encoding", "utf-8")
    base_dir = params.get("base_dir")
    create_backup = params.get("create_backup", True)

    # Create a request for the agent
    request = AgentRequest(
        task_type="write_file",
        inputs={
            "file_path": file_path,
            "content": content,
            "encoding": encoding,
            "base_dir": base_dir,
            "create_backup": create_backup,
            "requires_confirmation": True
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def handle_confirm_write_file(params):
    """Handle confirm_write_file method."""
    file_path = params.get("file_path", "")
    content = params.get("content", "")
    encoding = params.get("encoding", "utf-8")
    base_dir = params.get("base_dir")
    create_backup = params.get("create_backup", True)

    # Create a request for the agent
    request = AgentRequest(
        task_type="confirm_write_file",
        inputs={
            "file_path": file_path,
            "content": content,
            "encoding": encoding,
            "base_dir": base_dir,
            "create_backup": create_backup
        }
    )

    # Execute the request
    response = await agent.execute(request)

    # Check for errors
    if response.status == "error":
        raise Exception(response.error)

    # Return the results
    return response.results


async def main(host: str = "localhost", port: int = 8765, log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Start the Prismata Agent service.

    Args:
        host: The host to bind to.
        port: The port to listen on.
        log_level: The logging level.
        log_file: Optional path to a log file.
    """
    # Configure logging
    logger = setup_logger(
        "prismata",
        level=log_level,
        log_file=log_file,
        log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info(f"Starting Prismata Agent service on {host}:{port}")

    # Create the agent
    agent = LangGraphAgent()

    # Create the transport
    transport = WebSocketTransport(host=host, port=port)

    # Initialize recovery service
    recovery_service = RecoveryService(history_file=".prismata/operation_history.json")

    # Error handling and recovery endpoints
    async def handle_get_operation_history(params):
        """Handle get_operation_history method."""
        operation_type = params.get("operation_type")
        status = params.get("status")
        limit = params.get("limit", 100)
        offset = params.get("offset", 0)

        operations = recovery_service.get_operations(
            operation_type=operation_type,
            status=status,
            limit=limit,
            offset=offset
        )

        return {
            "operations": [op.to_dict() for op in operations],
            "total": len(operations),
            "limit": limit,
            "offset": offset
        }

    async def handle_get_operation(params):
        """Handle get_operation method."""
        operation_id = params.get("operation_id")

        if not operation_id:
            raise ValueError("operation_id is required")

        try:
            operation = recovery_service.get_operation(operation_id)
            return operation.to_dict()
        except ValueError as e:
            raise Exception(str(e))

    async def handle_retry_operation(params):
        """Handle retry_operation method."""
        operation_id = params.get("operation_id")

        if not operation_id:
            raise ValueError("operation_id is required")

        try:
            result = recovery_service.retry_operation(operation_id)
            return {
                "success": True,
                "operation_id": operation_id,
                "result": result
            }
        except Exception as e:
            error_info = ErrorHandler.handle_exception(
                exception=e,
                message=f"Error retrying operation {operation_id}: {str(e)}",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                details={
                    "operation_id": operation_id,
                    "stack_trace": traceback.format_exc()
                }
            )

            return {
                "success": False,
                "operation_id": operation_id,
                "error": error_info.to_dict()
            }

    async def handle_recover_operation(params):
        """Handle recover_operation method."""
        operation_id = params.get("operation_id")
        strategy_name = params.get("strategy_name")

        if not operation_id:
            raise ValueError("operation_id is required")

        if not strategy_name:
            raise ValueError("strategy_name is required")

        try:
            result = recovery_service.recover_operation(operation_id, strategy_name)
            return {
                "success": True,
                "operation_id": operation_id,
                "strategy_name": strategy_name,
                "result": result
            }
        except Exception as e:
            error_info = ErrorHandler.handle_exception(
                exception=e,
                message=f"Error recovering operation {operation_id} with strategy {strategy_name}: {str(e)}",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                details={
                    "operation_id": operation_id,
                    "strategy_name": strategy_name,
                    "stack_trace": traceback.format_exc()
                }
            )

            return {
                "success": False,
                "operation_id": operation_id,
                "strategy_name": strategy_name,
                "error": error_info.to_dict()
            }

    # Register method handlers
    transport.register_method_handler("generate_code", handle_generate_code)
    transport.register_method_handler("analyze_code", handle_analyze_code)
    transport.register_method_handler("analyze_cross_file_dependencies", handle_analyze_cross_file_dependencies)
    transport.register_method_handler("refactor_code", handle_refactor_code)
    transport.register_method_handler("complete_code", handle_complete_code)
    transport.register_method_handler("read_file", handle_read_file)
    transport.register_method_handler("get_file_metadata", handle_get_file_metadata)
    transport.register_method_handler("write_file", handle_write_file)
    transport.register_method_handler("confirm_write_file", handle_confirm_write_file)

    # Register error handling and recovery endpoints
    transport.register_method_handler("get_operation_history", handle_get_operation_history)
    transport.register_method_handler("get_operation", handle_get_operation)
    transport.register_method_handler("retry_operation", handle_retry_operation)
    transport.register_method_handler("recover_operation", handle_recover_operation)

    # Start the transport
    await transport.start()

    # Keep the server running
    try:
        logger.info("Agent service is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await transport.stop()
        logger.info("Agent service stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prismata Agent Service")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("--log-file", help="Path to log file")

    args = parser.parse_args()

    asyncio.run(main(host=args.host, port=args.port, log_level=args.log_level, log_file=args.log_file))
