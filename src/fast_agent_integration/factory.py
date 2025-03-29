"""
Fast-Agent Factory Module

This module provides a factory for creating Fast-Agent agents in the AI-Orchestration-Platform.
It integrates with the AgentManager to register Fast-Agent as an available agent type.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Type, cast

from agent_manager.manager import Agent, AgentManager
from agent_manager.adapter import AdapterFactory, AdapterAgent
from fast_agent_integration.fast_agent_adapter import FastAgentAdapterImpl, create_fast_agent_adapter

# Configure logging
logger = logging.getLogger(__name__)


class FastAgentFactory:
    """Factory for creating Fast-Agent agents."""
    
    def __init__(
        self,
        agent_manager: AgentManager,
        config_path: Optional[str] = None,
        app_name: str = "ai_orchestration_platform",
        api_key: Optional[str] = None,
    ):
        """
        Initialize a new FastAgentFactory.
        
        Args:
            agent_manager: The AgentManager to register with
            config_path: Path to the Fast-Agent configuration file
            app_name: Name of the MCP application
            api_key: API key for authenticating with the orchestrator
        """
        self.agent_manager = agent_manager
        self.config_path = config_path
        self.app_name = app_name
        self.api_key = api_key
        self.adapter_factory = AdapterFactory(
            adapter_class=FastAgentAdapterImpl,
            config_path=config_path,
            app_name=app_name,
            api_key=api_key,
        )
    
    async def initialize(self) -> None:
        """Initialize the factory and register with the AgentManager."""
        try:
            # Initialize the adapter
            await self.adapter_factory.get_adapter()
            
            # Register the factory with the AgentManager
            self.agent_manager.register_agent_type(
                name="fast_agent",
                agent_class=self._create_agent_wrapper,
            )
            
            logger.info("Registered Fast-Agent factory with AgentManager")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fast-Agent factory: {str(e)}")
            raise
    
    def _create_agent_wrapper(self, agent_id: str, name: str, description: Optional[str] = None, **kwargs) -> Agent:
        """
        Wrapper for creating a Fast-Agent agent.
        
        This method is called by the AgentManager when creating a new agent of type "fast_agent".
        It creates an event loop if one doesn't exist and runs the async creation.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Optional description of the agent
            **kwargs: Additional parameters for the agent
            
        Returns:
            The newly created Agent
        """
        # Get or create an event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async creation
        return loop.run_until_complete(self._create_agent_async(agent_id, name, description, **kwargs))
    
    async def _create_agent_async(self, agent_id: str, name: str, description: Optional[str] = None, **kwargs) -> Agent:
        """
        Asynchronously create a Fast-Agent agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Optional description of the agent
            **kwargs: Additional parameters for the agent
            
        Returns:
            The newly created Agent
        """
        return await self.adapter_factory.create_agent(agent_id, name, description, **kwargs)
    
    async def shutdown(self) -> None:
        """Shutdown the factory and release resources."""
        await self.adapter_factory.shutdown()
        logger.info("Fast-Agent factory shut down")


# Function to register the Fast-Agent factory with the AgentManager
async def register_fast_agent_factory(
    agent_manager: AgentManager,
    config_path: Optional[str] = None,
    app_name: str = "ai_orchestration_platform",
    api_key: Optional[str] = None,
) -> FastAgentFactory:
    """
    Register the Fast-Agent factory with the AgentManager.
    
    Args:
        agent_manager: The AgentManager to register with
        config_path: Path to the Fast-Agent configuration file
        app_name: Name of the MCP application
        api_key: API key for authenticating with the orchestrator
        
    Returns:
        The FastAgentFactory instance
    """
    factory = FastAgentFactory(
        agent_manager=agent_manager,
        config_path=config_path,
        app_name=app_name,
        api_key=api_key,
    )
    
    await factory.initialize()
    
    return factory
