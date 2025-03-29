"""
Mock Agent Manager Dagger Adapter module for testing.

This module provides mock implementations of Agent Manager Dagger Adapter classes and functions
for testing purposes.
"""

from typing import Dict, List, Any, Optional
import asyncio

from src.agent_manager.adapter import AgentAdapter, AgentAdapterConfig
from src.agent_manager.schemas import AgentCapability, AgentStatus, AgentExecutionResult, AgentExecutionConfig
from src.orchestrator.error_handling import RetryHandler, IntegrationError


class DaggerAdapterConfig(AgentAdapterConfig):
    """Mock DaggerAdapterConfig class."""
    
    def __init__(
        self,
        container_registry=None,
        container_credentials=None,
        workflow_directory=None,
        workflow_defaults=None,
        max_concurrent_executions=5,
        timeout_seconds=600,
        max_retries=3,
        retry_backoff_factor=0.5,
        retry_jitter=True,
        caching_enabled=True,
        cache_directory=None,
        cache_ttl_seconds=3600,
        **kwargs
    ):
        """Initialize a new DaggerAdapterConfig."""
        super().__init__(**kwargs)
        self.container_registry = container_registry
        self.container_credentials = container_credentials or {}
        self.workflow_directory = workflow_directory
        self.workflow_defaults = workflow_defaults or {}
        self.max_concurrent_executions = max_concurrent_executions
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_jitter = retry_jitter
        self.caching_enabled = caching_enabled
        self.cache_directory = cache_directory
        self.cache_ttl_seconds = cache_ttl_seconds


class DaggerAdapter(AgentAdapter):
    """Mock DaggerAdapter class."""
    
    def __init__(self, config):
        """Initialize a new DaggerAdapter."""
        super().__init__(config)
        self.config = config
        self._engine = "mock-engine"
        self._active_workflows = {}
        self._execution_semaphore = asyncio.Semaphore(config.max_concurrent_executions)
        self._cache = {}
        
        self._retry_handler = RetryHandler(
            max_retries=config.max_retries,
            backoff_factor=config.retry_backoff_factor,
            jitter=config.retry_jitter,
            retry_exceptions=[
                IntegrationError,
                ConnectionError,
                TimeoutError,
                Exception
            ]
        )
    
    async def initialize(self):
        """Initialize the Dagger adapter."""
        return True
    
    async def get_capabilities(self):
        """Get the capabilities of this adapter."""
        return [
            AgentCapability(
                name="containerized_workflow",
                description="Execute workflows in containers with Dagger",
                parameters={
                    "container_image": "Image to use for the container",
                    "workflow_definition": "Definition of the workflow to execute",
                    "inputs": "Inputs for the workflow",
                    "volumes": "Volumes to mount in the container",
                    "environment": "Environment variables for the container",
                }
            ),
            AgentCapability(
                name="dagger_pipeline",
                description="Execute a Dagger pipeline",
                parameters={
                    "pipeline_definition": "Definition of the pipeline to execute",
                    "inputs": "Inputs for the pipeline",
                    "source_directory": "Directory containing the source code"
                }
            )
        ]
    
    async def get_status(self):
        """Get the status of this adapter."""
        active_count = len(self._active_workflows)
        is_ready = self._engine is not None and active_count < self.config.max_concurrent_executions
        
        return AgentStatus(
            adapter_id=self.id,
            is_ready=is_ready,
            current_load=active_count,
            max_load=self.config.max_concurrent_executions,
            status="running" if is_ready else "busy",
            details={
                "active_workflows": active_count,
                "capacity": f"{active_count}/{self.config.max_concurrent_executions}"
            }
        )
    
    async def execute(self, config):
        """Execute a task with the Dagger engine."""
        workflow_type = config.execution_type
        workflow_params = config.parameters or {}
        
        if workflow_type not in ["containerized_workflow", "dagger_pipeline"]:
            return AgentExecutionResult(
                success=False,
                error=f"Unsupported workflow type: {workflow_type}",
                result=None
            )
        
        async with self._execution_semaphore:
            execution_id = f"{self.id}_{config.task_id}_{len(self._active_workflows)}"
            self._active_workflows[execution_id] = {
                "status": "running",
                "start_time": asyncio.get_event_loop().time()
            }
            
            try:
                # Mock successful execution
                result = {"output": "Mock execution output"}
                
                return AgentExecutionResult(
                    success=True,
                    error=None,
                    result=result
                )
            except Exception as e:
                return AgentExecutionResult(
                    success=False,
                    error=str(e),
                    result=None
                )
            finally:
                if execution_id in self._active_workflows:
                    self._active_workflows.pop(execution_id)
    
    async def shutdown(self):
        """Shut down the Dagger adapter."""
        self._engine = None
        return True
    
    @classmethod
    def from_config(cls, config_dict):
        """Create a DaggerAdapter from a configuration dictionary."""
        config = DaggerAdapterConfig(**config_dict)
        return cls(config)
