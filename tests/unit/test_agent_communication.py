"""
Tests for the Agent Communication Module

This module contains tests for the Agent Communication Module in the AI-Orchestration-Platform.
"""

import asyncio
import json
import pytest
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from orchestrator.communication import (
    Message,
    MessageType,
    MessagePriority,
    MessageBroker,
    AgentCommunicationManager,
    get_communication_manager
)
from orchestrator.auth import get_token_manager, AuthenticationError, AuthorizationError
from orchestrator.error_handling import ResourceError


class TestMessage:
    """Tests for the Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        # Create a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, world!"},
            sender_id="agent1",
            recipient_id="agent2",
            correlation_id="corr123",
            priority=MessagePriority.HIGH,
            ttl=60,
            metadata={"key": "value"},
        )
        
        # Check message properties
        assert message.message_type == MessageType.DIRECT
        assert message.content == {"text": "Hello, world!"}
        assert message.sender_id == "agent1"
        assert message.recipient_id == "agent2"
        assert message.correlation_id == "corr123"
        assert message.priority == MessagePriority.HIGH
        assert message.ttl == 60
        assert message.metadata == {"key": "value"}
        assert message.delivered is False
        assert message.delivered_at is None
        assert message.expires_at is not None
    
    def test_message_expiration(self):
        """Test message expiration."""
        # Create a message with a short TTL
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, world!"},
            sender_id="agent1",
            recipient_id="agent2",
            ttl=0,  # Expire immediately
        )
        
        # Check that the message is expired
        assert message.is_expired() is True
        
        # Create a message with no TTL
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, world!"},
            sender_id="agent1",
            recipient_id="agent2",
            ttl=None,  # Never expire
        )
        
        # Check that the message is not expired
        assert message.is_expired() is False
    
    def test_message_delivery(self):
        """Test marking a message as delivered."""
        # Create a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, world!"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        # Check that the message is not delivered
        assert message.delivered is False
        assert message.delivered_at is None
        
        # Mark the message as delivered
        message.mark_delivered()
        
        # Check that the message is delivered
        assert message.delivered is True
        assert message.delivered_at is not None
    
    def test_message_serialization(self):
        """Test serializing and deserializing a message."""
        # Create a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, world!"},
            sender_id="agent1",
            recipient_id="agent2",
            correlation_id="corr123",
            priority=MessagePriority.HIGH,
            ttl=60,
            metadata={"key": "value"},
        )
        
        # Serialize the message
        message_dict = message.to_dict()
        
        # Deserialize the message
        message2 = Message.from_dict(message_dict)
        
        # Check that the messages are equal
        assert message2.id == message.id
        assert message2.message_type == message.message_type
        assert message2.content == message.content
        assert message2.sender_id == message.sender_id
        assert message2.recipient_id == message.recipient_id
        assert message2.correlation_id == message.correlation_id
        assert message2.priority == message.priority
        assert message2.ttl == message.ttl
        assert message2.metadata == message.metadata
        assert message2.delivered == message.delivered
        assert message2.delivered_at == message.delivered_at
        assert message2.expires_at == message.expires_at


@pytest.fixture
def message_broker():
    """Fixture for creating a MessageBroker."""
    broker = MessageBroker()
    yield broker
    # Clean up
    asyncio.run(broker.shutdown())


class TestMessageBroker:
    """Tests for the MessageBroker class."""
    
    @pytest.mark.asyncio
    async def test_register_agent(self, message_broker):
        """Test registering an agent with the broker."""
        # Register an agent
        await message_broker.register_agent("agent1")
        
        # Check that the agent is registered
        assert "agent1" in message_broker.message_queues
        assert "agent1" in message_broker.online_agents
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self, message_broker):
        """Test unregistering an agent from the broker."""
        # Register an agent
        await message_broker.register_agent("agent1")
        
        # Unregister the agent
        await message_broker.unregister_agent("agent1")
        
        # Check that the agent is unregistered
        assert "agent1" not in message_broker.online_agents
    
    @pytest.mark.asyncio
    async def test_send_direct_message(self, message_broker):
        """Test sending a direct message."""
        # Register agents
        await message_broker.register_agent("agent1")
        await message_broker.register_agent("agent2")
        
        # Create a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, agent2!"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        # Send the message
        message_id = await message_broker.send_message(message)
        
        # Check that the message was sent
        assert message_id == message.id
        
        # Check that the message is in the recipient's queue
        messages = await message_broker.get_messages("agent2", mark_delivered=False)
        assert len(messages) == 1
        assert messages[0].id == message.id
        assert messages[0].content == {"text": "Hello, agent2!"}
    
    @pytest.mark.asyncio
    async def test_send_broadcast_message(self, message_broker):
        """Test sending a broadcast message."""
        # Register agents
        await message_broker.register_agent("agent1")
        await message_broker.register_agent("agent2")
        await message_broker.register_agent("agent3")
        
        # Create a message
        message = Message(
            message_type=MessageType.BROADCAST,
            content={"text": "Hello, everyone!"},
            sender_id="agent1",
        )
        
        # Send the message
        message_id = await message_broker.send_message(message)
        
        # Check that the message was sent
        assert message_id == message.id
        
        # Check that the message is in the recipients' queues
        messages2 = await message_broker.get_messages("agent2", mark_delivered=False)
        assert len(messages2) == 1
        assert messages2[0].content == {"text": "Hello, everyone!"}
        
        messages3 = await message_broker.get_messages("agent3", mark_delivered=False)
        assert len(messages3) == 1
        assert messages3[0].content == {"text": "Hello, everyone!"}
        
        # Check that the message is not in the sender's queue
        messages1 = await message_broker.get_messages("agent1", mark_delivered=False)
        assert len(messages1) == 0
    
    @pytest.mark.asyncio
    async def test_get_messages(self, message_broker):
        """Test getting messages for an agent."""
        # Register agents
        await message_broker.register_agent("agent1")
        await message_broker.register_agent("agent2")
        
        # Create and send messages
        message1 = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, agent2!"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        message2 = Message(
            message_type=MessageType.DIRECT,
            content={"text": "How are you?"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        await message_broker.send_message(message1)
        await message_broker.send_message(message2)
        
        # Get messages without marking as delivered
        messages = await message_broker.get_messages("agent2", mark_delivered=False)
        assert len(messages) == 2
        
        # Get messages and mark as delivered
        messages = await message_broker.get_messages("agent2", mark_delivered=True)
        assert len(messages) == 2
        
        # Check that the messages are marked as delivered
        assert messages[0].delivered is True
        assert messages[0].delivered_at is not None
        assert messages[1].delivered is True
        assert messages[1].delivered_at is not None
        
        # Check that the queue is empty
        messages = await message_broker.get_messages("agent2", mark_delivered=False)
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_message_priority(self, message_broker):
        """Test message priority ordering."""
        # Register agents
        await message_broker.register_agent("agent1")
        await message_broker.register_agent("agent2")
        
        # Create and send messages with different priorities
        message_low = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Low priority"},
            sender_id="agent1",
            recipient_id="agent2",
            priority=MessagePriority.LOW,
        )
        
        message_medium = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Medium priority"},
            sender_id="agent1",
            recipient_id="agent2",
            priority=MessagePriority.MEDIUM,
        )
        
        message_high = Message(
            message_type=MessageType.DIRECT,
            content={"text": "High priority"},
            sender_id="agent1",
            recipient_id="agent2",
            priority=MessagePriority.HIGH,
        )
        
        # Send in reverse priority order
        await message_broker.send_message(message_low)
        await message_broker.send_message(message_medium)
        await message_broker.send_message(message_high)
        
        # Get messages
        messages = await message_broker.get_messages("agent2", mark_delivered=True)
        
        # Check that messages are ordered by priority
        assert len(messages) == 3
        assert messages[0].content == {"text": "High priority"}
        assert messages[1].content == {"text": "Medium priority"}
        assert messages[2].content == {"text": "Low priority"}
    
    @pytest.mark.asyncio
    async def test_delivery_callbacks(self, message_broker):
        """Test message delivery callbacks."""
        # Register agents
        await message_broker.register_agent("agent1")
        await message_broker.register_agent("agent2")
        
        # Create a callback
        received_messages = []
        
        def callback(message):
            received_messages.append(message)
        
        # Register the callback
        await message_broker.register_delivery_callback("agent2", callback)
        
        # Create and send a message
        message = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello, agent2!"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        await message_broker.send_message(message)
        
        # Check that the callback was called
        assert len(received_messages) == 1
        assert received_messages[0].id == message.id
        assert received_messages[0].content == {"text": "Hello, agent2!"}
        
        # Unregister the callback
        await message_broker.unregister_delivery_callback("agent2", callback)
        
        # Send another message
        message2 = Message(
            message_type=MessageType.DIRECT,
            content={"text": "Hello again!"},
            sender_id="agent1",
            recipient_id="agent2",
        )
        
        await message_broker.send_message(message2)
        
        # Check that the callback was not called
        assert len(received_messages) == 1


@pytest.fixture
def communication_manager():
    """Fixture for creating an AgentCommunicationManager."""
    manager = AgentCommunicationManager()
    yield manager
    # Clean up
    asyncio.run(manager.broker.shutdown())


class TestAgentCommunicationManager:
    """Tests for the AgentCommunicationManager class."""
    
    @pytest.mark.asyncio
    async def test_register_agent(self, communication_manager):
        """Test registering an agent with the communication manager."""
        # Register an agent
        await communication_manager.register_agent(
            "agent1",
            capabilities={"supports_broadcast": True}
        )
        
        # Check that the agent is registered
        assert "agent1" in communication_manager.agent_capabilities
        assert communication_manager.agent_capabilities["agent1"] == {"supports_broadcast": True}
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self, communication_manager):
        """Test unregistering an agent from the communication manager."""
        # Register an agent
        await communication_manager.register_agent("agent1")
        
        # Unregister the agent
        await communication_manager.unregister_agent("agent1")
        
        # Check that the agent is unregistered
        assert "agent1" not in communication_manager.agent_capabilities
    
    @pytest.mark.asyncio
    async def test_send_message(self, communication_manager):
        """Test sending a message through the communication manager."""
        # Register agents
        await communication_manager.register_agent("agent1")
        await communication_manager.register_agent("agent2")
        
        # Send a message
        message_id = await communication_manager.send_message(
            sender_id="agent1",
            message_type=MessageType.DIRECT,
            content={"text": "Hello, agent2!"},
            recipient_id="agent2",
        )
        
        # Check that the message was sent
        assert message_id is not None
        
        # Get messages for the recipient
        messages = await communication_manager.get_messages("agent2")
        
        # Check that the message was received
        assert len(messages) == 1
        assert messages[0]["content"] == {"text": "Hello, agent2!"}
        assert messages[0]["sender_id"] == "agent1"
        assert messages[0]["recipient_id"] == "agent2"
    
    @pytest.mark.asyncio
    async def test_get_agent_capabilities(self, communication_manager):
        """Test getting agent capabilities."""
        # Register an agent with capabilities
        await communication_manager.register_agent(
            "agent1",
            capabilities={"supports_broadcast": True, "max_message_size": 1024}
        )
        
        # Get the agent's capabilities
        capabilities = await communication_manager.get_agent_capabilities("agent1")
        
        # Check the capabilities
        assert capabilities == {"supports_broadcast": True, "max_message_size": 1024}
        
        # Test getting capabilities for a non-existent agent
        with pytest.raises(ResourceError):
            await communication_manager.get_agent_capabilities("non_existent_agent")


class TestCommunicationManagerSingleton:
    """Tests for the communication manager singleton."""
    
    def test_get_communication_manager(self):
        """Test getting the communication manager singleton."""
        # Get the communication manager
        manager1 = get_communication_manager()
        manager2 = get_communication_manager()
        
        # Check that they are the same instance
        assert manager1 is manager2
