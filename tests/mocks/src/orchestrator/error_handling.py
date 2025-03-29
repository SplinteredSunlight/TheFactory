"""
Mock Orchestrator Error Handling module for testing.

This module provides mock implementations of Orchestrator error handling classes and functions
for testing purposes.
"""

class RetryHandler:
    """Mock RetryHandler class."""
    
    def __init__(self, max_retries=3, backoff_factor=0.5, jitter=True, retry_exceptions=None):
        """Initialize a new RetryHandler."""
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or []
    
    async def execute(self, func):
        """Execute a function with retry logic."""
        return await func()


class IntegrationError(Exception):
    """Mock IntegrationError class."""
    
    def __init__(self, message):
        """Initialize a new IntegrationError."""
        self.message = message
        super().__init__(message)
