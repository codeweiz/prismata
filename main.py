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
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_agent.agent.base_agent import AgentRequest
from core_agent.agent.langgraph_agent import LangGraphAgent
from communication.transport.websocket_transport import WebSocketTransport
from shared.utils.logging_utils import setup_logger


async def handle_generate_code(params):
    """Handle generate_code method."""
    prompt = params.get("prompt", "")
    context = params.get("context")
    language = params.get("language", "python")
    options = params.get("options", {})

    # Create a request for the agent
    request = AgentRequest(
        task_type="generate_code",
        inputs={
            "prompt": prompt,
            "context": context,
            "language": language,
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

    # Register method handlers
    transport.register_method_handler("generate_code", handle_generate_code)
    transport.register_method_handler("analyze_code", handle_analyze_code)
    transport.register_method_handler("read_file", handle_read_file)
    transport.register_method_handler("get_file_metadata", handle_get_file_metadata)
    transport.register_method_handler("write_file", handle_write_file)
    transport.register_method_handler("confirm_write_file", handle_confirm_write_file)

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
