"""
Tests for WebSocket transport.

This module contains tests for the WebSocket transport.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from communication.transport.websocket_transport import WebSocketTransport


# Create an async mock for websockets.serve
async def async_mock_serve(*args, **kwargs):
    # Create a mock server with an async wait_closed method
    mock_server = MagicMock()
    mock_server.wait_closed = AsyncMock()
    return mock_server


class TestWebSocketTransport(unittest.TestCase):
    """Test case for WebSocket transport."""

    def setUp(self):
        """Set up the test case."""
        self.transport = WebSocketTransport(host="localhost", port=8765)
        self.handler = AsyncMock()
        self.transport.register_method_handler("test_method", self.handler)

    async def async_test_start_stop(self):
        """Test starting and stopping the transport."""
        # Patch websockets.serve
        with patch("websockets.serve", side_effect=async_mock_serve) as mock_serve:
            # The mock server is already created in async_mock_serve

            # Start the transport
            await self.transport.start()
            mock_serve.assert_called_once_with(
                self.transport._handle_client,
                "localhost",
                8765
            )

            # Stop the transport
            await self.transport.stop()
            # Get the server from the transport
            server = self.transport.server
            server.close.assert_called_once()
            server.wait_closed.assert_called_once()

    def test_start_stop(self):
        """Run the async test for starting and stopping the transport."""
        asyncio.run(self.async_test_start_stop())

    async def async_test_handle_request(self):
        """Test handling a request."""
        # Patch websockets.serve
        with patch("websockets.serve", side_effect=async_mock_serve) as mock_serve:
            # The mock server is already created in async_mock_serve

            # Start the transport
            await self.transport.start()

            # Create a request
            request_data = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "test_method",
                "params": {"param1": "value1"}
            }

            # Set up the handler to return a result
            self.handler.return_value = {"result": "success"}

            # Handle the request
            response_data = await self.transport.handle_request(request_data)

            # Check the response
            self.assertEqual(response_data["jsonrpc"], "2.0")
            self.assertEqual(response_data["id"], "1")
            self.assertEqual(response_data["result"], {"result": "success"})

            # Check that the handler was called with the correct parameters
            self.handler.assert_called_once_with({"param1": "value1"})

            # Stop the transport
            await self.transport.stop()

    def test_handle_request(self):
        """Run the async test for handling a request."""
        asyncio.run(self.async_test_handle_request())

    async def async_test_handle_request_method_not_found(self):
        """Test handling a request with a method that doesn't exist."""
        # Patch websockets.serve
        with patch("websockets.serve", side_effect=async_mock_serve) as mock_serve:
            # The mock server is already created in async_mock_serve

            # Start the transport
            await self.transport.start()

            # Create a request with a non-existent method
            request_data = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "non_existent_method",
                "params": {"param1": "value1"}
            }

            # Handle the request
            response_data = await self.transport.handle_request(request_data)

            # Check the response
            self.assertEqual(response_data["jsonrpc"], "2.0")
            self.assertEqual(response_data["id"], "1")
            self.assertIn("error", response_data)
            self.assertEqual(response_data["error"]["code"], -32601)  # Method not found

            # Stop the transport
            await self.transport.stop()

    def test_handle_request_method_not_found(self):
        """Run the async test for handling a request with a method that doesn't exist."""
        asyncio.run(self.async_test_handle_request_method_not_found())


if __name__ == "__main__":
    unittest.main()
