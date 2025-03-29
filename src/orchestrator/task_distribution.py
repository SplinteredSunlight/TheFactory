"""
Task Distribution Module for AI-Orchestration-Platform

This module provides functionality for distributing tasks to appropriate agents
based on their capabilities, availability, and other factors.
"""

import asyncio
import logging
import random
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from src.orchestrator.communication import (
    get_communication_manager,
    MessageType,
    MessagePriority,
    Message
)
from src.orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ErrorSeverity,
    Component,
    ResourceError,
    get_error_handler
)

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class TaskDistributionStrategy(str, Enum):
    """Strategies for distributing tasks to agents."""
    CAPABILITY_MATCH = "capability_match"  # Match tasks to agents based on capabilities
    ROUND_ROBIN = "round_robin"  # Distribute tasks evenly among capable agents
    LOAD_BALANCED = "load_balanced"  # Distribute tasks based on agent load
    PRIORITY_BASED = "priority_based"  # Distribute tasks based on agent priority/ranking
    CUSTOM = "custom"  # Custom distribution strategy


class TaskDistributionError(BaseError):
    """Error raised when task distribution fails."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.ORCHESTRATOR_TASK_DISTRIBUTION_FAILED,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = Component.ORCHESTRATOR,
        documentation_url: Optional[str] = None,
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component,
            http_status=500,
            documentation_url=documentation_url,
        )


class TaskDistributor:
    """
    Handles the distribution of tasks to appropriate agents.
    
    The TaskDistributor is responsible for:
    1. Matching tasks to agents based on capabilities and requirements
    2. Implementing different distribution strategies
    3. Monitoring task execution and handling failures
    4. Load balancing across available agents
    """
    
    def __init__(self):
        """Initialize a new TaskDistributor."""
        self.communication_manager = get_communication_manager()
        
        # Cache of agent capabilities
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # Cache of agent load (number of active tasks)
        self.agent_load: Dict[str, int] = {}
        
        # Cache of agent priorities (higher is better)
        self.agent_priorities: Dict[str, int] = {}
        
        # Set of agents that are currently online
        self.online_agents: Set[str] = set()
        
        # Default distribution strategy
        self.default_strategy = TaskDistributionStrategy.CAPABILITY_MATCH
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        priority: int = 1
    ) -> None:
        """
        Register an agent with the task distributor.
        
        Args:
            agent_id: ID of the agent to register
            capabilities: List of agent capabilities
            priority: Priority of the agent (higher is better)
        """
        async with self.lock:
            self.agent_capabilities[agent_id] = capabilities
            self.agent_load[agent_id] = 0
            self.agent_priorities[agent_id] = priority
            self.online_agents.add(agent_id)
            
            logger.info(f"Agent {agent_id} registered with task distributor")
    
    async def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the task distributor.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        async with self.lock:
            self.agent_capabilities.pop(agent_id, None)
            self.agent_load.pop(agent_id, None)
            self.agent_priorities.pop(agent_id, None)
            self.online_agents.discard(agent_id)
            
            logger.info(f"Agent {agent_id} unregistered from task distributor")
    
    async def update_agent_status(
        self,
        agent_id: str,
        is_online: bool,
        current_load: Optional[int] = None
    ) -> None:
        """
        Update the status of an agent.
        
        Args:
            agent_id: ID of the agent
            is_online: Whether the agent is online
            current_load: Current load of the agent (number of active tasks)
        """
        async with self.lock:
            if is_online:
                self.online_agents.add(agent_id)
            else:
                self.online_agents.discard(agent_id)
            
            if current_load is not None and agent_id in self.agent_load:
                self.agent_load[agent_id] = current_load
    
    async def find_suitable_agents(
        self,
        required_capabilities: List[str],
        excluded_agents: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find agents that have the required capabilities.
        
        Args:
            required_capabilities: List of capabilities required for the task
            excluded_agents: List of agent IDs to exclude from consideration
            
        Returns:
            List of agent IDs that have the required capabilities
        """
        excluded = set(excluded_agents or [])
        suitable_agents = []
        
        async with self.lock:
            for agent_id, capabilities in self.agent_capabilities.items():
                if agent_id in excluded or agent_id not in self.online_agents:
                    continue
                
                # Check if the agent has all required capabilities
                if all(cap in capabilities for cap in required_capabilities):
                    suitable_agents.append(agent_id)
        
        return suitable_agents
    
    async def select_agent(
        self,
        suitable_agents: List[str],
        strategy: Optional[TaskDistributionStrategy] = None
    ) -> str:
        """
        Select an agent from the list of suitable agents using the specified strategy.
        
        Args:
            suitable_agents: List of suitable agent IDs
            strategy: Distribution strategy to use
            
        Returns:
            ID of the selected agent
            
        Raises:
            TaskDistributionError: If no suitable agent is found
        """
        if not suitable_agents:
            raise TaskDistributionError(
                message="No suitable agent found for task",
                details={"strategy": strategy}
            )
        
        # Use default strategy if none specified
        if strategy is None:
            strategy = self.default_strategy
        
        async with self.lock:
            if strategy == TaskDistributionStrategy.CAPABILITY_MATCH:
                # Just return the first suitable agent
                return suitable_agents[0]
            
            elif strategy == TaskDistributionStrategy.ROUND_ROBIN:
                # Simple round-robin: return a random agent
                return random.choice(suitable_agents)
            
            elif strategy == TaskDistributionStrategy.LOAD_BALANCED:
                # Find the agent with the lowest load
                min_load = float('inf')
                selected_agent = None
                
                for agent_id in suitable_agents:
                    load = self.agent_load.get(agent_id, 0)
                    if load < min_load:
                        min_load = load
                        selected_agent = agent_id
                
                return selected_agent
            
            elif strategy == TaskDistributionStrategy.PRIORITY_BASED:
                # Find the agent with the highest priority
                max_priority = -1
                selected_agent = None
                
                for agent_id in suitable_agents:
                    priority = self.agent_priorities.get(agent_id, 0)
                    if priority > max_priority:
                        max_priority = priority
                        selected_agent = agent_id
                
                return selected_agent
            
            else:
                # Default to the first agent
                return suitable_agents[0]
    
    async def distribute_task(
        self,
        task_id: str,
        task_type: str,
        required_capabilities: List[str],
        task_data: Dict[str, Any],
        sender_id: str,
        strategy: Optional[TaskDistributionStrategy] = None,
        excluded_agents: Optional[List[str]] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Distribute a task to an appropriate agent.
        
        Args:
            task_id: ID of the task
            task_type: Type of the task
            required_capabilities: Capabilities required for the task
            task_data: Data for the task
            sender_id: ID of the sender
            strategy: Distribution strategy to use
            excluded_agents: List of agent IDs to exclude
            priority: Priority of the task
            ttl: Time-to-live in seconds
            metadata: Additional metadata for the task
            auth_token: Authentication token for the sender
            
        Returns:
            Dictionary containing the distribution result
            
        Raises:
            TaskDistributionError: If task distribution fails
        """
        try:
            # Find suitable agents
            suitable_agents = await self.find_suitable_agents(
                required_capabilities=required_capabilities,
                excluded_agents=excluded_agents
            )
            
            if not suitable_agents:
                raise TaskDistributionError(
                    message="No suitable agent found for task",
                    details={
                        "task_id": task_id,
                        "task_type": task_type,
                        "required_capabilities": required_capabilities
                    }
                )
            
            # Select an agent using the specified strategy
            selected_agent = await self.select_agent(
                suitable_agents=suitable_agents,
                strategy=strategy
            )
            
            # Update agent load
            async with self.lock:
                self.agent_load[selected_agent] = self.agent_load.get(selected_agent, 0) + 1
            
            # Create task message
            task_message = {
                "task_id": task_id,
                "task_type": task_type,
                "data": task_data,
                "sender_id": sender_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Send task request to the selected agent
            message_id = await self.communication_manager.send_message(
                sender_id=sender_id,
                message_type=MessageType.TASK_REQUEST,
                content=task_message,
                recipient_id=selected_agent,
                correlation_id=task_id,
                priority=priority,
                ttl=ttl,
                metadata=metadata,
                auth_token=auth_token,
            )
            
            logger.info(f"Task {task_id} distributed to agent {selected_agent}")
            
            return {
                "task_id": task_id,
                "agent_id": selected_agent,
                "message_id": message_id,
                "status": "distributed",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            if isinstance(e, TaskDistributionError):
                error_handler.log_error(e, {
                    "task_id": task_id,
                    "task_type": task_type,
                    "sender_id": sender_id
                })
                raise
            
            error = TaskDistributionError(
                message=f"Failed to distribute task: {str(e)}",
                details={
                    "task_id": task_id,
                    "task_type": task_type,
                    "sender_id": sender_id
                }
            )
            error_handler.log_error(error, {
                "task_id": task_id,
                "task_type": task_type,
                "sender_id": sender_id
            })
            raise error
    
    async def handle_task_response(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Handle a task response from an agent.
        
        Args:
            task_id: ID of the task
            agent_id: ID of the agent that executed the task
            status: Status of the task execution
            result: Result of the task execution
            error: Error message if the task failed
        """
        # Update agent load
        async with self.lock:
            if agent_id in self.agent_load:
                self.agent_load[agent_id] = max(0, self.agent_load.get(agent_id, 0) - 1)
        
        logger.info(f"Task {task_id} completed by agent {agent_id} with status {status}")


# Singleton instance
_task_distributor_instance: Optional[TaskDistributor] = None


def get_task_distributor() -> TaskDistributor:
    """
    Get the TaskDistributor singleton instance.
    
    Returns:
        The TaskDistributor instance
    """
    global _task_distributor_instance
    
    if _task_distributor_instance is None:
        _task_distributor_instance = TaskDistributor()
    
    return _task_distributor_instance
