# Task Management MCP Server Implementation Guide

This guide provides step-by-step instructions for implementing a standalone Task Management MCP server that integrates with the Project Master Dashboard. The implementation will allow for managing the completion of projects without requiring external servers or browser access.

## Prerequisites

- Python 3.8+
- Node.js 16+ (for Project Master Dashboard UI)
- AI-Orchestration-Platform codebase
- MCP server libraries

## Implementation Steps

### 1. Create the Task Management MCP Server

Create a new file at `src/task_manager/mcp_servers/task_manager_server.py`:

```python
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority, Task, Phase, Project


class TaskManagerServer:
    """MCP Server that provides access to the Task Management system."""

    def __init__(self, data_dir: Optional[str] = None, auth_token: Optional[str] = None):
        """Initialize the Task Manager MCP Server."""
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
        
        # Handle templated resources
        if uri.startswith("task-manager://projects/"):
            parts = uri.split("/")
            
            # Handle project information
            if len(parts) == 4:
                project_id = parts[3]
                project = self.task_manager.get_project(project_id)
                if not project:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {project_id}")
                
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(project.to_dict(), indent=2),
                        }
                    ],
                }
            
            # Handle project phases
            elif len(parts) == 5 and parts[4] == "phases":
                project_id = parts[3]
                project = self.task_manager.get_project(project_id)
                if not project:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {project_id}")
                
                phases = {p_id: p.to_dict() for p_id, p in project.phases.items()}
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(phases, indent=2),
                        }
                    ],
                }
            
            # Handle project tasks
            elif len(parts) == 5 and parts[4] == "tasks":
                project_id = parts[3]
                project = self.task_manager.get_project(project_id)
                if not project:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {project_id}")
                
                tasks = {t_id: t.to_dict() for t_id, t in project.tasks.items()}
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(tasks, indent=2),
                        }
                    ],
                }
        
        # Handle task information
        elif uri.startswith("task-manager://tasks/"):
            task_id = uri.split("/")[3]
            task = self.task_manager.get_task(task_id)
            if not task:
                raise McpError(ErrorCode.NotFound, f"Task not found: {task_id}")
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(task.to_dict(), indent=2),
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
                    "description": "Update an existing project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project to update",
                            },
                            "name": {
                                "type": "string",
                                "description": "New name for the project",
                            },
                            "description": {
                                "type": "string",
                                "description": "New description for the project",
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
                    "description": "Delete a project",
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
                            "phase_id": {
                                "type": "string",
                                "description": "ID for the new phase",
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
                        "required": ["project_id", "phase_id", "name"],
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
                                "description": "Status of the task",
                                "enum": [s.value for s in TaskStatus],
                            },
                            "priority": {
                                "type": "string",
                                "description": "Priority of the task",
                                "enum": [p.value for p in TaskPriority],
                            },
                            "progress": {
                                "type": "number",
                                "description": "Progress of the task (0-100)",
                            },
                            "assignee_id": {
                                "type": "string",
                                "description": "ID of the assignee",
                            },
                            "assignee_type": {
                                "type": "string",
                                "description": "Type of the assignee (agent, user, etc.)",
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
                                "description": "New name for the task",
                            },
                            "description": {
                                "type": "string",
                                "description": "New description for the task",
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
                                "description": "New status for the task",
                                "enum": [s.value for s in TaskStatus],
                            },
                            "priority": {
                                "type": "string",
                                "description": "New priority for the task",
                                "enum": [p.value for p in TaskPriority],
                            },
                            "progress": {
                                "type": "number",
                                "description": "New progress for the task (0-100)",
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
                                "description": "Additional metadata for the task",
                            },
                            "result": {
                                "type": "object",
                                "description": "Result of the task execution",
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
                
                # Task status tools
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
                                "description": "New status for the task",
                                "enum": [s.value for s in TaskStatus],
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
                                "description": "New progress for the task (0-100)",
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
                                "enum": [s.value for s in TaskStatus],
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
                                "description": "Type of the assignee",
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
                
                if not result:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {args['project_id']}")
                
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
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": result}, indent=2),
                        }
                    ],
                }
            
            # Phase management tools
            elif tool_name == "create_phase":
                # Validate required arguments
                if "project_id" not in args or "phase_id" not in args or "name" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: project_id, phase_id, and name",
                    )
                
                # Get the project
                project = self.task_manager.get_project(args["project_id"])
                if not project:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {args['project_id']}")
                
                # Create the phase
                result = project.add_phase(
                    phase_id=args["phase_id"],
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
                            "text": json.dumps(result.to_dict(), indent=2),
                        }
                    ],
                }
            
            # Task management tools
            elif tool_name == "create_task":
                # Validate required arguments
                if "name" not in args or "description" not in args or "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: name, description, and project_id",
                    )
                
                # Call the task manager
                result = self.task_manager.create_task(
                    name=args["name"],
                    description=args["description"],
                    project_id=args["project_id"],
                    phase_id=args.get("phase_id"),
                    parent_id=args.get("parent_id"),
                    status=args.get("status", TaskStatus.PLANNED.value),
                    priority=args.get("priority", TaskPriority.MEDIUM.value),
                    progress=args.get("progress", 0.0),
                    assignee_id=args.get("assignee_id"),
                    assignee_type=args.get("assignee_type"),
                    metadata=args.get("metadata"),
                )
                
                if not result:
                    raise McpError(ErrorCode.NotFound, f"Project not found: {args['project_id']}")
                
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
                
                if not result:
                    raise McpError(ErrorCode.NotFound, f"Task not found: {args['task_id']}")
                
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
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": result}, indent=2),
                        }
                    ],
                }
            
            # Task status tools
            elif tool_name == "update_task_status":
                # Validate required arguments
                if "task_id" not in args or "status" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: task_id and status",
                    )
                
                # Call the task manager
                result = self.task_manager.update_task_status(
                    task_id=args["task_id"],
                    status=args["status"],
                )
                
                if not result:
                    raise McpError(ErrorCode.NotFound, f"Task not found: {args['task_id']}")
                
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
                if "task_id" not in args or "progress" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: task_id and progress",
                    )
                
                # Call the task manager
                result = self.task_manager.update_task_progress(
                    task_id=args["task_id"],
                    progress=args["progress"],
                )
                
                if not result:
                    raise McpError(ErrorCode.NotFound, f"Task not found: {args['task_id']}")
                
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
                if "project_id" not in args or "phase_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: project_id and phase_id",
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
                if "project_id" not in args or "status" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameters: project_id and status",
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
                            "text": json.dumps({
                                "tasks": [task.to_dict() for task in tasks]
                            }, indent=2),
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
                            "text": json.dumps({
                                "tasks": [task.to_dict() for task in tasks]
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
        print("Task Manager MCP server running on stdio", file=sys.stderr)


if __name__ == "__main__":
    # Get data directory from environment variable or use default
    data_dir = os.environ.get("TASK_MANAGER_DATA_DIR")
    auth_token = os.environ.get("TASK_MANAGER_AUTH_TOKEN")
    
    server = TaskManagerServer(data_dir, auth_token)
    asyncio.run(server.run())
```

