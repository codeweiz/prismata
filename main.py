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

from core_agent.agent.langgraph_agent import LangGraphAgent
from communication.transport.websocket_transport import WebSocketTransport


async def handle_generate_code(params):
    """Handle generate_code method."""
    prompt = params.get("prompt", "")
    context = params.get("context")
    language = params.get("language", "python")
    options = params.get("options", {})
    
    # This is a placeholder implementation
    # In a real implementation, this would call the agent
    return {
        "code": f"# Generated code for: {prompt}\n\ndef example_function():\n    # TODO: Implement based on prompt\n    pass",
        "explanation": "This is a placeholder implementation.",
        "language": language
    }


async def handle_analyze_code(params):
    """Handle analyze_code method."""
    file_path = params.get("file_path", "")
    content = params.get("content", "")
    
    # This is a placeholder implementation
    # In a real implementation, this would call the agent
    return {
        "file_path": file_path,
        "language": "python",
        "symbols": [
            {
                "name": "example_function",
                "kind": 12,  # Function
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 2, "character": 8}
                },
                "selection_range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 16}
                },
                "detail": "Example function"
            }
        ],
        "imports": []
    }


async def main(host: str = "localhost", port: int = 8765, log_level: str = "INFO"):
    """
    Start the Prismata Agent service.
    
    Args:
        host: The host to bind to.
        port: The port to listen on.
        log_level: The logging level.
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create the agent
    agent = LangGraphAgent()
    
    # Create the transport
    transport = WebSocketTransport(host=host, port=port)
    
    # Register method handlers
    transport.register_method_handler("generate_code", handle_generate_code)
    transport.register_method_handler("analyze_code", handle_analyze_code)
    
    # Start the transport
    await transport.start()
    
    # Keep the server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        await transport.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prismata Agent Service")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    
    args = parser.parse_args()
    
    asyncio.run(main(host=args.host, port=args.port, log_level=args.log_level))
