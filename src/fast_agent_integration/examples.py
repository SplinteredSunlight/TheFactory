"""
Fast-Agent Integration Examples

This module provides examples of how to use the Fast-Agent adapter in the AI-Orchestration-Platform.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

from agent_manager.manager import AgentManager
from fast_agent_integration.factory import register_fast_agent_factory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_usage_example():
    """
    Basic example of using the Fast-Agent adapter.
    
    This example demonstrates how to:
    1. Create an AgentManager
    2. Register the Fast-Agent factory
    3. Create a Fast-Agent agent
    4. Execute the agent
    5. Clean up resources
    """
    # Create an AgentManager
    agent_manager = AgentManager()
    
    # Register the Fast-Agent factory
    factory = await register_fast_agent_factory(
        agent_manager=agent_manager,
        app_name="example-app",
        api_key=os.environ.get("ORCHESTRATOR_API_KEY"),
    )
    
    try:
        # Create a Fast-Agent agent
        agent = agent_manager.create_agent(
            agent_type="fast_agent",
            name="Example Agent",
            description="An example agent that demonstrates the Fast-Agent adapter",
            instruction="You are a helpful AI assistant that provides concise and accurate information.",
            model="gpt-4",
            use_anthropic=False,
        )
        
        logger.info(f"Created agent: {agent.name} (ID: {agent.id})")
        
        # Execute the agent
        result = agent.execute(
            query="What are the key features of the AI-Orchestration-Platform?",
        )
        
        logger.info(f"Agent response: {result['outputs']['response']}")
        
        # List all agents
        agents = agent_manager.list_agents()
        logger.info(f"Registered agents: {len(agents)}")
        
        # Find agents by capability
        text_agents = agent_manager.find_agents_by_capability("text_generation")
        logger.info(f"Agents with text_generation capability: {len(text_agents)}")
        
    finally:
        # Clean up resources
        await factory.shutdown()
        logger.info("Resources cleaned up")


async def advanced_usage_example():
    """
    Advanced example of using the Fast-Agent adapter.
    
    This example demonstrates how to:
    1. Create multiple agents with different configurations
    2. Execute agents with different parameters
    3. Handle errors
    4. Use agent capabilities
    """
    # Create an AgentManager
    agent_manager = AgentManager()
    
    # Register the Fast-Agent factory
    factory = await register_fast_agent_factory(
        agent_manager=agent_manager,
        app_name="advanced-example",
        api_key=os.environ.get("ORCHESTRATOR_API_KEY"),
    )
    
    try:
        # Create a code generation agent
        code_agent = agent_manager.create_agent(
            agent_type="fast_agent",
            name="Code Assistant",
            description="An agent that specializes in generating and explaining code",
            instruction="""You are a code assistant that helps users write and understand code.
            Always provide clear explanations and follow best practices.""",
            model="gpt-4",
            use_anthropic=False,
        )
        
        # Create a creative writing agent
        writing_agent = agent_manager.create_agent(
            agent_type="fast_agent",
            name="Creative Writer",
            description="An agent that specializes in creative writing",
            instruction="""You are a creative writing assistant that helps users with
            storytelling, poetry, and other creative writing tasks.""",
            model="claude-3-opus-20240229",
            use_anthropic=True,
        )
        
        logger.info(f"Created code agent: {code_agent.name} (ID: {code_agent.id})")
        logger.info(f"Created writing agent: {writing_agent.name} (ID: {writing_agent.id})")
        
        # Execute the code agent
        code_result = code_agent.execute(
            query="Write a Python function that calculates the Fibonacci sequence up to n terms.",
        )
        
        logger.info(f"Code agent response: {code_result['outputs']['response'][:100]}...")
        
        # Execute the writing agent
        writing_result = writing_agent.execute(
            query="Write a short poem about artificial intelligence.",
        )
        
        logger.info(f"Writing agent response: {writing_result['outputs']['response'][:100]}...")
        
        # Try to execute with an invalid query
        try:
            invalid_result = code_agent.execute(
                query="",  # Empty query
            )
        except ValueError as e:
            logger.error(f"Error executing agent: {str(e)}")
        
        # Find agents by capability
        code_agents = agent_manager.find_agents_by_capability("code_generation")
        logger.info(f"Agents with code_generation capability: {len(code_agents)}")
        
    finally:
        # Clean up resources
        await factory.shutdown()
        logger.info("Resources cleaned up")


def run_example(example_func):
    """
    Run an async example function.
    
    Args:
        example_func: The async function to run
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example_func())


if __name__ == "__main__":
    # Run the basic example
    print("\n=== Running Basic Example ===\n")
    run_example(basic_usage_example)
    
    # Run the advanced example
    print("\n=== Running Advanced Example ===\n")
    run_example(advanced_usage_example)
