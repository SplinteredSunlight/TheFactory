"""
Mock MCP Server module for testing.

This module provides mock implementations of MCP Server classes and functions
for testing purposes.
"""

class Server:
    """Mock MCP Server class."""
    
    def __init__(self, info, config):
        """Initialize a new Server."""
        self.info = info
        self.config = config
        self._request_handlers = {}
        self.tool_handlers = {}
        self.onerror = None
    
    def set_request_handler(self, schema, handler):
        """Set a request handler."""
        self._request_handlers[schema.__name__] = handler
    
    async def connect(self, transport):
        """Connect to a transport."""
        pass
    
    async def close(self):
        """Close the server."""
        pass
