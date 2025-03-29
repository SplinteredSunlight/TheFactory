"""
Fast-Agent Adapter Implementation

This module implements the AgentAdapter interface for the Fast-Agent framework.
It provides a bridge between the AI-Orchestration-Platform and Fast-Agent.
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, cast

from agent_manager.adapter import AgentAdapter
from fast_agent_integration.adapter import FastAgentAdapter as CoreFastAgentAdapter, get_adapter
from orchestrator.auth import AuthenticationError, AuthorizationError

# Configure logging
logger = logging.getLogger(__name__)


class FastAgentAdapterImpl(AgentAdapter):
    """Implementation of the AgentAdapter interface for Fast-Agent."""
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        app_name: str = "ai_orchestration_platform",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Fast-Agent adapter.
        
        Args:
            config_path: Path to the Fast-Agent configuration file
            app_name: Name of the MCP application
            api_key: API key for authenticating with the orchestrator
        """
        self.config_path = config_path
        self.app_name = app_name
        self.api_key = api_key
        self.core_adapter: Optional[CoreFastAgentAdapter] = None
        
        # Store agent metadata
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self) -> None:
        """Initialize the adapter."""
        try:
            # Get the core adapter
            self.core_adapter = await get_adapter(
                config_path=self.config_path,
                app_name=self.app_name,
                api_key=self.api_key,
            )
            
            logger.info(f"Initialized Fast-Agent adapter for {self.app_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fast-Agent adapter: {str(e)}")
            raise
    
    async def create_agent(
        self,
        agent_id: str,
        name: str,
        description: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a new agent using this adapter.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Optional description of the agent
            **kwargs: Additional parameters for the agent
                - instruction: Instructions for the agent
                - model: Model to use (default: gpt-4)
                - servers: List of MCP servers to use
                - use_anthropic: Whether to use Anthropic instead of OpenAI
            
        Returns:
            The agent ID in the Fast-Agent framework
            
        Raises:
            ValueError: If the adapter is not initialized
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        if not self.core_adapter:
            raise ValueError("Fast-Agent adapter not initialized")
        
        # Extract parameters from kwargs
        instruction = kwargs.get("instruction", f"You are an AI agent named {name}.")
        if description:
            instruction += f" {description}"
            
        model = kwargs.get("model", "gpt-4")
        servers = kwargs.get("servers")
        use_anthropic = kwargs.get("use_anthropic", False)
        
        # Create the agent
        try:
            external_id = await self.core_adapter.create_agent(
                name=name,
                instruction=instruction,
                model=model,
                servers=servers,
                use_anthropic=use_anthropic,
            )
            
            # Store agent metadata
            self.agent_metadata[external_id] = {
                "agent_id": agent_id,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "model": model,
                "use_anthropic": use_anthropic,
                "servers": servers,
                "instruction": instruction,
            }
            
            logger.info(f"Created Fast-Agent agent {name} with ID {external_id}")
            
            return external_id
            
        except Exception as e:
            logger.error(f"Failed to create Fast-Agent agent {name}: {str(e)}")
            raise
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get information about an agent.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            Dictionary containing agent information
            
        Raises:
            ValueError: If the adapter is not initialized
            KeyError: If the agent doesn't exist
        """
        if not self.core_adapter:
            raise ValueError("Fast-Agent adapter not initialized")
        
        try:
            # Get agent info from the core adapter
            agent_info = await self.core_adapter.orchestrator.get_agent(agent_id)
            
            # Combine with stored metadata
            metadata = self.agent_metadata.get(agent_id, {})
            
            # Determine capabilities based on the agent's model and provider
            capabilities = []
            if "capabilities" in agent_info:
                provider = agent_info["capabilities"].get("provider", "openai")
                model = agent_info["capabilities"].get("model", "gpt-4")
                
                # Add capabilities based on the model and provider
                capabilities.append("text_generation")
                capabilities.append("conversation")
                
                if "gpt-4" in model:
                    capabilities.append("code_generation")
                    capabilities.append("reasoning")
                
                if provider == "anthropic":
                    capabilities.append("long_context")
            
            # Combine all information
            result = {
                "id": agent_id,
                "name": metadata.get("name", agent_info.get("name", "")),
                "description": metadata.get("description", ""),
                "capabilities": capabilities,
                "status": "idle",  # We don't have real-time status from Fast-Agent
                "created_at": metadata.get("created_at", datetime.now().isoformat()),
                "last_active": None,
                "metadata": {
                    "framework": "fast-agent",
                    "model": agent_info.get("capabilities", {}).get("model", "gpt-4"),
                    "provider": agent_info.get("capabilities", {}).get("provider", "openai"),
                    "servers": agent_info.get("capabilities", {}).get("servers", []),
                    "instruction": metadata.get("instruction", ""),
                }
            }
            
            return result
            
        except KeyError:
            logger.error(f"Agent not found: {agent_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to get agent info for {agent_id}: {str(e)}")
            raise
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents managed by this adapter.
        
        Returns:
            List of agent dictionaries
            
        Raises:
            ValueError: If the adapter is not initialized
        """
        if not self.core_adapter:
            raise ValueError("Fast-Agent adapter not initialized")
        
        try:
            # Get all agents from the orchestrator
            agents = await self.core_adapter.orchestrator.list_agents()
            
            # Convert to the expected format
            result = []
            for agent in agents:
                agent_id = agent.get("agent_id")
                if not agent_id:
                    continue
                
                try:
                    agent_info = await self.get_agent(agent_id)
                    result.append(agent_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for agent {agent_id}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}")
            raise
    
    async def execute_agent(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute an agent with the provided inputs.
        
        Args:
            agent_id: ID of the agent to execute
            **kwargs: Input parameters for the agent
                - query: The query to send to the agent
                - use_anthropic: Whether to use Anthropic instead of OpenAI
            
        Returns:
            Dictionary containing the agent execution results
            
        Raises:
            ValueError: If the adapter is not initialized
            KeyError: If the agent doesn't exist
        """
        if not self.core_adapter:
            raise ValueError("Fast-Agent adapter not initialized")
        
        # Extract parameters from kwargs
        query = kwargs.get("query")
        if not query:
            raise ValueError("Missing required parameter: query")
            
        use_anthropic = kwargs.get("use_anthropic")
        
        try:
            # Run the agent
            response = await self.core_adapter.run_agent(
                agent_id=agent_id,
                query=query,
                use_anthropic=use_anthropic,
            )
            
            # Update last active timestamp
            if agent_id in self.agent_metadata:
                self.agent_metadata[agent_id]["last_active"] = datetime.now().isoformat()
            
            # Format the response
            result = {
                "agent_id": agent_id,
                "status": "success",
                "outputs": {
                    "response": response,
                    "query": query,
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except ValueError as e:
            logger.error(f"Agent not found: {agent_id}")
            raise KeyError(f"Agent not found: {agent_id}") from e
        except Exception as e:
            logger.error(f"Failed to execute agent {agent_id}: {str(e)}")
            
            # Format the error response
            result = {
                "agent_id": agent_id,
                "status": "error",
                "outputs": {
                    "error": str(e),
                    "query": query,
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return result
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            True if the agent was deleted, False otherwise
            
        Raises:
            ValueError: If the adapter is not initialized
        """
        if not self.core_adapter:
            raise ValueError("Fast-Agent adapter not initialized")
        
        try:
            # Delete the agent
            success = await self.core_adapter.delete_agent(agent_id)
            
            # Remove from metadata
            if success and agent_id in self.agent_metadata:
                del self.agent_metadata[agent_id]
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the adapter and release resources."""
        if self.core_adapter:
            try:
                await self.core_adapter.shutdown()
                logger.info("Fast-Agent adapter shut down")
            except Exception as e:
                logger.error(f"Error shutting down Fast-Agent adapter: {str(e)}")
            
            self.core_adapter = None


# Factory function to create a FastAgentAdapterImpl instance
def create_fast_agent_adapter(
    config_path: Optional[str] = None,
    app_name: str = "ai_orchestration_platform",
    api_key: Optional[str] = None,
) -> FastAgentAdapterImpl:
    """
    Create a new FastAgentAdapterImpl instance.
    
    Args:
        config_path: Path to the Fast-Agent configuration file
        app_name: Name of the MCP application
        api_key: API key for authenticating with the orchestrator
        
    Returns:
        A new FastAgentAdapterImpl instance
    """
    return FastAgentAdapterImpl(
        config_path=config_path,
        app_name=app_name,
        api_key=api_key,
    )
