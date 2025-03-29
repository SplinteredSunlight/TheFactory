"""
Example demonstrating the use of the Dagger Communication Manager.

This example shows how to use the Dagger Communication Manager to enable
communication between Dagger containers. It demonstrates container registration,
message sending, and message receiving.

To run this example:
1. Make sure the AI-Orchestration-Platform is installed
2. Run this script: python examples/dagger/dagger_communication_example.py
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional

import dagger

from src.orchestrator.communication import (
    MessageType,
    MessagePriority,
)
from src.orchestrator.dagger_communication import (
    get_dagger_communication_manager,
)
from src.orchestrator.dagger_circuit_breaker import (
    DaggerCircuitBreakerError,
)
from src.orchestrator.error_handling import (
    SystemError,
    ErrorCode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockDaggerContainer:
    """Mock Dagger container for demonstration purposes."""
    
    def __init__(self, container_id: str, fail_probability: float = 0.0):
        """
        Initialize a new MockDaggerContainer.
        
        Args:
            container_id: ID of the container
            fail_probability: Probability of failure (0.0 to 1.0)
        """
        self.container_id = container_id
        self.fail_probability = fail_probability
        self.messages: List[Dict[str, Any]] = []
    
    async def register(self, communication_manager) -> None:
        """
        Register the container with the communication manager.
        
        Args:
            communication_manager: The communication manager to register with
        """
        capabilities = {
            "supported_message_types": [
                MessageType.DIRECT,
                MessageType.BROADCAST,
                MessageType.TASK_REQUEST,
                MessageType.TASK_RESPONSE,
            ],
            "max_message_size": 1024 * 1024,  # 1 MB
            "supports_encryption": True,
            "dagger_version": "0.3.0",
        }
        
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to register container {self.container_id}")
        
        await communication_manager.register_container(
            container_id=self.container_id,
            capabilities=capabilities,
            use_circuit_breaker=True  # Default behavior
        )
        
        logger.info(f"Container {self.container_id} registered")
    
    async def unregister(self, communication_manager) -> None:
        """
        Unregister the container from the communication manager.
        
        Args:
            communication_manager: The communication manager to unregister from
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to unregister container {self.container_id}")
        
        await communication_manager.unregister_container(
            container_id=self.container_id,
            use_circuit_breaker=True  # Default behavior
        )
        
        logger.info(f"Container {self.container_id} unregistered")
    
    async def send_message(
        self,
        communication_manager,
        recipient_id: str,
        content: Any,
        message_type: MessageType = MessageType.DIRECT,
        use_circuit_breaker: bool = True,
    ) -> str:
        """
        Send a message to another container.
        
        Args:
            communication_manager: The communication manager to send the message through
            recipient_id: ID of the recipient container
            content: Content of the message
            message_type: Type of the message
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            The message ID
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to send message from container {self.container_id}")
        
        message_id = await communication_manager.send_message(
            sender_id=self.container_id,
            message_type=message_type,
            content=content,
            recipient_id=recipient_id if message_type != MessageType.BROADCAST else None,
            priority=MessagePriority.MEDIUM,
            ttl=60,  # 1 minute
            use_circuit_breaker=use_circuit_breaker,
        )
        
        logger.info(f"Container {self.container_id} sent {message_type} message {message_id} to {recipient_id if message_type != MessageType.BROADCAST else 'all'}")
        
        return message_id
    
    async def get_messages(
        self,
        communication_manager,
        use_circuit_breaker: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for the container.
        
        Args:
            communication_manager: The communication manager to get messages from
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            List of messages for the container
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to get messages for container {self.container_id}")
        
        messages = await communication_manager.get_messages(
            container_id=self.container_id,
            use_circuit_breaker=use_circuit_breaker,
        )
        
        self.messages.extend(messages)
        
        logger.info(f"Container {self.container_id} received {len(messages)} messages")
        
        return messages


async def demonstrate_dagger_communication() -> None:
    """Demonstrate the Dagger Communication Manager."""
    # Get the communication manager
    communication_manager = get_dagger_communication_manager()
    
    # Create containers with different failure probabilities
    reliable_container = MockDaggerContainer(container_id="reliable_container", fail_probability=0.0)
    unreliable_container = MockDaggerContainer(container_id="unreliable_container", fail_probability=0.8)
    
    try:
        # Register containers
        logger.info("Registering containers...")
        await reliable_container.register(communication_manager)
        
        try:
            await unreliable_container.register(communication_manager)
        except Exception as e:
            logger.error(f"Failed to register unreliable container: {str(e)}")
        
        # Send direct messages
        logger.info("\nSending direct messages...")
        for i in range(3):
            try:
                await reliable_container.send_message(
                    communication_manager=communication_manager,
                    recipient_id="unreliable_container",
                    content={"message": f"Hello {i} from reliable container"},
                    message_type=MessageType.DIRECT,
                )
            except SystemError as e:
                if e.code == ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN:
                    logger.warning(f"Circuit breaker is open: {str(e)}")
                else:
                    logger.error(f"System error: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
            
            # Add a small delay to see the circuit breaker state changes
            await asyncio.sleep(0.5)
        
        # Send broadcast messages
        logger.info("\nSending broadcast messages...")
        for i in range(2):
            try:
                await reliable_container.send_message(
                    communication_manager=communication_manager,
                    recipient_id=None,  # Broadcast to all
                    content={"message": f"Broadcast {i} from reliable container"},
                    message_type=MessageType.BROADCAST,
                )
            except SystemError as e:
                if e.code == ErrorCode.SYSTEM_CIRCUIT_BREAKER_OPEN:
                    logger.warning(f"Circuit breaker is open: {str(e)}")
                else:
                    logger.error(f"System error: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending broadcast message: {str(e)}")
            
            # Add a small delay
            await asyncio.sleep(0.5)
        
        # Get messages
        logger.info("\nGetting messages...")
        try:
            messages = await reliable_container.get_messages(communication_manager)
            logger.info(f"Reliable container has {len(messages)} messages")
            for message in messages:
                logger.info(f"Message from {message['sender_id']}: {message['content']}")
        except Exception as e:
            logger.error(f"Error getting messages for reliable container: {str(e)}")
        
        try:
            messages = await unreliable_container.get_messages(communication_manager)
            logger.info(f"Unreliable container has {len(messages)} messages")
            for message in messages:
                logger.info(f"Message from {message['sender_id']}: {message['content']}")
        except Exception as e:
            logger.error(f"Error getting messages for unreliable container: {str(e)}")
        
        # Demonstrate cross-system communication
        logger.info("\nDemonstrating cross-system communication...")
        
        # Create a non-Dagger agent
        from src.orchestrator.communication import get_communication_manager
        base_manager = get_communication_manager()
        
        # Register a non-Dagger agent
        await base_manager.register_agent(
            agent_id="non_dagger_agent",
            capabilities={"supports_dagger": False}
        )
        
        # Send a message from a Dagger container to a non-Dagger agent
        try:
            await reliable_container.send_message(
                communication_manager=communication_manager,
                recipient_id="non_dagger_agent",
                content={"message": "Hello from Dagger container to non-Dagger agent"},
                message_type=MessageType.DIRECT,
            )
            logger.info("Message sent from Dagger container to non-Dagger agent")
        except Exception as e:
            logger.error(f"Error sending message to non-Dagger agent: {str(e)}")
        
        # Get messages for the non-Dagger agent
        try:
            messages = await base_manager.get_messages(
                agent_id="non_dagger_agent"
            )
            logger.info(f"Non-Dagger agent has {len(messages)} messages")
            for message in messages:
                logger.info(f"Message from {message['sender_id']}: {message['content']}")
        except Exception as e:
            logger.error(f"Error getting messages for non-Dagger agent: {str(e)}")
        
        # Send a message from a non-Dagger agent to a Dagger container
        try:
            await base_manager.send_message(
                sender_id="non_dagger_agent",
                message_type=MessageType.DIRECT,
                content={"message": "Hello from non-Dagger agent to Dagger container"},
                recipient_id="reliable_container",
                priority=MessagePriority.MEDIUM,
            )
            logger.info("Message sent from non-Dagger agent to Dagger container")
        except Exception as e:
            logger.error(f"Error sending message from non-Dagger agent: {str(e)}")
        
        # Get messages for the Dagger container
        try:
            messages = await reliable_container.get_messages(communication_manager)
            logger.info(f"Reliable container has {len(messages)} messages")
            for message in messages:
                logger.info(f"Message from {message['sender_id']}: {message['content']}")
        except Exception as e:
            logger.error(f"Error getting messages for reliable container: {str(e)}")
        
        # Unregister containers
        logger.info("\nUnregistering containers...")
        await reliable_container.unregister(communication_manager)
        
        try:
            await unreliable_container.unregister(communication_manager)
        except Exception as e:
            logger.error(f"Failed to unregister unreliable container: {str(e)}")
        
        # Unregister non-Dagger agent
        await base_manager.unregister_agent(agent_id="non_dagger_agent")
    
    finally:
        # Shutdown the communication managers
        logger.info("\nShutting down communication managers...")
        await communication_manager.shutdown()
        await base_manager.shutdown()


async def demonstrate_with_real_dagger() -> None:
    """Demonstrate using the Dagger Communication Manager with real Dagger containers."""
    # This is a placeholder for a real Dagger implementation
    # In a real implementation, you would use the Dagger SDK to create and manage containers
    
    # Get the communication manager
    communication_manager = get_dagger_communication_manager()
    
    try:
        # Create a Dagger client
        async with dagger.Connection() as client:
            # Create containers
            container1 = client.container().from_("alpine:latest")
            container2 = client.container().from_("alpine:latest")
            
            # Register containers with the communication manager
            await communication_manager.register_container(
                container_id="container1",
                capabilities={
                    "dagger_version": "0.3.0",
                    "supported_message_types": [MessageType.DIRECT, MessageType.BROADCAST]
                }
            )
            
            await communication_manager.register_container(
                container_id="container2",
                capabilities={
                    "dagger_version": "0.3.0",
                    "supported_message_types": [MessageType.DIRECT, MessageType.BROADCAST]
                }
            )
            
            # Send a message from container1 to container2
            await communication_manager.send_message(
                sender_id="container1",
                message_type=MessageType.DIRECT,
                content={"command": "echo 'Hello from container1'"},
                recipient_id="container2",
                priority=MessagePriority.HIGH,
            )
            
            # Get messages for container2
            messages = await communication_manager.get_messages("container2")
            
            # Process messages
            for message in messages:
                if message["message_type"] == MessageType.DIRECT:
                    command = message["content"].get("command")
                    if command:
                        # Execute the command in container2
                        result = await container2.with_exec(["/bin/sh", "-c", command]).stdout()
                        logger.info(f"Command result: {result}")
            
            # Unregister containers
            await communication_manager.unregister_container("container1")
            await communication_manager.unregister_container("container2")
    
    finally:
        # Shutdown the communication manager
        await communication_manager.shutdown()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_dagger_communication())
    
    # Uncomment to run the real Dagger demonstration
    # asyncio.run(demonstrate_with_real_dagger())