### 2. Create a Standalone CLI Tool (task-dashboard)

Create an executable script at the root of the project:

```bash
#!/usr/bin/env python3
"""
Task Dashboard - Standalone Task Management Tool

This script launches a standalone task management dashboard with an MCP server.
It provides a unified interface for managing tasks without requiring external
servers or browser access.
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Function to find an available port
def find_available_port(start_port=8080, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port  # Fallback to the start port if none available


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Task Dashboard - Standalone Task Management Tool")
parser.add_argument("--data-dir", help="Directory to store task data")
parser.add_argument("--port", type=int, help="Port for the HTTP server")
parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
parser.add_argument("--auth-token", help="Authentication token for the MCP server")
parser.add_argument("--config", help="Path to configuration file")
args = parser.parse_args()

# Set up paths
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
dashboard_dir = script_dir / "project_master_dashboard"
data_dir = Path(args.data_dir) if args.data_dir else script_dir / ".task-manager"

# Ensure data directory exists
os.makedirs(data_dir, exist_ok=True)

# Set up environment variables
os.environ["TASK_MANAGER_DATA_DIR"] = str(data_dir)
if args.auth_token:
    os.environ["TASK_MANAGER_AUTH_TOKEN"] = args.auth_token

# Find an available port
http_port = args.port if args.port else find_available_port()

# Create a configuration file for the dashboard
config_path = Path(args.config) if args.config else dashboard_dir / "config.json"

if not config_path.exists():
    print(f"Creating configuration file at {config_path}...")
    with open(config_path, "w") as f:
        f.write(f"""{{
  "api": {{
    "baseUrl": "http://localhost:{http_port}",
    "authToken": "{args.auth_token or ''}",
    "refreshInterval": 5000
  }},
  "ui": {{
    "theme": "light",
    "defaultView": "projects",
    "refreshInterval": 5000,
    "showCompletedTasks": true
  }}
}}
""")

# Start MCP server
print("Starting Task Management MCP server...")
mcp_server_path = script_dir / "src" / "task_manager" / "mcp_servers" / "task_manager_server.py"

# Make sure the script is executable
os.chmod(mcp_server_path, 0o755)

# Start the MCP server process
mcp_process = subprocess.Popen(
    [sys.executable, str(mcp_server_path)],
    env=os.environ,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    # Don't pass stdin/stdout from the parent process to avoid blocking
    bufsize=1,
    universal_newlines=True,
)

# Define HTTP server handler
class DashboardHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(dashboard_dir), **kwargs)

# Start HTTP server
print(f"Starting HTTP server on port {http_port}...")
httpd = HTTPServer(("localhost", http_port), DashboardHTTPHandler)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()

# Open browser
if not args.no_browser:
    webbrowser.open(f"http://localhost:{http_port}")

print(f"Task Dashboard running at http://localhost:{http_port}")
print("Press Ctrl+C to exit")

# Handle termination
def signal_handler(sig, frame):
    print("\nShutting down...")
    httpd.shutdown()
    if mcp_process:
        mcp_process.terminate()
        mcp_process.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    signal_handler(signal.SIGINT, None)
```

