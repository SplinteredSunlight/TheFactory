"""
Tests for the Task Distribution module.

This module contains tests for the task distribution functionality in the AI-Orchestration-Platform.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.orchestrator.task_distribution import (
    TaskDistributor,
    TaskDistributionStrategy,
    TaskDistributionError,
    get_task_distributor
)
from src.orchestrator.communication import MessageType, MessagePriority


@pytest.fixture
def task_distributor():
    """Create a TaskDistributor instance for testing."""
    distributor = TaskDistributor()
    # Mock the communication manager
    distributor.communication_manager = AsyncMock()
    distributor.communication_manager.send_message = AsyncMock(return_value="message-id-123")
    return distributor


@pytest.mark.asyncio
async def test_register_agent(task_distributor):
    """Test registering an agent with the task distributor."""
    agent_id = "agent-123"
    capabilities = ["text_processing", "code_generation"]
    priority = 2
    
    await task_distributor.register_agent(agent_id, capabilities, priority)
    
    assert agent_id in task_distributor.agent_capabilities
    assert task_distributor.agent_capabilities[agent_id] == capabilities
    assert task_distributor.agent_priorities[agent_id] == priority
    assert task_distributor.agent_load[agent_id] == 0
    assert agent_id in task_distributor.online_agents


@pytest.mark.asyncio
async def test_unregister_agent(task_distributor):
    """Test unregistering an agent from the task distributor."""
    agent_id = "agent-123"
    capabilities = ["text_processing", "code_generation"]
    
    # Register the agent first
    await task_distributor.register_agent(agent_id, capabilities)
    
    # Verify the agent is registered
    assert agent_id in task_distributor.agent_capabilities
    
    # Unregister the agent
    await task_distributor.unregister_agent(agent_id)
    
    # Verify the agent is unregistered
    assert agent_id not in task_distributor.agent_capabilities
    assert agent_id not in task_distributor.agent_load
    assert agent_id not in task_distributor.agent_priorities
    assert agent_id not in task_distributor.online_agents


@pytest.mark.asyncio
async def test_update_agent_status(task_distributor):
    """Test updating an agent's status."""
    agent_id = "agent-123"
    capabilities = ["text_processing", "code_generation"]
    
    # Register the agent first
    await task_distributor.register_agent(agent_id, capabilities)
    
    # Update the agent's status to offline
    await task_distributor.update_agent_status(agent_id, False)
    
    # Verify the agent is offline
    assert agent_id not in task_distributor.online_agents
    
    # Update the agent's status to online with a load
    await task_distributor.update_agent_status(agent_id, True, 5)
    
    # Verify the agent is online with the specified load
    assert agent_id in task_distributor.online_agents
    assert task_distributor.agent_load[agent_id] == 5


@pytest.mark.asyncio
async def test_find_suitable_agents(task_distributor):
    """Test finding suitable agents based on capabilities."""
    # Register some agents with different capabilities
    await task_distributor.register_agent(
        "agent-1", ["text_processing", "code_generation"]
    )
    await task_distributor.register_agent(
        "agent-2", ["text_processing", "image_analysis"]
    )
    await task_distributor.register_agent(
        "agent-3", ["code_generation", "data_extraction"]
    )
    
    # Find agents with text_processing capability
    suitable_agents = await task_distributor.find_suitable_agents(["text_processing"])
    
    # Verify the suitable agents
    assert len(suitable_agents) == 2
    assert "agent-1" in suitable_agents
    assert "agent-2" in suitable_agents
    
    # Find agents with code_generation and text_processing capabilities
    suitable_agents = await task_distributor.find_suitable_agents(
        ["code_generation", "text_processing"]
    )
    
    # Verify the suitable agents
    assert len(suitable_agents) == 1
    assert "agent-1" in suitable_agents
    
    # Find agents with a capability that no agent has
    suitable_agents = await task_distributor.find_suitable_agents(["unknown_capability"])
    
    # Verify no agents are found
    assert len(suitable_agents) == 0
    
    # Find agents with exclusions
    suitable_agents = await task_distributor.find_suitable_agents(
        ["text_processing"], ["agent-1"]
    )
    
    # Verify the suitable agents (agent-1 should be excluded)
    assert len(suitable_agents) == 1
    assert "agent-2" in suitable_agents


@pytest.mark.asyncio
async def test_select_agent_capability_match(task_distributor):
    """Test selecting an agent using the CAPABILITY_MATCH strategy."""
    suitable_agents = ["agent-1", "agent-2", "agent-3"]
    
    # Select an agent using the CAPABILITY_MATCH strategy
    selected_agent = await task_distributor.select_agent(
        suitable_agents, TaskDistributionStrategy.CAPABILITY_MATCH
    )
    
    # Verify the selected agent is the first one
    assert selected_agent == "agent-1"


@pytest.mark.asyncio
async def test_select_agent_round_robin(task_distributor):
    """Test selecting an agent using the ROUND_ROBIN strategy."""
    suitable_agents = ["agent-1", "agent-2", "agent-3"]
    
    # Select an agent using the ROUND_ROBIN strategy
    with patch("random.choice", return_value="agent-2"):
        selected_agent = await task_distributor.select_agent(
            suitable_agents, TaskDistributionStrategy.ROUND_ROBIN
        )
    
    # Verify the selected agent is the one returned by random.choice
    assert selected_agent == "agent-2"


