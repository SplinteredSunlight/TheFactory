"""
Fast-Agent Adapter Module

This module provides a bridge between the AI-Orchestration-Platform and Fast-Agent.
It allows the orchestrator to create and manage Fast-Agent agents and workflows.
"""

import asyncio
import os
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent, AgentConfig
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Import the Orchestrator API Client and Result Reporting Client
from fast_agent_integration.orchestrator_client import get_client
from fast_agent_integration.result_reporting import get_result_reporting_client, ResultType, ResultSeverity
from orchestrator.auth import AuthenticationError, AuthorizationError
from orchestrator.error_handling import (
    BaseError, 
    ErrorCode, 
    ErrorSeverity, 
    Component,
    IntegrationError, 
    SystemError, 
    RetryHandler, 
    CircuitBreaker,
    get_error_handler
)

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class FastAgentAdapter:
    """Adapter for integrating Fast-Agent with the AI-Orchestration-Platform."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        app_name: str = "ai_orchestration_platform",
        api_key: Optional[str] = None,
    ):
        """Initialize the Fast-Agent adapter.

        Args:
            config_path: Path to the Fast-Agent configuration file
            app_name: Name of the MCP application
            api_key: API key for authenticating with the orchestrator
        """
        self.app_name = app_name
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "fast_agent.yaml",
        )
        
        # Initialize the MCP app
        try:
            self.app = MCPApp(name=app_name, config_path=self.config_path)
        except Exception as e:
            raise SystemError(
                message=f"Failed to initialize Fast-Agent MCP app: {str(e)}",
                code=ErrorCode.FAST_AGENT_INITIALIZATION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.CRITICAL,
                details={"app_name": app_name, "config_path": self.config_path}
            )
        
        # Initialize the orchestrator client and result reporting client
        self.orchestrator = None  # Will be initialized in initialize()
        self.result_reporter = None  # Will be initialized in initialize()
        
        # Store active agents
        self.active_agents: Dict[str, Agent] = {}
        
        # Authentication
        self.api_key = api_key or os.environ.get("ORCHESTRATOR_API_KEY") or "fast-agent-default-key"
        self.client_id = f"fast-agent-{app_name}"
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

    async def initialize(self):
        """Initialize the Fast-Agent adapter."""
        # Get the orchestrator client
        self.orchestrator = await get_client(
            api_key=self.api_key,
            client_id=f"fast-agent-{self.app_name}",
        )
        
        # Get the result reporting client
        self.result_reporter = await get_result_reporting_client(
            agent_id=f"fast-agent-{self.app_name}",
            api_key=self.api_key,
            client_id=f"result-reporter-{self.app_name}",
        )
        
        # Report agent status as online
        if self.result_reporter:
            await self.result_reporter.report_agent_status(
                is_online=True,
                current_load=0
            )
    
    async def ensure_authenticated(self) -> bool:
        """Ensure that the adapter is authenticated.
        
        Returns:
            True if the adapter is authenticated, False otherwise
        """
        # The orchestrator client handles authentication automatically
        return True

    async def create_agent(
        self,
        name: str,
        instruction: str,
        model: str = "gpt-4",
        servers: Optional[List[str]] = None,
        use_anthropic: bool = False,
    ) -> str:
        """Create a new Fast-Agent agent.

        Args:
            name: Name of the agent
            instruction: Instructions for the agent
            model: Model to use
            servers: List of MCP servers to use
            use_anthropic: Whether to use Anthropic instead of OpenAI

        Returns:
            The agent ID
        
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            SystemError: If agent creation fails
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            raise IntegrationError(
                message="Circuit breaker is open, too many recent failures",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={"circuit_breaker_state": "open"}
            )
        
        # Generate a unique agent ID
        agent_id = f"{name.lower().replace(' ', '_')}_{len(self.active_agents)}"
        
        try:
            # Configure the agent
            agent_config = AgentConfig(
                name=name,
                instruction=instruction,
                servers=servers or ["fetch", "filesystem", "orchestrator"],
                model=model,
            )
            
            # Create the agent
            agent = Agent(config=agent_config)
            
            # Store the agent
            self.active_agents[agent_id] = agent
            
            # Register the agent with the orchestrator
            agent_token = await self.orchestrator.register_agent(
                agent_id=agent_id,
                name=name,
                capabilities={
                    "model": model,
                    "servers": servers or ["fetch", "filesystem", "orchestrator"],
                    "provider": "anthropic" if use_anthropic else "openai",
                }
            )
            
            # Store the agent token
            agent.auth_token = agent_token["auth_token"]
            
            logger.info(f"Registered agent {agent_id} with orchestrator")
            
            # Record success with circuit breaker
            self.circuit_breaker.record_success()
            
            # Report agent creation
            if self.result_reporter:
                await self.result_reporter.report_agent_log(
                    log_message=f"Agent {agent_id} created successfully",
                    severity=ResultSeverity.INFO,
                    log_context={
                        "agent_id": agent_id,
                        "name": name,
                        "model": model,
                        "capabilities": {
                            "model": model,
                            "servers": servers or ["fetch", "filesystem", "orchestrator"],
                            "provider": "anthropic" if use_anthropic else "openai",
                        }
                    }
                )
            
            return agent_id
            
        except (AuthenticationError, AuthorizationError) as e:
            # Remove the agent from active agents
            self.active_agents.pop(agent_id, None)
            
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {
                "agent_id": agent_id,
                "name": name,
                "model": model
            })
            
            raise
        except Exception as e:
            # Remove the agent from active agents
            self.active_agents.pop(agent_id, None)
            
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Convert to standardized error
            system_error = SystemError(
                message=f"Failed to create agent: {str(e)}",
                code=ErrorCode.FAST_AGENT_INITIALIZATION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={
                    "agent_id": agent_id,
                    "name": name,
                    "model": model,
                    "original_error": str(e)
                }
            )
            
            # Log the error
            error_handler.log_error(system_error, {
                "agent_id": agent_id,
                "name": name,
                "model": model
            })
            
            raise system_error

    async def run_agent(
        self,
        agent_id: str,
        query: str,
        use_anthropic: Optional[bool] = None,
    ) -> str:
        """Run an agent with the given query.

        Args:
            agent_id: ID of the agent to run
            query: Query to send to the agent
            use_anthropic: Whether to use Anthropic instead of OpenAI (overrides agent default)

        Returns:
            The agent's response
            
        Raises:
            ResourceError: If the agent is not found
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            SystemError: If agent execution fails
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            raise IntegrationError(
                message="Circuit breaker is open, too many recent failures",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={"circuit_breaker_state": "open"}
            )
        
        # Get the agent
        agent = self.active_agents.get(agent_id)
        if not agent:
            raise ResourceError(
                message=f"Agent not found: {agent_id}",
                code=ErrorCode.ORCHESTRATOR_AGENT_NOT_FOUND,
                component=Component.FAST_AGENT,
                details={"agent_id": agent_id}
            )
        
        # Authenticate the agent if needed
        if not hasattr(agent, "auth_token") or not agent.auth_token:
            logger.warning(f"Agent {agent_id} has no auth token, attempting to register")
            try:
                await self.create_agent(
                    name=agent.config.name,
                    instruction=agent.config.instruction,
                    model=agent.config.model,
                    servers=agent.config.servers,
                    use_anthropic=False,  # Will be determined later
                )
            except Exception as e:
                error_handler.log_error(e, {"agent_id": agent_id})
                raise SystemError(
                    message=f"Failed to register agent {agent_id}: {str(e)}",
                    code=ErrorCode.FAST_AGENT_INITIALIZATION_FAILED,
                    component=Component.FAST_AGENT,
                    details={"agent_id": agent_id}
                )
        
        try:
            result = None
            
            # Run the agent
            async with self.app.run():
                async with agent:
                    # Get agent capabilities from the orchestrator
                    try:
                        agent_info = await self.orchestrator.get_agent(agent_id)
                    except Exception as e:
                        error_handler.log_error(e, {"agent_id": agent_id})
                        raise SystemError(
                            message=f"Failed to get agent info: {str(e)}",
                            code=ErrorCode.FAST_AGENT_EXECUTION_FAILED,
                            component=Component.FAST_AGENT,
                            details={"agent_id": agent_id}
                        )
                
                    # Determine whether to use Anthropic or OpenAI
                    if use_anthropic is None:
                        use_anthropic = agent_info.get("capabilities", {}).get("provider") == "anthropic"
                    
                    # Attach the appropriate LLM
                    try:
                        if use_anthropic:
                            llm = await agent.attach_llm(AnthropicAugmentedLLM)
                        else:
                            llm = await agent.attach_llm(OpenAIAugmentedLLM)
                    except Exception as e:
                        raise IntegrationError(
                            message=f"Failed to attach LLM to agent {agent_id}: {str(e)}",
                            code=ErrorCode.FAST_AGENT_INITIALIZATION_FAILED,
                            component=Component.FAST_AGENT,
                            details={
                                "agent_id": agent_id,
                                "use_anthropic": use_anthropic
                            }
                        )
                    
                    # Generate a response to the query
                    try:
                        result = await llm.generate_str(message=query)
                    except Exception as e:
                        raise SystemError(
                            message=f"Failed to generate response for agent {agent_id}: {str(e)}",
                            code=ErrorCode.FAST_AGENT_EXECUTION_FAILED,
                            component=Component.FAST_AGENT,
                            details={
                                "agent_id": agent_id,
                                "query_length": len(query)
                            }
                        )
            
            logger.info(f"Agent {agent_id} successfully processed query")
            
            # Record success with circuit breaker
            self.circuit_breaker.record_success()
            
            # Report task completion
            if self.result_reporter:
                await self.result_reporter.report_task_completion(
                    task_id=f"query-{agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    result_data={
                        "agent_id": agent_id,
                        "query_length": len(query),
                        "response_length": len(result) if result else 0,
                        "success": True
                    }
                )
            
            return result
            
        except (AuthenticationError, AuthorizationError) as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {
                "agent_id": agent_id,
                "query_length": len(query)
            })
            
            raise
        except Exception as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Convert to standardized error
            system_error = SystemError(
                message=f"Failed to run agent {agent_id}: {str(e)}",
                code=ErrorCode.FAST_AGENT_EXECUTION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={
                    "agent_id": agent_id,
                    "query_length": len(query),
                    "original_error": str(e)
                }
            )
            
            # Log the error
            error_handler.log_error(system_error, {
                "agent_id": agent_id,
                "query_length": len(query)
            })
            
            # Report task error
            if self.result_reporter:
                await self.result_reporter.report_task_error(
                    task_id=f"query-{agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    error_message=str(system_error),
                    error_details={
                        "agent_id": agent_id,
                        "query_length": len(query),
                        "error_code": system_error.code.value,
                        "error_component": system_error.component.value,
                        "error_severity": system_error.severity.value
                    }
                )
            
            raise system_error

    async def create_and_run_agent(
        self,
        name: str,
        instruction: str,
        query: str,
        model: str = "gpt-4",
        servers: Optional[List[str]] = None,
        use_anthropic: bool = False,
    ) -> Dict[str, Any]:
        """Create and run an agent in a single operation.

        Args:
            name: Name of the agent
            instruction: Instructions for the agent
            query: Query to send to the agent
            model: Model to use
            servers: List of MCP servers to use
            use_anthropic: Whether to use Anthropic instead of OpenAI

        Returns:
            Dictionary containing the agent ID and response
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            SystemError: If agent creation or execution fails
        """
        try:
            # Create the agent
            agent_id = await self.create_agent(
                name=name,
                instruction=instruction,
                model=model,
                servers=servers,
                use_anthropic=use_anthropic,
            )
            
            # Run the agent
            response = await self.run_agent(
                agent_id=agent_id,
                query=query,
                use_anthropic=use_anthropic,
            )
            
            # Report metrics about the operation
            if self.result_reporter:
                await self.result_reporter.report_agent_metrics(
                    metrics={
                        "operation": "create_and_run_agent",
                        "agent_id": agent_id,
                        "query_length": len(query),
                        "response_length": len(response) if response else 0,
                        "model": model,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            
            return {
                "agent_id": agent_id,
                "response": response,
            }
        except BaseError as e:
            # Log the error with context
            error_handler.log_error(e, {
                "name": name,
                "model": model,
                "query_length": len(query)
            })
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent.

        Args:
            agent_id: ID of the agent to delete

        Returns:
            True if the agent was deleted, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            ResourceError: If the agent doesn't exist
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            raise IntegrationError(
                message="Circuit breaker is open, too many recent failures",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={"circuit_breaker_state": "open"}
            )
        
        # Remove the agent from active agents
        agent = self.active_agents.pop(agent_id, None)
        if not agent:
            return False
        
        try:
            # Unregister the agent from the orchestrator
            await self.orchestrator.unregister_agent(agent_id)
            
            logger.info(f"Unregistered agent {agent_id} from orchestrator")
            
            # Record success with circuit breaker
            self.circuit_breaker.record_success()
            
            # Report agent deletion
            if self.result_reporter:
                await self.result_reporter.report_agent_log(
                    log_message=f"Agent {agent_id} deleted successfully",
                    severity=ResultSeverity.INFO,
                    log_context={"agent_id": agent_id}
                )
            
            return True
        except Exception as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {"agent_id": agent_id})
            
            return False
    

    async def shutdown(self):
        """Shutdown the Fast-Agent adapter."""
        # Close all active agents
        for agent_id in list(self.active_agents.keys()):
            try:
                await self.delete_agent(agent_id)
            except Exception as e:
                error_handler.log_error(e, {"agent_id": agent_id, "operation": "shutdown"})
                logger.error(f"Error deleting agent {agent_id} during shutdown: {str(e)}")
        
        # Report adapter going offline
        if self.result_reporter:
            try:
                await self.result_reporter.report_agent_status(
                    is_online=False
                )
                await self.result_reporter.shutdown()
                logger.info("Result reporting client shut down")
            except Exception as e:
                error_handler.log_error(e, {"operation": "shutdown_result_reporter"})
                logger.error(f"Error shutting down result reporting client: {str(e)}")
        
        # Shutdown the orchestrator client
        if self.orchestrator:
            try:
                await self.orchestrator.shutdown()
                logger.info("Orchestrator client shut down")
            except Exception as e:
                error_handler.log_error(e, {"operation": "shutdown_orchestrator"})
                logger.error(f"Error shutting down orchestrator client: {str(e)}")


# Singleton instance
_adapter_instance: Optional[FastAgentAdapter] = None


async def get_adapter(
    config_path: Optional[str] = None,
    app_name: str = "ai_orchestration_platform",
    api_key: Optional[str] = None,
) -> FastAgentAdapter:
    """Get the Fast-Agent adapter singleton instance.

    Args:
        config_path: Path to the Fast-Agent configuration file
        app_name: Name of the MCP application
        api_key: API key for authenticating with the orchestrator

    Returns:
        The Fast-Agent adapter instance
    """
    global _adapter_instance
    
    if _adapter_instance is None:
        _adapter_instance = FastAgentAdapter(
            config_path=config_path,
            app_name=app_name,
            api_key=api_key,
        )
        await _adapter_instance.initialize()
    
    return _adapter_instance
