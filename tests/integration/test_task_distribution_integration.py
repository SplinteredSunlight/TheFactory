"""
Integration tests for the Task Distribution functionality.

This module contains integration tests for the task distribution functionality
in the AI-Orchestration-Platform, focusing on the integration between the
OrchestrationEngine and TaskDistributor.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.orchestrator.engine import OrchestrationEngine
from src.orchestrator.task_distribution import (
    TaskDistributor,
    TaskDistributionStrategy,
    TaskDistributionError,
    get_task_distributor
)
from src.orchestrator.communication import MessageType, MessagePriority
from src.orchestrator.auth import AuthenticationError, AuthorizationError


@pytest.fixture
def orchestration_engine():
    """Create an OrchestrationEngine instance for testing."""
    engine = OrchestrationEngine()
    
    # Mock the token manager
    engine.token_manager = MagicMock()
    engine.token_manager.validate_token.return_value = (True, {"sub": "client-123", "exp": 1000000000})
    
    # Mock the communication manager
    engine.communication_manager = AsyncMock()
    
    return engine


@pytest.fixture
def task_distributor():
    """Create a TaskDistributor instance for testing."""
    distributor = TaskDistributor()
    # Mock the communication manager
    distributor.communication_manager = AsyncMock()
    distributor.communication_manager.send_message = AsyncMock(return_value="message-id-123")
    return distributor


@pytest.mark.asyncio
async def test_execute_task_with_distribution(orchestration_engine):
    """Test executing a task with distribution to an agent."""
    # Mock the get_task method
    orchestration_engine.get_task = AsyncMock(return_value={
        "task_id": "task-123",
        "name": "Test Task",
        "description": "A test task",
        "agent_id": None,  # No agent assigned yet
        "priority": 3,
        "status": "pending",
        "created_at": "2025-03-09T01:30:00Z",
    })
    
    # Mock the task distributor
    mock_distributor = AsyncMock()
    mock_distributor.distribute_task = AsyncMock(return_value={
        "task_id": "task-123",
        "agent_id": "agent-456",
        "message_id": "message-id-789",
        "status": "distributed",
        "timestamp": "2025-03-09T01:35:00Z",
    })
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Execute the task
        result = await orchestration_engine.execute_task(
            task_id="task-123",
            parameters={
                "required_capabilities": ["text_processing", "code_generation"],
                "distribution_strategy": "capability_match",
                "priority": "high",
            }
        )
        
        # Verify the result
        assert result["task_id"] == "task-123"
        assert result["status"] == "distributed"
        assert result["agent_id"] == "agent-456"
        assert result["message_id"] == "message-id-789"
        
        # Verify the task distributor was called
        mock_distributor.distribute_task.assert_called_once()
        call_args = mock_distributor.distribute_task.call_args[1]
        assert call_args["task_id"] == "task-123"
        assert call_args["task_type"] == "Test Task"
        assert call_args["required_capabilities"] == ["text_processing", "code_generation"]
        assert call_args["strategy"] == TaskDistributionStrategy.CAPABILITY_MATCH
        assert call_args["priority"] == MessagePriority.HIGH


@pytest.mark.asyncio
async def test_execute_task_with_assigned_agent(orchestration_engine):
    """Test executing a task with an already assigned agent."""
    # Mock the get_task method to return a task with an assigned agent
    orchestration_engine.get_task = AsyncMock(return_value={
        "task_id": "task-123",
        "name": "Test Task",
        "description": "A test task",
        "agent_id": "agent-456",  # Agent already assigned
        "priority": 3,
        "status": "pending",
        "created_at": "2025-03-09T01:30:00Z",
    })
    
    # Execute the task
    result = await orchestration_engine.execute_task(
        task_id="task-123",
        parameters={}
    )
    
    # Verify the result
    assert result["task_id"] == "task-123"
    assert result["status"] == "completed"
    assert result["agent_id"] == "agent-456"
    assert "result" in result


@pytest.mark.asyncio
async def test_distribute_task_method(orchestration_engine):
    """Test the distribute_task method of OrchestrationEngine."""
    # Mock the get_task method
    orchestration_engine.get_task = AsyncMock(return_value={
        "task_id": "task-123",
        "name": "Test Task",
        "description": "A test task",
        "agent_id": None,
        "priority": 3,
        "status": "pending",
        "created_at": "2025-03-09T01:30:00Z",
    })
    
    # Mock the task distributor
    mock_distributor = AsyncMock()
    mock_distributor.distribute_task = AsyncMock(return_value={
        "task_id": "task-123",
        "agent_id": "agent-456",
        "message_id": "message-id-789",
        "status": "distributed",
        "timestamp": "2025-03-09T01:35:00Z",
    })
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Distribute the task
        result = await orchestration_engine.distribute_task(
            task_id="task-123",
            required_capabilities=["text_processing", "code_generation"],
            task_data={"prompt": "Write a function"},
            distribution_strategy="load_balanced",
            priority="high",
            auth_token="token-123"
        )
        
        # Verify the result
        assert result["task_id"] == "task-123"
        assert result["agent_id"] == "agent-456"
        assert result["message_id"] == "message-id-789"
        assert result["status"] == "distributed"
        
        # Verify the token was validated
        orchestration_engine.token_manager.validate_token.assert_called_once_with(
            "token-123",
            required_scopes=["task:write"]
        )
        
        # Verify the task distributor was called
        mock_distributor.distribute_task.assert_called_once()
        call_args = mock_distributor.distribute_task.call_args[1]
        assert call_args["task_id"] == "task-123"
        assert call_args["task_type"] == "Test Task"
        assert call_args["required_capabilities"] == ["text_processing", "code_generation"]
        assert call_args["task_data"] == {"prompt": "Write a function"}
        assert call_args["strategy"] == TaskDistributionStrategy.LOAD_BALANCED
        assert call_args["priority"] == MessagePriority.HIGH
        assert call_args["auth_token"] == "token-123"


@pytest.mark.asyncio
async def test_distribute_task_authentication_error(orchestration_engine):
    """Test the distribute_task method with an invalid token."""
    # Mock the token manager to raise an authentication error
    orchestration_engine.token_manager.validate_token.return_value = (False, {})
    
    # Try to distribute the task with an invalid token
    with pytest.raises(AuthenticationError):
        await orchestration_engine.distribute_task(
            task_id="task-123",
            required_capabilities=["text_processing"],
            task_data={},
            auth_token="invalid-token"
        )


@pytest.mark.asyncio
async def test_handle_task_response(orchestration_engine):
    """Test the handle_task_response method of OrchestrationEngine."""
    # Mock the task distributor
    mock_distributor = AsyncMock()
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Handle a task response
        result = await orchestration_engine.handle_task_response(
            task_id="task-123",
            agent_id="agent-456",
            status="completed",
            result={"output": "Task completed successfully"},
            auth_token="token-123"
        )
        
        # Verify the result
        assert result["task_id"] == "task-123"
        assert result["agent_id"] == "agent-456"
        assert result["status"] == "completed"
        assert result["result"] == {"output": "Task completed successfully"}
        
        # Verify the token was validated
        orchestration_engine.token_manager.validate_token.assert_called_once_with(
            "token-123",
            required_scopes=["agent:execute"]
        )
        
        # Verify the task distributor was called
        mock_distributor.handle_task_response.assert_called_once_with(
            task_id="task-123",
            agent_id="agent-456",
            status="completed",
            result={"output": "Task completed successfully"},
            error=None
        )


@pytest.mark.asyncio
async def test_handle_task_response_authorization_error(orchestration_engine):
    """Test the handle_task_response method with a token from a different agent."""
    # Mock the token manager to return a different agent ID
    orchestration_engine.token_manager.validate_token.return_value = (
        True, {"sub": "agent:different-agent"}
    )
    
    # Try to handle a task response with a token from a different agent
    with pytest.raises(AuthorizationError):
        await orchestration_engine.handle_task_response(
            task_id="task-123",
            agent_id="agent-456",
            status="completed",
            result={},
            auth_token="token-123"
        )


@pytest.mark.asyncio
async def test_register_agent_with_distributor(orchestration_engine):
    """Test the register_agent_with_distributor method of OrchestrationEngine."""
    # Mock the task distributor
    mock_distributor = AsyncMock()
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Register an agent
        result = await orchestration_engine.register_agent_with_distributor(
            agent_id="agent-123",
            capabilities=["text_processing", "code_generation"],
            priority=2,
            auth_token="token-123"
        )
        
        # Verify the result
        assert result["agent_id"] == "agent-123"
        assert result["capabilities"] == ["text_processing", "code_generation"]
        assert result["priority"] == 2
        assert result["status"] == "registered"
        
        # Verify the token was validated
        orchestration_engine.token_manager.validate_token.assert_called_once_with(
            "token-123",
            required_scopes=["agent:write"]
        )
        
        # Verify the task distributor was called
        mock_distributor.register_agent.assert_called_once_with(
            agent_id="agent-123",
            capabilities=["text_processing", "code_generation"],
            priority=2
        )


@pytest.mark.asyncio
async def test_unregister_agent_from_distributor(orchestration_engine):
    """Test the unregister_agent_from_distributor method of OrchestrationEngine."""
    # Mock the task distributor
    mock_distributor = AsyncMock()
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Unregister an agent
        result = await orchestration_engine.unregister_agent_from_distributor(
            agent_id="agent-123",
            auth_token="token-123"
        )
        
        # Verify the result
        assert result["agent_id"] == "agent-123"
        assert result["status"] == "unregistered"
        
        # Verify the token was validated
        orchestration_engine.token_manager.validate_token.assert_called_once_with(
            "token-123",
            required_scopes=["agent:write"]
        )
        
        # Verify the task distributor was called
        mock_distributor.unregister_agent.assert_called_once_with(
            agent_id="agent-123"
        )


@pytest.mark.asyncio
async def test_update_agent_status_in_distributor(orchestration_engine):
    """Test the update_agent_status_in_distributor method of OrchestrationEngine."""
    # Mock the task distributor
    mock_distributor = AsyncMock()
    
    # Patch the get_task_distributor function
    with patch('src.orchestrator.engine.get_task_distributor', return_value=mock_distributor):
        # Update agent status
        result = await orchestration_engine.update_agent_status_in_distributor(
            agent_id="agent-123",
            is_online=True,
            current_load=5,
            auth_token="token-123"
        )
        
        # Verify the result
        assert result["agent_id"] == "agent-123"
        assert result["is_online"] is True
        assert result["current_load"] == 5
        assert result["status"] == "updated"
        
        # Verify the token was validated
        orchestration_engine.token_manager.validate_token.assert_called_once_with(
            "token-123",
            required_scopes=["agent:write"]
        )
        
        # Verify the task distributor was called
        mock_distributor.update_agent_status.assert_called_once_with(
            agent_id="agent-123",
            is_online=True,
            current_load=5
        )
