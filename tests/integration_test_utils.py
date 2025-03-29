"""
Integration Test Utilities

This module provides utility functions for integration testing.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable

import pytest
from src.orchestrator.engine import OrchestrationEngine
from src.fast_agent_integration.adapter import FastAgentAdapter, get_adapter
from src.fast_agent_integration.fast_agent_adapter import FastAgentAdapterImpl, create_fast_agent_adapter
from src.orchestrator.auth import AuthenticationError, AuthorizationError

from tests.integration_test_config import get_test_config, get_test_agent_config, get_test_task_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("integration_tests")

# Get test configuration
config = get_test_config()
TEST_ENV = config["test_env"]
AUTH_CONFIG = config["auth_config"]


class IntegrationTestEnvironment:
    """Class for managing the integration test environment."""
    
    def __init__(self):
        """Initialize the integration test environment."""
        self.orchestrator = None
        self.fast_agent_adapter = None
        self.mcp_server_process = None
        self.auth_token = None
        self.registered_agents = {}
        self.created_tasks = {}
    
    async def setup(self):
        """Set up the integration test environment."""
        logger.info("Setting up integration test environment")
        
        # Start the MCP server
        await self.start_mcp_server()
        
        # Initialize the orchestrator
        self.orchestrator = OrchestrationEngine()
        
        # Initialize the Fast-Agent adapter
        self.fast_agent_adapter = create_fast_agent_adapter(
            config_path=TEST_ENV["config_path"],
            app_name="integration_test",
            api_key=AUTH_CONFIG["api_key"]
        )
        await self.fast_agent_adapter.initialize()
        
        # Get an authentication token
        token_info = await self.orchestrator.authenticate(
            api_key=AUTH_CONFIG["api_key"],
            client_id=AUTH_CONFIG["client_id"],
            scope=AUTH_CONFIG["scopes"]
        )
        self.auth_token = token_info["access_token"]
        
        logger.info("Integration test environment set up successfully")
    
    async def teardown(self):
        """Tear down the integration test environment."""
        logger.info("Tearing down integration test environment")
        
        # Clean up registered agents
        for agent_id in list(self.registered_agents.keys()):
            try:
                await self.unregister_agent(agent_id)
            except Exception as e:
                logger.warning(f"Error unregistering agent {agent_id}: {str(e)}")
        
        # Shut down the Fast-Agent adapter
        if self.fast_agent_adapter:
            await self.fast_agent_adapter.shutdown()
        
        # Stop the MCP server
        await self.stop_mcp_server()
        
        logger.info("Integration test environment torn down successfully")
    
    async def start_mcp_server(self):
        """Start the MCP server."""
        logger.info("Starting MCP server")
        
        # Check if the MCP server is already running
        if self.mcp_server_process and self.mcp_server_process.poll() is None:
            logger.info("MCP server is already running")
            return
        
        # Start the MCP server as a subprocess
        try:
            self.mcp_server_process = subprocess.Popen(
                ["python", TEST_ENV["mcp_server_path"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the server to start
            time.sleep(2)
            
            if self.mcp_server_process.poll() is not None:
                stderr = self.mcp_server_process.stderr.read()
                raise RuntimeError(f"Failed to start MCP server: {stderr}")
            
            logger.info("MCP server started successfully")
            
        except Exception as e:
            logger.error(f"Error starting MCP server: {str(e)}")
            raise
    
    async def stop_mcp_server(self):
        """Stop the MCP server."""
        if self.mcp_server_process:
            logger.info("Stopping MCP server")
            
            try:
                # Terminate the process
                self.mcp_server_process.terminate()
                
                # Wait for the process to terminate
                try:
                    self.mcp_server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self.mcp_server_process.kill()
                    self.mcp_server_process.wait()
                
                logger.info("MCP server stopped successfully")
                
            except Exception as e:
                logger.error(f"Error stopping MCP server: {str(e)}")
            
            self.mcp_server_process = None
    
    async def register_agent(self, agent_type: str) -> Dict[str, Any]:
        """Register an agent for testing.
        
        Args:
            agent_type: Type of agent to register
            
        Returns:
            Dictionary containing agent information
        """
        logger.info(f"Registering agent of type: {agent_type}")
        
        # Get the agent configuration
        agent_config = get_test_agent_config(agent_type)
        
        # Validate the token first
        await self.orchestrator.validate_token(
            token=self.auth_token,
            required_scopes=["agent:write"]
        )
        
        # Register the agent
        agent_token = await self.orchestrator.register_agent(
            agent_id=agent_config["agent_id"],
            name=agent_config["name"],
            capabilities=agent_config["capabilities"]
        )
        
        # Store the agent information
        self.registered_agents[agent_config["agent_id"]] = {
            "agent_id": agent_config["agent_id"],
            "auth_token": agent_token["auth_token"],
            "agent_type": agent_type
        }
        
        logger.info(f"Agent registered successfully: {agent_config['agent_id']}")
        
        return {
            "agent_id": agent_config["agent_id"],
            "auth_token": agent_token["auth_token"],
            "agent_type": agent_type
        }
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if the agent was unregistered, False otherwise
        """
        logger.info(f"Unregistering agent: {agent_id}")
        
        # Validate the token first
        await self.orchestrator.validate_token(
            token=self.auth_token,
            required_scopes=["agent:write"]
        )
        
        # Unregister the agent
        unregistered = await self.orchestrator.unregister_agent(agent_id)
        
        if unregistered:
            # Remove from registered agents
            self.registered_agents.pop(agent_id, None)
            logger.info(f"Agent unregistered successfully: {agent_id}")
        else:
            logger.warning(f"Failed to unregister agent: {agent_id}")
        
        return unregistered
    
    async def create_task(self, task_type: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a task for testing.
        
        Args:
            task_type: Type of task to create
            agent_id: ID of the agent to assign the task to
            
        Returns:
            Dictionary containing task information
        """
        logger.info(f"Creating task of type: {task_type}")
        
        # Get the task configuration
        task_config = get_test_task_config(task_type)
        
        # Validate the token first
        await self.orchestrator.validate_token(
            token=self.auth_token,
            required_scopes=["task:write"]
        )
        
        # Use the provided agent ID or the first registered agent
        if agent_id is None and self.registered_agents:
            agent_id = next(iter(self.registered_agents.keys()))
        
        # Create the task
        task_info = await self.orchestrator.create_task(
            name=task_config["name"],
            description=task_config["description"],
            agent_id=agent_id,
            priority=task_config.get("priority", 3)
        )
        
        # Store the task information
        self.created_tasks[task_info["task_id"]] = {
            "task_id": task_info["task_id"],
            "task_type": task_type,
            "agent_id": agent_id
        }
        
        logger.info(f"Task created successfully: {task_info['task_id']}")
        
        return task_info
    
    async def execute_task(self, task_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task.
        
        Args:
            task_id: ID of the task to execute
            parameters: Parameters for the task execution
            
        Returns:
            Dictionary containing task execution results
        """
        logger.info(f"Executing task: {task_id}")
        
        # Validate the token first
        await self.orchestrator.validate_token(
            token=self.auth_token,
            required_scopes=["task:write"]
        )
        
        # Execute the task
        execution_result = await self.orchestrator.execute_task(
            task_id=task_id,
            parameters=parameters or {}
        )
        
        logger.info(f"Task executed successfully: {task_id}")
        
        return execution_result


# Fixture for the integration test environment
@pytest.fixture
async def test_env():
    """Fixture for the integration test environment."""
    env = IntegrationTestEnvironment()
    await env.setup()
    yield env
    await env.teardown()


# Utility functions for tests

async def with_retry(
    func: Callable[..., Awaitable[Any]],
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    expected_exceptions: Tuple[Exception, ...] = (Exception,),
    *args,
    **kwargs
) -> Any:
    """Execute a function with retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retries
        backoff_factor: Backoff factor for retry delays
        expected_exceptions: Exceptions to catch and retry
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function
        
    Raises:
        Exception: If the function fails after all retries
    """
    retries = 0
    last_exception = None
    
    while retries <= max_retries:
        try:
            return await func(*args, **kwargs)
        except expected_exceptions as e:
            last_exception = e
            retries += 1
            if retries <= max_retries:
                # Exponential backoff
                delay = backoff_factor * (2 ** (retries - 1))
                logger.warning(f"Retry {retries}/{max_retries} after error: {str(e)}")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed after {max_retries} retries: {str(e)}")
                raise
    
    # This should never happen, but just in case
    raise last_exception if last_exception else RuntimeError("Unknown error in with_retry")


async def wait_for_condition(
    condition_func: Callable[..., Awaitable[bool]],
    timeout: float = 30.0,
    interval: float = 0.5,
    *args,
    **kwargs
) -> bool:
    """Wait for a condition to be true.
    
    Args:
        condition_func: Function that returns True when the condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        *args: Arguments for the condition function
        **kwargs: Keyword arguments for the condition function
        
    Returns:
        True if the condition was met, False if the timeout was reached
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if await condition_func(*args, **kwargs):
            return True
        await asyncio.sleep(interval)
    
    return False


def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique ID for testing.
    
    Args:
        prefix: Prefix for the ID
        
    Returns:
        Unique ID
    """
    import uuid
    return f"{prefix}{uuid.uuid4().hex[:8]}"