Make the script executable:

```bash
chmod +x task-dashboard
```

### 3. Update the Project Master Dashboard

Modify the API module in the Project Master Dashboard to connect to the MCP server:

```javascript
// project_master_dashboard/js/api.js

/**
 * API module for connecting to the Task Management MCP server
 */
class TaskManagerApi {
  constructor(config) {
    this.config = config;
    this.baseUrl = config.api.baseUrl || "http://localhost:8080";
    this.authToken = config.api.authToken || "";
    this.refreshInterval = config.api.refreshInterval || 5000;
    this.mcpTools = {};
    this.loadMcpTools();
  }

  async loadMcpTools() {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/tools`);
      const data = await response.json();
      this.mcpTools = data.tools.reduce((acc, tool) => {
        acc[tool.name] = tool;
        return acc;
      }, {});
    } catch (error) {
      console.error("Failed to load MCP tools:", error);
    }
  }

  async callMcpTool(name, args = {}) {
    if (this.authToken) {
      args.auth_token = this.authToken;
    }
    
    try {
      const response = await fetch(`${this.baseUrl}/mcp/call`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name,
          arguments: args
        })
      });
      
      const data = await response.json();
      if (data.isError) {
        throw new Error(data.content[0].text);
      }
      
      return JSON.parse(data.content[0].text);
    } catch (error) {
      console.error(`Failed to call MCP tool ${name}:`, error);
      throw error;
    }
  }

  async getProjects() {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/resource?uri=task-manager://projects`);
      const data = await response.json();
      return JSON.parse(data.contents[0].text);
    } catch (error) {
      console.error("Failed to get projects:", error);
      return {};
    }
  }

  async getProject(projectId) {
    try {
      const response = await fetch(`${this.baseUrl}/mcp/resource?uri=task-manager://projects/${projectId}`);
      const data = await response.json();
      return JSON.parse(data.contents[0].text);
    } catch (error) {
      console.error(`Failed to get project ${projectId}:`, error);
      return null;
    }
  }

  async createProject(name, description, metadata) {
    return await this.callMcpTool("create_project", {
      name,
      description,
      metadata
    });
  }

  async updateProject(projectId, data) {
    return await this.callMcpTool("update_project", {
      project_id: projectId,
      ...data
    });
  }

  async deleteProject(projectId) {
    return await this.callMcpTool("delete_project", {
      project_id: projectId
    });
  }

  async createPhase(projectId, phaseId, name, description, order, metadata) {
    return await this.callMcpTool("create_phase", {
      project_id: projectId,
      phase_id: phaseId,
      name,
      description,
      order,
      metadata
    });
  }

  async createTask(projectId, name, description, phaseId, parentId, status, priority, progress, assigneeId, assigneeType, metadata) {
    return await this.callMcpTool("create_task", {
      project_id: projectId,
      name,
      description,
      phase_id: phaseId,
      parent_id: parentId,
      status,
      priority,
      progress,
      assignee_id: assigneeId,
      assignee_type: assigneeType,
      metadata
    });
  }

  async updateTask(taskId, data) {
    return await this.callMcpTool("update_task", {
      task_id: taskId,
      ...data
    });
  }

  async updateTaskStatus(taskId, status) {
    return await this.callMcpTool("update_task_status", {
      task_id: taskId,
      status
    });
  }

  async updateTaskProgress(taskId, progress) {
    return await this.callMcpTool("update_task_progress", {
      task_id: taskId,
      progress
    });
  }

  async deleteTask(taskId) {
    return await this.callMcpTool("delete_task", {
      task_id: taskId
    });
  }

  async calculateProjectProgress(projectId) {
    return await this.callMcpTool("calculate_project_progress", {
      project_id: projectId
    });
  }

  async calculatePhaseProgress(projectId, phaseId) {
    return await this.callMcpTool("calculate_phase_progress", {
      project_id: projectId,
      phase_id: phaseId
    });
  }

  async getTasksByStatus(projectId, status) {
    return await this.callMcpTool("get_tasks_by_status", {
      project_id: projectId,
      status
    });
  }

  async getTasksByAssignee(assigneeId, assigneeType) {
    return await this.callMcpTool("get_tasks_by_assignee", {
      assignee_id: assigneeId,
      assignee_type: assigneeType
    });
  }
}

