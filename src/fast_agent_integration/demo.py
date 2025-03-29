"""
Fast-Agent Integration Demo

This script demonstrates how to import and use Fast-Agent within the AI-Orchestration-Platform.
It showcases the authentication mechanism between AI-Orchestrator and Fast-Agent.
"""

import asyncio
import os
import time
import logging
from typing import Optional, Dict, Any

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent, AgentConfig
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from rich import print

from orchestrator.auth import AuthenticationError, AuthorizationError
from fast_agent_integration.adapter import get_adapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastAgentDemo:
    """Demo class for Fast-Agent integration."""

    def __init__(self, app_name: str = "ai_orchestration_platform", api_key: Optional[str] = None):
        """Initialize the Fast-Agent demo.

        Args:
            app_name: Name of the MCP application
            api_key: API key for authenticating with the orchestrator
        """
        self.app_name = app_name
        self.api_key = api_key or os.environ.get("ORCHESTRATOR_API_KEY") or "fast-agent-default-key"
        self.app = MCPApp(name=app_name)

    async def run_basic_agent(
        self,
        query: str,
        agent_name: str = "orchestrator_agent",
        model: str = "gpt-4",
        use_anthropic: bool = False,
    ) -> str:
        """Run a basic agent with the given query.

        Args:
            query: The query to send to the agent
            agent_name: Name of the agent
            model: Model to use (default: gpt-4)
            use_anthropic: Whether to use Anthropic instead of OpenAI

        Returns:
            The agent's response
        """
        result = None

        async with self.app.run():
            # Configure the agent
            agent_config = AgentConfig(
                name=agent_name,
                instruction="""You are an AI orchestration agent that helps users 
                with various tasks. You have access to tools and can execute 
                commands to accomplish user goals.""",
                servers=["fetch", "filesystem", "orchestrator"],  # Include orchestrator MCP server
                model=model,
            )

            # Create the agent
            agent = Agent(config=agent_config)

            async with agent:
                # Attach the appropriate LLM
                if use_anthropic:
                    llm = await agent.attach_llm(AnthropicAugmentedLLM)
                else:
                    llm = await agent.attach_llm(OpenAIAugmentedLLM)

                # Generate a response to the query
                result = await llm.generate_str(message=query)

        return result
    
    async def run_authenticated_agent(
        self,
        query: str,
        agent_name: str = "orchestrator_agent",
        instruction: str = "You are an AI orchestration agent that helps users with various tasks.",
        model: str = "gpt-4",
        use_anthropic: bool = False,
    ) -> Dict[str, Any]:
        """Run an agent with authentication.

        Args:
            query: The query to send to the agent
            agent_name: Name of the agent
            instruction: Instructions for the agent
            model: Model to use (default: gpt-4)
            use_anthropic: Whether to use Anthropic instead of OpenAI

        Returns:
            Dictionary containing the agent ID and response
        """
        try:
            # Get the adapter
            adapter = await get_adapter(app_name=self.app_name, api_key=self.api_key)
            
            # Create and run the agent
            result = await adapter.create_and_run_agent(
                name=agent_name,
                instruction=instruction,
                query=query,
                model=model,
                use_anthropic=use_anthropic,
            )
            
            return result
            
        except (AuthenticationError, AuthorizationError) as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                "agent_id": None,
                "response": f"Error: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return {
                "agent_id": None,
                "response": f"Error: {str(e)}",
            }


async def main():
    """Run the Fast-Agent demo."""
    # Get API key from environment variable
    api_key = os.environ.get("ORCHESTRATOR_API_KEY")
    
    # Create demo instance
    demo = FastAgentDemo(api_key=api_key)
    
    # Example query
    query = "What are the key features of AI orchestration platforms?"
    
    print("🤖 Running basic Fast-Agent demo...")
    start = time.time()
    
    response = await demo.run_basic_agent(query)
    
    end = time.time()
    t = end - start
    
    print(f"✅ Response received in {t:.2f}s")
    print(f"📝 Response: {response}")
    
    print("\n🔐 Running authenticated Fast-Agent demo...")
    start = time.time()
    
    result = await demo.run_authenticated_agent(
        query="How does authentication work in AI orchestration platforms?",
        agent_name="auth_demo_agent",
        instruction="""You are an AI orchestration agent that specializes in authentication 
        and security. Explain concepts clearly and provide practical examples.""",
    )
    
    end = time.time()
    t = end - start
    
    print(f"✅ Response received in {t:.2f}s")
    print(f"🆔 Agent ID: {result['agent_id']}")
    print(f"📝 Response: {result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
