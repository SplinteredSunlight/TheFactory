"""
Agent Communication Module for AI-Orchestration-Platform

This module provides functionality for agents to communicate with each other
in the AI-Orchestration-Platform. It defines a communication protocol, message
format, and APIs for sending and receiving messages.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Callable, Tuple

from src.orchestrator.auth import get_token_manager, AuthenticationError, AuthorizationError
from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker, CircuitBreakerOpenError
from src.orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ErrorSeverity,
    Component,
    ResourceError,
    IntegrationError,
    SystemError,
    get_error_handler
)
from src.orchestrator.rate_limiting import get_rate_limiter, RateLimitExceededError

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class MessageType(str, Enum):
    """Types of messages that can be exchanged between agents."""
    DIRECT = "direct"  # Direct message to a specific agent
    BROADCAST = "broadcast"  # Broadcast message to all agents
    TASK_REQUEST = "task_request"  # Request for a task to be performed
    TASK_RESPONSE = "task_response"  # Response to a task request
    STATUS_UPDATE = "status_update"  # Status update from an agent
    ERROR = "error"  # Error message
    SYSTEM = "system"  # System message


class MessagePriority(str, Enum):
    """Priority levels for messages."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Message:
    """Represents a message exchanged between agents."""
    
    def __init__(
        self,
        message_type: MessageType,
        content: Any,
        sender_id: str,
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new Message.
        
        Args:
            message_type: Type of the message
            content: Content of the message
            sender_id: ID of the agent sending the message
            recipient_id: ID of the agent receiving the message (None for broadcasts)
            correlation_id: ID to correlate related messages (e.g., request/response)
            priority: Priority of the message
            ttl: Time-to-live in seconds (None for no expiration)
            metadata: Additional metadata for the message
        """
        self.id = str(uuid.uuid4())
        self.message_type = message_type
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.correlation_id = correlation_id or self.id
        self.priority = priority
        self.ttl = ttl
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.delivered = False
        self.delivered_at: Optional[datetime] = None
        self.expires_at = datetime.now().timestamp() + ttl if ttl else None
    
    def is_expired(self) -> bool:
        """
        Check if the message has expired.
        
        Returns:
            True if the message has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.now().timestamp() > self.expires_at
    
    def mark_delivered(self) -> None:
        """Mark the message as delivered."""
        self.delivered = True
        self.delivered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary representation.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "id": self.id,
            "message_type": self.message_type,
            "content": self.content,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "ttl": self.ttl,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "delivered": self.delivered,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "expires_at": self.expires_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary representation.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A new Message instance
        """
        message = cls(
            message_type=data["message_type"],
            content=data["content"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            correlation_id=data.get("correlation_id"),
            priority=data.get("priority", MessagePriority.MEDIUM),
            ttl=data.get("ttl"),
            metadata=data.get("metadata", {}),
        )
        
        message.id = data["id"]
        
        # Parse datetime fields if they exist
        if "created_at" in data and data["created_at"]:
            message.created_at = datetime.fromisoformat(data["created_at"])
        
        message.delivered = data.get("delivered", False)
        
        if "delivered_at" in data and data["delivered_at"]:
            message.delivered_at = datetime.fromisoformat(data["delivered_at"])
        
        message.expires_at = data.get("expires_at")
        
        return message


class MessageBroker:
    """
    Broker for handling message routing and delivery between agents.
    
    The MessageBroker is responsible for:
    1. Routing messages to the appropriate recipients
    2. Storing messages for agents that are offline
    3. Managing message queues and priorities
    4. Handling message expiration
    """
    
    def __init__(self):
        """Initialize a new MessageBroker."""
        # Queue of messages for each agent
        self.message_queues: Dict[str, List[Message]] = {}
        
        # Set of online agents
        self.online_agents: Set[str] = set()
        
        # Callbacks for message delivery
        self.delivery_callbacks: Dict[str, List[Callable[[Message], None]]] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        # Start the message expiration task
        self.expiration_task = asyncio.create_task(self._expire_messages())
    
    async def register_agent(self, agent_id: str) -> None:
        """
        Register an agent with the broker.
        
        Args:
            agent_id: ID of the agent to register
        """
        async with self.lock:
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = []
            self.online_agents.add(agent_id)
            logger.info(f"Agent {agent_id} registered with message broker")
    
    async def unregister_agent(
        self,
        agent_id: str,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Unregister an agent from the broker.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        async with self.lock:
            self.online_agents.discard(agent_id)
            logger.info(f"Agent {agent_id} unregistered from message broker")
    
    async def send_message(self, message: Message) -> str:
        """
        Send a message to its recipient(s).
        
        Args:
            message: The message to send
            
        Returns:
            The message ID
            
        Raises:
            ResourceError: If the recipient agent doesn't exist
        """
        async with self.lock:
            # Check if the sender exists
            if message.sender_id not in self.message_queues:
                await self.register_agent(message.sender_id)
            
            # Handle different message types
            if message.message_type == MessageType.BROADCAST:
                # Send to all agents except the sender
                for agent_id in self.message_queues:
                    if agent_id != message.sender_id:
                        # Create a copy of the message for each recipient
                        recipient_message = Message(
                            message_type=message.message_type,
                            content=message.content,
                            sender_id=message.sender_id,
                            recipient_id=agent_id,
                            correlation_id=message.correlation_id,
                            priority=message.priority,
                            ttl=message.ttl,
                            metadata=message.metadata.copy(),
                        )
                        recipient_message.id = f"{message.id}_{agent_id}"
                        
                        # Add to recipient's queue
                        self._add_to_queue(agent_id, recipient_message)
                
                logger.info(f"Broadcast message {message.id} sent to {len(self.message_queues) - 1} agents")
            else:
                # Direct message to a specific recipient
                if not message.recipient_id:
                    raise ValueError("Recipient ID is required for non-broadcast messages")
                
                # Check if the recipient exists
                if message.recipient_id not in self.message_queues:
                    raise ResourceError(
                        message=f"Recipient agent {message.recipient_id} not found",
                        code=ErrorCode.ORCHESTRATOR_AGENT_NOT_FOUND,
                        component=Component.ORCHESTRATOR,
                        details={"agent_id": message.recipient_id}
                    )
                
                # Add to recipient's queue
                self._add_to_queue(message.recipient_id, message)
                
                logger.info(f"Message {message.id} sent to agent {message.recipient_id}")
            
            # Deliver messages to online agents
            await self._deliver_messages()
            
            return message.id
    
    def _add_to_queue(self, agent_id: str, message: Message) -> None:
        """
        Add a message to an agent's queue.
        
        Args:
            agent_id: ID of the agent
            message: The message to add
        """
        # Create the queue if it doesn't exist
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = []
        
        # Add the message to the queue
        self.message_queues[agent_id].append(message)
        
        # Sort the queue by priority
        self.message_queues[agent_id].sort(
            key=lambda m: (
                0 if m.priority == MessagePriority.HIGH else
                1 if m.priority == MessagePriority.MEDIUM else
                2
            )
        )
    
    async def _deliver_messages(self) -> None:
        """Deliver messages to online agents."""
        for agent_id in self.online_agents:
            if agent_id in self.message_queues and self.message_queues[agent_id]:
                # Get callbacks for this agent
                callbacks = self.delivery_callbacks.get(agent_id, [])
                
                # If there are callbacks, deliver the messages
                if callbacks:
                    messages = self.message_queues[agent_id].copy()
                    self.message_queues[agent_id] = []
                    
                    for message in messages:
                        # Skip expired messages
                        if message.is_expired():
                            continue
                        
                        # Mark as delivered
                        message.mark_delivered()
                        
                        # Call all callbacks
                        for callback in callbacks:
                            try:
                                callback(message)
                            except Exception as e:
                                error_handler.log_error(e, {
                                    "agent_id": agent_id,
                                    "message_id": message.id,
                                    "operation": "deliver_message"
                                })
                                logger.error(f"Error delivering message {message.id} to agent {agent_id}: {str(e)}")
    
    async def get_messages(self, agent_id: str, mark_delivered: bool = True) -> List[Message]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: ID of the agent
            mark_delivered: Whether to mark the messages as delivered
            
        Returns:
            List of messages for the agent
        """
        async with self.lock:
            if agent_id not in self.message_queues:
                return []
            
            # Get messages that haven't expired
            messages = [m for m in self.message_queues[agent_id] if not m.is_expired()]
            
            # Mark as delivered if requested
            if mark_delivered:
                for message in messages:
                    message.mark_delivered()
                
                # Clear the queue
                self.message_queues[agent_id] = []
            
            return messages
    
    async def register_delivery_callback(
        self,
        agent_id: str,
        callback: Callable[[Message], None]
    ) -> None:
        """
        Register a callback for message delivery.
        
        Args:
            agent_id: ID of the agent
            callback: Function to call when a message is delivered
        """
        async with self.lock:
            if agent_id not in self.delivery_callbacks:
                self.delivery_callbacks[agent_id] = []
            
            self.delivery_callbacks[agent_id].append(callback)
    
    async def unregister_delivery_callback(
        self,
        agent_id: str,
        callback: Callable[[Message], None]
    ) -> None:
        """
        Unregister a callback for message delivery.
        
        Args:
            agent_id: ID of the agent
            callback: Function to unregister
        """
        async with self.lock:
            if agent_id in self.delivery_callbacks:
                self.delivery_callbacks[agent_id] = [
                    cb for cb in self.delivery_callbacks[agent_id]
                    if cb != callback
                ]
    
    async def _expire_messages(self) -> None:
        """Periodically remove expired messages from queues."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self.lock:
                    for agent_id in self.message_queues:
                        self.message_queues[agent_id] = [
                            m for m in self.message_queues[agent_id]
                            if not m.is_expired()
                        ]
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_handler.log_error(e, {"operation": "expire_messages"})
                logger.error(f"Error in message expiration task: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the message broker."""
        if hasattr(self, 'expiration_task') and self.expiration_task:
            self.expiration_task.cancel()
            try:
                await self.expiration_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Message broker shut down")


class AgentCommunicationManager:
    """
    Manager for agent communication in the AI-Orchestration-Platform.
    
    The AgentCommunicationManager provides a high-level API for agent communication,
    handling authentication, message routing, and error handling.
    """
    
    def __init__(self):
        """Initialize a new AgentCommunicationManager."""
        self.broker = MessageBroker()
        self.token_manager = get_token_manager()
        
        # Store agent communication capabilities
        self.agent_capabilities: Dict[str, Dict[str, Any]] = {}
        
        # Initialize the circuit breaker for agent communication
        self.circuit_breaker = get_circuit_breaker("agent_communication")
    
    async def register_agent(
        self,
        agent_id: str,
        capabilities: Optional[Dict[str, Any]] = None,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Register an agent with the communication manager.
        
        Args:
            agent_id: ID of the agent to register
            capabilities: Communication capabilities of the agent
        """
        # Register agent with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.register_agent(agent_id)
                )
            else:
                # Register without circuit breaker
                await self.broker.register_agent(agent_id)
            
            # Store capabilities
            self.agent_capabilities[agent_id] = capabilities or {}
            
            logger.info(f"Agent {agent_id} registered with communication manager")
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to register agent: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    async def unregister_agent(
        self,
        agent_id: str,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Unregister an agent from the communication manager.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        # Unregister agent with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.unregister_agent(agent_id)
                )
            else:
                # Unregister without circuit breaker
                await self.broker.unregister_agent(agent_id)
            
            # Remove capabilities
            self.agent_capabilities.pop(agent_id, None)
            
            logger.info(f"Agent {agent_id} unregistered from communication manager")
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to unregister agent: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    async def send_message(
        self,
        sender_id: str,
        message_type: MessageType,
        content: Any,
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
        use_circuit_breaker: bool = True,
    ) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            sender_id: ID of the agent sending the message
            message_type: Type of the message
            content: Content of the message
            recipient_id: ID of the agent receiving the message (None for broadcasts)
            correlation_id: ID to correlate related messages
            priority: Priority of the message
            ttl: Time-to-live in seconds
            metadata: Additional metadata for the message
            auth_token: Authentication token for the sender
            
        Returns:
            The message ID
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the sender doesn't have permission to send the message
            ResourceError: If the recipient agent doesn't exist
            RateLimitExceededError: If the rate limit is exceeded
        """
        # Validate authentication if a token is provided
        if auth_token:
            is_valid, payload = self.token_manager.validate_token(
                auth_token,
                required_scopes=["agent:execute"]
            )
            
            if not is_valid:
                raise AuthenticationError(
                    message="Invalid authentication token",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                    details={"agent_id": sender_id}
                )
            
            # Check if the token belongs to the sender
            token_agent_id = payload.get("sub", "").replace("agent:", "")
            if token_agent_id != sender_id:
                raise AuthorizationError(
                    message="Token does not belong to the sender",
                    code=ErrorCode.AUTH_FORBIDDEN,
                    details={"agent_id": sender_id, "token_agent_id": token_agent_id}
                )
        
        # Check rate limits
        rate_limiter = get_rate_limiter()
        is_allowed, retry_after = await rate_limiter.check_rate_limit(
            agent_id=sender_id,
            message_type=message_type,
            priority=priority,
        )
        
        if not is_allowed:
            raise RateLimitExceededError(
                message="Rate limit exceeded for message sending",
                details={
                    "sender_id": sender_id,
                    "message_type": message_type,
                    "priority": priority
                },
                retry_after=retry_after or 60
            )
        
        # Create the message
        message = Message(
            message_type=message_type,
            content=content,
            sender_id=sender_id,
            recipient_id=recipient_id,
            correlation_id=correlation_id,
            priority=priority,
            ttl=ttl,
            metadata=metadata or {},
        )
        
        # Send the message with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                return await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.send_message(message)
                )
            else:
                # Send without circuit breaker
                return await self.broker.send_message(message)
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "message_type": message_type
                }
            )
            error_handler.log_error(error, {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message_type": message_type
            })
            raise error
        except ResourceError as e:
            error_handler.log_error(e, {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message_type": message_type
            })
            raise
        except Exception as e:
            error = SystemError(
                message=f"Failed to send message: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "message_type": message_type
                }
            )
            error_handler.log_error(error, {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "message_type": message_type
            })
            raise error
    
    async def get_messages(
        self,
        agent_id: str,
        mark_delivered: bool = True,
        auth_token: Optional[str] = None,
        use_circuit_breaker: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for an agent.
        
        Args:
            agent_id: ID of the agent
            mark_delivered: Whether to mark the messages as delivered
            auth_token: Authentication token for the agent
            
        Returns:
            List of messages for the agent
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the agent doesn't have permission to get messages
        """
        # Validate authentication if a token is provided
        if auth_token:
            is_valid, payload = self.token_manager.validate_token(
                auth_token,
                required_scopes=["agent:execute"]
            )
            
            if not is_valid:
                raise AuthenticationError(
                    message="Invalid authentication token",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                    details={"agent_id": agent_id}
                )
            
            # Check if the token belongs to the agent
            token_agent_id = payload.get("sub", "").replace("agent:", "")
            if token_agent_id != agent_id:
                raise AuthorizationError(
                    message="Token does not belong to the agent",
                    code=ErrorCode.AUTH_FORBIDDEN,
                    details={"agent_id": agent_id, "token_agent_id": token_agent_id}
                )
        
        # Get messages with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                messages = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.get_messages(agent_id, mark_delivered)
                )
            else:
                # Get messages without circuit breaker
                messages = await self.broker.get_messages(agent_id, mark_delivered)
                
            return [message.to_dict() for message in messages]
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to get messages: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    async def register_delivery_callback(
        self,
        agent_id: str,
        callback: Callable[[Message], None],
        auth_token: Optional[str] = None,
        use_circuit_breaker: bool = True,
    ) -> None:
        """
        Register a callback for message delivery.
        
        Args:
            agent_id: ID of the agent
            callback: Function to call when a message is delivered
            auth_token: Authentication token for the agent
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the agent doesn't have permission to register a callback
        """
        # Validate authentication if a token is provided
        if auth_token:
            is_valid, payload = self.token_manager.validate_token(
                auth_token,
                required_scopes=["agent:execute"]
            )
            
            if not is_valid:
                raise AuthenticationError(
                    message="Invalid authentication token",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                    details={"agent_id": agent_id}
                )
            
            # Check if the token belongs to the agent
            token_agent_id = payload.get("sub", "").replace("agent:", "")
            if token_agent_id != agent_id:
                raise AuthorizationError(
                    message="Token does not belong to the agent",
                    code=ErrorCode.AUTH_FORBIDDEN,
                    details={"agent_id": agent_id, "token_agent_id": token_agent_id}
                )
        
        # Register callback with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.register_delivery_callback(agent_id, callback)
                )
            else:
                # Register without circuit breaker
                await self.broker.register_delivery_callback(agent_id, callback)
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to register delivery callback: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    async def unregister_delivery_callback(
        self,
        agent_id: str,
        callback: Callable[[Message], None],
        auth_token: Optional[str] = None,
        use_circuit_breaker: bool = True,
    ) -> None:
        """
        Unregister a callback for message delivery.
        
        Args:
            agent_id: ID of the agent
            callback: Function to unregister
            auth_token: Authentication token for the agent
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the agent doesn't have permission to unregister a callback
        """
        # Validate authentication if a token is provided
        if auth_token:
            is_valid, payload = self.token_manager.validate_token(
                auth_token,
                required_scopes=["agent:execute"]
            )
            
            if not is_valid:
                raise AuthenticationError(
                    message="Invalid authentication token",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                    details={"agent_id": agent_id}
                )
            
            # Check if the token belongs to the agent
            token_agent_id = payload.get("sub", "").replace("agent:", "")
            if token_agent_id != agent_id:
                raise AuthorizationError(
                    message="Token does not belong to the agent",
                    code=ErrorCode.AUTH_FORBIDDEN,
                    details={"agent_id": agent_id, "token_agent_id": token_agent_id}
                )
        
        # Unregister callback with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.unregister_delivery_callback(agent_id, callback)
                )
            else:
                # Unregister without circuit breaker
                await self.broker.unregister_delivery_callback(agent_id, callback)
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to unregister delivery callback: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    async def get_agent_capabilities(
        self,
        agent_id: str,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Get the communication capabilities of an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary of agent capabilities
            
        Raises:
            ResourceError: If the agent doesn't exist
        """
        # Get agent capabilities with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                return await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._get_agent_capabilities_internal(agent_id)
                )
            else:
                # Get capabilities without circuit breaker
                return self._get_agent_capabilities_internal(agent_id)
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
        except ResourceError:
            # Re-raise resource errors
            raise
        except Exception as e:
            error = SystemError(
                message=f"Failed to get agent capabilities: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"agent_id": agent_id}
            )
            error_handler.log_error(error, {"agent_id": agent_id})
            raise error
    
    def _get_agent_capabilities_internal(self, agent_id: str) -> Dict[str, Any]:
        """
        Internal method to get agent capabilities.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary of agent capabilities
            
        Raises:
            ResourceError: If the agent doesn't exist
        """
        if agent_id not in self.agent_capabilities:
            raise ResourceError(
                message=f"Agent {agent_id} not found",
                code=ErrorCode.ORCHESTRATOR_AGENT_NOT_FOUND,
                component=Component.ORCHESTRATOR,
                details={"agent_id": agent_id}
            )
        
        return self.agent_capabilities[agent_id]
    
    async def shutdown(self, use_circuit_breaker: bool = True) -> None:
        """Shutdown the communication manager."""
        # Shutdown broker with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.shutdown()
                )
            else:
                # Shutdown without circuit breaker
                await self.broker.shutdown()
            
            # Shutdown the rate limiter
            rate_limiter = get_rate_limiter()
            await rate_limiter.shutdown()
            
            logger.info("Agent communication manager shut down")
        except CircuitBreakerOpenError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for agent communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"operation": "shutdown"}
            )
            error_handler.log_error(error, {"operation": "shutdown"})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to shutdown communication manager: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"operation": "shutdown"}
            )
            error_handler.log_error(error, {"operation": "shutdown"})
            raise error


# Singleton instance
_communication_manager_instance: Optional[AgentCommunicationManager] = None


def get_communication_manager() -> AgentCommunicationManager:
    """
    Get the AgentCommunicationManager singleton instance.
    
    Returns:
        The AgentCommunicationManager instance
    """
    global _communication_manager_instance
    
    if _communication_manager_instance is None:
        _communication_manager_instance = AgentCommunicationManager()
    
    return _communication_manager_instance
