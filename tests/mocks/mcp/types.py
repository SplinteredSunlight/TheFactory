"""
Mock MCP types module for testing.

This module provides mock implementations of MCP types classes and functions
for testing purposes.
"""

class CallToolRequestSchema:
    """Mock CallToolRequestSchema class."""
    __name__ = "CallToolRequestSchema"

class ErrorCode:
    """Mock ErrorCode class."""
    InvalidRequest = "InvalidRequest"
    InvalidParams = "InvalidParams"
    MethodNotFound = "MethodNotFound"
    NotFound = "NotFound"
    Unauthorized = "Unauthorized"
    InternalError = "InternalError"

class ListResourcesRequestSchema:
    """Mock ListResourcesRequestSchema class."""
    __name__ = "ListResourcesRequestSchema"

class ListResourceTemplatesRequestSchema:
    """Mock ListResourceTemplatesRequestSchema class."""
    __name__ = "ListResourceTemplatesRequestSchema"

class ListToolsRequestSchema:
    """Mock ListToolsRequestSchema class."""
    __name__ = "ListToolsRequestSchema"

class McpError(Exception):
    """Mock McpError class."""
    
    def __init__(self, code, message):
        """Initialize a new McpError."""
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

class ReadResourceRequestSchema:
    """Mock ReadResourceRequestSchema class."""
    __name__ = "ReadResourceRequestSchema"