// Export the API
window.TaskManagerApi = TaskManagerApi;
```

### 4. Create HTTP API Proxy for MCP Server

Create a new file at `src/task_manager/mcp_proxy.py`:

```python
#!/usr/bin/env python3
"""
MCP Server Proxy for Task Management

This module provides an HTTP API that proxies requests to the Task Manager MCP server.
It allows web clients to interact with the MCP server using RESTful HTTP requests.
"""

import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the Task Manager MCP Server
from src.task_manager.mcp_servers.task_manager_server import TaskManagerServer


class McpToolRequest(BaseModel):
    """Model for an MCP tool call request."""
    name: str
    arguments: Dict[str, Any]


class McpResourceRequest(BaseModel):
    """Model for an MCP resource request."""
    uri: str


class McpProxy:
    """
    Proxy for the Task Manager MCP server.
    
    This class handles HTTP requests and forwards them to the MCP server.
    """
    
    def __init__(self, data_dir: Optional[str] = None, auth_token: Optional[str] = None):
        """Initialize the MCP proxy."""
        self.data_dir = data_dir
        self.auth_token = auth_token
        self.server = None
        self.api = FastAPI(title="Task Manager MCP Proxy")
        
        # Add CORS middleware
        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        """Set up the API routes."""
        
        @self.api.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "Task Manager MCP Proxy"}
        
        @self.api.post("/mcp/call")
        async def call_tool(request: McpToolRequest):
            """Call an MCP tool."""
            if not self.server:
                raise HTTPException(status_code=503, detail="MCP server not initialized")
            
            try:
                result = await self.server._handle_call_tool(request)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.get("/mcp/tools")
        async def list_tools():
            """List available MCP tools."""
            if not self.server:
                raise HTTPException(status_code=503, detail="MCP server not initialized")
            
            try:
                result = await self.server._handle_list_tools(None)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.get("/mcp/resource")
        async def get_resource(uri: str):
            """Get an MCP resource."""
            if not self.server:
                raise HTTPException(status_code=503, detail="MCP server not initialized")
            
            class MockRequest:
                def __init__(self, uri):
                    self.params = MockParams(uri)
            
            class MockParams:
                def __init__(self, uri):
                    self.uri = uri
            
            try:
                result = await self.server._handle_read_resource(MockRequest(uri))
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.get("/mcp/resources")
        async def list_resources():
            """List available MCP resources."""
            if not self.server:
                raise HTTPException(status_code=503, detail="MCP server not initialized")
            
            try:
                result = await self.server._handle_list_resources(None)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            
            # Add the connection to active connections
            self.connections.add(websocket)
            
            try:
                while True:
                    # Wait for messages from the client
                    data = await websocket.receive_text()
                    
                    # Parse the message as JSON
                    try:
                        message = json.loads(data)
                        
                        # Handle different message types
                        if message.get("type") == "subscribe":
                            # Subscribe to updates for a project
                            project_id = message.get("project_id")
                            if project_id:
                                if project_id not in self.subscriptions:
                                    self.subscriptions[project_id] = set()
                                self.subscriptions[project_id].add(websocket)
                        
                        elif message.get("type") == "unsubscribe":
                            # Unsubscribe from updates for a project
                            project_id = message.get("project_id")
                            if project_id and project_id in self.subscriptions:
                                self.subscriptions[project_id].discard(websocket)
                    
                    except json.JSONDecodeError:
                        # Ignore invalid messages
                        pass
            
            except WebSocketDisconnect:
                # Remove the connection from active connections
                self.connections.discard(websocket)
                
                # Remove from all subscriptions
                for project_id, connections in self.subscriptions.items():
                    connections.discard(websocket)
    
    async def start_server(self):
        """Start the MCP server."""
        self.server = TaskManagerServer(self.data_dir, self.auth_token)
        self.connections = set()
        self.subscriptions = {}
        
        # Start a task to notify subscribers of changes
        asyncio.create_task(self._notify_subscribers())
    
    async def _notify_subscribers(self):
        """Notify subscribers of changes."""
        last_modified = {}
        
        while True:
            try:
                # Check for changes in projects
                for project_id, project in self.server.task_manager.projects.items():
                    # Skip if no subscribers
                    if project_id not in self.subscriptions or not self.subscriptions[project_id]:
                        continue
                    
                    # Check if the project has been modified
                    if (project_id not in last_modified or 
                        project.updated_at > last_modified[project_id]):
                        
                        # Update the last modified time
                        last_modified[project_id] = project.updated_at
                        
                        # Notify subscribers
                        for websocket in self.subscriptions[project_id]:
                            try:
                                await websocket.send_text(json.dumps({
                                    "type": "update",
                                    "project_id": project_id,
                                    "timestamp": datetime.now().isoformat(),
                                }))
                            except Exception:
                                # Remove the connection if it's closed
                                self.subscriptions[project_id].discard(websocket)
                                self.connections.discard(websocket)
            
            except Exception as e:
                print(f"Error in notify subscribers: {e}")
            
            # Wait before checking again
            await asyncio.sleep(1)
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the MCP proxy."""
        # Start the MCP server
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_server())
        
        # Run the API
        uvicorn.run(self.api, host=host, port=port)


if __name__ == "__main__":
    # Get data directory from environment variable or use default
    data_dir = os.environ.get("TASK_MANAGER_DATA_DIR")
    auth_token = os.environ.get("TASK_MANAGER_AUTH_TOKEN")
    port = int(os.environ.get("PORT", "8080"))
    
    proxy = McpProxy(data_dir, auth_token)
    proxy.run(port=port)
```

### 5. Create a Dagger Integration for Task Management

Create a new file at `src/task_manager/dagger_integration.py`:

```python
"""
Dagger Integration for Task Management

