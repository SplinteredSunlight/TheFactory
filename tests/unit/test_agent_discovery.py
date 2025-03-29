"""
Tests for the Agent Discovery module.

This module contains tests for the AgentDiscoveryService and AgentCapabilitiesRegistry classes.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.orchestrator.agent_discovery import (
    AgentCapability,
    AgentInfo,
    AgentDiscoveryService,
    AgentCapabilitiesRegistry,
    get_agent_discovery_service,
    get_agent_capabilities_registry
)


@pytest.fixture
def mock_communication_manager():
    """Mock communication manager for testing."""
    mock = MagicMock()
    mock.register_agent = MagicMock(return_value=asyncio.Future())
    mock.register_agent.return_value.set_result({"success": True})
    mock.unregister_agent = MagicMock(return_value=asyncio.Future())
    mock.unregister_agent.return_value.set_result({"success": True})
    mock.send_message = MagicMock(return_value=asyncio.Future())
    mock.send_message.return_value.set_result({"message_id": "test_message_id"})
    return mock


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
async def discovery_service(mock_communication_manager, mock_circuit_breaker):
    """Create a discovery service for testing."""
    with patch("src.orchestrator.agent_discovery.get_dagger_communication_manager", return_value=mock_communication_manager), \
         patch("src.orchestrator.agent_discovery.get_circuit_breaker", return_value=mock_circuit_breaker):
        service = AgentDiscoveryService(heartbeat_interval=1, inactive_timeout=2)
        await service.initialize()
        yield service
        await service.shutdown()


@pytest.fixture
async def capabilities_registry(discovery_service):
    """Create a capabilities registry for testing."""
    with patch("src.orchestrator.agent_discovery.get_agent_discovery_service", return_value=discovery_service):
        registry = AgentCapabilitiesRegistry()
        yield registry


class TestAgentCapability:
    """Tests for the AgentCapability class."""
    
    def test_init(self):
        """Test initialization."""
        cap = AgentCapability("test_capability", "1.0.0", {"key": "value"})
        assert cap.name == "test_capability"
        assert cap.version == "1.0.0"
        assert cap.metadata == {"key": "value"}
    
    def test_to_dict(self):
        """Test to_dict method."""
        cap = AgentCapability("test_capability", "1.0.0", {"key": "value"})
        cap_dict = cap.to_dict()
        assert cap_dict["name"] == "test_capability"
        assert cap_dict["version"] == "1.0.0"
        assert cap_dict["metadata"] == {"key": "value"}
    
    def test_from_dict(self):
        """Test from_dict method."""
        cap_dict = {
            "name": "test_capability",
            "version": "1.0.0",
            "metadata": {"key": "value"}
        }
        cap = AgentCapability.from_dict(cap_dict)
        assert cap.name == "test_capability"
        assert cap.version == "1.0.0"
        assert cap.metadata == {"key": "value"}


class TestAgentInfo:
    """Tests for the AgentInfo class."""
    
    def test_init(self):
        """Test initialization."""
        capabilities = [
            AgentCapability("capability1", "1.0.0"),
            AgentCapability("capability2", "2.0.0")
        ]
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=capabilities,
            status="idle",
            metadata={"key": "value"}
        )
        assert agent.agent_id == "test_agent"
        assert agent.name == "Test Agent"
        assert len(agent.capabilities) == 2
        assert agent.status == "idle"
        assert agent.metadata == {"key": "value"}
        assert (datetime.now() - agent.last_heartbeat).total_seconds() < 1
    
    def test_update_heartbeat(self):
        """Test update_heartbeat method."""
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        old_heartbeat = agent.last_heartbeat
        old_updated_at = agent.updated_at
        
        # Wait a bit to ensure the timestamps change
        import time
        time.sleep(0.01)
        
        agent.update_heartbeat()
        assert agent.last_heartbeat > old_heartbeat
        assert agent.updated_at > old_updated_at
    
    def test_update_status(self):
        """Test update_status method."""
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        old_updated_at = agent.updated_at
        
        # Wait a bit to ensure the timestamps change
        import time
        time.sleep(0.01)
        
        agent.update_status("busy")
        assert agent.status == "busy"
        assert agent.updated_at > old_updated_at
    
    def test_update_capabilities(self):
        """Test update_capabilities method."""
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        old_updated_at = agent.updated_at
        
        # Wait a bit to ensure the timestamps change
        import time
        time.sleep(0.01)
        
        new_capabilities = [
            AgentCapability("capability1", "1.0.0"),
            AgentCapability("capability2", "2.0.0")
        ]
        agent.update_capabilities(new_capabilities)
        assert len(agent.capabilities) == 2
        assert agent.updated_at > old_updated_at
    
    def test_update_metadata(self):
        """Test update_metadata method."""
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        old_updated_at = agent.updated_at
        
        # Wait a bit to ensure the timestamps change
        import time
        time.sleep(0.01)
        
        agent.update_metadata({"key": "value"})
        assert agent.metadata == {"key": "value"}
        assert agent.updated_at > old_updated_at
    
    def test_is_active(self):
        """Test is_active method."""
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        assert agent.is_active(timeout_seconds=60)
        
        # Set last heartbeat to 2 minutes ago
        agent.last_heartbeat = datetime.now() - timedelta(minutes=2)
        assert not agent.is_active(timeout_seconds=60)
    
    def test_to_dict(self):
        """Test to_dict method."""
        capabilities = [
            AgentCapability("capability1", "1.0.0"),
            AgentCapability("capability2", "2.0.0")
        ]
        agent = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=capabilities,
            status="idle",
            metadata={"key": "value"}
        )
        agent_dict = agent.to_dict()
        assert agent_dict["agent_id"] == "test_agent"
        assert agent_dict["name"] == "Test Agent"
        assert len(agent_dict["capabilities"]) == 2
        assert agent_dict["status"] == "idle"
        assert agent_dict["metadata"] == {"key": "value"}
        assert "last_heartbeat" in agent_dict
        assert "registered_at" in agent_dict
        assert "updated_at" in agent_dict
        assert "is_active" in agent_dict
    
    def test_from_dict(self):
        """Test from_dict method."""
        agent_dict = {
            "agent_id": "test_agent",
            "name": "Test Agent",
            "capabilities": [
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability2", "version": "2.0.0"}
            ],
            "status": "idle",
            "metadata": {"key": "value"},
            "last_heartbeat": datetime.now().isoformat(),
            "registered_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        agent = AgentInfo.from_dict(agent_dict)
        assert agent.agent_id == "test_agent"
        assert agent.name == "Test Agent"
        assert len(agent.capabilities) == 2
        assert agent.status == "idle"
        assert agent.metadata == {"key": "value"}


@pytest.mark.asyncio
class TestAgentDiscoveryService:
    """Tests for the AgentDiscoveryService class."""
    
    async def test_register_agent(self, discovery_service, mock_communication_manager):
        """Test register_agent method."""
        result = await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability2", "version": "2.0.0"}
            ],
            status="idle",
            metadata={"key": "value"}
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["name"] == "Test Agent"
        assert result["status"] == "idle"
        assert "registered_at" in result
        assert result["message"] == "Agent registered successfully"
        
        # Check that the agent was added to the registry
        assert "test_agent" in discovery_service.agents
        assert discovery_service.agents["test_agent"].name == "Test Agent"
        assert len(discovery_service.agents["test_agent"].capabilities) == 2
        
        # Check that the communication manager was called
        mock_communication_manager.register_agent.assert_called_once()
    
    async def test_unregister_agent(self, discovery_service, mock_communication_manager):
        """Test unregister_agent method."""
        # Register an agent first
        await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        
        # Unregister the agent
        result = await discovery_service.unregister_agent(
            agent_id="test_agent"
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["success"] is True
        assert result["message"] == "Agent unregistered successfully"
        
        # Check that the agent was removed from the registry
        assert "test_agent" not in discovery_service.agents
        
        # Check that the communication manager was called
        mock_communication_manager.unregister_agent.assert_called_once()
    
    async def test_update_agent_status(self, discovery_service, mock_communication_manager):
        """Test update_agent_status method."""
        # Register an agent first
        await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        
        # Update the agent status
        result = await discovery_service.update_agent_status(
            agent_id="test_agent",
            status="busy"
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["status"] == "busy"
        assert result["success"] is True
        assert result["message"] == "Agent status updated successfully"
        
        # Check that the agent status was updated
        assert discovery_service.agents["test_agent"].status == "busy"
        
        # Check that the communication manager was called
        mock_communication_manager.send_message.assert_called_once()
    
    async def test_heartbeat(self, discovery_service):
        """Test heartbeat method."""
        # Register an agent first
        await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        
        # Set the last heartbeat to 30 seconds ago
        old_heartbeat = datetime.now() - timedelta(seconds=30)
        discovery_service.agents["test_agent"].last_heartbeat = old_heartbeat
        
        # Send a heartbeat
        result = await discovery_service.heartbeat(
            agent_id="test_agent",
            status="busy",
            metadata={"key": "value"}
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["success"] is True
        assert result["message"] == "Heartbeat received successfully"
        
        # Check that the agent was updated
        assert discovery_service.agents["test_agent"].status == "busy"
        assert discovery_service.agents["test_agent"].metadata == {"key": "value"}
        assert discovery_service.agents["test_agent"].last_heartbeat > old_heartbeat
    
    async def test_get_agent(self, discovery_service):
        """Test get_agent method."""
        # Register an agent first
        await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[]
        )
        
        # Get the agent
        agent = await discovery_service.get_agent(
            agent_id="test_agent"
        )
        
        assert agent is not None
        assert agent["agent_id"] == "test_agent"
        assert agent["name"] == "Test Agent"
    
    async def test_list_agents(self, discovery_service):
        """Test list_agents method."""
        # Register some agents
        await discovery_service.register_agent(
            agent_id="agent1",
            name="Agent 1",
            capabilities=[{"name": "capability1", "version": "1.0.0"}],
            status="idle"
        )
        await discovery_service.register_agent(
            agent_id="agent2",
            name="Agent 2",
            capabilities=[{"name": "capability2", "version": "2.0.0"}],
            status="busy"
        )
        
        # List all agents
        agents = await discovery_service.list_agents()
        assert len(agents) == 2
        
        # List agents by status
        idle_agents = await discovery_service.list_agents(status="idle")
        assert len(idle_agents) == 1
        assert idle_agents[0]["agent_id"] == "agent1"
        
        busy_agents = await discovery_service.list_agents(status="busy")
        assert len(busy_agents) == 1
        assert busy_agents[0]["agent_id"] == "agent2"
        
        # List agents by capability
        cap1_agents = await discovery_service.list_agents(capability="capability1")
        assert len(cap1_agents) == 1
        assert cap1_agents[0]["agent_id"] == "agent1"
        
        cap2_agents = await discovery_service.list_agents(capability="capability2")
        assert len(cap2_agents) == 1
        assert cap2_agents[0]["agent_id"] == "agent2"
    
    async def test_find_agents_by_capability(self, discovery_service):
        """Test find_agents_by_capability method."""
        # Register some agents
        await discovery_service.register_agent(
            agent_id="agent1",
            name="Agent 1",
            capabilities=[
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability3", "version": "3.0.0"}
            ],
            status="idle"
        )
        await discovery_service.register_agent(
            agent_id="agent2",
            name="Agent 2",
            capabilities=[
                {"name": "capability2", "version": "2.0.0"},
                {"name": "capability3", "version": "3.1.0"}
            ],
            status="busy"
        )
        
        # Find agents by capability
        cap1_agents = await discovery_service.find_agents_by_capability(
            capability="capability1"
        )
        assert len(cap1_agents) == 1
        assert cap1_agents[0]["agent_id"] == "agent1"
        
        cap2_agents = await discovery_service.find_agents_by_capability(
            capability="capability2"
        )
        assert len(cap2_agents) == 1
        assert cap2_agents[0]["agent_id"] == "agent2"
        
        cap3_agents = await discovery_service.find_agents_by_capability(
            capability="capability3"
        )
        assert len(cap3_agents) == 2
        
        # Find agents by capability and version
        cap3_v3_agents = await discovery_service.find_agents_by_capability(
            capability="capability3",
            version="3.0.0"
        )
        assert len(cap3_v3_agents) == 1
        assert cap3_v3_agents[0]["agent_id"] == "agent1"
        
        # Find agents by capability and status
        cap3_idle_agents = await discovery_service.find_agents_by_capability(
            capability="capability3",
            status="idle"
        )
        assert len(cap3_idle_agents) == 1
        assert cap3_idle_agents[0]["agent_id"] == "agent1"
    
    async def test_find_agents_by_capabilities(self, discovery_service):
        """Test find_agents_by_capabilities method."""
        # Register some agents
        await discovery_service.register_agent(
            agent_id="agent1",
            name="Agent 1",
            capabilities=[
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability3", "version": "3.0.0"}
            ],
            status="idle"
        )
        await discovery_service.register_agent(
            agent_id="agent2",
            name="Agent 2",
            capabilities=[
                {"name": "capability2", "version": "2.0.0"},
                {"name": "capability3", "version": "3.1.0"}
            ],
            status="busy"
        )
        await discovery_service.register_agent(
            agent_id="agent3",
            name="Agent 3",
            capabilities=[
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability2", "version": "2.0.0"},
                {"name": "capability3", "version": "3.0.0"}
            ],
            status="idle"
        )
        
        # Find agents with multiple capabilities (match_all=True)
        agents = await discovery_service.find_agents_by_capabilities(
            capabilities=[
                {"name": "capability1"},
                {"name": "capability3"}
            ],
            match_all=True
        )
        assert len(agents) == 2
        assert set(agent["agent_id"] for agent in agents) == {"agent1", "agent3"}
        
        # Find agents with multiple capabilities (match_all=False)
        agents = await discovery_service.find_agents_by_capabilities(
            capabilities=[
                {"name": "capability1"},
                {"name": "capability2"}
            ],
            match_all=False
        )
        assert len(agents) == 3
        assert set(agent["agent_id"] for agent in agents) == {"agent1", "agent2", "agent3"}
        
        # Find agents with multiple capabilities and status
        agents = await discovery_service.find_agents_by_capabilities(
            capabilities=[
                {"name": "capability1"},
                {"name": "capability3"}
            ],
            match_all=True,
            status="idle"
        )
        assert len(agents) == 2
        assert set(agent["agent_id"] for agent in agents) == {"agent1", "agent3"}
    
    async def test_negotiate_capabilities(self, discovery_service):
        """Test negotiate_capabilities method."""
        # Register an agent
        await discovery_service.register_agent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=[
                {"name": "capability1", "version": "1.0.0"},
                {"name": "capability2", "version": "2.0.0"},
                {"name": "capability3", "version": "3.0.0"}
            ]
        )
        
        # Negotiate capabilities (all required capabilities available)
        result = await discovery_service.negotiate_capabilities(
            agent_id="test_agent",
            required_capabilities=[
                {"name": "capability1"},
                {"name": "capability2"}
            ],
            optional_capabilities=[
                {"name": "capability3"},
                {"name": "capability4"}
            ]
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["success"] is True
        assert result["message"] == "Capability negotiation successful"
        assert len(result["required_capabilities"]) == 2
        assert len(result["available_optional_capabilities"]) == 1
        
        # Negotiate capabilities (missing required capability)
        result = await discovery_service.negotiate_capabilities(
            agent_id="test_agent",
            required_capabilities=[
                {"name": "capability1"},
                {"name": "capability4"}
            ]
        )
        
        assert result["agent_id"] == "test_agent"
        assert result["success"] is False
        assert result["message"] == "Agent is missing required capabilities"
        assert len(result["missing_capabilities"]) == 1
        assert result["missing_capabilities"][0]["name"] == "capability4"


@pytest.mark.asyncio
class TestAgentCapabilitiesRegistry:
    """Tests for the AgentCapabilitiesRegistry class."""
    
    async def test_register_capability(self, capabilities_registry):
        """Test register_capability method."""
        result = await capabilities_registry.register_capability(
            name="test_capability",
            description="Test capability",
            versions=["1.0.0", "2.0.0"],
            schema={"type": "object"},
            metadata={"key": "value"}
        )
        
        assert result["name"] == "test_capability"
        assert result["success"] is True
        assert result["message"] == "Capability registered successfully"
        
        # Check that the capability was added to the registry
        assert "test_capability" in capabilities_registry.capabilities
        assert capabilities_registry.capabilities["test_capability"]["description"] == "Test capability"
        assert capabilities_registry.capabilities["test_capability"]["versions"] == ["1.0.0", "2.0.0"]
        assert capabilities_registry.capabilities["test_capability"]["schema"] == {"type": "object"}
        assert capabilities_registry.capabilities["test_capability"]["metadata"] == {"key": "value"}
    
    async def test_unregister_capability(self, capabilities_registry):
        """Test unregister_capability method."""
        # Register a capability first
        await capabilities_registry.register_capability(
            name="test_capability",
            description="Test capability",
            versions=["1.0.0"]
        )
        
        # Unregister the capability
        result = await capabilities_registry.unregister_capability(
            name="test_capability"
        )
        
        assert result["name"] == "test_capability"
        assert result["success"] is True
        assert result["message"] == "Capability unregistered successfully"
        
        # Check that the capability was removed from the registry
        assert "test_capability" not in capabilities_registry.capabilities
    
    async def test_get_capability(self, capabilities_registry):
        """Test get_capability method."""
        # Register a capability first
        await capabilities_registry.register_capability(
            name="test_capability",
            description="Test capability",
            versions=["1.0.0"]
        )
        
        # Get the capability
        capability = await capabilities_registry.get_capability(
            name="test_capability"
        )
        
        assert capability is not None
        assert capability["name"] == "test_capability"
        assert capability["description"] == "Test capability"
        assert capability["versions"] == ["1.0.0"]
    
    async def test_list_capabilities(self, capabilities_registry):
        """Test list_capabilities method."""
        # Register some capabilities
        await capabilities_registry.register_capability(
            name="capability1",
            description="Capability 1",
            versions=["1.0.0", "1.1.0"]
        )
        await capabilities_registry.register_capability(
            name="capability2",
            description="Capability 2",
            versions=["2.0.0"]
        )
        
        # List all capabilities
        capabilities = await capabilities_registry.list_capabilities()
        assert len(capabilities) == 2
        
        # List capabilities by version
        v1_capabilities = await capabilities_registry.list_capabilities(version="1.0.0")
        assert len(v1_capabilities) == 1
        assert v1_capabilities[0]["name"] == "capability1"
    
    async def test_validate_capability(self, capabilities_registry):
        """Test validate_capability method."""
        # Register a capability with a schema
        await capabilities_registry.register_capability(
            name="test_capability",
            description="Test capability",
            versions=["1.0.0"],
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "number"}
                },
                "required": ["name", "value"]
            }
        )
        
        # Validate valid data
        is_valid, error = await capabilities_registry.validate_capability(
            name="test_capability",
            version="1.0.0",
            data={"name": "test", "value": 42}
        )
        
        assert is_valid is True
        assert error is None
        
        # Validate invalid data
        is_valid, error = await capabilities_registry.validate_capability(
            name="test_capability",
            version="1.0.0",
            data={"name": "test"}  # Missing required field
        )
        
        assert is_valid is False
        assert error is not None


def test_get_agent_discovery_service():
    """Test get_agent_discovery_service function."""
    with patch("src.orchestrator.agent_discovery.AgentDiscoveryService") as mock_service, \
         patch("asyncio.new_event_loop"), \
         patch("asyncio.set_event_loop"), \
         patch("asyncio.get_event_loop"):
        
        # Mock the initialize method
        mock_instance = mock_service.return_value
        mock_instance.initialize.return_value = asyncio.Future()
        mock_instance.initialize.return_value.set_result(None)
        
        # Call the function
        service = get_agent_discovery_service()
        
        # Check that the service was created with the default parameters
        mock_service.assert_called_once_with(heartbeat_interval=30, inactive_timeout=60)
        
        # Check that the service was initialized
        mock_instance.initialize.assert_called_once()
        
        # Check that the function returns the mock instance
        assert service == mock_instance


def test_get_agent_capabilities_registry():
    """Test get_agent_capabilities_registry function."""
    with patch("src.orchestrator.agent_discovery.AgentCapabilitiesRegistry") as mock_registry:
        # Call the function
        registry = get_agent_capabilities_registry()
        
        # Check that the registry was created
        mock_registry.assert_called_once()
        
        # Check that the function returns the mock instance
        assert registry == mock_registry.return_value
