"""
Base transport implementation.

This module defines the base transport class that all specific transports will inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from communication.protocol import JsonRpcRequest, JsonRpcResponse


class BaseTransport(ABC):
    """Base class for all transport implementations."""
    
    def __init__(self):
        """Initialize the transport."""
        self.handlers = {}
    
    def register_method_handler(self, method: str, handler: Callable):
        """
        Register a handler for a specific method.
        
        Args:
            method: The method name to handle.
            handler: The handler function that will process requests for this method.
        """
        self.handlers[method] = handler
    
    @abstractmethod
    async def start(self):
        """Start the transport server."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the transport server."""
        pass
    
    @abstractmethod
    async def send_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """
        Send a request to the server.
        
        Args:
            request: The JSON-RPC request to send.
            
        Returns:
            The JSON-RPC response from the server.
        """
        pass
    
    @abstractmethod
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming request.
        
        Args:
            request_data: The raw request data.
            
        Returns:
            The response data to send back.
        """
        pass
