"""
Unit tests for the Dagger Communication implementation.

This module tests the Dagger-specific communication implementation that extends
the base communication module with Dagger container communication capabilities.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator.communication import (
    MessageType,
    MessagePriority,
    Message
)
from src.orchestrator.dagger_communication import (
    DaggerMessageBroker,
    DaggerCommunicationManager,
    get_dagger_communication_manager
)
from src.orchestrator.dagger_circuit_breaker import (
    DaggerCircuitBreakerError
)
from src.orchestrator.error_handling import (
    ResourceError,
    SystemError
)


class TestDaggerMessageBroker:
    """Test cases for the DaggerMessageBroker class."""

    @pytest.fixture
    def broker(self):
        """Create a DaggerMessageBroker instance for testing."""
        broker = DaggerMessageBroker()
        # Patch the expiration task to avoid background tasks during tests
        broker.expiration_task = MagicMock()
        return broker

    @pytest.mark.asyncio
    async def test_register_container(self, broker):
        """Test registering a container with the broker."""
        await broker.register_container("container1")
        assert "container1" in broker.message_queues
        assert "container1" in broker.online_containers

    @pytest.mark.asyncio
    async def test_unregister_container(self, broker):
        """Test unregistering a container from the broker."""
        await broker.register_container("container1")
        await broker.unregister_container("container1")
        assert "container1" not in broker.online_containers

    @pytest.mark.asyncio
    async def test_send_direct_message(self, broker):
        """Test sending a direct message."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient")
        
        # Create a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, recipient!"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        
        # Send the message
        message_id = await broker.send_message(message)
        
        # Check that the message was added to the recipient's queue
        assert len(broker.message_queues["recipient"]) == 1
        assert broker.message_queues["recipient"][0].content == {"text": "Hello, recipient!"}
        assert broker.message_queues["recipient"][0].sender_id == "sender"

    @pytest.mark.asyncio
    async def test_send_broadcast_message(self, broker):
        """Test sending a broadcast message."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient1")
        await broker.register_container("recipient2")
        
        # Create a message
        message = Message(
            message_type=MessageType.BROADCAST,
            content={"text": "Hello, everyone!"},
            sender_id="sender",
            priority=MessagePriority.MEDIUM
        )
        
        # Send the message
        message_id = await broker.send_message(message)
        
        # Check that the message was added to all recipients' queues
        assert len(broker.message_queues["recipient1"]) == 1
        assert len(broker.message_queues["recipient2"]) == 1
        assert broker.message_queues["recipient1"][0].content == {"text": "Hello, everyone!"}
        assert broker.message_queues["recipient2"][0].content == {"text": "Hello, everyone!"}

    @pytest.mark.asyncio
    async def test_get_messages(self, broker):
        """Test getting messages for a container."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient")
        
        # Create and send a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, recipient!"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        await broker.send_message(message)
        
        # Get messages for the recipient
        messages = await broker.get_messages("recipient")
        
        # Check that the message was retrieved
        assert len(messages) == 1
        assert messages[0].content == {"text": "Hello, recipient!"}
        assert messages[0].sender_id == "sender"
        
        # Check that the message was marked as delivered and removed from the queue
        assert messages[0].delivered
        assert len(broker.message_queues["recipient"]) == 0

    @pytest.mark.asyncio
    async def test_message_priority(self, broker):
        """Test that messages are sorted by priority."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient")
        
        # Create and send messages with different priorities
        low_priority_message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Low priority"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.LOW
        )
        high_priority_message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "High priority"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.HIGH
        )
        medium_priority_message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Medium priority"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        
        # Send messages in reverse priority order
        await broker.send_message(low_priority_message)
        await broker.send_message(medium_priority_message)
        await broker.send_message(high_priority_message)
        
        # Get messages for the recipient
        messages = await broker.get_messages("recipient", mark_delivered=False)
        
        # Check that messages are sorted by priority
        assert len(messages) == 3
        assert messages[0].content == {"text": "High priority"}
        assert messages[1].content == {"text": "Medium priority"}
        assert messages[2].content == {"text": "Low priority"}

    @pytest.mark.asyncio
    async def test_message_expiration(self, broker):
        """Test that expired messages are not returned."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient")
        
        # Create a message with a short TTL
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "This will expire"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM,
            ttl=0.1  # 100ms TTL
        )
        
        # Send the message
        await broker.send_message(message)
        
        # Wait for the message to expire
        await asyncio.sleep(0.2)
        
        # Get messages for the recipient
        messages = await broker.get_messages("recipient")
        
        # Check that no messages were returned
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_delivery_callbacks(self, broker):
        """Test registering and using delivery callbacks."""
        # Register containers
        await broker.register_container("sender")
        await broker.register_container("recipient")
        
        # Create a callback
        callback_messages = []
        def callback(message):
            callback_messages.append(message)
        
        # Register the callback
        await broker.register_delivery_callback("recipient", callback)
        
        # Create and send a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, recipient!"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        await broker.send_message(message)
        
        # Check that the callback was called
        assert len(callback_messages) == 1
        assert callback_messages[0].content == {"text": "Hello, recipient!"}
        assert callback_messages[0].sender_id == "sender"
        
        # Unregister the callback
        await broker.unregister_delivery_callback("recipient", callback)
        
        # Send another message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello again!"},
            sender_id="sender",
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        await broker.send_message(message)
        
        # Check that the callback was not called again
        assert len(callback_messages) == 1

    @pytest.mark.asyncio
    async def test_shutdown(self, broker):
        """Test shutting down the broker."""
        # Mock the expiration task
        broker.expiration_task = MagicMock()
        broker.expiration_task.cancel = MagicMock()
        
        # Shutdown the broker
        await broker.shutdown()
        
        # Check that the expiration task was cancelled
        broker.expiration_task.cancel.assert_called_once()