This module provides utilities for integrating Dagger workflows with the task management system.
It allows tasks to be executed as containerized workflows and updates task status based on workflow results.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent_manager.dagger_adapter import DaggerAdapter
from src.task_manager.manager import get_task_manager, TaskStatus, Task


class TaskWorkflowIntegration:
    """
    Integration between the task management system and Dagger workflows.
    
    This class provides methods for creating Dagger workflows from tasks and
    updating task status based on workflow execution results.
    """
    
    def __init__(self, dagger_config_path: Optional[str] = None):
        """
        Initialize the task workflow integration.
        
        Args:
            dagger_config_path: Path to the Dagger configuration file
        """
        self.task_manager = get_task_manager()
        self.dagger_adapter = DaggerAdapter(config_path=dagger_config_path)
    
    async def initialize(self):
        """Initialize the integration."""
        await self.dagger_adapter.initialize()
    
    async def create_workflow_from_task(
        self,
        task_id: str,
        workflow_name: Optional[str] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a Dagger workflow from a task.
        
        Args:
            task_id: ID of the task to convert to a workflow
            workflow_name: Name for the workflow (defaults to task name)
            custom_inputs: Custom inputs for the workflow
            
        Returns:
            ID of the created workflow
        """
        # Get the task
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Update task status
        self.task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        # Create the workflow
        workflow_id = await self.dagger_adapter.create_workflow(
            name=workflow_name or task.name,
            description=task.description,
            inputs=custom_inputs or task.metadata.get("workflow_inputs", {}),
        )
        
        # Add the workflow ID to the task metadata
        self.task_manager.update_task(
            task_id=task_id,
            metadata={
                "workflow_id": workflow_id,
                "workflow_created_at": datetime.now().isoformat(),
            },
        )
        
        return workflow_id
    
    async def execute_task_workflow(
        self,
        task_id: str,
        workflow_id: Optional[str] = None,
        custom_inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow for a task.
        
        Args:
            task_id: ID of the task
            workflow_id: ID of the workflow (if not provided, a new workflow will be created)
            custom_inputs: Custom inputs for the workflow
            
        Returns:
            Result of the workflow execution
        """
        # Get the task
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Get or create the workflow
        if not workflow_id:
            workflow_id = task.metadata.get("workflow_id")
            if not workflow_id:
                workflow_id = await self.create_workflow_from_task(
                    task_id=task_id,
                    custom_inputs=custom_inputs,
                )
        
        # Update task status
        self.task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        self.task_manager.update_task(
            task_id=task_id,
            metadata={
                "workflow_id": workflow_id,
                "workflow_started_at": datetime.now().isoformat(),
            },
        )
        
        try:
            # Execute the workflow
            result = await self.dagger_adapter.execute_workflow(
                workflow_id=workflow_id,
                inputs=custom_inputs or task.metadata.get("workflow_inputs", {}),
            )
            
            # Update task status and result
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                result=result,
                metadata={
                    "workflow_completed_at": datetime.now().isoformat(),
                    "workflow_status": "completed",
                },
            )
            
            return result
        
        except Exception as e:
            # Update task status and error
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                metadata={
                    "workflow_failed_at": datetime.now().isoformat(),
                    "workflow_status": "failed",
                    "workflow_error": str(e),
                },
            )
            
            raise
    
    async def create_workflows_for_project(
        self,
        project_id: str,
        phase_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
    ) -> Dict[str, str]:
        """
        Create workflows for all tasks in a project or phase.
        
        Args:
            project_id: ID of the project
            phase_id: ID of the phase (optional)
            status: Filter tasks by status (optional)
            
        Returns:
            Dictionary mapping task IDs to workflow IDs
        """
        # Get the project
        project = self.task_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Filter tasks
        tasks = []
        for task_id, task in project.tasks.items():
            if phase_id and task.phase_id != phase_id:
                continue
            if status and task.status != status:
                continue
            tasks.append(task)
        
        # Create workflows
        result = {}
        for task in tasks:
            try:
                workflow_id = await self.create_workflow_from_task(task.id)
                result[task.id] = workflow_id
            except Exception as e:
                print(f"Failed to create workflow for task {task.id}: {e}")
        
        return result
    
    async def execute_workflows_for_project(
        self,
        project_id: str,
        phase_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
    ) -> Dict[str, Any]:
        """
        Execute workflows for all tasks in a project or phase.
        
        Args:
            project_id: ID of the project
            phase_id: ID of the phase (optional)
            status: Filter tasks by status (optional)
            
        Returns:
            Dictionary mapping task IDs to execution results
        """
        # Get the project
        project = self.task_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Filter tasks
        tasks = []
        for task_id, task in project.tasks.items():
            if phase_id and task.phase_id != phase_id:
                continue
            if status and task.status != status:
                continue
            tasks.append(task)
        
        # Execute workflows
        result = {}
        for task in tasks:
            try:
                execution_result = await self.execute_task_workflow(task.id)
                result[task.id] = {
                    "status": "completed",
                    "result": execution_result,
                }
            except Exception as e:
                result[task.id] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        return result
    
    async def shutdown(self):
        """Shutdown the integration."""
        await self.dagger_adapter.shutdown()


