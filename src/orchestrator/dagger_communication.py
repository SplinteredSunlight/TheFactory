"""
Dagger Communication Module for AI-Orchestration-Platform

This module provides functionality for agents to communicate with each other
using Dagger's container communication capabilities. It extends the base
communication module to work with Dagger containers.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, Callable, Tuple

import dagger

from src.orchestrator.communication import (
    AgentCommunicationManager,
    MessageType,
    MessagePriority,
    Message,
    get_communication_manager
)
from src.orchestrator.dagger_circuit_breaker import (
    DaggerCircuitBreaker,
    execute_with_circuit_breaker,
    get_circuit_breaker_registry,
    DaggerCircuitBreakerError
)
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


class DaggerMessageBroker:
    """
    Broker for handling message routing and delivery between Dagger containers.
    
    The DaggerMessageBroker is responsible for:
    1. Routing messages to the appropriate Dagger containers
    2. Storing messages for containers that are offline
    3. Managing message queues and priorities
    4. Handling message expiration
    """
    
    def __init__(self):
        """Initialize a new DaggerMessageBroker."""
        # Queue of messages for each container
        self.message_queues: Dict[str, List[Message]] = {}
        
        # Set of online containers
        self.online_containers: Set[str] = set()
        
        # Callbacks for message delivery
        self.delivery_callbacks: Dict[str, List[Callable[[Message], None]]] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        # Start the message expiration task
        self.expiration_task = asyncio.create_task(self._expire_messages())
    
    async def register_container(self, container_id: str) -> None:
        """
        Register a container with the broker.
        
        Args:
            container_id: ID of the container to register
        """
        async with self.lock:
            if container_id not in self.message_queues:
                self.message_queues[container_id] = []
            self.online_containers.add(container_id)
            logger.info(f"Container {container_id} registered with Dagger message broker")
    
    async def unregister_container(self, container_id: str) -> None:
        """
        Unregister a container from the broker.
        
        Args:
            container_id: ID of the container to unregister
        """
        async with self.lock:
            self.online_containers.discard(container_id)
            logger.info(f"Container {container_id} unregistered from Dagger message broker")
    
    async def send_message(self, message: Message) -> str:
        """
        Send a message to its recipient(s).
        
        Args:
            message: The message to send
            
        Returns:
            The message ID
            
        Raises:
            ResourceError: If the recipient container doesn't exist
        """
        async with self.lock:
            # Check if the sender exists
            if message.sender_id not in self.message_queues:
                await self.register_container(message.sender_id)
            
            # Handle different message types
            if message.message_type == MessageType.BROADCAST:
                # Send to all containers except the sender
                for container_id in self.message_queues:
                    if container_id != message.sender_id:
                        # Create a copy of the message for each recipient
                        recipient_message = Message(
                            message_type=message.message_type,
                            content=message.content,
                            sender_id=message.sender_id,
                            recipient_id=container_id,
                            correlation_id=message.correlation_id,
                            priority=message.priority,
                            ttl=message.ttl,
                            metadata=message.metadata.copy(),
                        )
                        recipient_message.id = f"{message.id}_{container_id}"
                        
                        # Add to recipient's queue
                        self._add_to_queue(container_id, recipient_message)
                
                logger.info(f"Broadcast message {message.id} sent to {len(self.message_queues) - 1} containers")
            else:
                # Direct message to a specific recipient
                if not message.recipient_id:
                    raise ValueError("Recipient ID is required for non-broadcast messages")
                
                # Check if the recipient exists
                if message.recipient_id not in self.message_queues:
                    raise ResourceError(
                        message=f"Recipient container {message.recipient_id} not found",
                        code=ErrorCode.ORCHESTRATOR_AGENT_NOT_FOUND,
                        component=Component.ORCHESTRATOR,
                        details={"container_id": message.recipient_id}
                    )
                
                # Add to recipient's queue
                self._add_to_queue(message.recipient_id, message)
                
                logger.info(f"Message {message.id} sent to container {message.recipient_id}")
            
            # Deliver messages to online containers
            await self._deliver_messages()
            
            return message.id
    
    def _add_to_queue(self, container_id: str, message: Message) -> None:
        """
        Add a message to a container's queue.
        
        Args:
            container_id: ID of the container
            message: The message to add
        """
        # Create the queue if it doesn't exist
        if container_id not in self.message_queues:
            self.message_queues[container_id] = []
        
        # Add the message to the queue
        self.message_queues[container_id].append(message)
        
        # Sort the queue by priority
        self.message_queues[container_id].sort(
            key=lambda m: (
                0 if m.priority == MessagePriority.HIGH else
                1 if m.priority == MessagePriority.MEDIUM else
                2
            )
        )
    
    async def _deliver_messages(self) -> None:
        """Deliver messages to online containers."""
        for container_id in self.online_containers:
            if container_id in self.message_queues and self.message_queues[container_id]:
                # Get callbacks for this container
                callbacks = self.delivery_callbacks.get(container_id, [])
                
                # If there are callbacks, deliver the messages
                if callbacks:
                    messages = self.message_queues[container_id].copy()
                    self.message_queues[container_id] = []
                    
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
                                    "container_id": container_id,
                                    "message_id": message.id,
                                    "operation": "deliver_message"
                                })
                                logger.error(f"Error delivering message {message.id} to container {container_id}: {str(e)}")
    
    async def get_messages(self, container_id: str, mark_delivered: bool = True) -> List[Message]:
        """
        Get messages for a container.
        
        Args:
            container_id: ID of the container
            mark_delivered: Whether to mark the messages as delivered
            
        Returns:
            List of messages for the container
        """
        async with self.lock:
            if container_id not in self.message_queues:
                return []
            
            # Get messages that haven't expired
            messages = [m for m in self.message_queues[container_id] if not m.is_expired()]
            
            # Mark as delivered if requested
            if mark_delivered:
                for message in messages:
                    message.mark_delivered()
                
                # Clear the queue
                self.message_queues[container_id] = []
            
            return messages
    
    async def register_delivery_callback(
        self,
        container_id: str,
        callback: Callable[[Message], None]
    ) -> None:
        """
        Register a callback for message delivery.
        
        Args:
            container_id: ID of the container
            callback: Function to call when a message is delivered
        """
        async with self.lock:
            if container_id not in self.delivery_callbacks:
                self.delivery_callbacks[container_id] = []
            
            self.delivery_callbacks[container_id].append(callback)
    
    async def unregister_delivery_callback(
        self,
        container_id: str,
        callback: Callable[[Message], None]
    ) -> None:
        """
        Unregister a callback for message delivery.
        
        Args:
            container_id: ID of the container
            callback: Function to unregister
        """
        async with self.lock:
            if container_id in self.delivery_callbacks:
                self.delivery_callbacks[container_id] = [
                    cb for cb in self.delivery_callbacks[container_id]
                    if cb != callback
                ]
    
    async def _expire_messages(self) -> None:
        """Periodically remove expired messages from queues."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self.lock:
                    for container_id in self.message_queues:
                        self.message_queues[container_id] = [
                            m for m in self.message_queues[container_id]
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
        
        logger.info("Dagger message broker shut down")


class DaggerCommunicationManager:
    """
    Manager for communication between Dagger containers in the AI-Orchestration-Platform.
    
    The DaggerCommunicationManager provides a high-level API for container communication,
    handling authentication, message routing, and error handling specifically for Dagger.
    """
    
    def __init__(self):
        """Initialize a new DaggerCommunicationManager."""
        self.broker = DaggerMessageBroker()
        self.base_manager = get_communication_manager()
        
        # Store container communication capabilities
        self.container_capabilities: Dict[str, Dict[str, Any]] = {}
        
        # Initialize the circuit breaker for Dagger communication
        self.circuit_breaker = get_circuit_breaker_registry().get_or_create("dagger_communication")
    
    async def register_container(
        self,
        container_id: str,
        capabilities: Optional[Dict[str, Any]] = None,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Register a container with the communication manager.
        
        Args:
            container_id: ID of the container to register
            capabilities: Communication capabilities of the container
            use_circuit_breaker: Whether to use the circuit breaker
        """
        # Register container with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.register_container(container_id)
                )
            else:
                # Register without circuit breaker
                await self.broker.register_container(container_id)
            
            # Store capabilities
            self.container_capabilities[container_id] = capabilities or {}
            
            # Also register with the base communication manager for cross-system communication
            await self.base_manager.register_agent(
                agent_id=container_id,
                capabilities=capabilities,
                use_circuit_breaker=use_circuit_breaker
            )
            
            logger.info(f"Container {container_id} registered with Dagger communication manager")
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to register container: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
    
    async def unregister_container(
        self,
        container_id: str,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Unregister a container from the communication manager.
        
        Args:
            container_id: ID of the container to unregister
            use_circuit_breaker: Whether to use the circuit breaker
        """
        # Unregister container with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.broker.unregister_container(container_id)
                )
            else:
                # Unregister without circuit breaker
                await self.broker.unregister_container(container_id)
            
            # Remove capabilities
            self.container_capabilities.pop(container_id, None)
            
            # Also unregister from the base communication manager
            await self.base_manager.unregister_agent(
                agent_id=container_id,
                use_circuit_breaker=use_circuit_breaker
            )
            
            logger.info(f"Container {container_id} unregistered from Dagger communication manager")
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to unregister container: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
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
        use_circuit_breaker: bool = True,
    ) -> str:
        """
        Send a message from one container to another.
        
        Args:
            sender_id: ID of the container sending the message
            message_type: Type of the message
            content: Content of the message
            recipient_id: ID of the container receiving the message (None for broadcasts)
            correlation_id: ID to correlate related messages
            priority: Priority of the message
            ttl: Time-to-live in seconds
            metadata: Additional metadata for the message
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            The message ID
            
        Raises:
            ResourceError: If the recipient container doesn't exist
            RateLimitExceededError: If the rate limit is exceeded
        """
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
        
        # Add Dagger-specific metadata
        message.metadata["dagger"] = True
        
        # Send the message with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                return await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._send_message_internal(message)
                )
            else:
                # Send without circuit breaker
                return await self._send_message_internal(message)
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
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
    
    async def _send_message_internal(self, message: Message) -> str:
        """
        Internal method to send a message.
        
        Args:
            message: The message to send
            
        Returns:
            The message ID
        """
        # Check if both sender and recipient are Dagger containers
        sender_is_dagger = self._is_dagger_container(message.sender_id)
        recipient_is_dagger = (
            message.message_type == MessageType.BROADCAST or
            (message.recipient_id and self._is_dagger_container(message.recipient_id))
        )
        
        if sender_is_dagger and recipient_is_dagger:
            # Both are Dagger containers, use Dagger-specific communication
            return await self.broker.send_message(message)
        else:
            # At least one is not a Dagger container, use base communication manager
            return await self.base_manager.send_message(
                sender_id=message.sender_id,
                message_type=message.message_type,
                content=message.content,
                recipient_id=message.recipient_id,
                correlation_id=message.correlation_id,
                priority=message.priority,
                ttl=message.ttl,
                metadata=message.metadata,
                use_circuit_breaker=False,  # We're already using our own circuit breaker
            )
    
    def _is_dagger_container(self, container_id: str) -> bool:
        """
        Check if an ID belongs to a Dagger container.
        
        Args:
            container_id: ID to check
            
        Returns:
            True if the ID belongs to a Dagger container, False otherwise
        """
        return container_id in self.container_capabilities
    
    async def get_messages(
        self,
        container_id: str,
        mark_delivered: bool = True,
        use_circuit_breaker: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a container.
        
        Args:
            container_id: ID of the container
            mark_delivered: Whether to mark the messages as delivered
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            List of messages for the container
        """
        # Get messages with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    messages = await execute_with_circuit_breaker(
                        self.circuit_breaker,
                        lambda: self.broker.get_messages(container_id, mark_delivered)
                    )
                    return [message.to_dict() for message in messages]
                else:
                    # Not a Dagger container, use base communication manager
                    return await self.base_manager.get_messages(
                        agent_id=container_id,
                        mark_delivered=mark_delivered,
                        use_circuit_breaker=False,  # We're already using our own circuit breaker
                    )
            else:
                # Get messages without circuit breaker
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    messages = await self.broker.get_messages(container_id, mark_delivered)
                    return [message.to_dict() for message in messages]
                else:
                    # Not a Dagger container, use base communication manager
                    return await self.base_manager.get_messages(
                        agent_id=container_id,
                        mark_delivered=mark_delivered,
                        use_circuit_breaker=False,
                    )
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to get messages: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
    
    async def register_delivery_callback(
        self,
        container_id: str,
        callback: Callable[[Message], None],
        use_circuit_breaker: bool = True,
    ) -> None:
        """
        Register a callback for message delivery.
        
        Args:
            container_id: ID of the container
            callback: Function to call when a message is delivered
            use_circuit_breaker: Whether to use the circuit breaker
        """
        # Register callback with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    await execute_with_circuit_breaker(
                        self.circuit_breaker,
                        lambda: self.broker.register_delivery_callback(container_id, callback)
                    )
                else:
                    # Not a Dagger container, use base communication manager
                    await self.base_manager.register_delivery_callback(
                        agent_id=container_id,
                        callback=callback,
                        use_circuit_breaker=False,  # We're already using our own circuit breaker
                    )
            else:
                # Register without circuit breaker
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    await self.broker.register_delivery_callback(container_id, callback)
                else:
                    # Not a Dagger container, use base communication manager
                    await self.base_manager.register_delivery_callback(
                        agent_id=container_id,
                        callback=callback,
                        use_circuit_breaker=False,
                    )
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to register delivery callback: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
    
    async def unregister_delivery_callback(
        self,
        container_id: str,
        callback: Callable[[Message], None],
        use_circuit_breaker: bool = True,
    ) -> None:
        """
        Unregister a callback for message delivery.
        
        Args:
            container_id: ID of the container
            callback: Function to unregister
            use_circuit_breaker: Whether to use the circuit breaker
        """
        # Unregister callback with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    await execute_with_circuit_breaker(
                        self.circuit_breaker,
                        lambda: self.broker.unregister_delivery_callback(container_id, callback)
                    )
                else:
                    # Not a Dagger container, use base communication manager
                    await self.base_manager.unregister_delivery_callback(
                        agent_id=container_id,
                        callback=callback,
                        use_circuit_breaker=False,  # We're already using our own circuit breaker
                    )
            else:
                # Unregister without circuit breaker
                if self._is_dagger_container(container_id):
                    # Dagger container, use Dagger-specific communication
                    await self.broker.unregister_delivery_callback(container_id, callback)
                else:
                    # Not a Dagger container, use base communication manager
                    await self.base_manager.unregister_delivery_callback(
                        agent_id=container_id,
                        callback=callback,
                        use_circuit_breaker=False,
                    )
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except Exception as e:
            error = SystemError(
                message=f"Failed to unregister delivery callback: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
    
    async def get_container_capabilities(
        self,
        container_id: str,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Get the communication capabilities of a container.
        
        Args:
            container_id: ID of the container
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            Dictionary of container capabilities
            
        Raises:
            ResourceError: If the container doesn't exist
        """
        # Get container capabilities with circuit breaker if enabled
        try:
            if use_circuit_breaker:
                # Use circuit breaker to protect against cascading failures
                return await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._get_container_capabilities_internal(container_id)
                )
            else:
                # Get capabilities without circuit breaker
                return self._get_container_capabilities_internal(container_id)
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
                code=ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.WARNING,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
        except ResourceError:
            # Re-raise resource errors
            raise
        except Exception as e:
            error = SystemError(
                message=f"Failed to get container capabilities: {str(e)}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
                component=Component.ORCHESTRATOR,
                severity=ErrorSeverity.ERROR,
                details={"container_id": container_id}
            )
            error_handler.log_error(error, {"container_id": container_id})
            raise error
    
    def _get_container_capabilities_internal(self, container_id: str) -> Dict[str, Any]:
        """
        Internal method to get container capabilities.
        
        Args:
            container_id: ID of the container
            
        Returns:
            Dictionary of container capabilities
            
        Raises:
            ResourceError: If the container doesn't exist
        """
        if container_id not in self.container_capabilities:
            raise ResourceError(
                message=f"Container {container_id} not found",
                code=ErrorCode.ORCHESTRATOR_AGENT_NOT_FOUND,
                component=Component.ORCHESTRATOR,
                details={"container_id": container_id}
            )
        
        return self.container_capabilities[container_id]
    
    async def shutdown(self, use_circuit_breaker: bool = True) -> None:
        """
        Shutdown the communication manager.
        
        Args:
            use_circuit_breaker: Whether to use the circuit breaker
        """
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
            
            logger.info("Dagger communication manager shut down")
        except DaggerCircuitBreakerError as e:
            # Circuit breaker is open, log and raise the error
            error = SystemError(
                message=f"Circuit breaker is open for Dagger communication: {str(e)}",
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
_dagger_communication_manager_instance: Optional[DaggerCommunicationManager] = None


def get_dagger_communication_manager() -> DaggerCommunicationManager:
    """
    Get the DaggerCommunicationManager singleton instance.
    
    Returns:
        The DaggerCommunicationManager instance
    """
    global _dagger_communication_manager_instance
    
    if _dagger_communication_manager_instance is None:
        _dagger_communication_manager_instance = DaggerCommunicationManager()
    
    return _dagger_communication_manager_instance
