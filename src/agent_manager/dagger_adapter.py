"""
Dagger Adapter Module

This module provides an adapter for integrating Dagger.io's containerized workflow 
capabilities with the AI-Orchestration-Platform.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
import dagger
from pydagger import Engine

from src.agent_manager.adapter import AgentAdapter, AgentAdapterConfig
from src.agent_manager.schemas import (
    AgentCapability,
    AgentStatus,
    AgentExecutionResult,
    AgentExecutionConfig
)
from src.orchestrator.error_handling import RetryHandler, IntegrationError
from src.orchestrator.circuit_breaker import CircuitBreaker, execute_with_circuit_breaker, get_circuit_breaker

logger = logging.getLogger(__name__)

class DaggerAdapterConfig(AgentAdapterConfig):
    """Configuration for the Dagger adapter."""
    
    def __init__(
        self,
        container_registry: Optional[str] = None,
        container_credentials: Optional[Dict[str, str]] = None,
        workflow_directory: Optional[str] = None,
        workflow_defaults: Optional[Dict[str, Any]] = None,
        max_concurrent_executions: int = 5,
        timeout_seconds: int = 600,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        retry_jitter: bool = True,
        caching_enabled: bool = True,
        cache_directory: Optional[str] = None,
        cache_ttl_seconds: int = 3600,
        **kwargs
    ):
        """
        Initialize a new DaggerAdapterConfig.
        
        Args:
            container_registry: Optional registry URL for container images
            container_credentials: Optional credentials for container registry
            workflow_directory: Directory containing workflow definitions
            workflow_defaults: Default parameters for workflows
            max_concurrent_executions: Maximum number of concurrent workflow executions
            timeout_seconds: Default timeout for workflow executions in seconds
            max_retries: Maximum number of retries for transient failures
            retry_backoff_factor: Backoff factor for retry delays
            retry_jitter: Whether to add jitter to retry delays
            caching_enabled: Whether to enable caching for workflow executions
            cache_directory: Directory to store cache files
            cache_ttl_seconds: Time-to-live for cache entries in seconds
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)
        self.container_registry = container_registry
        self.container_credentials = container_credentials or {}
        self.workflow_directory = workflow_directory or os.path.join(os.getcwd(), "workflows")
        self.workflow_defaults = workflow_defaults or {}
        self.max_concurrent_executions = max_concurrent_executions
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_jitter = retry_jitter
        self.caching_enabled = caching_enabled
        self.cache_directory = cache_directory or os.path.join(os.getcwd(), ".dagger_cache")
        self.cache_ttl_seconds = cache_ttl_seconds
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert the configuration to a dictionary."""
            config_dict = super().to_dict()
            config_dict.update({
                "container_registry": self.container_registry,
                # Don't include credentials in dictionary representation
                "workflow_directory": self.workflow_directory,
                "workflow_defaults": self.workflow_defaults,
                "max_concurrent_executions": self.max_concurrent_executions,
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "retry_backoff_factor": self.retry_backoff_factor,
                "retry_jitter": self.retry_jitter,
                "caching_enabled": self.caching_enabled,
                "cache_directory": self.cache_directory,
                "cache_ttl_seconds": self.cache_ttl_seconds
            })
            return config_dict


class DaggerAdapter(AgentAdapter):
    """
    Adapter for Dagger.io containerized workflow engine.
    
    This adapter provides integration with Dagger's containerized workflow 
    capabilities, allowing workflows to be executed in containers.
    """
    
    def __init__(self, config: DaggerAdapterConfig):
        """
        Initialize a new DaggerAdapter.
        
        Args:
            config: Configuration for the adapter
        """
        super().__init__(config)
        self.config = config
        self._engine = None
        self._active_workflows = {}
        self._execution_semaphore = asyncio.Semaphore(config.max_concurrent_executions)
        self._cache = {}
        
        # Initialize the retry handler
        self._retry_handler = RetryHandler(
            max_retries=config.max_retries,
            backoff_factor=config.retry_backoff_factor,
            jitter=config.retry_jitter,
            retry_exceptions=[
                IntegrationError,
                ConnectionError,
                TimeoutError,
                Exception  # Retry on all exceptions for now, can be refined later
            ]
        )
        
        # Initialize the circuit breaker
        self._circuit_breaker = get_circuit_breaker("dagger_operations")
        
    async def initialize(self) -> bool:
        """
        Initialize the Dagger adapter.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            # Create the workflow directory if it doesn't exist
            if not os.path.exists(self.config.workflow_directory):
                os.makedirs(self.config.workflow_directory)
                
            # Create the cache directory if it doesn't exist and caching is enabled
            if self.config.caching_enabled and not os.path.exists(self.config.cache_directory):
                os.makedirs(self.config.cache_directory)
                
            # Initialize the Dagger client
            self._engine = Engine()
            await self._setup_registry_auth()
            
            # Load cache from disk if caching is enabled
            if self.config.caching_enabled:
                await self._load_cache()
            
            logger.info("Dagger adapter initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Dagger adapter: {e}")
            return False
    
    async def _load_cache(self) -> None:
        """
        Load the cache from disk.
        """
        import json
        import time
        
        try:
            cache_file = os.path.join(self.config.cache_directory, "cache.json")
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                
                # Filter out expired cache entries
                current_time = time.time()
                self._cache = {
                    key: value for key, value in cache_data.items()
                    if value.get("expiry", 0) > current_time
                }
                
                logger.info(f"Loaded {len(self._cache)} cache entries")
            else:
                logger.info("No cache file found, starting with empty cache")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self._cache = {}
    
    async def _save_cache(self) -> None:
        """
        Save the cache to disk.
        """
        import json
        
        try:
            cache_file = os.path.join(self.config.cache_directory, "cache.json")
            with open(cache_file, "w") as f:
                json.dump(self._cache, f)
            
            logger.debug(f"Saved {len(self._cache)} cache entries")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Generate a cache key for the given parameters.
        
        Args:
            params: Parameters to generate a cache key for
            
        Returns:
            Cache key as a string
        """
        import hashlib
        import json
        
        # Create a deterministic string representation of the parameters
        # Sort keys to ensure consistent ordering
        params_str = json.dumps(params, sort_keys=True)
        
        # Generate a hash of the parameters
        return hashlib.sha256(params_str.encode()).hexdigest()
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a result from the cache.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached result or None if not found or expired
        """
        import time
        
        if not self.config.caching_enabled:
            return None
        
        cache_entry = self._cache.get(cache_key)
        if not cache_entry:
            return None
        
        # Check if the cache entry has expired
        expiry = cache_entry.get("expiry", 0)
        if expiry < time.time():
            # Remove expired entry
            self._cache.pop(cache_key, None)
            return None
        
        logger.debug(f"Cache hit for key {cache_key}")
        return cache_entry.get("result")
    
    async def _add_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Add a result to the cache.
        
        Args:
            cache_key: Cache key to store the result under
            result: Result to cache
        """
        import time
        
        if not self.config.caching_enabled:
            return
        
        # Calculate expiry time
        expiry = time.time() + self.config.cache_ttl_seconds
        
        # Store in cache
        self._cache[cache_key] = {
            "result": result,
            "expiry": expiry,
            "timestamp": time.time()
        }
        
        logger.debug(f"Added result to cache with key {cache_key}")
        
        # Save cache to disk
        await self._save_cache()
    
    async def _setup_registry_auth(self):
        """Set up authentication for container registries."""
        if not self.config.container_registry or not self.config.container_credentials:
            return
            
        username = self.config.container_credentials.get("username")
        password = self.config.container_credentials.get("password")
        
        if not username or not password:
            logger.warning("Container registry credentials incomplete")
            return
            
        try:
            # This would be implemented with actual registry auth setup
            # For now, just log that auth would be set up
            logger.info(f"Setting up auth for registry: {self.config.container_registry}")
        except Exception as e:
            logger.error(f"Failed to set up registry auth: {e}")
    
    async def get_capabilities(self) -> List[AgentCapability]:
        """
        Get the capabilities of this adapter.
        
        Returns:
            List of agent capabilities
        """
        # Dagger adapter can execute containerized workflows
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
    
    async def get_status(self) -> AgentStatus:
        """
        Get the status of this adapter.
        
        Returns:
            Status of the agent
        """
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
    
    async def execute(self, config: AgentExecutionConfig) -> AgentExecutionResult:
        """
        Execute a task with the Dagger engine.
        
        Args:
            config: Configuration for the execution
            
        Returns:
            Result of the execution
            
        Raises:
            ValueError: If the execution configuration is invalid
            RuntimeError: If the execution fails
        """
        # Extract execution parameters
        workflow_type = config.execution_type
        workflow_params = config.parameters or {}
        timeout = workflow_params.get("timeout", self.config.timeout_seconds)
        
        # Validate the workflow type
        if workflow_type not in ["containerized_workflow", "dagger_pipeline"]:
            return AgentExecutionResult(
                success=False,
                error=f"Unsupported workflow type: {workflow_type}",
                result=None
            )
            
        # Acquire execution semaphore to limit concurrent executions
        async with self._execution_semaphore:
            execution_id = f"{self.id}_{config.task_id}_{len(self._active_workflows)}"
            self._active_workflows[execution_id] = {
                "status": "running",
                "start_time": asyncio.get_event_loop().time()
            }
            
            try:
                # Check if retries are enabled for this execution
                enable_retry = workflow_params.get("enable_retry", True)
                
                # Determine if circuit breaker should be used
                use_circuit_breaker = workflow_params.get("use_circuit_breaker", True)
                
                if workflow_type == "containerized_workflow":
                    operation = lambda: self._execute_containerized_workflow(workflow_params)
                else:  # dagger_pipeline
                    operation = lambda: self._execute_dagger_pipeline(workflow_params)
                
                # Apply retry and circuit breaker as needed
                if enable_retry and use_circuit_breaker:
                    # Execute with both retry and circuit breaker
                    result = await self._execute_with_circuit_breaker_and_retry(operation)
                elif enable_retry:
                    # Execute with retry only
                    result = await self._execute_with_retry(operation)
                elif use_circuit_breaker:
                    # Execute with circuit breaker only
                    result = await self._execute_with_circuit_breaker(operation)
                else:
                    # Execute without retry or circuit breaker
                    result = await operation()
                    
                return AgentExecutionResult(
                    success=True,
                    error=None,
                    result=result
                )
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                return AgentExecutionResult(
                    success=False,
                    error=str(e),
                    result=None
                )
            finally:
                # Clean up
                if execution_id in self._active_workflows:
                    self._active_workflows.pop(execution_id)
    
    async def _execute_with_retry(self, func):
        """
        Execute a function with retry logic for transient failures.
        
        Args:
            func: Function to execute
            
        Returns:
            Result of the function
            
        Raises:
            Exception: If all retries fail
        """
        return await self._retry_handler.execute(func)
    
    async def _execute_with_circuit_breaker(self, func):
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Exception: If the function fails
        """
        return await execute_with_circuit_breaker(self._circuit_breaker, func)
    
    async def _execute_with_circuit_breaker_and_retry(self, func):
        """
        Execute a function with both circuit breaker and retry protection.
        
        Args:
            func: Function to execute
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Exception: If all retries fail
        """
        return await execute_with_circuit_breaker(
            self._circuit_breaker,
            lambda: self._retry_handler.execute(func)
        )
    
    async def _execute_containerized_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a containerized workflow.
        
        Args:
            params: Parameters for the workflow
            
        Returns:
            Result of the workflow execution
            
        Raises:
            ValueError: If the parameters are invalid
            RuntimeError: If the execution fails
        """
        # Check if caching is enabled and if we have a cached result
        if self.config.caching_enabled:
            # Skip caching if explicitly disabled for this execution
            skip_cache = params.get("skip_cache", False)
            if not skip_cache:
                cache_key = self._get_cache_key(params)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"Using cached result for workflow execution")
                    return cached_result
        
        container_image = params.get("container_image")
        if not container_image:
            raise ValueError("Container image is required")
            
        workflow_definition = params.get("workflow_definition")
        inputs = params.get("inputs", {})
        volumes = params.get("volumes", [])
        environment = params.get("environment", {})
        
        async with dagger.Connection() as client:
            # Start with the container
            container = client.container().from_(container_image)
            
            # Add environment variables
            for key, value in environment.items():
                container = container.with_env_variable(key, value)
                
            # Mount volumes
            for volume in volumes:
                source = volume.get("source")
                target = volume.get("target")
                if source and target:
                    # Create a host directory
                    source_dir = client.host().directory(source)
                    # Mount it
                    container = container.with_mounted_directory(target, source_dir)
            
            # If workflow definition is a file, load it
            if isinstance(workflow_definition, str) and os.path.exists(workflow_definition):
                with open(workflow_definition, "r") as f:
                    workflow_content = f.read()
                    # Write the workflow to a file in the container
                    container = container.with_new_file("/workflow.yml", workflow_content)
                    
            # Execute the workflow
            result = await container.with_exec(
                ["dagger", "run", "/workflow.yml"], 
                inputs=inputs
            ).stdout()
            
            result_dict = {"stdout": result}
            
            # Cache the result if caching is enabled
            if self.config.caching_enabled and not skip_cache:
                cache_key = self._get_cache_key(params)
                await self._add_to_cache(cache_key, result_dict)
            
            return result_dict
    
    async def _execute_dagger_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Dagger pipeline.
        
        Args:
            params: Parameters for the pipeline
            
        Returns:
            Result of the pipeline execution
            
        Raises:
            ValueError: If the parameters are invalid
            RuntimeError: If the execution fails
        """
        # Check if caching is enabled and if we have a cached result
        if self.config.caching_enabled:
            # Skip caching if explicitly disabled for this execution
            skip_cache = params.get("skip_cache", False)
            if not skip_cache:
                cache_key = self._get_cache_key(params)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"Using cached result for pipeline execution")
                    return cached_result
        
        pipeline_definition = params.get("pipeline_definition")
        if not pipeline_definition:
            raise ValueError("Pipeline definition is required")
            
        inputs = params.get("inputs", {})
        source_directory = params.get("source_directory", ".")
        
        async with dagger.Connection() as client:
            # Set up the source directory
            source = client.host().directory(source_directory)
            
            # Set up the pipeline
            pipeline = None
            
            # If pipeline definition is a file path, load it
            if isinstance(pipeline_definition, str) and os.path.exists(pipeline_definition):
                # This would be implemented with actual Dagger pipeline loading
                # For now, we'll just simulate the execution
                result = {"message": f"Executed pipeline from {pipeline_definition}"}
            else:
                # Pipeline is defined inline
                # This would be implemented with actual Dagger pipeline execution
                # For now, we'll just simulate the execution
                result = {"message": "Executed inline pipeline"}
            
            result_dict = {"result": result, "inputs": inputs}
            
            # Cache the result if caching is enabled
            if self.config.caching_enabled and not skip_cache:
                cache_key = self._get_cache_key(params)
                await self._add_to_cache(cache_key, result_dict)
                
            return result_dict
    
    async def shutdown(self) -> bool:
        """
        Shut down the Dagger adapter.
        
        Returns:
            True if shutdown succeeded, False otherwise
        """
        try:
            # Wait for active workflows to complete
            if self._active_workflows:
                logger.info(f"Waiting for {len(self._active_workflows)} active workflows to complete")
                # In a real implementation, we would wait or provide cancellation options
            
            # Save cache to disk if caching is enabled
            if self.config.caching_enabled:
                await self._save_cache()
                
            self._engine = None
            logger.info("Dagger adapter shut down successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to shut down Dagger adapter: {e}")
            return False
    
    @classmethod
    def from_config(cls, config_dict: Dict[str, Any]) -> 'DaggerAdapter':
        """
        Create a DaggerAdapter from a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            A new DaggerAdapter instance
        """
        config = DaggerAdapterConfig(**config_dict)
        return cls(config)
