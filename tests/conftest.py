"""
Pytest Configuration for Integration Tests

This module provides pytest fixtures and configuration for integration tests.
"""

import asyncio
import logging
import os
import pytest
import sys
from typing import Dict, Any, Optional, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import test utilities
from tests.integration_test_utils import (
    IntegrationTestEnvironment,
    with_retry,
    wait_for_condition,
    generate_unique_id
)
from tests.integration_test_config import (
    get_test_config,
    get_test_agent_config,
    get_test_task_config
)

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


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    # Register markers
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "auth: mark a test as an authentication test")
    config.addinivalue_line("markers", "agent: mark a test as an agent management test")
    config.addinivalue_line("markers", "task: mark a test as a task management test")
    config.addinivalue_line("markers", "error: mark a test as an error handling test")
    config.addinivalue_line("markers", "mcp: mark a test as an MCP server test")


# Fixtures

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def session_test_env():
    """Create a test environment for the session."""
    env = IntegrationTestEnvironment()
    await env.setup()
    yield env
    await env.teardown()


@pytest.fixture
async def test_env(session_test_env):
    """Create a clean test environment for each test."""
    # Clean up any agents or tasks from previous tests
    for agent_id in list(session_test_env.registered_agents.keys()):
        try:
            await session_test_env.unregister_agent(agent_id)
        except Exception as e:
            logger.warning(f"Error unregistering agent {agent_id}: {str(e)}")
    
    session_test_env.registered_agents = {}
    session_test_env.created_tasks = {}
    
    # Get a fresh authentication token
    token_info = await session_test_env.orchestrator.authenticate(
        api_key=AUTH_CONFIG["api_key"],
        client_id=AUTH_CONFIG["client_id"],
        scope=AUTH_CONFIG["scopes"]
    )
    session_test_env.auth_token = token_info["access_token"]
    
    yield session_test_env


@pytest.fixture
async def openai_agent(test_env):
    """Register an OpenAI agent for testing."""
    agent_info = await test_env.register_agent("openai_agent")
    yield agent_info
    await test_env.unregister_agent(agent_info["agent_id"])


@pytest.fixture
async def anthropic_agent(test_env):
    """Register an Anthropic agent for testing."""
    agent_info = await test_env.register_agent("anthropic_agent")
    yield agent_info
    await test_env.unregister_agent(agent_info["agent_id"])


@pytest.fixture
async def simple_task(test_env, openai_agent):
    """Create a simple task for testing."""
    task_info = await test_env.create_task("simple_task", openai_agent["agent_id"])
    yield task_info


@pytest.fixture
async def complex_task(test_env, anthropic_agent):
    """Create a complex task for testing."""
    task_info = await test_env.create_task("complex_task", anthropic_agent["agent_id"])
    yield task_info


@pytest.fixture
def unique_id():
    """Generate a unique ID for testing."""
    return generate_unique_id("test_")


# Helper fixtures

@pytest.fixture
def retry():
    """Fixture for the retry utility function."""
    return with_retry


@pytest.fixture
def wait_for():
    """Fixture for the wait_for_condition utility function."""
    return wait_for_condition


@pytest.fixture
def error_config():
    """Fixture for the error test configuration."""
    return config["error_test_config"]


@pytest.fixture
def circuit_breaker_config():
    """Fixture for the circuit breaker test configuration."""
    return config["circuit_breaker_config"]


@pytest.fixture
def retry_handler_config():
    """Fixture for the retry handler test configuration."""
    return config["retry_handler_config"]


@pytest.fixture
def mcp_server_config():
    """Fixture for the MCP server test configuration."""
    return config["mcp_server_config"]
