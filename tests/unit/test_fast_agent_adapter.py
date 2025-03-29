"""
Fast-Agent Adapter Tests

This module contains tests for the Fast-Agent adapter implementation.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import datetime

from agent_manager.manager import AgentManager
from agent_manager.adapter import AdapterAgent
from fast_agent_integration.fast_agent_adapter import FastAgentAdapterImpl
from fast_agent_integration.factory import FastAgentFactory, register_fast_agent_factory


class TestFastAgentAdapter(unittest.IsolatedAsyncioTestCase):
    """Test the FastAgentAdapterImpl class."""

    async def asyncSetUp(self):
        """Set up the test environment."""
        # Mock the core adapter
        self.mock_core_adapter = MagicMock()
        self.mock_core_adapter.create_agent = AsyncMock(return_value="test-external-id")
        self.mock_core_adapter.run_agent = AsyncMock(return_value="Test response")
        self.mock_core_adapter.delete_agent = AsyncMock(return_value=True)
        self.mock_core_adapter.orchestrator = MagicMock()
        self.mock_core_adapter.orchestrator.get_agent = AsyncMock(return_value={
            "agent_id": "test-external-id",
            "name": "Test Agent",
            "capabilities": {
                "model": "gpt-4",
                "provider": "openai",
                "servers": ["fetch", "filesystem", "orchestrator"],
            },
        })
        self.mock_core_adapter.orchestrator.list_agents = AsyncMock(return_value=[
            {
                "agent_id": "test-external-id",
                "name": "Test Agent",
            },
        ])
        
        # Create the adapter
        self.adapter = FastAgentAdapterImpl(
            app_name="test-app",
            api_key="test-api-key",
        )
        self.adapter.core_adapter = self.mock_core_adapter

    async def test_create_agent(self):
        """Test creating an agent."""
        # Create an agent
        external_id = await self.adapter.create_agent(
            agent_id="test-agent-id",
            name="Test Agent",
            description="Test description",
            instruction="Test instruction",
            model="gpt-4",
            use_anthropic=False,
        )
        
        # Check that the core adapter was called
        self.mock_core_adapter.create_agent.assert_called_once_with(
            name="Test Agent",
            instruction="Test instruction",
            model="gpt-4",
            servers=None,
            use_anthropic=False,
        )
        
        # Check that the agent was created
        self.assertEqual(external_id, "test-external-id")
        self.assertIn("test-external-id", self.adapter.agent_metadata)
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["agent_id"], "test-agent-id")
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["name"], "Test Agent")
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["description"], "Test description")
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["instruction"], "Test instruction")
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["model"], "gpt-4")
        self.assertEqual(self.adapter.agent_metadata["test-external-id"]["use_anthropic"], False)

    async def test_get_agent(self):
        """Test getting agent information."""
        # Add agent metadata
        self.adapter.agent_metadata["test-external-id"] = {
            "agent_id": "test-agent-id",
            "name": "Test Agent",
            "description": "Test description",
            "created_at": datetime.datetime.now().isoformat(),
            "model": "gpt-4",
            "use_anthropic": False,
            "servers": None,
            "instruction": "Test instruction",
        }
        
        # Get agent info
        agent_info = await self.adapter.get_agent("test-external-id")
        
        # Check that the core adapter was called
        self.mock_core_adapter.orchestrator.get_agent.assert_called_once_with("test-external-id")
        
        # Check the agent info
        self.assertEqual(agent_info["id"], "test-external-id")
        self.assertEqual(agent_info["name"], "Test Agent")
        self.assertEqual(agent_info["description"], "Test description")
        self.assertIn("text_generation", agent_info["capabilities"])
        self.assertIn("conversation", agent_info["capabilities"])
        self.assertIn("code_generation", agent_info["capabilities"])
        self.assertIn("reasoning", agent_info["capabilities"])
        self.assertEqual(agent_info["status"], "idle")
        self.assertEqual(agent_info["metadata"]["framework"], "fast-agent")
        self.assertEqual(agent_info["metadata"]["model"], "gpt-4")
        self.assertEqual(agent_info["metadata"]["provider"], "openai")
        self.assertEqual(agent_info["metadata"]["instruction"], "Test instruction")

    async def test_list_agents(self):
        """Test listing agents."""
        # Add agent metadata
        self.adapter.agent_metadata["test-external-id"] = {
            "agent_id": "test-agent-id",
            "name": "Test Agent",
            "description": "Test description",
            "created_at": datetime.datetime.now().isoformat(),
            "model": "gpt-4",
            "use_anthropic": False,
            "servers": None,
            "instruction": "Test instruction",
        }
        
        # List agents
        agents = await self.adapter.list_agents()
        
        # Check that the core adapter was called
        self.mock_core_adapter.orchestrator.list_agents.assert_called_once()
        self.mock_core_adapter.orchestrator.get_agent.assert_called_once_with("test-external-id")
        
        # Check the agents list
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]["id"], "test-external-id")
        self.assertEqual(agents[0]["name"], "Test Agent")
        self.assertEqual(agents[0]["description"], "Test description")
        self.assertIn("text_generation", agents[0]["capabilities"])
        self.assertEqual(agents[0]["status"], "idle")
        self.assertEqual(agents[0]["metadata"]["framework"], "fast-agent")
        self.assertEqual(agents[0]["metadata"]["model"], "gpt-4")
        self.assertEqual(agents[0]["metadata"]["provider"], "openai")
        self.assertEqual(agents[0]["metadata"]["instruction"], "Test instruction")

    async def test_execute_agent(self):
        """Test executing an agent."""
        # Add agent metadata
        self.adapter.agent_metadata["test-external-id"] = {
            "agent_id": "test-agent-id",
            "name": "Test Agent",
            "description": "Test description",
            "created_at": datetime.datetime.now().isoformat(),
            "model": "gpt-4",
            "use_anthropic": False,
            "servers": None,
            "instruction": "Test instruction",
        }
        
        # Execute the agent
        result = await self.adapter.execute_agent(
            agent_id="test-external-id",
            query="Test query",
            use_anthropic=True,
        )
        
        # Check that the core adapter was called
        self.mock_core_adapter.run_agent.assert_called_once_with(
            agent_id="test-external-id",
            query="Test query",
            use_anthropic=True,
        )
        
        # Check the result
        self.assertEqual(result["agent_id"], "test-external-id")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["outputs"]["response"], "Test response")
        self.assertEqual(result["outputs"]["query"], "Test query")
        self.assertIn("timestamp", result)

    async def test_delete_agent(self):
        """Test deleting an agent."""
        # Add agent metadata
        self.adapter.agent_metadata["test-external-id"] = {
            "agent_id": "test-agent-id",
            "name": "Test Agent",
            "description": "Test description",
            "created_at": datetime.datetime.now().isoformat(),
            "model": "gpt-4",
            "use_anthropic": False,
            "servers": None,
            "instruction": "Test instruction",
        }
        
        # Delete the agent
        success = await self.adapter.delete_agent("test-external-id")
        
        # Check that the core adapter was called
        self.mock_core_adapter.delete_agent.assert_called_once_with("test-external-id")
        
        # Check the result
        self.assertTrue(success)
        self.assertNotIn("test-external-id", self.adapter.agent_metadata)


class TestFastAgentFactory(unittest.IsolatedAsyncioTestCase):
    """Test the FastAgentFactory class."""

    async def asyncSetUp(self):
        """Set up the test environment."""
        # Create a mock agent manager
        self.agent_manager = MagicMock(spec=AgentManager)
        
        # Mock the adapter factory
        self.mock_adapter = MagicMock(spec=FastAgentAdapterImpl)
        self.mock_adapter.initialize = AsyncMock()
        self.mock_adapter.create_agent = AsyncMock(return_value="test-external-id")
        self.mock_adapter.get_agent = AsyncMock(return_value={
            "id": "test-external-id",
            "name": "Test Agent",
            "description": "Test description",
            "capabilities": ["text_generation", "conversation"],
            "status": "idle",
            "created_at": datetime.datetime.now().isoformat(),
            "last_active": None,
            "metadata": {
                "framework": "fast-agent",
                "model": "gpt-4",
                "provider": "openai",
                "instruction": "Test instruction",
            },
        })
        
        # Create a patch for the adapter factory
        self.adapter_factory_patch = patch("agent_manager.adapter.AdapterFactory.get_adapter", new=AsyncMock(return_value=self.mock_adapter))
        self.adapter_factory_patch.start()
        
        # Create a patch for the adapter agent
        self.adapter_agent_patch = patch("agent_manager.adapter.AdapterAgent", return_value=MagicMock(spec=AdapterAgent))
        self.mock_adapter_agent = self.adapter_agent_patch.start()
        
        # Create the factory
        self.factory = FastAgentFactory(
            agent_manager=self.agent_manager,
            app_name="test-app",
            api_key="test-api-key",
        )

    async def asyncTearDown(self):
        """Clean up after the test."""
        self.adapter_factory_patch.stop()
        self.adapter_agent_patch.stop()

    async def test_initialize(self):
        """Test initializing the factory."""
        # Initialize the factory
        await self.factory.initialize()
        
        # Check that the adapter was initialized
        self.mock_adapter.initialize.assert_called_once()
        
        # Check that the agent type was registered
        self.agent_manager.register_agent_type.assert_called_once_with(
            name="fast_agent",
            agent_class=self.factory._create_agent_wrapper,
        )

    async def test_create_agent(self):
        """Test creating an agent."""
        # Initialize the factory
        await self.factory.initialize()
        
        # Create an agent
        agent = await self.factory._create_agent_async(
            agent_id="test-agent-id",
            name="Test Agent",
            description="Test description",
            instruction="Test instruction",
            model="gpt-4",
            use_anthropic=False,
        )
        
        # Check that the adapter was called
        self.mock_adapter.create_agent.assert_called_once_with(
            agent_id="test-agent-id",
            name="Test Agent",
            description="Test description",
            instruction="Test instruction",
            model="gpt-4",
            use_anthropic=False,
        )
        
        # Check that the agent was created
        self.assertEqual(agent, self.mock_adapter_agent.return_value)

    async def test_shutdown(self):
        """Test shutting down the factory."""
        # Initialize the factory
        await self.factory.initialize()
        
        # Shutdown the factory
        await self.factory.shutdown()
        
        # Check that the adapter was shut down
        self.mock_adapter.shutdown.assert_called_once()


if __name__ == "__main__":
    unittest.main()
