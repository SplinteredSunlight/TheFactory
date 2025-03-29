"""
Agent Adapter Interface Module

This module defines the interface for agent adapters in the AI-Orchestration-Platform.
Adapters provide a standardized way to integrate different agent frameworks.
"""

import abc
import uuid
from typing import Dict, List, Any, Optional, Type, TypeVar

# Type variable for adapter implementations
T = TypeVar('T', bound='AgentAdapter')


class AgentCapability:
    """Represents a capability of an agent."""
    
    def __init__(self, name: str, description: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize a new AgentCapability.
        
        Args:
            name: Name of the capability
            description: Optional description of the capability
            parameters: Optional parameters for the capability
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the capability to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapability':
        """Create a capability from a dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            parameters=data.get("parameters")
        )


class AgentStatus:
    """Represents the status of an agent."""
    
    def __init__(
        self,
        adapter_id: str,
        is_ready: bool,
        current_load: int = 0,
        max_load: int = 10,
        status: str = "running",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AgentStatus.
        
        Args:
            adapter_id: ID of the adapter
            is_ready: Whether the agent is ready to execute tasks
            current_load: Current load of the agent
            max_load: Maximum load of the agent
            status: Status string
            details: Optional status details
        """
        self.adapter_id = adapter_id
        self.is_ready = is_ready
        self.current_load = current_load
        self.max_load = max_load
        self.status = status
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the status to a dictionary."""
        return {
            "adapter_id": self.adapter_id,
            "is_ready": self.is_ready,
            "current_load": self.current_load,
            "max_load": self.max_load,
            "status": self.status,
            "details": self.details
        }


class AgentExecutionConfig:
    """Configuration for agent execution."""
    
    def __init__(
        self,
        task_id: str,
        execution_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AgentExecutionConfig.
        
        Args:
            task_id: ID of the task to execute
            execution_type: Type of execution
            parameters: Parameters for the execution
            timeout_seconds: Timeout in seconds
            callback_url: Optional URL to call when execution completes
            metadata: Optional metadata for the execution
        """
        self.task_id = task_id
        self.execution_type = execution_type
        self.parameters = parameters or {}
        self.timeout_seconds = timeout_seconds
        self.callback_url = callback_url
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "task_id": self.task_id,
            "execution_type": self.execution_type,
            "parameters": self.parameters,
            "timeout_seconds": self.timeout_seconds,
            "callback_url": self.callback_url,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentExecutionConfig':
        """Create a configuration from a dictionary."""
        return cls(
            task_id=data["task_id"],
            execution_type=data["execution_type"],
            parameters=data.get("parameters"),
            timeout_seconds=data.get("timeout_seconds", 300),
            callback_url=data.get("callback_url"),
            metadata=data.get("metadata")
        )


class AgentExecutionResult:
    """Result of an agent execution."""
    
    def __init__(
        self,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Initialize a new AgentExecutionResult.
        
        Args:
            success: Whether the execution was successful
            result: Optional result of the execution
            error: Optional error message if the execution failed
        """
        self.success = success
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentExecutionResult':
        """Create a result from a dictionary."""
        return cls(
            success=data["success"],
            result=data.get("result"),
            error=data.get("error")
        )


class AgentAdapterConfig:
    """Base configuration for agent adapters."""
    
    def __init__(
        self,
        adapter_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a new AgentAdapterConfig.
        
        Args:
            adapter_id: Optional ID for the adapter
            name: Optional name for the adapter
            description: Optional description of the adapter
            **kwargs: Additional configuration parameters
        """
        self.adapter_id = adapter_id or str(uuid.uuid4())
        self.name = name
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "adapter_id": self.adapter_id,
            "name": self.name,
            "description": self.description
        }


class AgentAdapter(abc.ABC):
    """Base class for agent adapters."""
    
    def __init__(self, config: AgentAdapterConfig):
        """
        Initialize a new AgentAdapter.
        
        Args:
            config: Configuration for the adapter
        """
        self.id = config.adapter_id
        self.name = config.name
        self.description = config.description
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the adapter.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """
        Get the capabilities of this adapter.
        
        Returns:
            List of agent capabilities
        """
        pass
    
    @abc.abstractmethod
    async def get_status(self) -> AgentStatus:
        """
        Get the status of this adapter.
        
        Returns:
            Status of the agent
        """
        pass
    
    @abc.abstractmethod
    async def execute(self, config: AgentExecutionConfig) -> AgentExecutionResult:
        """
        Execute a task with this adapter.
        
        Args:
            config: Configuration for the execution
            
        Returns:
            Result of the execution
        """
        pass
    
    @abc.abstractmethod
    async def shutdown(self) -> bool:
        """
        Shut down the adapter.
        
        Returns:
            True if shutdown succeeded, False otherwise
        """
        pass
    
    @classmethod
    @abc.abstractmethod
    def from_config(cls: Type[T], config_dict: Dict[str, Any]) -> T:
        """
        Create an adapter from a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            A new adapter instance
        """
        pass