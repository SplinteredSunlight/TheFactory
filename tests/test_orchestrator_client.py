"""
Tests for the Orchestrator API Client

This module contains tests for the OrchestratorClient class, which provides
a client for interacting with the AI-Orchestration-Platform's Orchestrator API.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator.auth import AuthenticationError, AuthorizationError
from orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ResourceError,
    IntegrationError,
    SystemError
)
from orchestrator.communication import MessageType, MessagePriority
from orchestrator.task_distribution import TaskDistributionStrategy

from fast_agent_integration.orchestrator_client import OrchestratorClient, get_client


@pytest.fixture
def mock_orchestrator_engine():
    """Create a mock OrchestratorEngine."""
    with patch('fast_agent_integration.orchestrator_client.OrchestratorEngine') as mock_engine_class:
        mock_engine = AsyncMock()
        mock_engine_class.return_value = mock_engine
        
        # Mock authentication methods
        mock_engine.authenticate = AsyncMock(return_value={
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
        })
        
        mock_engine.refresh_token = AsyncMock(return_value={
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
        })
        
        mock_engine.validate_token = AsyncMock(return_value={
            "valid": True,
            "expires_in": 3600,
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
            "client_id": "test-client",
        })
        
        mock_engine.revoke_token = AsyncMock(return_value=True)
        
        # Mock agent management methods
        mock_engine.register_agent = AsyncMock(return_value={
            "agent_id": "test-agent",
            "auth_token": "test-agent-token",
            "expires_in": 86400,
        })
        
        mock_engine.authenticate_agent = AsyncMock(return_value={
            "access_token": "agent_access_token",
            "refresh_token": "agent_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": ["agent:execute"],
        })
        
        mock_engine.get_agent = AsyncMock(return_value={
            "agent_id": "test-agent",
            "name": "Test Agent",
            "capabilities": {
                "model": "gpt-4",
                "servers": ["fetch", "filesystem", "orchestrator"],
                "provider": "openai",
            },
            "created_at": "2025-03-09T13:00:00.000000",
            "is_active": True,
        })
        
        mock_engine.list_agents = AsyncMock(return_value=[
            {
                "agent_id": "test-agent-1",
                "name": "Test Agent 1",
                "capabilities": {
                    "model": "gpt-4",
                    "servers": ["fetch", "filesystem", "orchestrator"],
                    "provider": "openai",
                },
                "created_at": "2025-03-09T13:00:00.000000",
                "is_active": True,
            },
            {
                "agent_id": "test-agent-2",
                "name": "Test Agent 2",
                "capabilities": {
                    "model": "claude-3",
                    "servers": ["fetch", "filesystem", "orchestrator"],
                    "provider": "anthropic",
                },
                "created_at": "2025-03-09T13:30:00.000000",
                "is_active": True,
            }
        ])
        
        mock_engine.unregister_agent = AsyncMock(return_value=True)
        
        # Mock task management methods
        mock_engine.create_task = AsyncMock(return_value={
            "task_id": "test-task",
            "name": "Test Task",
            "description": "This is a test task",
            "agent_id": None,
            "priority": 3,
            "status": "created",
            "created_at": "2025-03-09T13:00:00.000000",
        })
        
        mock_engine.execute_task = AsyncMock(return_value={
            "task_id": "test-task",
            "agent_id": "test-agent",
            "status": "completed",
            "result": {"message": "Task executed successfully"},
            "completed_at": "2025-03-09T13:10:00.000000",
        })
        
        mock_engine.get_task = AsyncMock(return_value={
            "task_id": "test-task",
            "name": "Test Task",
            "description": "This is a test task",
            "agent_id": "test-agent",
            "priority": 3,
            "status": "completed",
            "created_at": "2025-03-09T13:00:00.000000",
            "completed_at": "2025-03-09T13:10:00.000000",
        })
        
        mock_engine.distribute_task = AsyncMock(return_value={
            "task_id": "test-task",
            "agent_id": "test-agent",
            "message_id": "test-message",
            "status": "distributed",
            "timestamp": "2025-03-09T13:05:00.000000",
        })
        
        mock_engine.handle_task_response = AsyncMock(return_value={
            "task_id": "test-task",
            "agent_id": "test-agent",
            "status": "completed",
            "result": {"message": "Task completed successfully"},
            "error": None,
            "completed_at": "2025-03-09T13:10:00.000000",
        })
        
        # Mock task distribution methods
        mock_engine.register_agent_with_distributor = AsyncMock(return_value={
            "agent_id": "test-agent",
            "capabilities": ["text_processing", "code_generation"],
            "priority": 1,
            "status": "registered",
            "timestamp": "2025-03-09T13:00:00.000000",
        })
        
        mock_engine.unregister_agent_from_distributor = AsyncMock(return_value={
            "agent_id": "test-agent",
            "status": "unregistered",
            "timestamp": "2025-03-09T13:30:00.000000",
        })
        
        mock_engine.update_agent_status_in_distributor = AsyncMock(return_value={
            "agent_id": "test-agent",
            "is_online": True,
            "current_load": 0,
            "status": "updated",
            "timestamp": "2025-03-09T13:15:00.000000",
        })
        
        # Mock agent communication methods
        mock_engine.send_agent_message = AsyncMock(return_value={
            "message_id": "test-message",
            "status": "sent",
            "timestamp": "2025-03-09T13:05:00.000000",
        })
        
        mock_engine.get_agent_messages = AsyncMock(return_value={
            "agent_id": "test-agent",
            "messages": [
                {
                    "id": "test-message-1",
                    "message_type": "direct",
                    "content": "Hello, agent!",
                    "sender_id": "orchestrator",
                    "recipient_id": "test-agent",
                    "correlation_id": "test-correlation",
                    "priority": "medium",
                    "ttl": None,
                    "metadata": {},
                    "created_at": "2025-03-09T13:00:00.000000",
                    "delivered": True,
                    "delivered_at": "2025-03-09T13:00:01.000000",
                    "expires_at": None,
                }
            ],
            "count": 1,
            "timestamp": "2025-03-09T13:05:00.000000",
        })
        
        mock_engine.get_agent_communication_capabilities = AsyncMock(return_value={
            "supports_direct": True,
            "supports_broadcast": True,
            "supports_task_requests": True,
            "max_message_size": 1048576,
        })
        
        # Mock system methods
        mock_engine.get_status = AsyncMock(return_value={
            "status": "running",
            "version": "0.1.0",
            "workflows": 0,
            "agents": 2,
            "uptime": "1h 30m",
            "features": {
                "agent_communication": True
            }
        })
        
        mock_engine.query = AsyncMock(return_value={
            "query": "test-query",
            "parameters": {},
            "result": {"message": "Query executed successfully"},
        })
        
        yield mock_engine


@pytest.fixture
async def client(mock_orchestrator_engine):
    """Create an OrchestratorClient instance."""
    client = OrchestratorClient(
        api_key="test-api-key",
        client_id="test-client",
    )
    await client.initialize()
    return client


@pytest.mark.asyncio
async def test_initialize(mock_orchestrator_engine):
    """Test initializing the client."""
    client = OrchestratorClient(
        api_key="test-api-key",
        client_id="test-client",
    )
    await client.initialize()
    
    # Check that authenticate was called
    mock_orchestrator_engine.authenticate.assert_called_once_with(
        api_key="test-api-key",
        client_id="test-client",
        scope=["agent:read", "agent:write", "task:read", "task:write"],
    )
    
    # Check that tokens were stored
    assert client.access_token == "test_access_token"
    assert client.refresh_token == "test_refresh_token"
    assert client.token_expiry == 3600


@pytest.mark.asyncio
async def test_authenticate(mock_orchestrator_engine):
    """Test authenticating with the orchestrator."""
    client = OrchestratorClient(
        api_key="test-api-key",
        client_id="test-client",
    )
    result = await client.authenticate()
    
    # Check that authenticate was called
    mock_orchestrator_engine.authenticate.assert_called_once_with(
        api_key="test-api-key",
        client_id="test-client",
        scope=["agent:read", "agent:write", "task:read", "task:write"],
    )
    
    # Check that tokens were stored
    assert client.access_token == "test_access_token"
    assert client.refresh_token == "test_refresh_token"
    assert client.token_expiry == 3600
    assert result is True


@pytest.mark.asyncio
async def test_refresh_auth_token(client, mock_orchestrator_engine):
    """Test refreshing the authentication token."""
    result = await client.refresh_auth_token()
    
    # Check that refresh_token was called
    mock_orchestrator_engine.refresh_token.assert_called_once_with(
        refresh_token="test_refresh_token",
        client_id="test-client",
    )
    
    # Check that tokens were updated
    assert client.access_token == "new_access_token"
    assert client.refresh_token == "new_refresh_token"
    assert client.token_expiry == 3600
    assert result is True


@pytest.mark.asyncio
async def test_ensure_authenticated_with_valid_token(client, mock_orchestrator_engine):
    """Test ensuring authentication with a valid token."""
    result = await client.ensure_authenticated()
    
    # Check that validate_token was called
    mock_orchestrator_engine.validate_token.assert_called_once_with(
        token="test_access_token",
        required_scopes=["agent:read"],
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_ensure_authenticated_with_invalid_token(client, mock_orchestrator_engine):
    """Test ensuring authentication with an invalid token."""
    # Make validate_token raise an error
    mock_orchestrator_engine.validate_token.side_effect = AuthenticationError("Invalid token")
    
    result = await client.ensure_authenticated()
    
    # Check that validate_token was called
    mock_orchestrator_engine.validate_token.assert_called_once_with(
        token="test_access_token",
        required_scopes=["agent:read"],
    )
    
    # Check that refresh_token was called
    mock_orchestrator_engine.refresh_token.assert_called_once_with(
        refresh_token="test_refresh_token",
        client_id="test-client",
    )
    
    # Check that tokens were updated
    assert client.access_token == "new_access_token"
    assert client.refresh_token == "new_refresh_token"
    assert client.token_expiry == 3600
    assert result is True


@pytest.mark.asyncio
async def test_register_agent(client, mock_orchestrator_engine):
    """Test registering an agent."""
    result = await client.register_agent(
        agent_id="test-agent",
        name="Test Agent",
        capabilities={
            "model": "gpt-4",
            "servers": ["fetch", "filesystem", "orchestrator"],
            "provider": "openai",
        }
    )
    
    # Check that register_agent was called
    mock_orchestrator_engine.register_agent.assert_called_once_with(
        agent_id="test-agent",
        name="Test Agent",
        capabilities={
            "model": "gpt-4",
            "servers": ["fetch", "filesystem", "orchestrator"],
            "provider": "openai",
        },
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "auth_token": "test-agent-token",
        "expires_in": 86400,
    }


@pytest.mark.asyncio
async def test_authenticate_agent(client, mock_orchestrator_engine):
    """Test authenticating an agent."""
    result = await client.authenticate_agent(
        agent_id="test-agent",
        auth_token="test-agent-token"
    )
    
    # Check that authenticate_agent was called
    mock_orchestrator_engine.authenticate_agent.assert_called_once_with(
        agent_id="test-agent",
        auth_token="test-agent-token",
        auth_token="test_access_token"
    )
    
    assert result == {
        "access_token": "agent_access_token",
        "refresh_token": "agent_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": ["agent:execute"],
    }


@pytest.mark.asyncio
async def test_get_agent(client, mock_orchestrator_engine):
    """Test getting agent information."""
    result = await client.get_agent("test-agent")
    
    # Check that get_agent was called
    mock_orchestrator_engine.get_agent.assert_called_once_with(
        agent_id="test-agent",
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "name": "Test Agent",
        "capabilities": {
            "model": "gpt-4",
            "servers": ["fetch", "filesystem", "orchestrator"],
            "provider": "openai",
        },
        "created_at": "2025-03-09T13:00:00.000000",
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_list_agents(client, mock_orchestrator_engine):
    """Test listing agents."""
    result = await client.list_agents()
    
    # Check that list_agents was called
    mock_orchestrator_engine.list_agents.assert_called_once_with(
        auth_token="test_access_token"
    )
    
    assert len(result) == 2
    assert result[0]["agent_id"] == "test-agent-1"
    assert result[1]["agent_id"] == "test-agent-2"


@pytest.mark.asyncio
async def test_unregister_agent(client, mock_orchestrator_engine):
    """Test unregistering an agent."""
    result = await client.unregister_agent("test-agent")
    
    # Check that unregister_agent was called
    mock_orchestrator_engine.unregister_agent.assert_called_once_with(
        agent_id="test-agent",
        auth_token="test_access_token"
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_create_task(client, mock_orchestrator_engine):
    """Test creating a task."""
    result = await client.create_task(
        name="Test Task",
        description="This is a test task",
        agent_id="test-agent",
        priority=3
    )
    
    # Check that create_task was called
    mock_orchestrator_engine.create_task.assert_called_once_with(
        name="Test Task",
        description="This is a test task",
        agent_id="test-agent",
        priority=3,
        auth_token="test_access_token"
    )
    
    assert result == {
        "task_id": "test-task",
        "name": "Test Task",
        "description": "This is a test task",
        "agent_id": None,
        "priority": 3,
        "status": "created",
        "created_at": "2025-03-09T13:00:00.000000",
    }


@pytest.mark.asyncio
async def test_execute_task(client, mock_orchestrator_engine):
    """Test executing a task."""
    result = await client.execute_task(
        task_id="test-task",
        parameters={"param1": "value1"}
    )
    
    # Check that execute_task was called
    mock_orchestrator_engine.execute_task.assert_called_once_with(
        task_id="test-task",
        parameters={"param1": "value1"},
        auth_token="test_access_token"
    )
    
    assert result == {
        "task_id": "test-task",
        "agent_id": "test-agent",
        "status": "completed",
        "result": {"message": "Task executed successfully"},
        "completed_at": "2025-03-09T13:10:00.000000",
    }


@pytest.mark.asyncio
async def test_get_task(client, mock_orchestrator_engine):
    """Test getting task information."""
    result = await client.get_task("test-task")
    
    # Check that get_task was called
    mock_orchestrator_engine.get_task.assert_called_once_with(
        task_id="test-task",
        auth_token="test_access_token"
    )
    
    assert result == {
        "task_id": "test-task",
        "name": "Test Task",
        "description": "This is a test task",
        "agent_id": "test-agent",
        "priority": 3,
        "status": "completed",
        "created_at": "2025-03-09T13:00:00.000000",
        "completed_at": "2025-03-09T13:10:00.000000",
    }


@pytest.mark.asyncio
async def test_distribute_task(client, mock_orchestrator_engine):
    """Test distributing a task."""
    result = await client.distribute_task(
        task_id="test-task",
        required_capabilities=["text_processing"],
        task_data={"input": "Test input"},
        distribution_strategy="capability_match",
        excluded_agents=["excluded-agent"],
        priority="high",
        ttl=3600,
        metadata={"source": "test"}
    )
    
    # Check that distribute_task was called
    mock_orchestrator_engine.distribute_task.assert_called_once_with(
        task_id="test-task",
        required_capabilities=["text_processing"],
        task_data={"input": "Test input"},
        distribution_strategy="capability_match",
        excluded_agents=["excluded-agent"],
        priority="high",
        ttl=3600,
        metadata={"source": "test"},
        auth_token="test_access_token"
    )
    
    assert result == {
        "task_id": "test-task",
        "agent_id": "test-agent",
        "message_id": "test-message",
        "status": "distributed",
        "timestamp": "2025-03-09T13:05:00.000000",
    }


@pytest.mark.asyncio
async def test_handle_task_response(client, mock_orchestrator_engine):
    """Test handling a task response."""
    result = await client.handle_task_response(
        task_id="test-task",
        agent_id="test-agent",
        status="completed",
        result={"message": "Task completed successfully"},
        error=None
    )
    
    # Check that handle_task_response was called
    mock_orchestrator_engine.handle_task_response.assert_called_once_with(
        task_id="test-task",
        agent_id="test-agent",
        status="completed",
        result={"message": "Task completed successfully"},
        error=None,
        auth_token="test_access_token"
    )
    
    assert result == {
        "task_id": "test-task",
        "agent_id": "test-agent",
        "status": "completed",
        "result": {"message": "Task completed successfully"},
        "error": None,
        "completed_at": "2025-03-09T13:10:00.000000",
    }


@pytest.mark.asyncio
async def test_register_agent_with_distributor(client, mock_orchestrator_engine):
    """Test registering an agent with the task distributor."""
    result = await client.register_agent_with_distributor(
        agent_id="test-agent",
        capabilities=["text_processing", "code_generation"],
        priority=1
    )
    
    # Check that register_agent_with_distributor was called
    mock_orchestrator_engine.register_agent_with_distributor.assert_called_once_with(
        agent_id="test-agent",
        capabilities=["text_processing", "code_generation"],
        priority=1,
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "capabilities": ["text_processing", "code_generation"],
        "priority": 1,
        "status": "registered",
        "timestamp": "2025-03-09T13:00:00.000000",
    }


@pytest.mark.asyncio
async def test_unregister_agent_from_distributor(client, mock_orchestrator_engine):
    """Test unregistering an agent from the task distributor."""
    result = await client.unregister_agent_from_distributor("test-agent")
    
    # Check that unregister_agent_from_distributor was called
    mock_orchestrator_engine.unregister_agent_from_distributor.assert_called_once_with(
        agent_id="test-agent",
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "status": "unregistered",
        "timestamp": "2025-03-09T13:30:00.000000",
    }


@pytest.mark.asyncio
async def test_update_agent_status_in_distributor(client, mock_orchestrator_engine):
    """Test updating agent status in the task distributor."""
    result = await client.update_agent_status_in_distributor(
        agent_id="test-agent",
        is_online=True,
        current_load=0
    )
    
    # Check that update_agent_status_in_distributor was called
    mock_orchestrator_engine.update_agent_status_in_distributor.assert_called_once_with(
        agent_id="test-agent",
        is_online=True,
        current_load=0,
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "is_online": True,
        "current_load": 0,
        "status": "updated",
        "timestamp": "2025-03-09T13:15:00.000000",
    }


@pytest.mark.asyncio
async def test_send_agent_message(client, mock_orchestrator_engine):
    """Test sending an agent message."""
    result = await client.send_agent_message(
        sender_id="orchestrator",
        message_type="direct",
        content="Hello, agent!",
        recipient_id="test-agent",
        correlation_id="test-correlation",
        priority="medium",
        ttl=3600,
        metadata={"source": "test"}
    )
    
    # Check that send_agent_message was called
    mock_orchestrator_engine.send_agent_message.assert_called_once_with(
        sender_id="orchestrator",
        message_type="direct",
        content="Hello, agent!",
        recipient_id="test-agent",
        correlation_id="test-correlation",
        priority="medium",
        ttl=3600,
        metadata={"source": "test"},
        auth_token="test_access_token"
    )
    
    assert result == {
        "message_id": "test-message",
        "status": "sent",
        "timestamp": "2025-03-09T13:05:00.000000",
    }


@pytest.mark.asyncio
async def test_get_agent_messages(client, mock_orchestrator_engine):
    """Test getting agent messages."""
    result = await client.get_agent_messages(
        agent_id="test-agent",
        mark_delivered=True
    )
    
    # Check that get_agent_messages was called
    mock_orchestrator_engine.get_agent_messages.assert_called_once_with(
        agent_id="test-agent",
        mark_delivered=True,
        auth_token="test_access_token"
    )
    
    assert result == {
        "agent_id": "test-agent",
        "messages": [
            {
                "id": "test-message-1",
                "message_type": "direct",
                "content": "Hello, agent!",
                "sender_id": "orchestrator",
                "recipient_id": "test-agent",
                "correlation_id": "test-correlation",
                "priority": "medium",
                "ttl": None,
                "metadata": {},
                "created_at": "2025-03-09T13:00:00.000000",
                "delivered": True,
                "delivered_at": "2025-03-09T13:00:01.000000",
                "expires_at": None,
            }
        ],
        "count": 1,
        "timestamp": "2025-03-09T13:05:00.000000",
    }


@pytest.mark.asyncio
async def test_get_agent_communication_capabilities(client, mock_orchestrator_engine):
    """Test getting agent communication capabilities."""
    result = await client.get_agent_communication_capabilities("test-agent")
    
    # Check that get_agent_communication_capabilities was called
    mock_orchestrator_engine.get_agent_communication_capabilities.assert_called_once_with(
        agent_id="test-agent",
        auth_token="test_access_token"
    )
    
    assert result == {
        "supports_direct": True,
        "supports_broadcast": True,
        "supports_task_requests": True,
        "max_message_size": 1048576,
    }


@pytest.mark.asyncio
async def test_get_status(client, mock_orchestrator_engine):
    """Test getting orchestrator status."""
    result = await client.get_status()
    
    # Check that get_status was called
    mock_orchestrator_engine.get_status.assert_called_once_with(
        auth_token="test_access_token"
    )
    
    assert result == {
        "status": "running",
        "version": "0.1.0",
        "workflows": 0,
        "agents": 2,
        "uptime": "1h 30m",
        "features": {
            "agent_communication": True
        }
    }


@pytest.mark.asyncio
async def test_query(client, mock_orchestrator_engine):
    """Test executing a query."""
    result = await client.query(
        query="test-query",
        parameters={"param1": "value1"}
    )
    
    # Check that query was called
    mock_orchestrator_engine.query.assert_called_once_with(
        query="test-query",
        parameters={"param1": "value1"},
        auth_token="test_access_token"
    )
    
    assert result == {
        "query": "test-query",
        "parameters": {},
        "result": {"message": "Query executed successfully"},
    }


@pytest.mark.asyncio
async def test_shutdown(client, mock_orchestrator_engine):
    """Test shutting down the client."""
    await client.shutdown()
    
    # Check that revoke_token was called for access token
    mock_orchestrator_engine.revoke_token.assert_any_call(
        "test_access_token"
    )
    
    # Check that revoke_token was called for refresh token
    mock_orchestrator_engine.revoke_token.assert_any_call(
        "test_refresh_token",
        token_type_hint="refresh_token"
    )


@pytest.mark.asyncio
async def test_get_client(mock_orchestrator_engine):
    """Test getting the client singleton."""
    # Reset the singleton instance
    from fast_agent_integration.orchestrator_client import _client_instance
    import fast_agent_integration.orchestrator_client
    fast_agent_integration.orchestrator_client._client_instance = None
    
    # Get the client
    client1 = await get_client(
        api_key="test-api-key",
        client_id="test-client"
    )
    
    # Get the client again
    client2 = await get_client(
        api_key="different-api-key",
        client_id="different-client"
    )
    
    # Check that the same instance is returned
    assert client1 is client2
    
    # Check that initialize was called only once
    mock_orchestrator_engine.authenticate.assert_called_once()
    
    # Reset the singleton instance
    fast_agent_integration.orchestrator_client._client_instance = None


@pytest.mark.asyncio
async def test_authentication_error(mock_orchestrator_engine):
    """Test handling authentication errors."""
    # Make authenticate raise an error
    mock_orchestrator_engine.authenticate.side_effect = AuthenticationError("Invalid API key")
    
    client = OrchestratorClient(
        api_key="invalid-api-key",
        client_id="test-client",
    )
    
    # Authenticate should return False
    result = await client.authenticate()
    assert result is False
    
    # Check that authenticate was called
    mock_orchestrator_engine.authenticate.assert_called_once_with(
        api_key="invalid-api-key",
        client_id="test-client",
        scope=["agent:read", "agent:write", "task:read", "task:write"],
    )
    
    # Tokens should not be set
    assert client.access_token is None
    assert client.refresh_token is None
    assert client.token_expiry is None


@pytest.mark.asyncio
async def test_circuit_breaker(mock_orchestrator_engine):
    """Test circuit breaker functionality."""
    client = OrchestratorClient(
        api_key="test-api-key",
        client_id="test-client",
    )
    await client.initialize()
    
    # Open the circuit breaker
    client.circuit_breaker.state = "open"
    
    # Try to call a method
    with pytest.raises(IntegrationError) as excinfo:
        await client.get_agent("test-agent")
    
    # Check the error
    assert "Circuit breaker is open" in str(excinfo.value)
    assert excinfo.value.code == ErrorCode.INTEGRATION_CONNECTION_FAILED
    
    # Check that get_agent was not called
    mock_orchestrator_engine.get_agent.assert_not_called()
