"""
Orchestrator API Client Module

This module provides a client for interacting with the AI-Orchestration-Platform's
Orchestrator API. It handles authentication, error handling, and provides methods
for all the available API endpoints.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable

from src.orchestrator.auth import AuthenticationError, AuthorizationError
from src.orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ErrorSeverity,
    Component,
    ResourceError,
    IntegrationError,
    SystemError,
    RetryHandler,
    CircuitBreaker,
    get_error_handler
)
from src.orchestrator.communication import MessageType, MessagePriority
from src.orchestrator.task_distribution import TaskDistributionStrategy

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class OrchestratorClient:
    """Client for interacting with the AI-Orchestration-Platform's Orchestrator API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: str = "orchestrator-client",
        base_url: Optional[str] = None,
    ):
        """Initialize the Orchestrator API client.

        Args:
            api_key: API key for authenticating with the orchestrator
            client_id: Identifier for the client
            base_url: Base URL for the orchestrator API (for remote orchestrators)
        """
        self.api_key = api_key or os.environ.get("ORCHESTRATOR_API_KEY") or "fast-agent-default-key"
        self.client_id = client_id
        self.base_url = base_url
        
        # Authentication state
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[int] = None
        
        # Error handling
        self.retry_handler = RetryHandler(
            max_retries=3,
            backoff_factor=0.5,
            jitter=True
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            reset_timeout=30,
            half_open_limit=3
        )
        
        # Import the orchestrator engine
        # If base_url is provided, we'll use HTTP client instead
        if not base_url:
            from src.orchestrator.engine import OrchestratorEngine
            self.orchestrator = OrchestratorEngine()
        else:
            # We'll implement HTTP client in the future
            self.orchestrator = None
            raise NotImplementedError("Remote orchestrator not yet implemented")

    async def initialize(self) -> None:
        """Initialize the client and authenticate with the orchestrator."""
        await self.authenticate()

    async def authenticate(self) -> bool:
        """Authenticate with the orchestrator.
        
        Returns:
            True if authentication was successful, False otherwise
        
        Raises:
            AuthenticationError: If authentication fails after retries
        """
        try:
            # Use retry handler for authentication
            auth_result = await self.retry_handler.execute(
                self._authenticate_internal
            )
            
            # Store the tokens
            self.access_token = auth_result["access_token"]
            self.refresh_token = auth_result["refresh_token"]
            self.token_expiry = int(auth_result["expires_in"])
            
            logger.info(f"Authenticated with orchestrator as {self.client_id}")
            return True
            
        except (AuthenticationError, AuthorizationError) as e:
            error_handler.log_error(e, {"client_id": self.client_id})
            return False
        except BaseError as e:
            error_handler.log_error(e, {"client_id": self.client_id})
            return False
    
    async def _authenticate_internal(self) -> Dict[str, Any]:
        """Internal authentication method used by retry handler."""
        try:
            # Authenticate with the orchestrator
            return await self.orchestrator.authenticate(
                api_key=self.api_key,
                client_id=self.client_id,
                scope=["agent:read", "agent:write", "task:read", "task:write"],
            )
        except (AuthenticationError, AuthorizationError) as e:
            # Convert to standardized error format
            if isinstance(e, AuthenticationError):
                raise AuthenticationError(
                    message=f"Authentication failed: {str(e)}",
                    code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                    details={"client_id": self.client_id},
                )
            else:
                raise AuthorizationError(
                    message=f"Authorization failed: {str(e)}",
                    code=ErrorCode.AUTH_INSUFFICIENT_SCOPE,
                    details={"client_id": self.client_id, "requested_scopes": ["agent:read", "agent:write", "task:read", "task:write"]},
                )
    
    async def refresh_auth_token(self) -> bool:
        """Refresh the authentication token.
        
        Returns:
            True if the token was refreshed successfully, False otherwise
        """
        if not self.refresh_token:
            logger.warning("No refresh token available, attempting full authentication")
            return await self.authenticate()
            
        try:
            # Use retry handler for token refresh
            auth_result = await self.retry_handler.execute(
                self._refresh_token_internal
            )
            
            # Store the tokens
            self.access_token = auth_result["access_token"]
            self.refresh_token = auth_result["refresh_token"]
            self.token_expiry = int(auth_result["expires_in"])
            
            logger.info(f"Refreshed authentication token for {self.client_id}")
            return True
            
        except (AuthenticationError, AuthorizationError) as e:
            error_handler.log_error(e, {"client_id": self.client_id})
            logger.warning(f"Token refresh failed, attempting full authentication")
            return await self.authenticate()
        except BaseError as e:
            error_handler.log_error(e, {"client_id": self.client_id})
            logger.warning(f"Token refresh failed with error: {e.code}, attempting full authentication")
            return await self.authenticate()
    
    async def _refresh_token_internal(self) -> Dict[str, Any]:
        """Internal token refresh method used by retry handler."""
        try:
            # Refresh the token
            return await self.orchestrator.refresh_token(
                refresh_token=self.refresh_token,
                client_id=self.client_id,
            )
        except (AuthenticationError, AuthorizationError) as e:
            # Convert to standardized error format
            if isinstance(e, AuthenticationError):
                raise AuthenticationError(
                    message=f"Token refresh failed: {str(e)}",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                    details={"client_id": self.client_id},
                )
            else:
                raise AuthorizationError(
                    message=f"Token refresh authorization failed: {str(e)}",
                    code=ErrorCode.AUTH_INSUFFICIENT_SCOPE,
                    details={"client_id": self.client_id},
                )
    
    async def ensure_authenticated(self) -> bool:
        """Ensure that the client is authenticated.
        
        Returns:
            True if the client is authenticated, False otherwise
        """
        if not self.access_token:
            return await self.authenticate()
            
        try:
            # Validate the token
            await self.orchestrator.validate_token(
                token=self.access_token,
                required_scopes=["agent:read"],
            )
            return True
            
        except (AuthenticationError, AuthorizationError) as e:
            # Token is invalid or expired, try to refresh it
            logger.info(f"Token validation failed: {str(e)}, attempting to refresh")
            return await self.refresh_auth_token()
        except Exception as e:
            # Unexpected error, log and try to refresh
            error_handler.log_error(e, {"client_id": self.client_id})
            logger.warning(f"Unexpected error during token validation: {str(e)}, attempting to refresh")
            return await self.refresh_auth_token()
    
    async def _execute_with_auth(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with authentication and error handling.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            Various other exceptions depending on the function
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            raise IntegrationError(
                message="Circuit breaker is open, too many recent failures",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
                component=Component.INTEGRATION,
                severity=ErrorSeverity.ERROR,
                details={"circuit_breaker_state": "open"}
            )
        
        # Ensure we're authenticated
        if not await self.ensure_authenticated():
            raise AuthenticationError(
                message="Failed to authenticate with orchestrator",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                details={"client_id": self.client_id}
            )
        
        try:
            # Add auth token to kwargs if not already present
            if "auth_token" not in kwargs and self.access_token:
                kwargs["auth_token"] = self.access_token
            
            # Use retry handler to execute the function
            result = await self.retry_handler.execute(func, *args, **kwargs)
            
            # Record success with circuit breaker
            self.circuit_breaker.record_success()
            
            return result
            
        except (AuthenticationError, AuthorizationError) as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Try to re-authenticate and retry once
            if await self.ensure_authenticated():
                # Update auth token in kwargs
                if "auth_token" in kwargs:
                    kwargs["auth_token"] = self.access_token
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success with circuit breaker
                    self.circuit_breaker.record_success()
                    
                    return result
                except Exception as retry_e:
                    # Record failure with circuit breaker
                    self.circuit_breaker.record_failure()
                    
                    # Log the error
                    error_handler.log_error(retry_e, {"client_id": self.client_id})
                    
                    # Re-raise the original error
                    raise e
            
            # Log the error
            error_handler.log_error(e, {"client_id": self.client_id})
            
            raise
        except Exception as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {"client_id": self.client_id})
            
            raise
    
    # Agent Management Methods
    
    async def register_agent(
        self,
        agent_id: str,
        name: str,
        capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register a new agent with the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Name of the agent
            capabilities: Dictionary of agent capabilities
            
        Returns:
            Dictionary containing the agent token information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.register_agent,
            agent_id=agent_id,
            name=name,
            capabilities=capabilities
        )
    
    async def authenticate_agent(
        self,
        agent_id: str,
        auth_token: str
    ) -> Dict[str, Any]:
        """Authenticate an agent with the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            auth_token: Authentication token for the agent
            
        Returns:
            Dictionary containing the token information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.authenticate_agent,
            agent_id=agent_id,
            auth_token=auth_token
        )
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get information about an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dictionary containing agent information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If the agent doesn't exist
        """
        return await self._execute_with_auth(
            self.orchestrator.get_agent,
            agent_id=agent_id
        )
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents registered with the orchestrator.
        
        Returns:
            List of agent dictionaries
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.list_agents
        )
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if the agent was unregistered, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.unregister_agent,
            agent_id=agent_id
        )
    
    # Task Management Methods
    
    async def create_task(
        self,
        name: str,
        description: str,
        agent_id: Optional[str] = None,
        priority: int = 3
    ) -> Dict[str, Any]:
        """Create a new task.
        
        Args:
            name: Name of the task
            description: Description of the task
            agent_id: ID of the agent to assign the task to
            priority: Priority of the task (1-5)
            
        Returns:
            Dictionary containing the task information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.create_task,
            name=name,
            description=description,
            agent_id=agent_id,
            priority=priority
        )
    
    async def execute_task(
        self,
        task_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task.
        
        Args:
            task_id: ID of the task to execute
            parameters: Parameters for the task execution
            
        Returns:
            Dictionary containing the task execution results
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If the task doesn't exist
        """
        return await self._execute_with_auth(
            self.orchestrator.execute_task,
            task_id=task_id,
            parameters=parameters
        )
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get information about a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Dictionary containing task information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If the task doesn't exist
        """
        return await self._execute_with_auth(
            self.orchestrator.get_task,
            task_id=task_id
        )
    
    async def distribute_task(
        self,
        task_id: str,
        required_capabilities: List[str],
        task_data: Dict[str, Any],
        distribution_strategy: Optional[str] = None,
        excluded_agents: Optional[List[str]] = None,
        priority: str = "medium",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Distribute a task to an appropriate agent.
        
        Args:
            task_id: ID of the task
            required_capabilities: Capabilities required for the task
            task_data: Data for the task
            distribution_strategy: Strategy for distributing the task
            excluded_agents: List of agent IDs to exclude
            priority: Priority of the task (high, medium, low)
            ttl: Time-to-live in seconds
            metadata: Additional metadata for the task
            
        Returns:
            Dictionary containing the distribution result
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If no suitable agent is found
        """
        return await self._execute_with_auth(
            self.orchestrator.distribute_task,
            task_id=task_id,
            required_capabilities=required_capabilities,
            task_data=task_data,
            distribution_strategy=distribution_strategy,
            excluded_agents=excluded_agents,
            priority=priority,
            ttl=ttl,
            metadata=metadata
        )
    
    async def handle_task_response(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle a task response from an agent.
        
        Args:
            task_id: ID of the task
            agent_id: ID of the agent that executed the task
            status: Status of the task execution
            result: Result of the task execution
            error: Error message if the task failed
            
        Returns:
            Dictionary containing the updated task information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.handle_task_response,
            task_id=task_id,
            agent_id=agent_id,
            status=status,
            result=result,
            error=error
        )
    
    # Task Distribution Methods
    
    async def register_agent_with_distributor(
        self,
        agent_id: str,
        capabilities: List[str],
        priority: int = 1
    ) -> Dict[str, Any]:
        """Register an agent with the task distributor.
        
        Args:
            agent_id: ID of the agent to register
            capabilities: List of agent capabilities
            priority: Priority of the agent (higher is better)
            
        Returns:
            Dictionary containing the registration result
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.register_agent_with_distributor,
            agent_id=agent_id,
            capabilities=capabilities,
            priority=priority
        )
    
    async def unregister_agent_from_distributor(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Unregister an agent from the task distributor.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            Dictionary containing the unregistration result
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.unregister_agent_from_distributor,
            agent_id=agent_id
        )
    
    async def update_agent_status_in_distributor(
        self,
        agent_id: str,
        is_online: bool,
        current_load: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update the status of an agent in the task distributor.
        
        Args:
            agent_id: ID of the agent
            is_online: Whether the agent is online
            current_load: Current load of the agent (number of active tasks)
            
        Returns:
            Dictionary containing the update result
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.update_agent_status_in_distributor,
            agent_id=agent_id,
            is_online=is_online,
            current_load=current_load
        )
    
    # Agent Communication Methods
    
    async def send_agent_message(
        self,
        sender_id: str,
        message_type: str,
        content: Any,
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: str = "medium",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message from one agent to another.
        
        Args:
            sender_id: ID of the agent sending the message
            message_type: Type of the message (direct, broadcast, task_request, etc.)
            content: Content of the message
            recipient_id: ID of the agent receiving the message (None for broadcasts)
            correlation_id: ID to correlate related messages
            priority: Priority of the message (high, medium, low)
            ttl: Time-to-live in seconds
            metadata: Additional metadata for the message
            
        Returns:
            Dictionary containing the message ID and status
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the sender doesn't have permission to send the message
            ResourceError: If the recipient agent doesn't exist
        """
        return await self._execute_with_auth(
            self.orchestrator.send_agent_message,
            sender_id=sender_id,
            message_type=message_type,
            content=content,
            recipient_id=recipient_id,
            correlation_id=correlation_id,
            priority=priority,
            ttl=ttl,
            metadata=metadata
        )
    
    async def get_agent_messages(
        self,
        agent_id: str,
        mark_delivered: bool = True
    ) -> Dict[str, Any]:
        """Get messages for an agent.
        
        Args:
            agent_id: ID of the agent
            mark_delivered: Whether to mark the messages as delivered
            
        Returns:
            Dictionary containing the messages and status
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the agent doesn't have permission to get messages
        """
        return await self._execute_with_auth(
            self.orchestrator.get_agent_messages,
            agent_id=agent_id,
            mark_delivered=mark_delivered
        )
    
    async def get_agent_communication_capabilities(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get the communication capabilities of an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary of agent communication capabilities
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If the agent doesn't exist
        """
        return await self._execute_with_auth(
            self.orchestrator.get_agent_communication_capabilities,
            agent_id=agent_id
        )
    
    # System Methods
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the orchestrator.
        
        Returns:
            Dictionary containing status information
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.get_status
        )
    
    async def query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a query against the orchestrator.
        
        Args:
            query: Query to execute
            parameters: Parameters for the query
            
        Returns:
            Dictionary containing the query results
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
        """
        return await self._execute_with_auth(
            self.orchestrator.query,
            query=query,
            parameters=parameters
        )
    
    async def shutdown(self) -> None:
        """Shutdown the client and release resources."""
        # Revoke the access token if we have one
        if self.access_token:
            try:
                await self.orchestrator.revoke_token(self.access_token)
                logger.info("Revoked access token during shutdown")
            except Exception as e:
                error_handler.log_error(e, {"operation": "revoke_access_token"})
                logger.error(f"Error revoking access token during shutdown: {str(e)}")
        
        # Revoke the refresh token if we have one
        if self.refresh_token:
            try:
                await self.orchestrator.revoke_token(self.refresh_token, token_type_hint="refresh_token")
                logger.info("Revoked refresh token during shutdown")
            except Exception as e:
                error_handler.log_error(e, {"operation": "revoke_refresh_token"})
                logger.error(f"Error revoking refresh token during shutdown: {str(e)}")


# Singleton instance
_client_instance: Optional[OrchestratorClient] = None


async def get_client(
    api_key: Optional[str] = None,
    client_id: str = "orchestrator-client",
    base_url: Optional[str] = None,
) -> OrchestratorClient:
    """Get the OrchestratorClient singleton instance.

    Args:
        api_key: API key for authenticating with the orchestrator
        client_id: Identifier for the client
        base_url: Base URL for the orchestrator API (for remote orchestrators)

    Returns:
        The OrchestratorClient instance
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = OrchestratorClient(
            api_key=api_key,
            client_id=client_id,
            base_url=base_url,
        )
        await _client_instance.initialize()
    
    return _client_instance
