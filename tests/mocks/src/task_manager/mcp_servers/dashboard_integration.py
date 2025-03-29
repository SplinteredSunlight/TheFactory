"""
Mock Dashboard Integration for Task Management MCP Server

This module provides a mock implementation of the Dashboard Integration for testing purposes.
"""

class DashboardIntegration:
    """Mock Dashboard Integration for the Task Manager MCP Server."""
    
    def __init__(self, server, task_manager):
        """Initialize the Dashboard Integration component.
        
        Args:
            server: The MCP server instance
            task_manager: The Task Manager instance
        """
        self.server = server
        self.task_manager = task_manager
        
        # No-op implementation for testing
        pass
