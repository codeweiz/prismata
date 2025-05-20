"""
WebSocket transport implementation.

This module implements the transport layer using WebSockets.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from communication.protocol import (ErrorCode, JsonRpcError, JsonRpcRequest,
                                   JsonRpcResponse)
from communication.transport.base_transport import BaseTransport

logger = logging.getLogger(__name__)


class WebSocketTransport(BaseTransport):
    """WebSocket transport implementation."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the WebSocket transport.
        
        Args:
            host: The host to bind to.
            port: The port to listen on.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
    
    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """
        Handle a client connection.
        
        Args:
            websocket: The WebSocket connection.
            path: The connection path.
        """
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    request_data = json.loads(message)
                    response_data = await self.handle_request(request_data)
                    await websocket.send(json.dumps(response_data))
                except json.JSONDecodeError:
                    error_response = JsonRpcResponse(
                        jsonrpc="2.0",
                        id=None,
                        error=JsonRpcError(
                            code=ErrorCode.PARSE_ERROR,
                            message="Invalid JSON"
                        ).dict()
                    )
                    await websocket.send(json.dumps(error_response.dict()))
                except Exception as e:
                    logger.exception("Error handling message")
                    error_response = JsonRpcResponse(
                        jsonrpc="2.0",
                        id=None,
                        error=JsonRpcError(
                            code=ErrorCode.INTERNAL_ERROR,
                            message=str(e)
                        ).dict()
                    )
                    await websocket.send(json.dumps(error_response.dict()))
        finally:
            self.clients.remove(websocket)
    
    async def send_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """
        Send a request to a connected client.
        
        This is a simplified implementation that would need to be expanded
        for a real-world scenario with multiple clients and request routing.
        
        Args:
            request: The JSON-RPC request to send.
            
        Returns:
            The JSON-RPC response from the client.
        """
        if not self.clients:
            raise RuntimeError("No clients connected")
        
        # In a real implementation, you would need to route to the correct client
        client = next(iter(self.clients))
        
        request_data = json.dumps(request.dict())
        await client.send(request_data)
        
        response_data = await client.recv()
        response = JsonRpcResponse.parse_raw(response_data)
        
        return response
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming request.
        
        Args:
            request_data: The raw request data.
            
        Returns:
            The response data to send back.
        """
        try:
            request = JsonRpcRequest(**request_data)
            
            if request.method not in self.handlers:
                return JsonRpcResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error=JsonRpcError(
                        code=ErrorCode.METHOD_NOT_FOUND,
                        message=f"Method '{request.method}' not found"
                    ).dict()
                ).dict()
            
            handler = self.handlers[request.method]
            result = await handler(request.params)
            
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request.id,
                result=result
            ).dict()
            
        except Exception as e:
            logger.exception("Error handling request")
            return JsonRpcResponse(
                jsonrpc="2.0",
                id=request_data.get("id", None),
                error=JsonRpcError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=str(e)
                ).dict()
            ).dict()
