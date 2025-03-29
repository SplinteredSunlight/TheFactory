"""
Tests for the circuit breaker integration with the agent communication module.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator.communication import (
    AgentCommunicationManager,
    Message,
    MessageType,
    MessagePriority,
)
from src.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenError,
)
from src.orchestrator.error_handling import (
    SystemError,
    ErrorCode,
    Component,
)


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker for testing."""
    circuit_breaker = MagicMock(spec=CircuitBreaker)
    circuit_breaker.state = CircuitBreakerState.CLOSED
    circuit_breaker.execute = AsyncMock()
    return circuit_breaker


@pytest.fixture
def mock_token_manager():
    """Create a mock token manager for testing."""
    token_manager = MagicMock()
    token_manager.validate_token.return_value = (True, {"sub": "agent:test_agent"})
    return token_manager


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter for testing."""
    rate_limiter = MagicMock()
    rate_limiter.check_rate_limit = AsyncMock(return_value=(True, None))
    rate_limiter.shutdown = AsyncMock()
    return rate_limiter


@pytest.fixture
def mock_error_handler():
    """Create a mock error handler for testing."""
    error_handler = MagicMock()
    error_handler.log_error = MagicMock()
    return error_handler


@pytest.fixture
async def communication_manager(mock_circuit_breaker, mock_token_manager, mock_rate_limiter, mock_error_handler):
    """Create a communication manager with mocked dependencies for testing."""
    with patch("src.orchestrator.communication.get_circuit_breaker", return_value=mock_circuit_breaker), \
         patch("src.orchestrator.communication.get_token_manager", return_value=mock_token_manager), \
         patch("src.orchestrator.communication.get_rate_limiter", return_value=mock_rate_limiter), \
         patch("src.orchestrator.communication.get_error_handler", return_value=mock_error_handler):
        
        manager = AgentCommunicationManager()
        manager.broker = MagicMock()
        manager.broker.register_agent = AsyncMock()
        manager.broker.unregister_agent = AsyncMock()
        manager.broker.send_message = AsyncMock(return_value="message_id")
        manager.broker.get_messages = AsyncMock(return_value=[])
        manager.broker.register_delivery_callback = AsyncMock()
        manager.broker.unregister_delivery_callback = AsyncMock()
        manager.broker.shutdown = AsyncMock()
        
        yield manager


@pytest.mark.asyncio
async def test_register_agent_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test registering an agent with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    capabilities = {"feature": "value"}
    
    # Act
    await communication_manager.register_agent(agent_id, capabilities, use_circuit_breaker=True)
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    assert agent_id in communication_manager.agent_capabilities
    assert communication_manager.agent_capabilities[agent_id] == capabilities


@pytest.mark.asyncio
async def test_register_agent_without_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test registering an agent with circuit breaker disabled."""
    # Arrange
    agent_id = "test_agent"
    capabilities = {"feature": "value"}
    
    # Act
    await communication_manager.register_agent(agent_id, capabilities, use_circuit_breaker=False)
    
    # Assert
    mock_circuit_breaker.execute.assert_not_called()
    communication_manager.broker.register_agent.assert_called_once_with(agent_id)
    assert agent_id in communication_manager.agent_capabilities
    assert communication_manager.agent_capabilities[agent_id] == capabilities


@pytest.mark.asyncio
async def test_register_agent_with_circuit_breaker_open(communication_manager, mock_circuit_breaker, mock_error_handler):
    """Test registering an agent when the circuit breaker is open."""
    # Arrange
    agent_id = "test_agent"
    capabilities = {"feature": "value"}
    mock_circuit_breaker.execute.side_effect = CircuitBreakerOpenError("Circuit breaker is open")
    
    # Act & Assert
    with pytest.raises(SystemError) as excinfo:
        await communication_manager.register_agent(agent_id, capabilities, use_circuit_breaker=True)
    
    # Verify the error
    assert excinfo.value.code == ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN
    assert excinfo.value.component == Component.ORCHESTRATOR
    mock_error_handler.log_error.assert_called_once()


