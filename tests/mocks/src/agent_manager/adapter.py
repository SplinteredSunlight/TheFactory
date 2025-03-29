"""
Mock Agent Manager Adapter module for testing.

This module provides mock implementations of Agent Manager adapter classes and functions
for testing purposes.
"""

from typing import Dict, List, Any, Optional


class AgentAdapterConfig:
    """Mock AgentAdapterConfig class."""
    
    def __init__(self, **kwargs):
        """Initialize a new AgentAdapterConfig."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {key: value for key, value in self.__dict__.items()}


class AgentAdapter:
    """Mock AgentAdapter class."""
    
    def __init__(self, config):
        """Initialize a new AgentAdapter."""
        self.config = config
        self.id = "mock-adapter-id"
