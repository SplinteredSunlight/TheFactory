"""
Integration Test Configuration

This module provides configuration options for the integration tests.
"""

import os
from typing import Dict, Any, Optional, List

# Test environment configuration
TEST_ENV = {
    "api_base_url": "http://localhost:8000/api/v1",
    "mcp_server_path": os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src",
        "fast_agent_integration",
        "mcp_servers",
        "orchestrator_server.py"
    ),
    "config_path": os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "fast_agent.yaml"
    ),
    "log_level": "INFO",
    "test_timeout": 30,  # seconds
}

# Authentication configuration
AUTH_CONFIG = {
    "api_key": "fast-agent-default-key",
    "client_id": "test-client",
    "scopes": ["agent:read", "agent:write", "task:read", "task:write"],
}

# Test agent configuration
TEST_AGENTS = {
    "openai_agent": {
        "agent_id": "test-openai-agent",
        "name": "Test OpenAI Agent",
        "description": "An agent for testing with OpenAI",
        "capabilities": {
            "model": "gpt-4",
            "servers": ["fetch", "filesystem", "orchestrator"],
            "provider": "openai"
        },
        "instruction": "You are a test agent for integration testing with OpenAI."
    },
    "anthropic_agent": {
        "agent_id": "test-anthropic-agent",
        "name": "Test Anthropic Agent",
        "description": "An agent for testing with Anthropic",
        "capabilities": {
            "model": "claude-3",
            "servers": ["fetch", "filesystem", "orchestrator"],
            "provider": "anthropic"
        },
        "instruction": "You are a test agent for integration testing with Anthropic."
    }
}

# Test task configuration
TEST_TASKS = {
    "simple_task": {
        "name": "Simple Test Task",
        "description": "A simple task for integration testing",
        "priority": 3,
        "parameters": {}
    },
    "complex_task": {
        "name": "Complex Test Task",
        "description": "A complex task for integration testing",
        "priority": 1,
        "parameters": {
            "input_data": "Test input data",
            "options": {
                "option1": True,
                "option2": False
            }
        }
    }
}

# Error test configuration
ERROR_TEST_CONFIG = {
    "invalid_api_key": "invalid-key",
    "invalid_token": "invalid-token",
    "non_existent_agent": "non-existent-agent",
    "non_existent_task": "non-existent-task",
    "limited_scopes": ["agent:read"],  # Limited scopes for testing authorization errors
}

# Circuit breaker test configuration
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,
    "reset_timeout": 30,
    "half_open_limit": 3,
}

# Retry handler test configuration
RETRY_HANDLER_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "jitter": True,
}

# MCP server test configuration
MCP_SERVER_CONFIG = {
    "server_name": "orchestrator",
    "resources": [
        "orchestrator://status",
        "orchestrator://agents"
    ],
    "resource_templates": [
        "orchestrator://agent/{agent_id}",
        "orchestrator://task/{task_id}"
    ],
    "tools": [
        "authenticate",
        "refresh_token",
        "validate_token",
        "revoke_token",
        "register_agent",
        "authenticate_agent",
        "create_task",
        "execute_task",
        "query_orchestrator"
    ]
}

def get_test_config() -> Dict[str, Any]:
    """Get the complete test configuration.
    
    Returns:
        Dictionary containing all test configuration options
    """
    return {
        "test_env": TEST_ENV,
        "auth_config": AUTH_CONFIG,
        "test_agents": TEST_AGENTS,
        "test_tasks": TEST_TASKS,
        "error_test_config": ERROR_TEST_CONFIG,
        "circuit_breaker_config": CIRCUIT_BREAKER_CONFIG,
        "retry_handler_config": RETRY_HANDLER_CONFIG,
        "mcp_server_config": MCP_SERVER_CONFIG,
    }

def get_test_agent_config(agent_type: str) -> Dict[str, Any]:
    """Get the configuration for a specific test agent.
    
    Args:
        agent_type: Type of agent to get configuration for
        
    Returns:
        Dictionary containing agent configuration
        
    Raises:
        KeyError: If the agent type is not found
    """
    if agent_type not in TEST_AGENTS:
        raise KeyError(f"Agent type not found: {agent_type}")
    
    return TEST_AGENTS[agent_type]

def get_test_task_config(task_type: str) -> Dict[str, Any]:
    """Get the configuration for a specific test task.
    
    Args:
        task_type: Type of task to get configuration for
        
    Returns:
        Dictionary containing task configuration
        
    Raises:
        KeyError: If the task type is not found
    """
    if task_type not in TEST_TASKS:
        raise KeyError(f"Task type not found: {task_type}")
    
    return TEST_TASKS[task_type]
