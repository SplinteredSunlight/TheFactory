#!/usr/bin/env python3
"""
Task Management MCP Server

This MCP server provides task management capabilities as MCP tools and resources.
It acts as a bridge between the Task Manager and MCP clients (including AI agents).
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Import the integrations
from src.task_manager.mcp_servers.dashboard_integration import DashboardIntegration
from src.task_manager.mcp_servers.dagger_workflow_integration import DaggerWorkflowIntegration

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

# Import the Task Manager
from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority, Task, Phase, Project


class TaskManagerServer:
    """MCP Server that provides access to the Task Management system."""

    def __init__(self, data_dir: Optional[str] = None, auth_token: Optional[str] = None, dagger_config_path: Optional[str] = None):
        """
        Initialize the Task Manager MCP Server.
        
        Args:
            data_dir: Directory for task manager data
            auth_token: Authentication token for API calls
            dagger_config_path: Path to the Dagger configuration file
        """
        self.server = Server(
            {
                "name": "task-manager",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                },
            },
        )

        # Initialize the task manager
        self.task_manager = get_task_manager(data_dir)
        self.auth_token = auth_token
        self.dagger_config_path = dagger_config_path

        # Set up request handlers
        self.setup_resource_handlers()
        self.setup_tool_handlers()
        
        # Initialize the integrations
        self.dashboard_integration = DashboardIntegration(self.server, self.task_manager)
        
        # Initialize the Dagger Workflow Integration if enabled
        self.dagger_workflow_integration = None
        if os.environ.get("TASK_MANAGER_DAGGER_ENABLED", "").lower() in ("1", "true", "yes"):
            # Get the templates directory
            templates_dir = os.environ.get("TASK_MANAGER_TEMPLATES_DIR", "config/templates/pipelines")
            
            # Initialize the Dagger Workflow Integration with the new TaskWorkflowIntegration
            self.dagger_workflow_integration = DaggerWorkflowIntegration(
                self.server, 
                self.task_manager, 
                dagger_config_path or os.environ.get("TASK_MANAGER_DAGGER_CONFIG"),
                templates_dir=templates_dir
            )
            
            # Log that we're using the new Dagger-based Task Management System
            print("Using new Dagger-based Task Management System", file=sys.stderr)

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
                    "uri": "task-manager://projects",
                    "name": "Projects",
                    "mimeType": "application/json",
                    "description": "List of all projects in the task manager",
                },
                {
                    "uri": "task-manager://status",
                    "name": "Task Manager Status",
                    "mimeType": "application/json",
                    "description": "Current status of the task management system",
                },
            ],
        }

    async def _handle_list_resource_templates(self, request):
        """Handle listing resource templates."""
        return {
            "resourceTemplates": [
                {
                    "uriTemplate": "task-manager://projects/{project_id}",
                    "name": "Project Information",
                    "mimeType": "application/json",
                    "description": "Information about a specific project",
                },
                {
                    "uriTemplate": "task-manager://projects/{project_id}/phases",
                    "name": "Project Phases",
                    "mimeType": "application/json",
                    "description": "Phases in a specific project",
                },
                {
                    "uriTemplate": "task-manager://projects/{project_id}/tasks",
                    "name": "Project Tasks",
                    "mimeType": "application/json",
                    "description": "Tasks in a specific project",
                },
                {
                    "uriTemplate": "task-manager://tasks/{task_id}",
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
        if uri == "task-manager://projects":
            # Get all projects
            projects = {p_id: p.to_dict() for p_id, p in self.task_manager.projects.items()}
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(projects, indent=2),
                    }
                ],
            }
        elif uri == "task-manager://status":
            # Get task manager status
            status = {
                "project_count": len(self.task_manager.projects),
                "tasks_by_status": self._get_tasks_by_status(),
                "timestamp": datetime.now().isoformat(),
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(status, indent=2),
                    }
                ],
            }
        
        # If we get here, the resource wasn't found
        raise McpError(ErrorCode.NotFound, f"Resource not found: {uri}")
    
    def _get_tasks_by_status(self):
        """Get counts of tasks by status across all projects."""
        counts = {status.value: 0 for status in TaskStatus}
        
        for project in self.task_manager.projects.values():
            for task in project.tasks.values():
                counts[task.status.value] += 1
        
        return counts

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
                # Project management tools
                {
                    "name": "create_project",
                    "description": "Create a new project in the task manager",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the project",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the project",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the project",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["name"],
                    },
                },
                {
                    "name": "update_project",
                    "description": "Update an existing project in the task manager",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "New name of the project",
                            },
                            "description": {
                                "type": "string",
                                "description": "New description of the project",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the project",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id"],
                    },
                },
                {
                    "name": "delete_project",
                    "description": "Delete a project from the task manager",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project to delete",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id"],
                    },
                },
                # Phase management tools
                {
                    "name": "create_phase",
                    "description": "Create a new phase in a project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the phase",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the phase",
                            },
                            "order": {
                                "type": "integer",
                                "description": "Order of the phase in the project",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the phase",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id", "name"],
                    },
                },
                # Task management tools
                {
                    "name": "create_task",
                    "description": "Create a new task in a project",
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
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project",
                            },
                            "phase_id": {
                                "type": "string",
                                "description": "ID of the phase (optional)",
                            },
                            "parent_id": {
                                "type": "string",
                                "description": "ID of the parent task (optional)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status of the task (planned, in_progress, completed, failed, blocked)",
                                "enum": ["planned", "in_progress", "completed", "failed", "blocked"],
                            },
                            "priority": {
                                "type": "string",
                                "description": "Priority of the task (low, medium, high, critical)",
                                "enum": ["low", "medium", "high", "critical"],
                            },
                            "progress": {
                                "type": "number",
                                "description": "Progress of the task (0-100)",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "assignee_id": {
                                "type": "string",
                                "description": "ID of the assignee (optional)",
                            },
                            "assignee_type": {
                                "type": "string",
                                "description": "Type of the assignee (user, agent, etc.)",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the task",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["name", "description", "project_id"],
                    },
                },
                {
                    "name": "update_task",
                    "description": "Update an existing task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "New name of the task",
                            },
                            "description": {
                                "type": "string",
                                "description": "New description of the task",
                            },
                            "phase_id": {
                                "type": "string",
                                "description": "New phase ID for the task",
                            },
                            "parent_id": {
                                "type": "string",
                                "description": "New parent task ID",
                            },
                            "status": {
                                "type": "string",
                                "description": "New status of the task",
                                "enum": ["planned", "in_progress", "completed", "failed", "blocked"],
                            },
                            "priority": {
                                "type": "string",
                                "description": "New priority of the task",
                                "enum": ["low", "medium", "high", "critical"],
                            },
                            "progress": {
                                "type": "number",
                                "description": "New progress of the task (0-100)",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "assignee_id": {
                                "type": "string",
                                "description": "New assignee ID",
                            },
                            "assignee_type": {
                                "type": "string",
                                "description": "New assignee type",
                            },
                            "metadata": {
                                "type": "object",
                                "description": "New metadata for the task",
                            },
                            "result": {
                                "type": "object",
                                "description": "Result of the task",
                            },
                            "error": {
                                "type": "string",
                                "description": "Error message if the task failed",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["task_id"],
                    },
                },
                {
                    "name": "delete_task",
                    "description": "Delete a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to delete",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["task_id"],
                    },
                },
                {
                    "name": "update_task_status",
                    "description": "Update the status of a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task",
                            },
                            "status": {
                                "type": "string",
                                "description": "New status of the task",
                                "enum": ["planned", "in_progress", "completed", "failed", "blocked"],
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["task_id", "status"],
                    },
                },
                {
                    "name": "update_task_progress",
                    "description": "Update the progress of a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task",
                            },
                            "progress": {
                                "type": "number",
                                "description": "New progress of the task (0-100)",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["task_id", "progress"],
                    },
                },
                # Calculation tools
                {
                    "name": "calculate_project_progress",
                    "description": "Calculate the progress of a project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id"],
                    },
                },
                {
                    "name": "calculate_phase_progress",
                    "description": "Calculate the progress of a phase",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project",
                            },
                            "phase_id": {
                                "type": "string",
                                "description": "ID of the phase",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id", "phase_id"],
                    },
                },
                # Query tools
                {
                    "name": "get_tasks_by_status",
                    "description": "Get all tasks with a specific status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status to filter by",
                                "enum": ["planned", "in_progress", "completed", "failed", "blocked"],
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["project_id", "status"],
                    },
                },
                {
                    "name": "get_tasks_by_assignee",
                    "description": "Get all tasks assigned to a specific assignee",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "assignee_id": {
                                "type": "string",
                                "description": "ID of the assignee",
                            },
                            "assignee_type": {
                                "type": "string",
                                "description": "Type of the assignee (optional)",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["assignee_id"],
                    },
                },
            ],
        }

    async def _handle_call_tool(self, request):
        """Handle calling tools."""
        tool_name = request.params.name
        args = request.params.arguments
        
        # Validate authentication
        if self.auth_token and args.get("auth_token") != self.auth_token:
            raise McpError(ErrorCode.Unauthorized, "Invalid authentication token")
        
        try:
            # Project management tools
            if tool_name == "create_project":
                # Validate required arguments
                if "name" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: name",
                    )
                
                # Call the task manager
                result = self.task_manager.create_project(
                    name=args["name"],
                    description=args.get("description"),
                    metadata=args.get("metadata"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_project":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                
                # Call the task manager
                result = self.task_manager.update_project(
                    project_id=args["project_id"],
                    name=args.get("name"),
                    description=args.get("description"),
                    metadata=args.get("metadata"),
                )
                
                if result is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Project not found: {args['project_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            elif tool_name == "delete_project":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                
                # Call the task manager
                result = self.task_manager.delete_project(
                    project_id=args["project_id"],
                )
                
                if not result:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Project not found: {args['project_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": True}, indent=2),
                        }
                    ],
                }
            
            # Phase management tools
            elif tool_name == "create_phase":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                if "name" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: name",
                    )
                
                # Get the project
                project = self.task_manager.get_project(args["project_id"])
                if project is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Project not found: {args['project_id']}",
                    )
                
                # Generate a phase ID
                import uuid
                phase_id = f"phase_{uuid.uuid4().hex[:8]}"
                
                # Create the phase
                phase = project.add_phase(
                    phase_id=phase_id,
                    name=args["name"],
                    description=args.get("description"),
                    order=args.get("order", 0),
                    metadata=args.get("metadata"),
                )
                
                # Save the data
                self.task_manager.save_data()
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(phase.to_dict(), indent=2),
                        }
                    ],
                }
            
            # Task management tools
            elif tool_name == "create_task":
                # Validate required arguments
                for param in ["name", "description", "project_id"]:
                    if param not in args:
                        raise McpError(
                            ErrorCode.InvalidParams,
                            f"Missing required parameter: {param}",
                        )
                
                # Call the task manager
                result = self.task_manager.create_task(
                    name=args["name"],
                    description=args["description"],
                    project_id=args["project_id"],
                    phase_id=args.get("phase_id"),
                    parent_id=args.get("parent_id"),
                    status=args.get("status", "planned"),
                    priority=args.get("priority", "medium"),
                    progress=args.get("progress", 0.0),
                    assignee_id=args.get("assignee_id"),
                    assignee_type=args.get("assignee_type"),
                    metadata=args.get("metadata"),
                )
                
                if result is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Project not found: {args['project_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_task":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                
                # Call the task manager
                result = self.task_manager.update_task(
                    task_id=args["task_id"],
                    name=args.get("name"),
                    description=args.get("description"),
                    phase_id=args.get("phase_id"),
                    parent_id=args.get("parent_id"),
                    status=args.get("status"),
                    priority=args.get("priority"),
                    progress=args.get("progress"),
                    assignee_id=args.get("assignee_id"),
                    assignee_type=args.get("assignee_type"),
                    metadata=args.get("metadata"),
                    result=args.get("result"),
                    error=args.get("error"),
                )
                
                if result is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Task not found: {args['task_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            elif tool_name == "delete_task":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                
                # Call the task manager
                result = self.task_manager.delete_task(
                    task_id=args["task_id"],
                )
                
                if not result:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Task not found: {args['task_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": True}, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_task_status":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                if "status" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: status",
                    )
                
                # Call the task manager
                result = self.task_manager.update_task_status(
                    task_id=args["task_id"],
                    status=args["status"],
                )
                
                if result is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Task not found: {args['task_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            elif tool_name == "update_task_progress":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                if "progress" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: progress",
                    )
                
                # Call the task manager
                result = self.task_manager.update_task_progress(
                    task_id=args["task_id"],
                    progress=args["progress"],
                )
                
                if result is None:
                    raise McpError(
                        ErrorCode.NotFound,
                        f"Task not found: {args['task_id']}",
                    )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            # Calculation tools
            elif tool_name == "calculate_project_progress":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                
                # Call the task manager
                result = self.task_manager.calculate_project_progress(
                    project_id=args["project_id"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"progress": result}, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "calculate_phase_progress":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                if "phase_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: phase_id",
                    )
                
                # Call the task manager
                result = self.task_manager.calculate_phase_progress(
                    project_id=args["project_id"],
                    phase_id=args["phase_id"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"progress": result}, indent=2),
                        }
                    ],
                }
            
            # Query tools
            elif tool_name == "get_tasks_by_status":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                if "status" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: status",
                    )
                
                # Call the task manager
                tasks = self.task_manager.get_tasks_by_status(
                    project_id=args["project_id"],
                    status=args["status"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"tasks": [task.to_dict() for task in tasks]},
                                indent=2,
                            ),
                        }
                    ],
                }
            
            elif tool_name == "get_tasks_by_assignee":
                # Validate required arguments
                if "assignee_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: assignee_id",
                    )
                
                # Call the task manager
                tasks = self.task_manager.get_tasks_by_assignee(
                    assignee_id=args["assignee_id"],
                    assignee_type=args.get("assignee_type"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {"tasks": [task.to_dict() for task in tasks]},
                                indent=2,
                            ),
                        }
                    ],
                }
            
            # If we get here, the tool wasn't found
            raise McpError(ErrorCode.MethodNotFound, f"Unknown tool: {tool_name}")
        except McpError:
            # Re-raise MCP errors
            raise
        except Exception as e:
            # Convert other exceptions to MCP errors
            raise McpError(ErrorCode.InternalError, f"Internal error: {str(e)}")

    async def run(self):
        """Run the MCP server."""
        transport = StdioServerTransport()
        await self.server.connect(transport)
        print("Task Management MCP server running on stdio", file=sys.stderr)
        
        # Log enabled integrations
        integrations = ["Dashboard Integration"]
        if self.dagger_workflow_integration:
            integrations.append("Dagger Workflow Integration")
        
        print(f"Enabled integrations: {', '.join(integrations)}", file=sys.stderr)


    async def shutdown(self):
        """Shutdown the MCP server."""
        # Shutdown integrations
        if self.dagger_workflow_integration:
            await self.dagger_workflow_integration.shutdown()
        
        # Close the server
        await self.server.close()


def main():
    """Run the Task Management MCP server."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Task Management MCP Server")
    parser.add_argument("--data-dir", help="Directory for task manager data")
    parser.add_argument("--auth-token", help="Authentication token for API calls")
    parser.add_argument("--dagger-config", help="Path to Dagger configuration file")
    parser.add_argument("--enable-dagger", action="store_true", help="Enable Dagger workflow integration")
    args = parser.parse_args()
    
    # Set environment variables
    if args.enable_dagger:
        os.environ["TASK_MANAGER_DAGGER_ENABLED"] = "1"
    if args.dagger_config:
        os.environ["TASK_MANAGER_DAGGER_CONFIG"] = args.dagger_config
    
    # Create and run the server
    server = TaskManagerServer(
        data_dir=args.data_dir, 
        auth_token=args.auth_token,
        dagger_config_path=args.dagger_config
    )
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