def get_task_workflow_integration(
    dagger_config_path: Optional[str] = None,
) -> TaskWorkflowIntegration:
    """
    Get a TaskWorkflowIntegration instance.
    
    Args:
        dagger_config_path: Path to the Dagger configuration file
        
    Returns:
        TaskWorkflowIntegration instance
    """
    integration = TaskWorkflowIntegration(dagger_config_path)
    
    # Create and run a new event loop to initialize the integration
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(integration.initialize())
    
    return integration
```

### 6. Update the task-dashboard Script to Support Dagger Integration

Modify the `task-dashboard` script to include Dagger integration:

```python
# Add Dagger support
parser.add_argument("--dagger", action="store_true", help="Enable Dagger integration")
parser.add_argument("--dagger-config", help="Path to Dagger configuration file")

# Enable Dagger integration if requested
if args.dagger:
    print("Enabling Dagger integration...")
    os.environ["TASK_MANAGER_DAGGER_ENABLED"] = "1"
    if args.dagger_config:
        os.environ["TASK_MANAGER_DAGGER_CONFIG"] = args.dagger_config
```

### 7. Testing the Implementation

1. Make the MCP server file executable:

```bash
chmod +x src/task_manager/mcp_servers/task_manager_server.py
```

2. Make the proxy server file executable:

```bash
chmod +x src/task_manager/mcp_proxy.py
```

3. Start the standalone dashboard:

```bash
./task-dashboard
```

4. Test creating a project and tasks through the dashboard

5. Test Dagger integration:

```bash
./task-dashboard --dagger --dagger-config config/dagger.yaml
```

## Conclusion

This implementation creates a standalone Task Management MCP server that integrates with the Project Master Dashboard. It provides a unified interface for managing tasks without requiring external servers or browser access. The implementation also includes integration with Dagger for task automation.

By following these steps, you'll have a powerful task management system that can be used to track the completion of your projects, including this AI-Orchestration-Platform project.