@pytest.mark.asyncio
async def test_select_agent_load_balanced(task_distributor):
    """Test selecting an agent using the LOAD_BALANCED strategy."""
    # Register some agents with different loads
    await task_distributor.register_agent("agent-1", ["text_processing"])
    await task_distributor.register_agent("agent-2", ["text_processing"])
    await task_distributor.register_agent("agent-3", ["text_processing"])
    
    # Set different loads
    task_distributor.agent_load["agent-1"] = 5
    task_distributor.agent_load["agent-2"] = 2
    task_distributor.agent_load["agent-3"] = 8
    
    # Select an agent using the LOAD_BALANCED strategy
    selected_agent = await task_distributor.select_agent(
        ["agent-1", "agent-2", "agent-3"], TaskDistributionStrategy.LOAD_BALANCED
    )
    
    # Verify the selected agent is the one with the lowest load
    assert selected_agent == "agent-2"


@pytest.mark.asyncio
async def test_select_agent_priority_based(task_distributor):
    """Test selecting an agent using the PRIORITY_BASED strategy."""
    # Register some agents with different priorities
    await task_distributor.register_agent("agent-1", ["text_processing"], 3)
    await task_distributor.register_agent("agent-2", ["text_processing"], 5)
    await task_distributor.register_agent("agent-3", ["text_processing"], 1)
    
    # Select an agent using the PRIORITY_BASED strategy
    selected_agent = await task_distributor.select_agent(
        ["agent-1", "agent-2", "agent-3"], TaskDistributionStrategy.PRIORITY_BASED
    )
    
    # Verify the selected agent is the one with the highest priority
    assert selected_agent == "agent-2"


@pytest.mark.asyncio
async def test_select_agent_no_suitable_agents(task_distributor):
    """Test selecting an agent when there are no suitable agents."""
    # Try to select an agent with an empty list
    with pytest.raises(TaskDistributionError):
        await task_distributor.select_agent([], TaskDistributionStrategy.CAPABILITY_MATCH)


@pytest.mark.asyncio
async def test_distribute_task(task_distributor):
    """Test distributing a task to an agent."""
    # Register some agents
    await task_distributor.register_agent(
        "agent-1", ["text_processing", "code_generation"]
    )
    await task_distributor.register_agent(
        "agent-2", ["text_processing", "image_analysis"]
    )
    
    # Distribute a task
    result = await task_distributor.distribute_task(
        task_id="task-123",
        task_type="code_generation",
        required_capabilities=["text_processing", "code_generation"],
        task_data={"prompt": "Write a function to calculate Fibonacci numbers"},
        sender_id="orchestrator",
        strategy=TaskDistributionStrategy.CAPABILITY_MATCH,
        priority=MessagePriority.HIGH,
    )
    
    # Verify the result
    assert result["task_id"] == "task-123"
    assert result["agent_id"] == "agent-1"
    assert result["message_id"] == "message-id-123"
    assert result["status"] == "distributed"
    
    # Verify the agent's load was updated
    assert task_distributor.agent_load["agent-1"] == 1
    
    # Verify the message was sent
    task_distributor.communication_manager.send_message.assert_called_once()
    call_args = task_distributor.communication_manager.send_message.call_args[1]
    assert call_args["sender_id"] == "orchestrator"
    assert call_args["message_type"] == MessageType.TASK_REQUEST
    assert call_args["recipient_id"] == "agent-1"
    assert call_args["correlation_id"] == "task-123"
    assert call_args["priority"] == MessagePriority.HIGH


@pytest.mark.asyncio
async def test_distribute_task_no_suitable_agents(task_distributor):
    """Test distributing a task when there are no suitable agents."""
    # Register an agent with different capabilities
    await task_distributor.register_agent("agent-1", ["text_processing"])
    
    # Try to distribute a task requiring capabilities the agent doesn't have
    with pytest.raises(TaskDistributionError):
        await task_distributor.distribute_task(
            task_id="task-123",
            task_type="code_generation",
            required_capabilities=["code_generation", "data_extraction"],
            task_data={"prompt": "Extract data from this document"},
            sender_id="orchestrator",
        )


@pytest.mark.asyncio
async def test_handle_task_response(task_distributor):
    """Test handling a task response from an agent."""
    # Register an agent and set its load
    await task_distributor.register_agent("agent-1", ["text_processing"])
    task_distributor.agent_load["agent-1"] = 3
    
    # Handle a task response
    await task_distributor.handle_task_response(
        task_id="task-123",
        agent_id="agent-1",
        status="completed",
        result={"output": "Task completed successfully"},
    )
    
    # Verify the agent's load was updated
    assert task_distributor.agent_load["agent-1"] == 2


@pytest.mark.asyncio
async def test_get_task_distributor():
    """Test getting the TaskDistributor singleton instance."""
    # Get the singleton instance
    distributor1 = get_task_distributor()
    distributor2 = get_task_distributor()
    
    # Verify both instances are the same
    assert distributor1 is distributor2
