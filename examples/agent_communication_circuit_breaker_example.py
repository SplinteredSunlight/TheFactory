"""
Example demonstrating the use of the circuit breaker pattern with the agent communication module.

This example shows how to use the circuit breaker pattern to protect against cascading failures
when communicating with agents. It demonstrates both the default behavior (circuit breaker enabled)
and how to disable the circuit breaker for specific calls.

To run this example:
1. Make sure the AI-Orchestration-Platform is installed
2. Run this script: python examples/agent_communication_circuit_breaker_example.py
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional

from src.orchestrator.communication import (
    AgentCommunicationManager,
    MessageType,
    MessagePriority,
    get_communication_manager,
)
from src.orchestrator.circuit_breaker import (
    CircuitBreakerOpenError,
    CircuitBreakerState,
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


class MockAgent:
    """Mock agent for demonstration purposes."""
    
    def __init__(self, agent_id: str, fail_probability: float = 0.0):
        """
        Initialize a new MockAgent.
        
        Args:
            agent_id: ID of the agent
            fail_probability: Probability of failure (0.0 to 1.0)
        """
        self.agent_id = agent_id
        self.fail_probability = fail_probability
        self.messages: List[Dict[str, Any]] = []
    
    async def register(self, communication_manager: AgentCommunicationManager) -> None:
        """
        Register the agent with the communication manager.
        
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
        }
        
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to register agent {self.agent_id}")
        
        await communication_manager.register_agent(
            agent_id=self.agent_id,
            capabilities=capabilities,
            use_circuit_breaker=True  # Default behavior
        )
        
        logger.info(f"Agent {self.agent_id} registered")
    
    async def unregister(self, communication_manager: AgentCommunicationManager) -> None:
        """
        Unregister the agent from the communication manager.
        
        Args:
            communication_manager: The communication manager to unregister from
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to unregister agent {self.agent_id}")
        
        await communication_manager.unregister_agent(
            agent_id=self.agent_id,
            use_circuit_breaker=True  # Default behavior
        )
        
        logger.info(f"Agent {self.agent_id} unregistered")
    
    async def send_message(
        self,
        communication_manager: AgentCommunicationManager,
        recipient_id: str,
        content: Any,
        use_circuit_breaker: bool = True,
    ) -> str:
        """
        Send a message to another agent.
        
        Args:
            communication_manager: The communication manager to send the message through
            recipient_id: ID of the recipient agent
            content: Content of the message
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            The message ID
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to send message from agent {self.agent_id}")
        
        message_id = await communication_manager.send_message(
            sender_id=self.agent_id,
            message_type=MessageType.DIRECT,
            content=content,
            recipient_id=recipient_id,
            priority=MessagePriority.MEDIUM,
            ttl=60,  # 1 minute
            use_circuit_breaker=use_circuit_breaker,
        )
        
        logger.info(f"Agent {self.agent_id} sent message {message_id} to {recipient_id}")
        
        return message_id
    
    async def get_messages(
        self,
        communication_manager: AgentCommunicationManager,
        use_circuit_breaker: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for the agent.
        
        Args:
            communication_manager: The communication manager to get messages from
            use_circuit_breaker: Whether to use the circuit breaker
            
        Returns:
            List of messages for the agent
        """
        # Simulate failure based on fail_probability
        if random.random() < self.fail_probability:
            raise Exception(f"Failed to get messages for agent {self.agent_id}")
        
        messages = await communication_manager.get_messages(
            agent_id=self.agent_id,
            use_circuit_breaker=use_circuit_breaker,
        )
        
        self.messages.extend(messages)
        
        logger.info(f"Agent {self.agent_id} received {len(messages)} messages")
        
        return messages


async def demonstrate_circuit_breaker() -> None:
    """Demonstrate the circuit breaker pattern with the agent communication module."""
    # Get the communication manager
    communication_manager = get_communication_manager()
    
    # Create agents with different failure probabilities
    reliable_agent = MockAgent(agent_id="reliable_agent", fail_probability=0.0)
    unreliable_agent = MockAgent(agent_id="unreliable_agent", fail_probability=0.8)
    
    try:
        # Register agents
        logger.info("Registering agents...")
        await reliable_agent.register(communication_manager)
        
        try:
            await unreliable_agent.register(communication_manager)
        except Exception as e:
            logger.error(f"Failed to register unreliable agent: {str(e)}")
        
        # Send messages with circuit breaker enabled (default)
        logger.info("\nSending messages with circuit breaker enabled (default)...")
        for i in range(5):
            try:
                await reliable_agent.send_message(
                    communication_manager=communication_manager,
                    recipient_id="unreliable_agent",
                    content={"message": f"Hello {i} with circuit breaker"},
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
        
        # Send messages with circuit breaker disabled
        logger.info("\nSending messages with circuit breaker disabled...")
        for i in range(5):
            try:
                await reliable_agent.send_message(
                    communication_manager=communication_manager,
                    recipient_id="unreliable_agent",
                    content={"message": f"Hello {i} without circuit breaker"},
                    use_circuit_breaker=False,
                )
            except Exception as e:
                logger.error(f"Error sending message without circuit breaker: {str(e)}")
            
            # Add a small delay
            await asyncio.sleep(0.5)
        
        # Get messages
        logger.info("\nGetting messages...")
        try:
            messages = await reliable_agent.get_messages(communication_manager)
            logger.info(f"Reliable agent has {len(messages)} messages")
        except Exception as e:
            logger.error(f"Error getting messages for reliable agent: {str(e)}")
        
        try:
            messages = await unreliable_agent.get_messages(communication_manager)
            logger.info(f"Unreliable agent has {len(messages)} messages")
        except Exception as e:
            logger.error(f"Error getting messages for unreliable agent: {str(e)}")
        
        # Show circuit breaker state
        logger.info("\nCircuit breaker state:")
        circuit_breaker = communication_manager.circuit_breaker
        logger.info(f"State: {circuit_breaker.state}")
        logger.info(f"Failure count: {circuit_breaker.failure_count}")
        logger.info(f"Success count: {circuit_breaker.success_count}")
        logger.info(f"Last failure time: {circuit_breaker.last_failure_time}")
        logger.info(f"Last success time: {circuit_breaker.last_success_time}")
        
        # Wait for the circuit breaker to close if it's open
        if circuit_breaker.state == CircuitBreakerState.OPEN:
            logger.info("\nWaiting for circuit breaker to close...")
            # Wait for the circuit breaker timeout (typically a few seconds)
            await asyncio.sleep(circuit_breaker.reset_timeout)
            logger.info(f"Circuit breaker state after waiting: {circuit_breaker.state}")
        
        # Unregister agents
        logger.info("\nUnregistering agents...")
        await reliable_agent.unregister(communication_manager)
        
        try:
            await unreliable_agent.unregister(communication_manager)
        except Exception as e:
            logger.error(f"Failed to unregister unreliable agent: {str(e)}")
    
    finally:
        # Shutdown the communication manager
        logger.info("\nShutting down communication manager...")
        await communication_manager.shutdown()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_circuit_breaker())
