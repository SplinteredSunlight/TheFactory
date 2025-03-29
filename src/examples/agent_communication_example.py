#!/usr/bin/env python3
"""
Agent Communication Example

This script demonstrates how to use the Agent Communication Module in the AI-Orchestration-Platform.
It creates two agents and shows how they can communicate with each other.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orchestrator.communication import (
    MessageType,
    MessagePriority,
    get_communication_manager
)
from orchestrator.engine import OrchestratorEngine
from orchestrator.error_handling import ResourceError


async def setup_agents(orchestrator: OrchestratorEngine) -> Dict[str, Any]:
    """
    Set up two agents for the demonstration.
    
    Args:
        orchestrator: The orchestration engine
        
    Returns:
        Dictionary containing agent information and tokens
    """
    print("Setting up agents...")
    
    # Register the first agent
    agent1_id = f"agent1_{uuid.uuid4().hex[:8]}"
    agent1_token_info = await orchestrator.register_agent(
        agent_id=agent1_id,
        name="Agent 1",
        capabilities={
            "type": "assistant",
            "skills": ["text_processing", "data_analysis"],
            "communication": {
                "supports_broadcast": True,
                "supports_task_requests": True,
                "max_message_size": 10240,
            }
        }
    )
    
    # Register the second agent
    agent2_id = f"agent2_{uuid.uuid4().hex[:8]}"
    agent2_token_info = await orchestrator.register_agent(
        agent_id=agent2_id,
        name="Agent 2",
        capabilities={
            "type": "worker",
            "skills": ["code_generation", "image_processing"],
            "communication": {
                "supports_broadcast": True,
                "supports_task_requests": True,
                "max_message_size": 10240,
            }
        }
    )
    
    # Authenticate the agents
    agent1_auth = await orchestrator.authenticate_agent(
        agent_id=agent1_id,
        auth_token=agent1_token_info["auth_token"]
    )
    
    agent2_auth = await orchestrator.authenticate_agent(
        agent_id=agent2_id,
        auth_token=agent2_token_info["auth_token"]
    )
    
    print(f"Agent 1 ID: {agent1_id}")
    print(f"Agent 2 ID: {agent2_id}")
    
    return {
        "agent1": {
            "id": agent1_id,
            "token": agent1_auth["access_token"]
        },
        "agent2": {
            "id": agent2_id,
            "token": agent2_auth["access_token"]
        }
    }


async def demonstrate_direct_messaging(
    orchestrator: OrchestratorEngine,
    agents: Dict[str, Dict[str, str]]
) -> None:
    """
    Demonstrate direct messaging between agents.
    
    Args:
        orchestrator: The orchestration engine
        agents: Dictionary containing agent information and tokens
    """
    print("\n=== Direct Messaging ===")
    
    # Agent 1 sends a message to Agent 2
    print("Agent 1 sends a message to Agent 2...")
    message1_result = await orchestrator.send_agent_message(
        sender_id=agents["agent1"]["id"],
        message_type="direct",
        content={
            "text": "Hello, Agent 2! I need your help with a task.",
            "timestamp": datetime.now().isoformat()
        },
        recipient_id=agents["agent2"]["id"],
        priority="high",
        auth_token=agents["agent1"]["token"]
    )
    
    print(f"Message sent: {message1_result['message_id']}")
    
    # Agent 2 receives the message
    print("\nAgent 2 checks for messages...")
    messages = await orchestrator.get_agent_messages(
        agent_id=agents["agent2"]["id"],
        auth_token=agents["agent2"]["token"]
    )
    
    print(f"Agent 2 has {messages['count']} messages")
    for message in messages["messages"]:
        print(f"Message from {message['sender_id']}: {message['content']['text']}")
    
    # Agent 2 replies to Agent 1
    print("\nAgent 2 replies to Agent 1...")
    message2_result = await orchestrator.send_agent_message(
        sender_id=agents["agent2"]["id"],
        message_type="direct",
        content={
            "text": "Hello, Agent 1! I'm ready to help. What do you need?",
            "timestamp": datetime.now().isoformat()
        },
        recipient_id=agents["agent1"]["id"],
        correlation_id=messages["messages"][0]["correlation_id"],  # Reply to the first message
        priority="medium",
        auth_token=agents["agent2"]["token"]
    )
    
    print(f"Reply sent: {message2_result['message_id']}")
    
    # Agent 1 receives the reply
    print("\nAgent 1 checks for messages...")
    messages = await orchestrator.get_agent_messages(
        agent_id=agents["agent1"]["id"],
        auth_token=agents["agent1"]["token"]
    )
    
    print(f"Agent 1 has {messages['count']} messages")
    for message in messages["messages"]:
        print(f"Message from {message['sender_id']}: {message['content']['text']}")


async def demonstrate_broadcast_messaging(
    orchestrator: OrchestratorEngine,
    agents: Dict[str, Dict[str, str]]
) -> None:
    """
    Demonstrate broadcast messaging.
    
    Args:
        orchestrator: The orchestration engine
        agents: Dictionary containing agent information and tokens
    """
    print("\n=== Broadcast Messaging ===")
    
    # Register a third agent to receive the broadcast
    agent3_id = f"agent3_{uuid.uuid4().hex[:8]}"
    agent3_token_info = await orchestrator.register_agent(
        agent_id=agent3_id,
        name="Agent 3",
        capabilities={
            "type": "observer",
            "skills": ["monitoring"],
            "communication": {
                "supports_broadcast": True,
                "max_message_size": 10240,
            }
        }
    )
    
    agent3_auth = await orchestrator.authenticate_agent(
        agent_id=agent3_id,
        auth_token=agent3_token_info["auth_token"]
    )
    
    agents["agent3"] = {
        "id": agent3_id,
        "token": agent3_auth["access_token"]
    }
    
    print(f"Agent 3 ID: {agent3_id}")
    
    # Agent 1 sends a broadcast message
    print("\nAgent 1 sends a broadcast message...")
    broadcast_result = await orchestrator.send_agent_message(
        sender_id=agents["agent1"]["id"],
        message_type="broadcast",
        content={
            "text": "Attention all agents! This is an important announcement.",
            "timestamp": datetime.now().isoformat()
        },
        priority="high",
        auth_token=agents["agent1"]["token"]
    )
    
    print(f"Broadcast sent: {broadcast_result['message_id']}")
    
    # Agents 2 and 3 receive the broadcast
    print("\nAgent 2 checks for messages...")
    messages2 = await orchestrator.get_agent_messages(
        agent_id=agents["agent2"]["id"],
        auth_token=agents["agent2"]["token"]
    )
    
    print(f"Agent 2 has {messages2['count']} messages")
    for message in messages2["messages"]:
        print(f"Message from {message['sender_id']}: {message['content']['text']}")
    
    print("\nAgent 3 checks for messages...")
    messages3 = await orchestrator.get_agent_messages(
        agent_id=agents["agent3"]["id"],
        auth_token=agents["agent3"]["token"]
    )
    
    print(f"Agent 3 has {messages3['count']} messages")
    for message in messages3["messages"]:
        print(f"Message from {message['sender_id']}: {message['content']['text']}")


async def demonstrate_task_request(
    orchestrator: OrchestratorEngine,
    agents: Dict[str, Dict[str, str]]
) -> None:
    """
    Demonstrate task request and response messaging.
    
    Args:
        orchestrator: The orchestration engine
        agents: Dictionary containing agent information and tokens
    """
    print("\n=== Task Request and Response ===")
    
    # Agent 1 sends a task request to Agent 2
    print("Agent 1 sends a task request to Agent 2...")
    task_request_result = await orchestrator.send_agent_message(
        sender_id=agents["agent1"]["id"],
        message_type="task_request",
        content={
            "task_type": "code_generation",
            "parameters": {
                "language": "python",
                "description": "Write a function to calculate the Fibonacci sequence"
            },
            "deadline": (datetime.now().timestamp() + 3600),  # 1 hour from now
            "timestamp": datetime.now().isoformat()
        },
        recipient_id=agents["agent2"]["id"],
        priority="high",
        auth_token=agents["agent1"]["token"]
    )
    
    print(f"Task request sent: {task_request_result['message_id']}")
    
    # Agent 2 receives the task request
    print("\nAgent 2 checks for messages...")
    messages = await orchestrator.get_agent_messages(
        agent_id=agents["agent2"]["id"],
        auth_token=agents["agent2"]["token"]
    )
    
    print(f"Agent 2 has {messages['count']} messages")
    for message in messages["messages"]:
        if message["message_type"] == "task_request":
            task = message["content"]
            print(f"Task request from {message['sender_id']}: {task['task_type']}")
            print(f"Parameters: {json.dumps(task['parameters'], indent=2)}")
    
    # Agent 2 sends a task response to Agent 1
    print("\nAgent 2 sends a task response to Agent 1...")
    task_response_result = await orchestrator.send_agent_message(
        sender_id=agents["agent2"]["id"],
        message_type="task_response",
        content={
            "task_id": messages["messages"][0]["id"],
            "status": "completed",
            "result": {
                "code": """def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    
    return fib