@pytest.mark.asyncio
async def test_unregister_agent_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test unregistering an agent with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    communication_manager.agent_capabilities[agent_id] = {"feature": "value"}
    
    # Act
    await communication_manager.unregister_agent(agent_id, use_circuit_breaker=True)
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    assert agent_id not in communication_manager.agent_capabilities


@pytest.mark.asyncio
async def test_unregister_agent_without_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test unregistering an agent with circuit breaker disabled."""
    # Arrange
    agent_id = "test_agent"
    communication_manager.agent_capabilities[agent_id] = {"feature": "value"}
    
    # Act
    await communication_manager.unregister_agent(agent_id, use_circuit_breaker=False)
    
    # Assert
    mock_circuit_breaker.execute.assert_not_called()
    communication_manager.broker.unregister_agent.assert_called_once_with(agent_id)
    assert agent_id not in communication_manager.agent_capabilities


@pytest.mark.asyncio
async def test_send_message_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test sending a message with circuit breaker enabled."""
    # Arrange
    sender_id = "test_sender"
    recipient_id = "test_recipient"
    message_type = MessageType.DIRECT
    content = {"key": "value"}
    
    # Act
    message_id = await communication_manager.send_message(
        sender_id=sender_id,
        message_type=message_type,
        content=content,
        recipient_id=recipient_id,
        use_circuit_breaker=True
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    assert message_id == "message_id"


@pytest.mark.asyncio
async def test_send_message_without_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test sending a message with circuit breaker disabled."""
    # Arrange
    sender_id = "test_sender"
    recipient_id = "test_recipient"
    message_type = MessageType.DIRECT
    content = {"key": "value"}
    
    # Act
    message_id = await communication_manager.send_message(
        sender_id=sender_id,
        message_type=message_type,
        content=content,
        recipient_id=recipient_id,
        use_circuit_breaker=False
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_not_called()
    assert message_id == "message_id"


@pytest.mark.asyncio
async def test_get_messages_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test getting messages with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    
    # Act
    messages = await communication_manager.get_messages(
        agent_id=agent_id,
        use_circuit_breaker=True
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    assert messages == []


@pytest.mark.asyncio
async def test_get_messages_without_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test getting messages with circuit breaker disabled."""
    # Arrange
    agent_id = "test_agent"
    
    # Act
    messages = await communication_manager.get_messages(
        agent_id=agent_id,
        use_circuit_breaker=False
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_not_called()
    assert messages == []


@pytest.mark.asyncio
async def test_register_delivery_callback_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test registering a delivery callback with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    callback = MagicMock()
    
    # Act
    await communication_manager.register_delivery_callback(
        agent_id=agent_id,
        callback=callback,
        use_circuit_breaker=True
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()


@pytest.mark.asyncio
async def test_unregister_delivery_callback_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test unregistering a delivery callback with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    callback = MagicMock()
    
    # Act
    await communication_manager.unregister_delivery_callback(
        agent_id=agent_id,
        callback=callback,
        use_circuit_breaker=True
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_agent_capabilities_with_circuit_breaker(communication_manager, mock_circuit_breaker):
    """Test getting agent capabilities with circuit breaker enabled."""
    # Arrange
    agent_id = "test_agent"
    capabilities = {"feature": "value"}
    communication_manager.agent_capabilities[agent_id] = capabilities
    
    # Act
    result = await communication_manager.get_agent_capabilities(
        agent_id=agent_id,
        use_circuit_breaker=True
    )
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    assert result == capabilities


@pytest.mark.asyncio
async def test_shutdown_with_circuit_breaker(communication_manager, mock_circuit_breaker, mock_rate_limiter):
    """Test shutting down the communication manager with circuit breaker enabled."""
    # Act
    await communication_manager.shutdown(use_circuit_breaker=True)
    
    # Assert
    mock_circuit_breaker.execute.assert_called_once()
    mock_rate_limiter.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_without_circuit_breaker(communication_manager, mock_circuit_breaker, mock_rate_limiter):
    """Test shutting down the communication manager with circuit breaker disabled."""
    # Act
    await communication_manager.shutdown(use_circuit_breaker=False)
    
    # Assert
    mock_circuit_breaker.execute.assert_not_called()
    communication_manager.broker.shutdown.assert_called_once()
    mock_rate_limiter.shutdown.assert_called_once()
