"""
Integration Testing Framework Tests

This module implements integration tests for the AI-Orchestration-Platform,
focusing on the integration between AI-Orchestrator and Fast-Agent.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional, List

from orchestrator.engine import OrchestratorEngine
from fast_agent_integration.adapter import FastAgentAdapter, get_adapter
from fast_agent_integration.fast_agent_adapter import FastAgentAdapterImpl, create_fast_agent_adapter
from orchestrator.auth import AuthenticationError, AuthorizationError


class TestIntegrationFramework:
    """Test class for the Integration Testing Framework."""

    @pytest.fixture
    async def orchestrator(self):
        """Create an orchestrator engine for testing."""
        engine = OrchestratorEngine()
        yield engine

    @pytest.fixture
    async def fast_agent_adapter(self):
        """Create a Fast-Agent adapter for testing."""
        adapter = create_fast_agent_adapter(
            config_path=None,  # Use default config path
            app_name="test_integration",
            api_key="fast-agent-default-key"
        )
        await adapter.initialize()
        yield adapter
        await adapter.shutdown()

    @pytest.fixture
    async def auth_token(self, orchestrator):
        """Get an authentication token for testing."""
        token_info = await orchestrator.authenticate(
            api_key="fast-agent-default-key",
            client_id="test-client",
            scope=["agent:read", "agent:write", "task:read", "task:write"]
        )
        return token_info["access_token"]

    @pytest.fixture
    async def agent_data(self):
        """Get test agent data."""
        return {
            "agent_id": "test-agent-1",
            "name": "Test Agent",
            "capabilities": {
                "model": "gpt-4",
                "servers": ["fetch", "filesystem", "orchestrator"],
                "provider": "openai"
            }
        }

    @pytest.fixture
    async def registered_agent(self, orchestrator, auth_token, agent_data):
        """Register an agent for testing."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["agent:write"]
        )
        
        # Register the agent
        agent_token = await orchestrator.register_agent(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            capabilities=agent_data["capabilities"]
        )
        
        return {
            "agent_id": agent_data["agent_id"],
            "auth_token": agent_token["auth_token"]
        }

    @pytest.fixture
    async def task_data(self):
        """Get test task data."""
        return {
            "name": "Test Task",
            "description": "A test task for integration testing",
            "priority": 3
        }

    @pytest.fixture
    async def created_task(self, orchestrator, auth_token, task_data, registered_agent):
        """Create a task for testing."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["task:write"]
        )
        
        # Create the task
        task_info = await orchestrator.create_task(
            name=task_data["name"],
            description=task_data["description"],
            agent_id=registered_agent["agent_id"],
            priority=task_data.get("priority", 3)
        )
        
        return task_info

    @pytest.mark.asyncio
    async def test_initial_authentication(self, orchestrator):
        """Test the initial authentication flow."""
        # Request an authentication token
        token_info = await orchestrator.authenticate(
            api_key="fast-agent-default-key",
            client_id="test-client",
            scope=["agent:read", "agent:write"]
        )
        
        assert "access_token" in token_info
        assert "refresh_token" in token_info
        assert token_info["token_type"] == "Bearer"
        
        # Validate the token
        token = token_info["access_token"]
        validation = await orchestrator.validate_token(
            token=token,
            required_scopes=["agent:read"]
        )
        
        assert validation["valid"] is True
        assert "agent:read" in validation["scope"]

    @pytest.mark.asyncio
    async def test_token_refresh(self, orchestrator):
        """Test the token refresh flow."""
        # Request an authentication token
        token_info = await orchestrator.authenticate(
            api_key="fast-agent-default-key",
            client_id="test-client",
            scope=["agent:read", "agent:write"]
        )
        
        refresh_token = token_info["refresh_token"]
        
        # Refresh the token
        new_token_info = await orchestrator.refresh_token(
            refresh_token=refresh_token,
            client_id="test-client"
        )
        
        assert "access_token" in new_token_info
        assert "refresh_token" in new_token_info
        
        # Validate the new token
        new_token = new_token_info["access_token"]
        validation = await orchestrator.validate_token(
            token=new_token,
            required_scopes=["agent:read"]
        )
        
        assert validation["valid"] is True
        assert "agent:read" in validation["scope"]

    @pytest.mark.asyncio
    async def test_token_revocation(self, orchestrator):
        """Test the token revocation flow."""
        # Request an authentication token
        token_info = await orchestrator.authenticate(
            api_key="fast-agent-default-key",
            client_id="test-client",
            scope=["agent:read", "agent:write"]
        )
        
        token = token_info["access_token"]
        
        # Revoke the token
        revoked = await orchestrator.revoke_token(
            token=token,
            token_type_hint="access_token"
        )
        
        assert revoked is True
        
        # Attempt to use the revoked token
        with pytest.raises(AuthenticationError):
            await orchestrator.validate_token(
                token=token,
                required_scopes=["agent:read"]
            )

    @pytest.mark.asyncio
    async def test_agent_registration(self, orchestrator, auth_token, agent_data):
        """Test the agent registration flow."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["agent:write"]
        )
        
        # Register the agent
        agent_token = await orchestrator.register_agent(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            capabilities=agent_data["capabilities"]
        )
        
        assert "agent_id" in agent_token
        assert "auth_token" in agent_token
        
        # Get the agent information
        agent_info = await orchestrator.get_agent(agent_data["agent_id"])
        
        assert agent_info["agent_id"] == agent_data["agent_id"]
        assert agent_info["name"] == agent_data["name"]
        assert agent_info["capabilities"] == agent_data["capabilities"]
        assert agent_info["is_active"] is True

    @pytest.mark.asyncio
    async def test_agent_authentication(self, orchestrator, registered_agent):
        """Test the agent authentication flow."""
        # Authenticate the agent
        token_info = await orchestrator.authenticate_agent(
            agent_id=registered_agent["agent_id"],
            auth_token=registered_agent["auth_token"]
        )
        
        assert "access_token" in token_info
        assert token_info["token_type"] == "Bearer"
        
        # Validate the token
        token = token_info["access_token"]
        validation = await orchestrator.validate_token(
            token=token,
            required_scopes=["agent:execute"]
        )
        
        assert validation["valid"] is True
        assert "agent:execute" in validation["scope"]

    @pytest.mark.asyncio
    async def test_agent_listing(self, orchestrator, auth_token, registered_agent):
        """Test the agent listing functionality."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["agent:read"]
        )
        
        # List all agents
        agents = await orchestrator.list_agents()
        
        # Verify the registered agent is in the list
        found = False
        for agent in agents:
            if agent["agent_id"] == registered_agent["agent_id"]:
                found = True
                break
                
        assert found is True

    @pytest.mark.asyncio
    async def test_agent_unregistration(self, orchestrator, auth_token, registered_agent):
        """Test the agent unregistration flow."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["agent:write"]
        )
        
        # Unregister the agent
        unregistered = await orchestrator.unregister_agent(registered_agent["agent_id"])
        
        assert unregistered is True
        
        # Attempt to get the agent information
        with pytest.raises(KeyError):
            await orchestrator.get_agent(registered_agent["agent_id"])

    @pytest.mark.asyncio
    async def test_task_creation(self, orchestrator, auth_token, task_data, registered_agent):
        """Test the task creation flow."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["task:write"]
        )
        
        # Create the task
        task_info = await orchestrator.create_task(
            name=task_data["name"],
            description=task_data["description"],
            agent_id=registered_agent["agent_id"],
            priority=task_data.get("priority", 3)
        )
        
        assert "task_id" in task_info
        assert task_info["name"] == task_data["name"]
        assert task_info["description"] == task_data["description"]
        assert task_info["agent_id"] == registered_agent["agent_id"]
        assert task_info["status"] == "created"

    @pytest.mark.asyncio
    async def test_task_execution(self, orchestrator, auth_token, created_task):
        """Test the task execution flow."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["task:write"]
        )
        
        # Execute the task
        execution_result = await orchestrator.execute_task(
            task_id=created_task["task_id"],
            parameters={}
        )
        
        assert execution_result["task_id"] == created_task["task_id"]
        assert execution_result["status"] == "completed"
        assert "result" in execution_result
        assert "completed_at" in execution_result

    @pytest.mark.asyncio
    async def test_authentication_error(self, orchestrator):
        """Test the authentication error handling."""
        # Attempt to authenticate with an invalid API key
        with pytest.raises(AuthenticationError):
            await orchestrator.authenticate(
                api_key="invalid-key",
                client_id="test-client",
                scope=["agent:read", "agent:write"]
            )
        
        # Attempt to use an invalid token
        with pytest.raises(AuthenticationError):
            await orchestrator.validate_token(
                token="invalid-token",
                required_scopes=["agent:read"]
            )

    @pytest.mark.asyncio
    async def test_authorization_error(self, orchestrator):
        """Test the authorization error handling."""
        # Authenticate with limited scopes
        token_info = await orchestrator.authenticate(
            api_key="fast-agent-default-key",
            client_id="test-client",
            scope=["agent:read"]  # Only agent:read scope
        )
        
        token = token_info["access_token"]
        
        # Attempt to perform an action requiring additional scopes
        with pytest.raises(AuthorizationError):
            # Validate token with agent:write scope
            await orchestrator.validate_token(
                token=token,
                required_scopes=["agent:write"]
            )

    @pytest.mark.asyncio
    async def test_resource_error(self, orchestrator, auth_token):
        """Test the resource error handling."""
        # Validate the token first
        await orchestrator.validate_token(
            token=auth_token,
            required_scopes=["agent:read", "task:read"]
        )
        
        # Attempt to get a non-existent agent
        with pytest.raises(KeyError):
            await orchestrator.get_agent("non-existent-agent")
        
        # Attempt to execute a non-existent task
        with pytest.raises(KeyError):
            await orchestrator.execute_task(
                task_id="non-existent-task",
                parameters={}
            )

    @pytest.mark.asyncio
    async def test_fast_agent_integration(self, fast_agent_adapter):
        """Test the integration between Fast-Agent and AI-Orchestrator."""
        # Create an agent
        agent_id = await fast_agent_adapter.create_agent(
            agent_id="test-integration-agent",
            name="Integration Test Agent",
            description="An agent for testing the integration",
            instruction="You are a test agent for integration testing.",
            model="gpt-4"
        )
        
        assert agent_id is not None
        
        # Get the agent information
        agent_info = await fast_agent_adapter.get_agent(agent_id)
        
        assert agent_info["id"] == agent_id
        assert agent_info["name"] == "Integration Test Agent"
        assert agent_info["description"] == "An agent for testing the integration"
        assert "capabilities" in agent_info
        
        # List all agents
        agents = await fast_agent_adapter.list_agents()
        
        # Verify the created agent is in the list
        found = False
        for agent in agents:
            if agent["id"] == agent_id:
                found = True
                break
                
        assert found is True
        
        # Delete the agent
        deleted = await fast_agent_adapter.delete_agent(agent_id)
        
        assert deleted is True