""",
                "language": "python",
                "explanation": "This function returns the first n numbers in the Fibonacci sequence."
            },
            "timestamp": datetime.now().isoformat()
        },
        recipient_id=agents["agent1"]["id"],
        correlation_id=messages["messages"][0]["correlation_id"],  # Reply to the task request
        priority="high",
        auth_token=agents["agent2"]["token"]
    )
    
    print(f"Task response sent: {task_response_result['message_id']}")
    
    # Agent 1 receives the task response
    print("\nAgent 1 checks for messages...")
    messages = await orchestrator.get_agent_messages(
        agent_id=agents["agent1"]["id"],
        auth_token=agents["agent1"]["token"]
    )
    
    print(f"Agent 1 has {messages['count']} messages")
    for message in messages["messages"]:
        if message["message_type"] == "task_response":
            response = message["content"]
            print(f"Task response from {message['sender_id']}: {response['status']}")
            print(f"Result: {json.dumps(response['result'], indent=2)}")


async def demonstrate_agent_capabilities(
    orchestrator: OrchestratorEngine,
    agents: Dict[str, Dict[str, str]]
) -> None:
    """
    Demonstrate getting agent capabilities.
    
    Args:
        orchestrator: The orchestration engine
        agents: Dictionary containing agent information and tokens
    """
    print("\n=== Agent Capabilities ===")
    
    # Get Agent 1's capabilities
    print("Getting Agent 1's capabilities...")
    agent1_capabilities = await orchestrator.get_agent_communication_capabilities(
        agent_id=agents["agent1"]["id"]
    )
    
    print(f"Agent 1 capabilities: {json.dumps(agent1_capabilities, indent=2)}")
    
    # Get Agent 2's capabilities
    print("\nGetting Agent 2's capabilities...")
    agent2_capabilities = await orchestrator.get_agent_communication_capabilities(
        agent_id=agents["agent2"]["id"]
    )
    
    print(f"Agent 2 capabilities: {json.dumps(agent2_capabilities, indent=2)}")
    
    # Try to get capabilities for a non-existent agent
    print("\nTrying to get capabilities for a non-existent agent...")
    try:
        await orchestrator.get_agent_communication_capabilities(
            agent_id="non_existent_agent"
        )
    except ResourceError as e:
        print(f"Error: {e}")


async def cleanup_agents(
    orchestrator: OrchestratorEngine,
    agents: Dict[str, Dict[str, str]]
) -> None:
    """
    Clean up the agents created for the demonstration.
    
    Args:
        orchestrator: The orchestration engine
        agents: Dictionary containing agent information and tokens
    """
    print("\n=== Cleaning Up ===")
    
    # Unregister all agents
    for agent_key, agent_info in agents.items():
        print(f"Unregistering {agent_key}...")
        success = await orchestrator.unregister_agent(agent_info["id"])
        print(f"Unregistered: {success}")


async def main():
    """Main function to run the demonstration."""
    print("Agent Communication Example")
    print("==========================")
    
    # Create the orchestration engine
    orchestrator = OrchestratorEngine()
    
    try:
        # Set up agents
        agents = await setup_agents(orchestrator)
        
        # Demonstrate direct messaging
        await demonstrate_direct_messaging(orchestrator, agents)
        
        # Demonstrate broadcast messaging
        await demonstrate_broadcast_messaging(orchestrator, agents)
        
        # Demonstrate task request and response
        await demonstrate_task_request(orchestrator, agents)
        
        # Demonstrate getting agent capabilities
        await demonstrate_agent_capabilities(orchestrator, agents)
        
        # Clean up
        await cleanup_agents(orchestrator, agents)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