@pytest.mark.asyncio
class TestDaggerCommunicationManager:
    """Test cases for the DaggerCommunicationManager class."""

    @pytest.fixture
    async def manager(self):
        """Create a DaggerCommunicationManager instance for testing."""
        # Create a manager with mocked dependencies
        manager = DaggerCommunicationManager()
        
        # Mock the broker
        manager.broker = MagicMock()
        manager.broker.register_container = AsyncMock()
        manager.broker.unregister_container = AsyncMock()
        manager.broker.send_message = AsyncMock(return_value="message-id")
        manager.broker.get_messages = AsyncMock(return_value=[])
        manager.broker.register_delivery_callback = AsyncMock()
        manager.broker.unregister_delivery_callback = AsyncMock()
        manager.broker.shutdown = AsyncMock()
        
        # Mock the base manager
        manager.base_manager = MagicMock()
        manager.base_manager.register_agent = AsyncMock()
        manager.base_manager.unregister_agent = AsyncMock()
        manager.base_manager.send_message = AsyncMock(return_value="message-id")
        manager.base_manager.get_messages = AsyncMock(return_value=[])
        manager.base_manager.register_delivery_callback = AsyncMock()
        manager.base_manager.unregister_delivery_callback = AsyncMock()
        
        # Mock the circuit breaker
        manager.circuit_breaker = MagicMock()
        
        return manager

    async def test_register_container(self, manager):
        """Test registering a container with the manager."""
        # Register a container
        await manager.register_container("container1", {"capability": "value"})
        
        # Check that the container was registered with the broker
        manager.broker.register_container.assert_called_once_with("container1")
        
        # Check that the container was registered with the base manager
        manager.base_manager.register_agent.assert_called_once_with(
            agent_id="container1",
            capabilities={"capability": "value"},
            use_circuit_breaker=True
        )
        
        # Check that the capabilities were stored
        assert manager.container_capabilities["container1"] == {"capability": "value"}

    async def test_unregister_container(self, manager):
        """Test unregistering a container from the manager."""
        # Register a container
        await manager.register_container("container1", {"capability": "value"})
        
        # Unregister the container
        await manager.unregister_container("container1")
        
        # Check that the container was unregistered from the broker
        manager.broker.unregister_container.assert_called_once_with("container1")
        
        # Check that the container was unregistered from the base manager
        manager.base_manager.unregister_agent.assert_called_once_with(
            agent_id="container1",
            use_circuit_breaker=True
        )
        
        # Check that the capabilities were removed
        assert "container1" not in manager.container_capabilities

    async def test_send_message_dagger_to_dagger(self, manager):
        """Test sending a message from a Dagger container to another Dagger container."""
        # Register containers
        await manager.register_container("sender", {"capability": "value"})
        await manager.register_container("recipient", {"capability": "value"})
        
        # Send a message
        message_id = await manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "Hello, recipient!"},
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM
        )
        
        # Check that the message was sent through the broker
        assert manager.broker.send_message.called
        
        # Check that the message was not sent through the base manager
        assert not manager.base_manager.send_message.called
        
        # Check that the message ID was returned
        assert message_id == "message-id"

    async def test_send_message_dagger_to_non_dagger(self, manager):
        """Test sending a message from a Dagger container to a non-Dagger agent."""
        # Register a Dagger container
        await manager.register_container("sender", {"capability": "value"})
        
        # Send a message to a non-Dagger agent
        message_id = await manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "Hello, agent!"},
            recipient_id="agent",
            priority=MessagePriority.MEDIUM
        )
        
        # Check that the message was sent through the base manager
        assert manager.base_manager.send_message.called
        
        # Check that the message was not sent through the broker
        assert not manager.broker.send_message.called
        
        # Check that the message ID was returned
        assert message_id == "message-id"

    async def test_get_messages_dagger_container(self, manager):
        """Test getting messages for a Dagger container."""
        # Register a Dagger container
        await manager.register_container("container1", {"capability": "value"})
        
        # Mock the broker to return messages
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, container1!"},
            sender_id="sender",
            recipient_id="container1",
            priority=MessagePriority.MEDIUM
        )
        manager.broker.get_messages.return_value = [message]
        
        # Get messages for the container
        messages = await manager.get_messages("container1")
        
        # Check that the messages were retrieved from the broker
        manager.broker.get_messages.assert_called_once_with("container1", True)
        
        # Check that the messages were not retrieved from the base manager
        assert not manager.base_manager.get_messages.called
        
        # Check that the messages were returned
        assert len(messages) == 1
        assert messages[0]["content"] == {"text": "Hello, container1!"}
        assert messages[0]["sender_id"] == "sender"

    async def test_get_messages_non_dagger_agent(self, manager):
        """Test getting messages for a non-Dagger agent."""
        # Get messages for a non-Dagger agent
        messages = await manager.get_messages("agent")
        
        # Check that the messages were retrieved from the base manager
        manager.base_manager.get_messages.assert_called_once_with(
            agent_id="agent",
            mark_delivered=True,
            use_circuit_breaker=False
        )
        
        # Check that the messages were not retrieved from the broker
        assert not manager.broker.get_messages.called

    async def test_get_container_capabilities(self, manager):
        """Test getting container capabilities."""
        # Register a container
        await manager.register_container("container1", {"capability": "value"})
        
        # Get the container capabilities
        capabilities = await manager.get_container_capabilities("container1")
        
        # Check that the capabilities were returned
        assert capabilities == {"capability": "value"}
        
        # Try to get capabilities for a non-existent container
        with pytest.raises(ResourceError):
            await manager.get_container_capabilities("non-existent")

    async def test_shutdown(self, manager):
        """Test shutting down the manager."""
        # Shutdown the manager
        await manager.shutdown()
        
        # Check that the broker was shut down
        manager.broker.shutdown.assert_called_once()


def test_get_dagger_communication_manager():
    """Test that get_dagger_communication_manager returns the same instance."""
    manager1 = get_dagger_communication_manager()
    manager2 = get_dagger_communication_manager()
    
    assert manager1 is manager2
    assert isinstance(manager1, DaggerCommunicationManager)
