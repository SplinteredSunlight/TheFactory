"""
Authentication Tests

This module contains tests for the authentication mechanism between AI-Orchestrator and Fast-Agent.
"""

import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock

from orchestrator.auth import (
    TokenManager,
    get_token_manager,
    AuthenticationError,
    AuthorizationError,
)
from orchestrator.engine import OrchestratorEngine
from fast_agent_integration.adapter import FastAgentAdapter, get_adapter


class TestTokenManager(unittest.TestCase):
    """Test the TokenManager class."""

    def setUp(self):
        """Set up the test environment."""
        self.token_manager = TokenManager(secret_key="test-secret-key")
        self.client_id = "test-client"
        self.api_key = self.token_manager.register_api_key(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

    def test_register_api_key(self):
        """Test registering an API key."""
        # Test that the API key was registered
        self.assertIn(self.api_key, self.token_manager.api_keys)
        self.assertEqual(self.token_manager.api_keys[self.api_key]["client_id"], self.client_id)
        self.assertEqual(self.token_manager.api_keys[self.api_key]["scopes"], ["test:read", "test:write"])

    def test_validate_api_key(self):
        """Test validating an API key."""
        # Test valid API key
        is_valid, client_id, scopes = self.token_manager.validate_api_key(self.api_key)
        self.assertTrue(is_valid)
        self.assertEqual(client_id, self.client_id)
        self.assertEqual(scopes, ["test:read", "test:write"])

        # Test invalid API key
        is_valid, client_id, scopes = self.token_manager.validate_api_key("invalid-key")
        self.assertFalse(is_valid)
        self.assertEqual(client_id, "")
        self.assertEqual(scopes, [])

        # Test valid API key with required scopes
        is_valid, client_id, scopes = self.token_manager.validate_api_key(
            self.api_key, required_scopes=["test:read"]
        )
        self.assertTrue(is_valid)
        self.assertEqual(client_id, self.client_id)
        self.assertEqual(scopes, ["test:read", "test:write"])

        # Test valid API key with missing required scopes
        is_valid, client_id, scopes = self.token_manager.validate_api_key(
            self.api_key, required_scopes=["test:admin"]
        )
        self.assertTrue(is_valid)
        self.assertEqual(client_id, self.client_id)
        self.assertEqual(scopes, [])

    def test_generate_token(self):
        """Test generating a JWT token."""
        token_info = self.token_manager.generate_token(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

        # Test that the token was generated
        self.assertIn("access_token", token_info)
        self.assertIn("refresh_token", token_info)
        self.assertIn("token_type", token_info)
        self.assertIn("expires_in", token_info)
        self.assertIn("scope", token_info)

        # Test that the token was stored
        token_id = None
        for jti, info in self.token_manager.tokens.items():
            if info["access_token"] == token_info["access_token"]:
                token_id = jti
                break

        self.assertIsNotNone(token_id)
        self.assertEqual(self.token_manager.tokens[token_id]["client_id"], self.client_id)
        self.assertEqual(self.token_manager.tokens[token_id]["scopes"], ["test:read", "test:write"])

    def test_validate_token(self):
        """Test validating a JWT token."""
        token_info = self.token_manager.generate_token(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

        # Test valid token
        is_valid, payload = self.token_manager.validate_token(token_info["access_token"])
        self.assertTrue(is_valid)
        self.assertEqual(payload["sub"], self.client_id)
        self.assertEqual(payload["scope"], ["test:read", "test:write"])

        # Test valid token with required scopes
        is_valid, payload = self.token_manager.validate_token(
            token_info["access_token"], required_scopes=["test:read"]
        )
        self.assertTrue(is_valid)
        self.assertEqual(payload["sub"], self.client_id)
        self.assertEqual(payload["scope"], ["test:read", "test:write"])

        # Test valid token with missing required scopes
        is_valid, payload = self.token_manager.validate_token(
            token_info["access_token"], required_scopes=["test:admin"]
        )
        self.assertFalse(is_valid)
        self.assertEqual(payload, {})

        # Test invalid token
        is_valid, payload = self.token_manager.validate_token("invalid-token")
        self.assertFalse(is_valid)
        self.assertEqual(payload, {})

    def test_refresh_token(self):
        """Test refreshing a JWT token."""
        token_info = self.token_manager.generate_token(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

        # Test refreshing a valid token
        new_token_info = self.token_manager.refresh_token(
            refresh_token=token_info["refresh_token"],
            client_id=self.client_id,
        )

        # Test that a new token was generated
        self.assertNotEqual(new_token_info["access_token"], token_info["access_token"])
        self.assertNotEqual(new_token_info["refresh_token"], token_info["refresh_token"])

        # Test that the old token was revoked
        is_valid, _ = self.token_manager.validate_token(token_info["access_token"])
        self.assertFalse(is_valid)

        # Test that the new token is valid
        is_valid, payload = self.token_manager.validate_token(new_token_info["access_token"])
        self.assertTrue(is_valid)
        self.assertEqual(payload["sub"], self.client_id)
        self.assertEqual(payload["scope"], ["test:read", "test:write"])

        # Test refreshing with an invalid refresh token
        with self.assertRaises(AuthenticationError):
            self.token_manager.refresh_token(
                refresh_token="invalid-token",
                client_id=self.client_id,
            )

        # Test refreshing with an invalid client ID
        with self.assertRaises(AuthenticationError):
            self.token_manager.refresh_token(
                refresh_token=new_token_info["refresh_token"],
                client_id="invalid-client",
            )

    def test_revoke_token(self):
        """Test revoking a JWT token."""
        token_info = self.token_manager.generate_token(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

        # Test revoking a valid access token
        success = self.token_manager.revoke_token(
            token=token_info["access_token"],
            token_type_hint="access_token",
        )
        self.assertTrue(success)

        # Test that the token was revoked
        is_valid, _ = self.token_manager.validate_token(token_info["access_token"])
        self.assertFalse(is_valid)

        # Test revoking an invalid access token
        success = self.token_manager.revoke_token(
            token="invalid-token",
            token_type_hint="access_token",
        )
        self.assertFalse(success)

        # Generate a new token for testing refresh token revocation
        token_info = self.token_manager.generate_token(
            client_id=self.client_id,
            scopes=["test:read", "test:write"],
        )

        # Test revoking a valid refresh token
        success = self.token_manager.revoke_token(
            token=token_info["refresh_token"],
            token_type_hint="refresh_token",
        )
        self.assertTrue(success)

        # Test that the token was revoked
        with self.assertRaises(AuthenticationError):
            self.token_manager.refresh_token(
                refresh_token=token_info["refresh_token"],
                client_id=self.client_id,
            )

        # Test revoking an invalid refresh token
        success = self.token_manager.revoke_token(
            token="invalid-token",
            token_type_hint="refresh_token",
        )
        self.assertFalse(success)

    def test_generate_agent_token(self):
        """Test generating an agent token."""
        agent_id = "test-agent"
        agent_name = "Test Agent"
        capabilities = {"model": "gpt-4", "provider": "openai"}

        agent_token = self.token_manager.generate_agent_token(
            agent_id=agent_id,
            name=agent_name,
            capabilities=capabilities,
        )

        # Test that the token was generated
        self.assertIn("agent_id", agent_token)
        self.assertIn("auth_token", agent_token)
        self.assertIn("expires_in", agent_token)

        # Test that the token was stored
        self.assertIn(agent_id, self.token_manager.agent_tokens)
        self.assertEqual(self.token_manager.agent_tokens[agent_id]["name"], agent_name)
        self.assertEqual(self.token_manager.agent_tokens[agent_id]["capabilities"], capabilities)
        self.assertEqual(self.token_manager.agent_tokens[agent_id]["auth_token"], agent_token["auth_token"])

    def test_validate_agent_token(self):
        """Test validating an agent token."""
        agent_id = "test-agent"
        agent_name = "Test Agent"
        capabilities = {"model": "gpt-4", "provider": "openai"}

        agent_token = self.token_manager.generate_agent_token(
            agent_id=agent_id,
            name=agent_name,
            capabilities=capabilities,
        )

        # Test valid token
        is_valid = self.token_manager.validate_agent_token(
            agent_id=agent_id,
            auth_token=agent_token["auth_token"],
        )
        self.assertTrue(is_valid)

        # Test invalid agent ID
        is_valid = self.token_manager.validate_agent_token(
            agent_id="invalid-agent",
            auth_token=agent_token["auth_token"],
        )
        self.assertFalse(is_valid)

        # Test invalid token
        is_valid = self.token_manager.validate_agent_token(
            agent_id=agent_id,
            auth_token="invalid-token",
        )
        self.assertFalse(is_valid)

    def test_get_agent_info(self):
        """Test getting agent information."""
        agent_id = "test-agent"
        agent_name = "Test Agent"
        capabilities = {"model": "gpt-4", "provider": "openai"}

        agent_token = self.token_manager.generate_agent_token(
            agent_id=agent_id,
            name=agent_name,
            capabilities=capabilities,
        )

        # Test getting valid agent info
        agent_info = self.token_manager.get_agent_info(agent_id)
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info["agent_id"], agent_id)
        self.assertEqual(agent_info["name"], agent_name)
        self.assertEqual(agent_info["capabilities"], capabilities)
        self.assertNotIn("auth_token", agent_info)  # Sensitive info should be removed

        # Test getting invalid agent info
        agent_info = self.token_manager.get_agent_info("invalid-agent")
        self.assertIsNone(agent_info)


class TestOrchestratorEngineAuth(unittest.IsolatedAsyncioTestCase):
    """Test the authentication methods in the OrchestratorEngine class."""

    async def asyncSetUp(self):
        """Set up the test environment."""
        self.engine = OrchestratorEngine()
        self.client_id = "test-client"
        self.api_key = "test-api-key"

        # Register the API key
        self.engine.token_manager.register_api_key(
            client_id=self.client_id,
            api_key=self.api_key,
            scopes=["agent:read", "agent:write", "task:read", "task:write"],
        )

    async def test_authenticate(self):
        """Test authenticating with the orchestrator."""
        # Test valid authentication
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Test that the token was generated
        self.assertIn("access_token", auth_result)
        self.assertIn("refresh_token", auth_result)
        self.assertIn("token_type", auth_result)
        self.assertIn("expires_in", auth_result)
        self.assertIn("scope", auth_result)

        # Test invalid API key
        with self.assertRaises(AuthenticationError):
            await self.engine.authenticate(
                api_key="invalid-key",
                client_id=self.client_id,
                scope=["agent:read", "agent:write"],
            )

        # Test invalid client ID
        with self.assertRaises(AuthenticationError):
            await self.engine.authenticate(
                api_key=self.api_key,
                client_id="invalid-client",
                scope=["agent:read", "agent:write"],
            )

        # Test insufficient scopes
        with self.assertRaises(AuthorizationError):
            await self.engine.authenticate(
                api_key=self.api_key,
                client_id=self.client_id,
                scope=["agent:admin"],
            )

    async def test_refresh_token(self):
        """Test refreshing a token."""
        # Authenticate first to get a token
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Test valid refresh
        refresh_result = await self.engine.refresh_token(
            refresh_token=auth_result["refresh_token"],
            client_id=self.client_id,
        )

        # Test that a new token was generated
        self.assertIn("access_token", refresh_result)
        self.assertIn("refresh_token", refresh_result)
        self.assertIn("token_type", refresh_result)
        self.assertIn("expires_in", refresh_result)
        self.assertIn("scope", refresh_result)
        self.assertNotEqual(refresh_result["access_token"], auth_result["access_token"])
        self.assertNotEqual(refresh_result["refresh_token"], auth_result["refresh_token"])

        # Test invalid refresh token
        with self.assertRaises(AuthenticationError):
            await self.engine.refresh_token(
                refresh_token="invalid-token",
                client_id=self.client_id,
            )

        # Test invalid client ID
        with self.assertRaises(AuthenticationError):
            await self.engine.refresh_token(
                refresh_token=refresh_result["refresh_token"],
                client_id="invalid-client",
            )

    async def test_validate_token(self):
        """Test validating a token."""
        # Authenticate first to get a token
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Test valid token
        validate_result = await self.engine.validate_token(
            token=auth_result["access_token"],
            required_scopes=["agent:read"],
        )

        # Test that the token is valid
        self.assertTrue(validate_result["valid"])
        self.assertIn("expires_in", validate_result)
        self.assertIn("scope", validate_result)
        self.assertIn("client_id", validate_result)
        self.assertEqual(validate_result["client_id"], self.client_id)

        # Test invalid token
        with self.assertRaises(AuthenticationError):
            await self.engine.validate_token(
                token="invalid-token",
                required_scopes=["agent:read"],
            )

        # Test insufficient scopes
        with self.assertRaises(AuthorizationError):
            await self.engine.validate_token(
                token=auth_result["access_token"],
                required_scopes=["agent:admin"],
            )

    async def test_revoke_token(self):
        """Test revoking a token."""
        # Authenticate first to get a token
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Test revoking a valid token
        success = await self.engine.revoke_token(
            token=auth_result["access_token"],
            token_type_hint="access_token",
        )
        self.assertTrue(success)

        # Test that the token is no longer valid
        with self.assertRaises(AuthenticationError):
            await self.engine.validate_token(
                token=auth_result["access_token"],
                required_scopes=["agent:read"],
            )

        # Test revoking an invalid token
        success = await self.engine.revoke_token(
            token="invalid-token",
            token_type_hint="access_token",
        )
        self.assertFalse(success)

    async def test_register_agent(self):
        """Test registering an agent."""
        # Authenticate first to get a token
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Test registering an agent
        agent_id = "test-agent"
        agent_name = "Test Agent"
        capabilities = {"model": "gpt-4", "provider": "openai"}

        agent_token = await self.engine.register_agent(
            agent_id=agent_id,
            name=agent_name,
            capabilities=capabilities,
        )

        # Test that the agent was registered
        self.assertIn("agent_id", agent_token)
        self.assertIn("auth_token", agent_token)
        self.assertIn("expires_in", agent_token)
        self.assertEqual(agent_token["agent_id"], agent_id)

        # Test that the agent info can be retrieved
        agent_info = await self.engine.get_agent(agent_id)
        self.assertEqual(agent_info["agent_id"], agent_id)
        self.assertEqual(agent_info["name"], agent_name)
        self.assertEqual(agent_info["capabilities"], capabilities)

    async def test_authenticate_agent(self):
        """Test authenticating an agent."""
        # Authenticate first to get a token
        auth_result = await self.engine.authenticate(
            api_key=self.api_key,
            client_id=self.client_id,
            scope=["agent:read", "agent:write"],
        )

        # Register an agent
        agent_id = "test-agent"
        agent_name = "Test Agent"
        capabilities = {"model": "gpt-4", "provider": "openai"}

        agent_token = await self.engine.register_agent(
            agent_id=agent_id,
            name=agent_name,
            capabilities=capabilities,
        )

        # Test authenticating the agent
        agent_auth_result = await self.engine.authenticate_agent(
            agent_id=agent_id,
            auth_token=agent_token["auth_token"],
        )

        # Test that the agent was authenticated
        self.assertIn("access_token", agent_auth_result)
        self.assertIn("refresh_token", agent_auth_result)
        self.assertIn("token_type", agent_auth_result)
        self.assertIn("expires_in", agent_auth_result)
        self.assertIn("scope", agent_auth_result)

        # Test invalid agent ID
        with self.assertRaises(AuthenticationError):
            await self.engine.authenticate_agent(
                agent_id="invalid-agent",
                auth_token=agent_token["auth_token"],
            )

        # Test invalid auth token
        with self.assertRaises(AuthenticationError):
            await self.engine.authenticate_agent(
                agent_id=agent_id,
                auth_token="invalid-token",
            )


class TestFastAgentAdapter(unittest.IsolatedAsyncioTestCase):
    """Test the FastAgentAdapter class."""

    async def asyncSetUp(self):
        """Set up the test environment."""
        # Mock the OrchestratorEngine
        self.mock_engine = MagicMock(spec=OrchestratorEngine)
        
        # Create a FastAgentAdapter with the mock engine
        self.adapter = FastAgentAdapter(
            app_name="test-app",
            api_key="test-api-key",
        )
        self.adapter.orchestrator = self.mock_engine
        
        # Mock the MCPApp
        self.adapter.app = MagicMock()
        
        # Set up mock return values
        self.mock_engine.authenticate.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
        }
        
        self.mock_engine.validate_token.return_value = {
            "valid": True,
            "expires_in": 3600,
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
            "client_id": "fast-agent-test-app",
        }
        
        self.mock_engine.refresh_token.return_value = {
            "access_token": "test-access-token-2",
            "refresh_token": "test-refresh-token-2",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
        }
        
        self.mock_engine.register_agent.return_value = {
            "agent_id": "test-agent",
            "auth_token": "test-agent-token",
            "expires_in": 86400,
        }
        
        self.mock_engine.get_agent.return_value = {
            "agent_id": "test-agent",
            "name": "Test Agent",
            "capabilities": {"model": "gpt-4", "provider": "openai"},
        }

    async def test_initialize(self):
        """Test initializing the adapter."""
        # Test that initialize calls authenticate
        await self.adapter.initialize()
        self.mock_engine.authenticate.assert_called_once_with(
            api_key="test-api-key",
            client_id="fast-agent-test-app",
            scope=["agent:read", "agent:write", "task:read", "task:write"],
        )
        
        # Test that the tokens were stored
        self.assertEqual(self.adapter.access_token, "test-access-token")
        self.assertEqual(self.adapter.refresh_token, "test-refresh-token")
        self.assertEqual(self.adapter.token_expiry, 3600)

    async def test_authenticate(self):
        """Test authenticating with the orchestrator."""
        # Test successful authentication
        result = await self.adapter.authenticate()
        self.assertTrue(result)
        self.mock_engine.authenticate.assert_called_once_with(
            api_key="test-api-key",
            client_id="fast-agent-test-app",
            scope=["agent:read", "agent:write", "task:read", "task:write"],
        )
        
        # Test failed authentication
        self.mock_engine.authenticate.side_effect = AuthenticationError("Invalid API key")
        result = await self.adapter.authenticate()
        self.assertFalse(result)

    async def test_refresh_auth_token(self):
        """Test refreshing the authentication token."""
        # Set up initial tokens
        self.adapter.access_token = "test-access-token"
        self.adapter.refresh_token = "test-refresh-token"
        
        # Test successful refresh
        result = await self.adapter.refresh_auth_token()
        self.assertTrue(result)
        self.mock_engine.refresh_token.assert_called_once_with(
            refresh_token="test-refresh-token",
            client_id="fast-agent-test-app",
        )
        
        # Test that the tokens were updated
        self.assertEqual(self.adapter.access_token, "test-access-token-2")
        self.assertEqual(self.adapter.refresh_token, "test-refresh-token-2")
        self.assertEqual(self.adapter.token_expiry, 3600)
        
        # Test failed refresh
        self.mock_engine.refresh_token.side_effect = AuthenticationError("Invalid refresh token")
        self.mock_engine.authenticate.return_value = {
            "access_token": "test-access-token-3",
            "refresh_token": "test-refresh-token-3",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": ["agent:read", "agent:write", "task:read", "task:write"],
        }
        
        result = await self.adapter.refresh_auth_token()
        self.assertTrue(result)
        self.mock_engine.authenticate.assert_called_once_with(
            api_key="test-api-key",
            client_id="fast-agent-test-app",
            scope=["agent:read", "agent:write", "task:read", "task:write"],
        )
        
        # Test that the tokens were updated
        self.assertEqual(self.adapter.access_token, "test-access-token-3")
        self.assertEqual(self.adapter.refresh_token, "test-refresh-token-3")
        self.assertEqual(self.adapter.token_expiry, 3600)

    async def test_ensure_authenticated(self):
        """Test ensuring the adapter is authenticated."""
        # Test with no token
        self.adapter.access_token = None
        result = await self.adapter.ensure_authenticated()
        self.assertTrue(result)
        self.mock_engine.authenticate.assert_called_once_with(
            api_key="test-api-key",
            client_id="fast-agent-test-app",
            scope=["agent:read", "agent:write", "task:read", "task:write"],
        )
        
        # Test with valid token
        self.adapter.access_token = "test-access-token"
        result = await self.adapter.ensure_authenticated()
        self.assertTrue(result)
        self.mock_engine.validate_token.assert_called_once_with(
            token="test-access-token",
            required_scopes=["agent:read"],
        )
        
        # Test with invalid token
        self.mock_engine.validate_token.side_effect = AuthenticationError("Invalid token")
        result = await self.adapter.ensure_authenticated()
        self.assertTrue(result)
        self.mock_engine.refresh_token.assert_called_once_with(
            refresh_token="test-refresh-token",
            client_id="fast-agent-test-app",
        )


if __name__ == "__main__":
    unittest.main()
