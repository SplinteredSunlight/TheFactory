#!/usr/bin/env python3
"""
Orchestrator MCP Server

This MCP server provides a bridge between Fast-Agent and the AI-Orchestration-Platform.
It exposes the orchestrator's functionality as MCP tools and resources.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListResourcesRequestSchema,
    ListResourceTemplatesRequestSchema,
    ListToolsRequestSchema,
    McpError,
    ReadResourceRequestSchema,
)

from src.orchestrator.communication import MessageType, MessagePriority
from src.orchestrator.task_distribution import TaskDistributionStrategy
from src.orchestrator.rate_limiting import RateLimitType, get_rate_limiter

# Import the AI-Orchestration-Platform engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.orchestrator.engine import OrchestratorEngine
from src.orchestrator.auth import AuthenticationError, AuthorizationError


class OrchestratorServer:
    """MCP Server that provides access to the AI-Orchestration-Platform."""

    def __init__(self):
        """Initialize the Orchestrator MCP Server."""
        self.server = Server(
            {
                "name": "orchestrator",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                },
            },
        )

        # Initialize the orchestrator engine
        self.orchestrator = OrchestratorEngine()

        # Set up request handlers
        self.setup_resource_handlers()
        self.setup_tool_handlers()

        # Error handling
        self.server.onerror = lambda error: print(f"[MCP Error] {error}", file=sys.stderr)
        
        # Handle graceful shutdown
        for signal_name in ["SIGINT", "SIGTERM"]:
            try:
                import signal
                signal_num = getattr(signal, signal_name)
                signal.signal(signal_num, self._handle_signal)
            except (ImportError, AttributeError):
                pass

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        asyncio.create_task(self.server.close())
        sys.exit(0)

    def setup_resource_handlers(self):
        """Set up resource handlers for the MCP server."""
        # List available resources
        self.server.set_request_handler(ListResourcesRequestSchema, self._handle_list_resources)
        
        # List resource templates
        self.server.set_request_handler(
            ListResourceTemplatesRequestSchema, self._handle_list_resource_templates
        )
        
        # Read resources
        self.server.set_request_handler(ReadResourceRequestSchema, self._handle_read_resource)

    async def _handle_list_resources(self, request):
        """Handle listing available resources."""
        return {
            "resources": [
                {
                    "uri": "orchestrator://status",
                    "name": "Orchestrator Status",
                    "mimeType": "application/json",
                    "description": "Current status of the AI-Orchestration-Platform",
                },
                {
                    "uri": "orchestrator://agents",
                    "name": "Available Agents",
                    "mimeType": "application/json",
                    "description": "List of available agents in the AI-Orchestration-Platform",
                },
            ],
        }

    async def _handle_list_resource_templates(self, request):
        """Handle listing resource templates."""
        return {
            "resourceTemplates": [
                {
                    "uriTemplate": "orchestrator://agent/{agent_id}",
                    "name": "Agent Information",
                    "mimeType": "application/json",
                    "description": "Information about a specific agent",
                },
                {
                    "uriTemplate": "orchestrator://task/{task_id}",
                    "name": "Task Information",
                    "mimeType": "application/json",
                    "description": "Information about a specific task",
                },
            ],
        }

    async def _handle_read_resource(self, request):
        """Handle reading resources."""
        uri = request.params.uri
        
        # Handle static resources
        if uri == "orchestrator://status":
            status = await self.orchestrator.get_status()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(status, indent=2),
                    }
                ],
            }
        elif uri == "orchestrator://agents":
            agents = await self.orchestrator.list_agents()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(agents, indent=2),
                    }
                ],
            }
        
        # Handle templated resources
        agent_match = uri.startswith("orchestrator://agent/")
        if agent_match:
            agent_id = uri.split("/")[-1]
            try:
                agent_info = await self.orchestrator.get_agent(agent_id)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(agent_info, indent=2),
                        }
                    ],
                }
            except Exception as e:
                raise McpError(ErrorCode.NotFound, f"Agent not found: {str(e)}")
        
        task_match = uri.startswith("orchestrator://task/")
        if task_match:
            task_id = uri.split("/")[-1]
            try:
                task_info = await self.orchestrator.get_task(task_id)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(task_info, indent=2),
                        }
                    ],
                }
            except Exception as e:
                raise McpError(ErrorCode.NotFound, f"Task not found: {str(e)}")
        
        # If we get here, the resource wasn't found
        raise McpError(ErrorCode.NotFound, f"Resource not found: {uri}")

    def setup_tool_handlers(self):
        """Set up tool handlers for the MCP server."""
        # List available tools
        self.server.set_request_handler(ListToolsRequestSchema, self._handle_list_tools)
        
        # Call tools
        self.server.set_request_handler(CallToolRequestSchema, self._handle_call_tool)

    async def _handle_list_tools(self, request):
        """Handle listing available tools."""
        return {
            "tools": [
                # Authentication tools
                {
                    "name": "authenticate",
                    "description": "Authenticate with the orchestrator using an API key",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "api_key": {
                                "type": "string",
                                "description": "API key to authenticate with",
                            },
                            "client_id": {
                                "type": "string",
                                "description": "Identifier for the client",
                            },
                            "scope": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "List of scopes to request",
                            },
                        },
                        "required": ["api_key", "client_id"],
                    },
                },
                {
                    "name": "refresh_token",
                    "description": "Refresh an authentication token",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "refresh_token": {
                                "type": "string",
                                "description": "Refresh token to use",
                            },
                            "client_id": {
                                "type": "string",
                                "description": "Identifier for the client",
                            },
                        },
                        "required": ["refresh_token", "client_id"],
                    },
                },
                {
                    "name": "validate_token",
                    "description": "Validate an authentication token",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "token": {
                                "type": "string",
                                "description": "Token to validate",
                            },
                            "required_scopes": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "List of scopes required for the operation",
                            },
                        },
                        "required": ["token"],
                    },
                },
                {
                    "name": "revoke_token",
                    "description": "Revoke an authentication token",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "token": {
                                "type": "string",
                                "description": "Token to revoke",
                            },
                            "token_type_hint": {
                                "type": "string",
                                "description": "Type of token (access_token or refresh_token)",
                                "enum": ["access_token", "refresh_token"],
                            },
                        },
                        "required": ["token"],
                    },
                },
                # Agent authentication tools
                {
                    "name": "register_agent",
                    "description": "Register a new agent with the orchestrator",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Unique identifier for the agent",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the agent",
                            },
                            "capabilities": {
                                "type": "object",
                                "description": "Dictionary of agent capabilities",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["agent_id", "name", "capabilities", "token"],
                    },
                },
                {
                    "name": "authenticate_agent",
                    "description": "Authenticate an agent with the orchestrator",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Unique identifier for the agent",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token for the agent",
                            },
                        },
                        "required": ["agent_id", "auth_token"],
                    },
                },
                # Task management tools
                {
                    "name": "create_task",
                    "description": "Create a new task in the orchestrator",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the task",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the task",
                            },
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent to assign the task to",
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority of the task (1-5)",
                                "minimum": 1,
                                "maximum": 5,
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["name", "description", "token"],
                    },
                },
                
                # Agent Communication tools
                {
                    "name": "send_message",
                    "description": "Send a message from one agent to another",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "sender_id": {
                                "type": "string",
                                "description": "ID of the agent sending the message",
                            },
                            "message_type": {
                                "type": "string",
                                "description": "Type of the message (direct, broadcast, task_request, etc.)",
                                "enum": [t.value for t in MessageType],
                            },
                            "content": {
                                "type": "object",
                                "description": "Content of the message",
                            },
                            "recipient_id": {
                                "type": "string",
                                "description": "ID of the agent receiving the message (None for broadcasts)",
                            },
                            "correlation_id": {
                                "type": "string",
                                "description": "ID to correlate related messages",
                            },
                            "priority": {
                                "type": "string",
                                "description": "Priority of the message (high, medium, low)",
                                "enum": [p.value for p in MessagePriority],
                                "default": "medium",
                            },
                            "ttl": {
                                "type": "integer",
                                "description": "Time-to-live in seconds",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the message",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the sender",
                            },
                        },
                        "required": ["sender_id", "message_type", "content", "token"],
                    },
                },
                {
                    "name": "get_messages",
                    "description": "Get messages for an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent",
                            },
                            "mark_delivered": {
                                "type": "boolean",
                                "description": "Whether to mark the messages as delivered",
                                "default": true,
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the agent",
                            },
                        },
                        "required": ["agent_id", "token"],
                    },
                },
                {
                    "name": "get_agent_communication_capabilities",
                    "description": "Get the communication capabilities of an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["agent_id", "token"],
                    },
                },
                # Rate limiting tools
                {
                    "name": "get_rate_limits",
                    "description": "Get the current rate limits for the system",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit_type": {
                                "type": "string",
                                "description": "Type of rate limit to get (agent, message_type, priority, global)",
                                "enum": [t.value for t in RateLimitType],
                            },
                            "key": {
                                "type": "string",
                                "description": "Key for the rate limit (agent ID, message type, priority level, etc.)",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["token"],
                    },
                },
                {
                    "name": "update_rate_limit",
                    "description": "Update a rate limit for the system",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit_type": {
                                "type": "string",
                                "description": "Type of rate limit to update (agent, message_type, priority, global)",
                                "enum": [t.value for t in RateLimitType],
                            },
                            "key": {
                                "type": "string",
                                "description": "Key for the rate limit (agent ID, message type, priority level, etc.)",
                            },
                            "max_tokens": {
                                "type": "integer",
                                "description": "Maximum number of tokens in the bucket",
                                "minimum": 1,
                            },
                            "interval": {
                                "type": "integer",
                                "description": "Interval in seconds for token replenishment",
                                "minimum": 1,
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["limit_type", "key", "max_tokens", "interval", "token"],
                    },
                },
                # Task Distribution tools
                {
                    "name": "distribute_task",
                    "description": "Distribute a task to an appropriate agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to distribute",
                            },
                            "required_capabilities": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "Capabilities required for the task",
                            },
                            "task_data": {
                                "type": "object",
                                "description": "Data for the task",
                            },
                            "distribution_strategy": {
                                "type": "string",
                                "description": "Strategy for distributing the task",
                                "enum": [s.value for s in TaskDistributionStrategy],
                            },
                            "excluded_agents": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "List of agent IDs to exclude",
                            },
                            "priority": {
                                "type": "string",
                                "description": "Priority of the task (high, medium, low)",
                                "enum": ["high", "medium", "low"],
                                "default": "medium",
                            },
                            "ttl": {
                                "type": "integer",
                                "description": "Time-to-live in seconds",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the task",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["task_id", "required_capabilities", "task_data", "token"],
                    },
                },
                {
                    "name": "handle_task_response",
                    "description": "Handle a task response from an agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task",
                            },
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent that executed the task",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status of the task execution",
                                "enum": ["completed", "failed", "in_progress"],
                            },
                            "result": {
                                "type": "object",
                                "description": "Result of the task execution",
                            },
                            "error": {
                                "type": "string",
                                "description": "Error message if the task failed",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["task_id", "agent_id", "status", "token"],
                    },
                },
                {
                    "name": "register_agent_with_distributor",
                    "description": "Register an agent with the task distributor",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent to register",
                            },
                            "capabilities": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                },
                                "description": "List of agent capabilities",
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority of the agent (higher is better)",
                                "default": 1,
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["agent_id", "capabilities", "token"],
                    },
                },
                {
                    "name": "unregister_agent_from_distributor",
                    "description": "Unregister an agent from the task distributor",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent to unregister",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["agent_id", "token"],
                    },
                },
                {
                    "name": "update_agent_status_in_distributor",
                    "description": "Update the status of an agent in the task distributor",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "ID of the agent",
                            },
                            "is_online": {
                                "type": "boolean",
                                "description": "Whether the agent is online",
                            },
                            "current_load": {
                                "type": "integer",
                                "description": "Current load of the agent (number of active tasks)",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["agent_id", "is_online", "token"],
                    },
                },
                {
                    "name": "execute_task",
                    "description": "Execute a task in the orchestrator",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to execute",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the task execution",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["task_id", "token"],
                    },
                },
                {
                    "name": "query_orchestrator",
                    "description": "Query the orchestrator for information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query to execute",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the query",
                            },
                            "token": {
                                "type": "string",
                                "description": "Authentication token for the request",
                            },
                        },
                        "required": ["query", "token"],
                    },
                },
            ],
        }

    async def _handle_call_tool(self, request):
        """Handle calling tools."""
        tool_name = request.params.name
        args = request.params.arguments
        
        try:
            # Authentication tools
            if tool_name == "authenticate":
                # Validate required arguments
                if "api_key" not in args or "client_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: api_key and client_id",
                    )
                
                # Call the orchestrator
                result = await self.orchestrator.authenticate(
                    api_key=args["api_key"],
                    client_id=args["client_id"],
                    scope=args.get("scope"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "refresh_token":
                # Validate required arguments
                if "refresh_token" not in args or "client_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: refresh_token and client_id",
                    )
                
                # Call the orchestrator
                result = await self.orchestrator.refresh_token(
                    refresh_token=args["refresh_token"],
                    client_id=args["client_id"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "validate_token":
                # Validate required arguments
                if "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: token",
                    )
                
                # Call the orchestrator
                result = await self.orchestrator.validate_token(
                    token=args["token"],
                    required_scopes=args.get("required_scopes"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "revoke_token":
                # Validate required arguments
                if "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: token",
                    )
                
                # Call the orchestrator
                result = await self.orchestrator.revoke_token(
                    token=args["token"],
                    token_type_hint=args.get("token_type_hint", "access_token"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": result}, indent=2),
                        }
                    ],
                }
            
            # Agent authentication tools
            elif tool_name == "register_agent":
                # Validate required arguments
                if "agent_id" not in args or "name" not in args or "capabilities" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id, name, capabilities, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.register_agent(
                    agent_id=args["agent_id"],
                    name=args["name"],
                    capabilities=args["capabilities"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "authenticate_agent":
                # Validate required arguments
                if "agent_id" not in args or "auth_token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id and auth_token",
                    )
                
                # Call the orchestrator
                result = await self.orchestrator.authenticate_agent(
                    agent_id=args["agent_id"],
                    auth_token=args["auth_token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            # Task management tools
            elif tool_name == "create_task":
                # Validate required arguments
                if "name" not in args or "description" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: name, description, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["task:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Set default values for optional arguments
                agent_id = args.get("agent_id")
                priority = args.get("priority", 3)
                
                # Call the orchestrator
                result = await self.orchestrator.create_task(
                    name=args["name"],
                    description=args["description"],
                    agent_id=agent_id,
                    priority=priority,
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "execute_task":
                # Validate required arguments
                if "task_id" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: task_id and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["task:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Set default values for optional arguments
                parameters = args.get("parameters", {})
                
                # Call the orchestrator
                result = await self.orchestrator.execute_task(
                    task_id=args["task_id"],
                    parameters=parameters,
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            # Task Distribution tools
            elif tool_name == "distribute_task":
                # Validate required arguments
                if "task_id" not in args or "required_capabilities" not in args or "task_data" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: task_id, required_capabilities, task_data, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["task:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.distribute_task(
                    task_id=args["task_id"],
                    required_capabilities=args["required_capabilities"],
                    task_data=args["task_data"],
                    distribution_strategy=args.get("distribution_strategy"),
                    excluded_agents=args.get("excluded_agents"),
                    priority=args.get("priority", "medium"),
                    ttl=args.get("ttl"),
                    metadata=args.get("metadata"),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "handle_task_response":
                # Validate required arguments
                if "task_id" not in args or "agent_id" not in args or "status" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: task_id, agent_id, status, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:execute"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.handle_task_response(
                    task_id=args["task_id"],
                    agent_id=args["agent_id"],
                    status=args["status"],
                    result=args.get("result"),
                    error=args.get("error"),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "register_agent_with_distributor":
                # Validate required arguments
                if "agent_id" not in args or "capabilities" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id, capabilities, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.register_agent_with_distributor(
                    agent_id=args["agent_id"],
                    capabilities=args["capabilities"],
                    priority=args.get("priority", 1),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "unregister_agent_from_distributor":
                # Validate required arguments
                if "agent_id" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.unregister_agent_from_distributor(
                    agent_id=args["agent_id"],
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_agent_status_in_distributor":
                # Validate required arguments
                if "agent_id" not in args or "is_online" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id, is_online, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:write"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.update_agent_status_in_distributor(
                    agent_id=args["agent_id"],
                    is_online=args["is_online"],
                    current_load=args.get("current_load"),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "query_orchestrator":
                # Validate required arguments
                if "query" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: query and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["task:read"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Set default values for optional arguments
                parameters = args.get("parameters", {})
                
                # Call the orchestrator
                result = await self.orchestrator.query(
                    query=args["query"],
                    parameters=parameters,
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            # Agent Communication tools
            elif tool_name == "send_message":
                # Validate required arguments
                if "sender_id" not in args or "message_type" not in args or "content" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: sender_id, message_type, content, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:execute"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.send_agent_message(
                    sender_id=args["sender_id"],
                    message_type=args["message_type"],
                    content=args["content"],
                    recipient_id=args.get("recipient_id"),
                    correlation_id=args.get("correlation_id"),
                    priority=args.get("priority", "medium"),
                    ttl=args.get("ttl"),
                    metadata=args.get("metadata"),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "get_messages":
                # Validate required arguments
                if "agent_id" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:execute"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.get_agent_messages(
                    agent_id=args["agent_id"],
                    mark_delivered=args.get("mark_delivered", True),
                    auth_token=args["token"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "get_agent_communication_capabilities":
                # Validate required arguments
                if "agent_id" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: agent_id and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["agent:read"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Call the orchestrator
                result = await self.orchestrator.get_agent_communication_capabilities(
                    agent_id=args["agent_id"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            # Rate limiting tools
            elif tool_name == "get_rate_limits":
                # Validate required arguments
                if "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["admin"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Get the rate limiter
                rate_limiter = get_rate_limiter()
                
                # Get the rate limits
                if "limit_type" in args:
                    limit_type = RateLimitType(args["limit_type"])
                    if "key" in args:
                        # Get a specific rate limit
                        key = args["key"]
                        if key in rate_limiter.rate_limits[limit_type]:
                            result = {
                                key: rate_limiter.rate_limits[limit_type][key]
                            }
                        else:
                            result = {
                                "default": rate_limiter.rate_limits[limit_type].get("default")
                            }
                    else:
                        # Get all rate limits for the type
                        result = rate_limiter.rate_limits[limit_type]
                else:
                    # Get all rate limits
                    result = {
                        limit_type.value: limits
                        for limit_type, limits in rate_limiter.rate_limits.items()
                    }
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_rate_limit":
                # Validate required arguments
                if "limit_type" not in args or "key" not in args or "max_tokens" not in args or "interval" not in args or "token" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: limit_type, key, max_tokens, interval, and token",
                    )
                
                # Validate the token
                try:
                    await self.orchestrator.validate_token(
                        token=args["token"],
                        required_scopes=["admin"],
                    )
                except (AuthenticationError, AuthorizationError) as e:
                    raise McpError(ErrorCode.Unauthorized, str(e))
                
                # Get the rate limiter
                rate_limiter = get_rate_limiter()
                
                # Update the rate limit
                limit_type = RateLimitType(args["limit_type"])
                key = args["key"]
                max_tokens = args["max_tokens"]
                interval = args["interval"]
                
                # Validate the parameters
                if max_tokens < 1:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "max_tokens must be at least 1",
                    )
                
                if interval < 1:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "interval must be at least 1",
                    )
                
                # Update the rate limit
                rate_limiter.rate_limits[limit_type][key] = (max_tokens, interval)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "limit_type": limit_type.value,
                                "key": key,
                                "max_tokens": max_tokens,
                                "interval": interval,
                            }, indent=2),
                        }
                    ],
                }
            
            else:
                raise McpError(
                    ErrorCode.MethodNotFound,
                    f"Unknown tool: {tool_name}",
                )
        
        except Exception as e:
            if isinstance(e, McpError):
                raise e
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}",
                    }
                ],
                "isError": True,
            }

    async def run(self):
        """Run the MCP server."""
        transport = StdioServerTransport()
        await self.server.connect(transport)
        print("Orchestrator MCP server running on stdio", file=sys.stderr)


if __name__ == "__main__":
    server = OrchestratorServer()
    asyncio.run(server.run())
