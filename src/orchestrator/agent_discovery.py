"""
Agent Discovery Module

This module provides functionality for discovering and managing agents in the AI-Orchestration-Platform.
It allows agents to register their presence, capabilities, and status, and provides methods for
finding agents based on their capabilities.
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import uuid

from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker
from src.orchestrator.dagger_communication import get_dagger_communication_manager

# Configure logging
logger = logging.getLogger(__name__)

class AgentCapability:
    """Represents a capability of an agent."""
    
    def __init__(self, name: str, version: str = "1.0.0", metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new AgentCapability.
        
        Args:
            name: Name of the capability
            version: Version of the capability
            metadata: Additional metadata for the capability
        """
        self.name = name
        self.version = version
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the capability to a dictionary representation.
        
        Returns:
            Dictionary representation of the capability
        """
        return {
            "name": self.name,
            "version": self.version,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapability':
        """
        Create a capability from a dictionary representation.
        
        Args:
            data: Dictionary representation of the capability
            
        Returns:
            A new AgentCapability instance
        """
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {})
        )


class AgentInfo:
    """Represents information about an agent."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[AgentCapability],
        status: str = "idle",
        last_heartbeat: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AgentInfo.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Name of the agent
            capabilities: List of agent capabilities
            status: Status of the agent
            last_heartbeat: Time of the last heartbeat from the agent
            metadata: Additional metadata for the agent
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.status = status
        self.last_heartbeat = last_heartbeat or datetime.now()
        self.metadata = metadata or {}
        self.registered_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_heartbeat(self) -> None:
        """Update the last heartbeat time."""
        self.last_heartbeat = datetime.now()
        self.updated_at = datetime.now()
    
    def update_status(self, status: str) -> None:
        """
        Update the agent status.
        
        Args:
            status: New status for the agent
        """
        self.status = status
        self.updated_at = datetime.now()
    
    def update_capabilities(self, capabilities: List[AgentCapability]) -> None:
        """
        Update the agent capabilities.
        
        Args:
            capabilities: New capabilities for the agent
        """
        self.capabilities = capabilities
        self.updated_at = datetime.now()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the agent metadata.
        
        Args:
            metadata: New metadata for the agent
        """
        self.metadata = metadata
        self.updated_at = datetime.now()
    
    def is_active(self, timeout_seconds: int = 60) -> bool:
        """
        Check if the agent is active based on the last heartbeat.
        
        Args:
            timeout_seconds: Number of seconds after which an agent is considered inactive
            
        Returns:
            True if the agent is active, False otherwise
        """
        return (datetime.now() - self.last_heartbeat).total_seconds() < timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent info to a dictionary representation.
        
        Returns:
            Dictionary representation of the agent info
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """
        Create an agent info from a dictionary representation.
        
        Args:
            data: Dictionary representation of the agent info
            
        Returns:
            A new AgentInfo instance
        """
        capabilities = [
            AgentCapability.from_dict(cap) for cap in data.get("capabilities", [])
        ]
        
        agent_info = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            capabilities=capabilities,
            status=data.get("status", "idle"),
            metadata=data.get("metadata", {})
        )
        
        # Parse datetime fields if they exist
        if "last_heartbeat" in data and data["last_heartbeat"]:
            agent_info.last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        if "registered_at" in data and data["registered_at"]:
            agent_info.registered_at = datetime.fromisoformat(data["registered_at"])
        if "updated_at" in data and data["updated_at"]:
            agent_info.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return agent_info


class AgentDiscoveryService:
    """Service for discovering and managing agents."""
    
    def __init__(self, heartbeat_interval: int = 30, inactive_timeout: int = 60):
        """
        Initialize a new AgentDiscoveryService.
        
        Args:
            heartbeat_interval: Interval in seconds for agent heartbeats
            inactive_timeout: Number of seconds after which an agent is considered inactive
        """
        self.agents: Dict[str, AgentInfo] = {}
        self.heartbeat_interval = heartbeat_interval
        self.inactive_timeout = inactive_timeout
        self.communication_manager = get_dagger_communication_manager()
        self.circuit_breaker = get_circuit_breaker("agent_discovery")
        self._heartbeat_task = None
        self._initialized = False
        
        # Cache for capability-based lookups
        self._capability_cache: Dict[str, Set[str]] = {}
        self._cache_expiry = datetime.now()
        self._cache_ttl = 60  # seconds
    
    async def initialize(self) -> None:
        """Initialize the agent discovery service."""
        if not self._initialized:
            # Start the heartbeat task
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._initialized = True
            logger.info("Agent Discovery Service initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the agent discovery service."""
        if self._initialized:
            # Cancel the heartbeat task
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            self._initialized = False
            logger.info("Agent Discovery Service shut down")
    
    async def _heartbeat_loop(self) -> None:
        """Background task for checking agent heartbeats."""
        while True:
            try:
                # Check for inactive agents
                inactive_agents = []
                for agent_id, agent_info in self.agents.items():
                    if not agent_info.is_active(self.inactive_timeout):
                        inactive_agents.append(agent_id)
                        agent_info.update_status("offline")
                
                # Log inactive agents
                if inactive_agents:
                    logger.info(f"Detected {len(inactive_agents)} inactive agents: {inactive_agents}")
                
                # Invalidate the capability cache
                self._invalidate_cache()
                
                # Wait for the next heartbeat interval
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying
    
    async def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: List[Dict[str, Any]],
        status: str = "idle",
        metadata: Optional[Dict[str, Any]] = None,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Register a new agent or update an existing one.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Name of the agent
            capabilities: List of agent capabilities
            status: Status of the agent
            metadata: Additional metadata for the agent
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            Dictionary containing the registration result
        """
        # Convert capabilities to AgentCapability objects
        agent_capabilities = [
            AgentCapability.from_dict(cap) if isinstance(cap, dict) else cap
            for cap in capabilities
        ]
        
        # Check if the agent already exists
        if agent_id in self.agents:
            # Update existing agent
            agent_info = self.agents[agent_id]
            agent_info.name = name
            agent_info.update_capabilities(agent_capabilities)
            agent_info.update_status(status)
            agent_info.update_heartbeat()
            if metadata:
                agent_info.update_metadata(metadata)
            
            logger.info(f"Updated agent: {agent_id}")
        else:
            # Create new agent
            agent_info = AgentInfo(
                agent_id=agent_id,
                name=name,
                capabilities=agent_capabilities,
                status=status,
                metadata=metadata
            )
            self.agents[agent_id] = agent_info
            
            logger.info(f"Registered new agent: {agent_id}")
        
        # Invalidate the capability cache
        self._invalidate_cache()
        
        # Register with the communication manager
        try:
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.register_agent(
                        agent_id=agent_id,
                        capabilities={
                            cap.name: {"version": cap.version, **cap.metadata}
                            for cap in agent_capabilities
                        },
                        use_circuit_breaker=True
                    )
                )
            else:
                await self.communication_manager.register_agent(
                    agent_id=agent_id,
                    capabilities={
                        cap.name: {"version": cap.version, **cap.metadata}
                        for cap in agent_capabilities
                    },
                    use_circuit_breaker=False
                )
        except Exception as e:
            logger.error(f"Failed to register agent with communication manager: {e}")
        
        return {
            "agent_id": agent_id,
            "name": name,
            "status": status,
            "registered_at": agent_info.registered_at.isoformat(),
            "message": "Agent registered successfully"
        }
    
    async def unregister_agent(
        self,
        agent_id: str,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Unregister an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            Dictionary containing the unregistration result
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            return {
                "agent_id": agent_id,
                "success": False,
                "message": "Agent not found"
            }
        
        # Get the agent info
        agent_info = self.agents[agent_id]
        
        # Remove the agent
        del self.agents[agent_id]
        
        # Invalidate the capability cache
        self._invalidate_cache()
        
        # Unregister from the communication manager
        try:
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.unregister_agent(
                        agent_id=agent_id,
                        use_circuit_breaker=True
                    )
                )
            else:
                await self.communication_manager.unregister_agent(
                    agent_id=agent_id,
                    use_circuit_breaker=False
                )
        except Exception as e:
            logger.error(f"Failed to unregister agent from communication manager: {e}")
        
        logger.info(f"Unregistered agent: {agent_id}")
        
        return {
            "agent_id": agent_id,
            "success": True,
            "message": "Agent unregistered successfully"
        }
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Update the status of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            status: New status for the agent
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            Dictionary containing the update result
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            return {
                "agent_id": agent_id,
                "success": False,
                "message": "Agent not found"
            }
        
        # Update the agent status
        agent_info = self.agents[agent_id]
        agent_info.update_status(status)
        agent_info.update_heartbeat()
        
        # Send status update via communication manager
        try:
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.send_message(
                        sender_id="agent_discovery",
                        message_type="agent_status_update",
                        content={
                            "agent_id": agent_id,
                            "status": status,
                            "timestamp": datetime.now().isoformat()
                        },
                        recipient_id="*",  # Broadcast to all agents
                        priority="normal",
                        use_circuit_breaker=True
                    )
                )
            else:
                await self.communication_manager.send_message(
                    sender_id="agent_discovery",
                    message_type="agent_status_update",
                    content={
                        "agent_id": agent_id,
                        "status": status,
                        "timestamp": datetime.now().isoformat()
                    },
                    recipient_id="*",  # Broadcast to all agents
                    priority="normal",
                    use_circuit_breaker=False
                )
        except Exception as e:
            logger.error(f"Failed to send agent status update: {e}")
        
        logger.debug(f"Updated agent status: {agent_id} -> {status}")
        
        return {
            "agent_id": agent_id,
            "status": status,
            "success": True,
            "message": "Agent status updated successfully"
        }
    
    async def heartbeat(
        self,
        agent_id: str,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a heartbeat for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            status: Optional new status for the agent
            metadata: Optional metadata to update
            
        Returns:
            Dictionary containing the heartbeat result
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            return {
                "agent_id": agent_id,
                "success": False,
                "message": "Agent not found"
            }
        
        # Update the agent heartbeat
        agent_info = self.agents[agent_id]
        agent_info.update_heartbeat()
        
        # Update status if provided
        if status:
            agent_info.update_status(status)
        
        # Update metadata if provided
        if metadata:
            agent_info.update_metadata(metadata)
        
        logger.debug(f"Received heartbeat from agent: {agent_id}")
        
        return {
            "agent_id": agent_id,
            "success": True,
            "message": "Heartbeat received successfully"
        }
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dictionary containing agent information, or None if the agent doesn't exist
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            return None
        
        # Return the agent info
        return self.agents[agent_id].to_dict()
    
    async def list_agents(
        self,
        status: Optional[str] = None,
        active_only: bool = False,
        capability: Optional[str] = None,
        capability_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all agents, optionally filtered by status, activity, or capability.
        
        Args:
            status: Filter agents by status
            active_only: Only include active agents
            capability: Filter agents by capability
            capability_version: Filter agents by capability version
            
        Returns:
            List of agent dictionaries
        """
        # Start with all agents
        filtered_agents = list(self.agents.values())
        
        # Filter by status if provided
        if status:
            filtered_agents = [
                agent for agent in filtered_agents
                if agent.status == status
            ]
        
        # Filter by activity if requested
        if active_only:
            filtered_agents = [
                agent for agent in filtered_agents
                if agent.is_active(self.inactive_timeout)
            ]
        
        # Filter by capability if provided
        if capability:
            filtered_agents = [
                agent for agent in filtered_agents
                if any(cap.name == capability for cap in agent.capabilities)
            ]
            
            # Further filter by capability version if provided
            if capability_version:
                filtered_agents = [
                    agent for agent in filtered_agents
                    if any(cap.name == capability and cap.version == capability_version
                          for cap in agent.capabilities)
                ]
        
        # Convert to dictionaries
        return [agent.to_dict() for agent in filtered_agents]
    
    async def find_agents_by_capability(
        self,
        capability: str,
        version: Optional[str] = None,
        status: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability: Capability to search for
            version: Optional version of the capability
            status: Optional status filter
            active_only: Only include active agents
            limit: Maximum number of agents to return
            
        Returns:
            List of agent dictionaries
        """
        # Check if we can use the cache
        cache_key = f"{capability}:{version or '*'}:{status or '*'}:{active_only}"
        if self._is_cache_valid() and cache_key in self._capability_cache:
            # Get agent IDs from cache
            agent_ids = self._capability_cache[cache_key]
            
            # Get agent info for each ID
            agents = [
                self.agents[agent_id].to_dict()
                for agent_id in agent_ids
                if agent_id in self.agents
            ]
            
            # Apply limit if provided
            if limit:
                agents = agents[:limit]
                
            return agents
        
        # Find agents with the capability
        matching_agents = []
        for agent_id, agent_info in self.agents.items():
            # Check if the agent has the capability
            has_capability = False
            for cap in agent_info.capabilities:
                if cap.name == capability:
                    # Check version if provided
                    if version and cap.version != version:
                        continue
                    has_capability = True
                    break
            
            if not has_capability:
                continue
                
            # Check status if provided
            if status and agent_info.status != status:
                continue
                
            # Check activity if requested
            if active_only and not agent_info.is_active(self.inactive_timeout):
                continue
                
            # Add the agent to the results
            matching_agents.append(agent_info.to_dict())
            
            # Stop if we've reached the limit
            if limit and len(matching_agents) >= limit:
                break
        
        # Update the cache
        if not self._is_cache_valid():
            self._refresh_cache()
        self._capability_cache[cache_key] = {
            agent["agent_id"] for agent in matching_agents
        }
        
        return matching_agents
    
    async def find_agents_by_capabilities(
        self,
        capabilities: List[Dict[str, str]],
        match_all: bool = True,
        status: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find agents that have specific capabilities.
        
        Args:
            capabilities: List of capabilities to search for, each with name and optional version
            match_all: Whether agents must have all capabilities or just one
            status: Optional status filter
            active_only: Only include active agents
            limit: Maximum number of agents to return
            
        Returns:
            List of agent dictionaries
        """
        # Find agents for each capability
        capability_results = []
        for cap in capabilities:
            cap_name = cap["name"]
            cap_version = cap.get("version")
            
            # Find agents with this capability
            agents = await self.find_agents_by_capability(
                capability=cap_name,
                version=cap_version,
                status=status,
                active_only=active_only
            )
            
            capability_results.append(set(agent["agent_id"] for agent in agents))
        
        # Combine results based on match_all
        if match_all:
            # Agents must have all capabilities
            if not capability_results:
                matching_agent_ids = set()
            else:
                matching_agent_ids = set.intersection(*capability_results)
        else:
            # Agents must have at least one capability
            matching_agent_ids = set.union(*capability_results) if capability_results else set()
        
        # Get agent info for each ID
        matching_agents = [
            self.agents[agent_id].to_dict()
            for agent_id in matching_agent_ids
            if agent_id in self.agents
        ]
        
        # Apply limit if provided
        if limit:
            matching_agents = matching_agents[:limit]
            
        return matching_agents
    
    async def negotiate_capabilities(
        self,
        agent_id: str,
        required_capabilities: List[Dict[str, str]],
        optional_capabilities: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Negotiate capabilities with an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            required_capabilities: List of required capabilities
            optional_capabilities: List of optional capabilities
            
        Returns:
            Dictionary containing the negotiation result
        """
        # Check if the agent exists
        if agent_id not in self.agents:
            return {
                "agent_id": agent_id,
                "success": False,
                "message": "Agent not found"
            }
        
        # Get the agent info
        agent_info = self.agents[agent_id]
        
        # Check required capabilities
        missing_capabilities = []
        for cap in required_capabilities:
            cap_name = cap["name"]
            cap_version = cap.get("version")
            
            # Check if the agent has this capability
            has_capability = False
            for agent_cap in agent_info.capabilities:
                if agent_cap.name == cap_name:
                    # Check version if provided
                    if cap_version and agent_cap.version != cap_version:
                        continue
                    has_capability = True
                    break
            
            if not has_capability:
                missing_capabilities.append(cap)
        
        # Check if all required capabilities are available
        if missing_capabilities:
            return {
                "agent_id": agent_id,
                "success": False,
                "message": "Agent is missing required capabilities",
                "missing_capabilities": missing_capabilities
            }
        
        # Check optional capabilities
        available_optional = []
        if optional_capabilities:
            for cap in optional_capabilities:
                cap_name = cap["name"]
                cap_version = cap.get("version")
                
                # Check if the agent has this capability
                for agent_cap in agent_info.capabilities:
                    if agent_cap.name == cap_name:
                        # Check version if provided
                        if cap_version and agent_cap.version != cap_version:
                            continue
                        available_optional.append(cap)
                        break
        
        return {
            "agent_id": agent_id,
            "success": True,
            "message": "Capability negotiation successful",
            "required_capabilities": required_capabilities,
            "available_optional_capabilities": available_optional
        }
    
    def _invalidate_cache(self) -> None:
        """Invalidate the capability cache."""
        self._cache_expiry = datetime.now()
    
    def _is_cache_valid(self) -> bool:
        """Check if the capability cache is valid."""
        return (datetime.now() - self._cache_expiry).total_seconds() < self._cache_ttl
    
    def _refresh_cache(self) -> None:
        """Refresh the capability cache."""
        self._capability_cache = {}
        self._cache_expiry = datetime.now() + timedelta(seconds=self._cache_ttl)


# Singleton instances
_agent_discovery_service: Optional[AgentDiscoveryService] = None
_agent_capabilities_registry: Optional[AgentCapabilitiesRegistry] = None

def get_agent_discovery_service(
    heartbeat_interval: int = 30,
    inactive_timeout: int = 60
) -> AgentDiscoveryService:
    """
    Get the singleton instance of the AgentDiscoveryService.
    
    Args:
        heartbeat_interval: Interval in seconds for agent heartbeats
        inactive_timeout: Number of seconds after which an agent is considered inactive
        
    Returns:
        AgentDiscoveryService instance
    """
    global _agent_discovery_service
    if _agent_discovery_service is None:
        _agent_discovery_service = AgentDiscoveryService(
            heartbeat_interval=heartbeat_interval,
            inactive_timeout=inactive_timeout
        )
        
        # Initialize the service
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_agent_discovery_service.initialize())
        except RuntimeError:
            # Create and run a new event loop if the current one is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_agent_discovery_service.initialize())
    
    return _agent_discovery_service


def get_agent_capabilities_registry() -> AgentCapabilitiesRegistry:
    """
    Get the singleton instance of the AgentCapabilitiesRegistry.
    
    Returns:
        AgentCapabilitiesRegistry instance
    """
    global _agent_capabilities_registry
    if _agent_capabilities_registry is None:
        _agent_capabilities_registry = AgentCapabilitiesRegistry()
    
    return _agent_capabilities_registry


class AgentCapabilitiesRegistry:
    """Registry for agent capabilities."""
    
    def __init__(self):
        """Initialize a new AgentCapabilitiesRegistry."""
        self.capabilities: Dict[str, Dict[str, Any]] = {}
        self.discovery_service = get_agent_discovery_service()
    
    async def register_capability(
        self,
        name: str,
        description: str,
        versions: List[str],
        schema: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new capability or update an existing one.
        
        Args:
            name: Name of the capability
            description: Description of the capability
            versions: List of supported versions
            schema: Optional JSON schema for the capability
            metadata: Additional metadata for the capability
            
        Returns:
            Dictionary containing the registration result
        """
        # Create or update the capability
        self.capabilities[name] = {
            "name": name,
            "description": description,
            "versions": versions,
            "schema": schema,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Registered capability: {name}")
        
        return {
            "name": name,
            "success": True,
            "message": "Capability registered successfully"
        }
    
    async def unregister_capability(self, name: str) -> Dict[str, Any]:
        """
        Unregister a capability.
        
        Args:
            name: Name of the capability
            
        Returns:
            Dictionary containing the unregistration result
        """
        # Check if the capability exists
        if name not in self.capabilities:
            return {
                "name": name,
                "success": False,
                "message": "Capability not found"
            }
        
        # Remove the capability
        del self.capabilities[name]
        
        logger.info(f"Unregistered capability: {name}")
        
        return {
            "name": name,
            "success": True,
            "message": "Capability unregistered successfully"
        }
    
    async def get_capability(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a capability.
        
        Args:
            name: Name of the capability
            
        Returns:
            Dictionary containing capability information, or None if the capability doesn't exist
        """
        # Check if the capability exists
        if name not in self.capabilities:
            return None
        
        # Return the capability info
        return self.capabilities[name]
    
    async def list_capabilities(
        self,
        version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all capabilities, optionally filtered by version.
        
        Args:
            version: Filter capabilities by version
            
        Returns:
            List of capability dictionaries
        """
        # Start with all capabilities
        capabilities = list(self.capabilities.values())
        
        # Filter by version if provided
        if version:
            capabilities = [
                cap for cap in capabilities
                if version in cap["versions"]
            ]
        
        return capabilities
    
    async def find_agents_with_capability(
        self,
        name: str,
        version: Optional[str] = None,
        status: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Args:
            name: Name of the capability
            version: Optional version of the capability
            status: Optional status filter
            active_only: Only include active agents
            limit: Maximum number of agents to return
            
        Returns:
            List of agent dictionaries
        """
        return await self.discovery_service.find_agents_by_capability(
            capability=name,
            version=version,
            status=status,
            active_only=active_only,
            limit=limit
        )
    
    async def validate_capability(
        self,
        name: str,
        version: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate data against a capability schema.
        
        Args:
            name: Name of the capability
            version: Version of the capability
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if the capability exists
        if name not in self.capabilities:
            return False, f"Capability not found: {name}"
        
        # Get the capability info
        capability = self.capabilities[name]
        
        # Check if the version is supported
        if version not in capability["versions"]:
            return False, f"Unsupported version: {version} for capability {name}"
        
        # Check if the capability has a schema
        if not capability.get("schema"):
            # No schema to validate against
            return True, None
        
        # Validate against the schema
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=capability["schema"])
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
