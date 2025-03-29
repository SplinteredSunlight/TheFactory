#!/usr/bin/env python3
"""
Dagger Workflow Integration for Task Management MCP Server

This module extends the Task Manager MCP Server with Dagger workflow capabilities,
allowing tasks to be executed as containerized workflows using Dagger.io.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from mcp.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListResourcesRequestSchema,
    ListResourceTemplatesRequestSchema,
    ListToolsRequestSchema,
    McpError,
    ReadResourceRequestSchema,
)

# Import the Task Manager and Dagger integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.task_manager.dagger_integration import get_task_workflow_integration
from src.task_manager.mcp_servers.workflow_templates import get_template_registry
from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker
from src.orchestrator.dagger_communication import get_dagger_communication_manager


class DaggerWorkflowIntegration:
    """Dagger Workflow Integration for the Task Manager MCP Server."""

    def __init__(self, server, task_manager=None, dagger_config_path=None, templates_dir=None):
        """Initialize the Dagger Workflow Integration component.
        
        Args:
            server: The MCP server instance
            task_manager: The Task Manager instance
            dagger_config_path: Path to the Dagger configuration file
            templates_dir: Directory to load workflow templates from
        """
        self.server = server
        self.task_manager = task_manager
        self.dagger_config_path = dagger_config_path
        self.workflow_integration = get_task_workflow_integration(dagger_config_path)
        self.template_registry = get_template_registry(templates_dir)
        
        # Get circuit breaker for MCP operations
        self.circuit_breaker = get_circuit_breaker("mcp_dagger_operations")
        
        # Get the Dagger communication manager
        self.communication_manager = get_dagger_communication_manager()
        
        # Container registry for tracking Dagger containers
        self.container_registry = {}
        
        # Set up Dagger workflow resources and tools
        self.setup_dagger_workflow_resources()
        self.setup_dagger_workflow_tools()
        
        # Log initialization
        logging.info("Dagger Workflow Integration initialized with config path: %s", dagger_config_path)

    def setup_dagger_workflow_resources(self):
        """Set up Dagger workflow resources for the MCP server."""
        # Add Dagger workflow resources to the list_resources handler
        original_list_resources = self.server._request_handlers.get(ListResourcesRequestSchema.__name__)
        
        async def enhanced_list_resources(request):
            """Enhanced handler for listing resources that includes Dagger workflow resources."""
            # Get original resources
            original_response = await original_list_resources(request)
            resources = original_response.get("resources", [])
            
            # Add Dagger workflow resources
            dagger_resources = [
                {
                    "uri": "task-manager://dagger/workflows",
                    "name": "Dagger Workflows",
                    "mimeType": "application/json",
                    "description": "List of all Dagger workflows in the task manager",
                },
                {
                    "uri": "task-manager://dagger/stats",
                    "name": "Dagger Workflow Statistics",
                    "mimeType": "application/json",
                    "description": "Statistics for Dagger workflows",
                },
                {
                    "uri": "task-manager://dagger/templates",
                    "name": "Dagger Workflow Templates",
                    "mimeType": "application/json",
                    "description": "List of available workflow templates",
                },
                {
                    "uri": "task-manager://dagger/containers",
                    "name": "Dagger Containers",
                    "mimeType": "application/json",
                    "description": "List of all Dagger containers",
                },
            ]
            
            resources.extend(dagger_resources)
            return {"resources": resources}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListResourcesRequestSchema, enhanced_list_resources)
        
        # Add Dagger workflow resource templates
        original_list_templates = self.server._request_handlers.get(ListResourceTemplatesRequestSchema.__name__)
        
        async def enhanced_list_templates(request):
            """Enhanced handler for listing resource templates that includes Dagger workflow templates."""
            # Get original templates
            original_response = await original_list_templates(request)
            templates = original_response.get("resourceTemplates", [])
            
            # Add Dagger workflow templates
            dagger_templates = [
                {
                    "uriTemplate": "task-manager://dagger/workflows/{task_id}",
                    "name": "Dagger Workflow for Task",
                    "mimeType": "application/json",
                    "description": "Dagger workflow information for a specific task",
                },
                {
                    "uriTemplate": "task-manager://dagger/projects/{project_id}/workflows",
                    "name": "Dagger Workflows for Project",
                    "mimeType": "application/json",
                    "description": "Dagger workflows for all tasks in a project",
                },
                {
                    "uriTemplate": "task-manager://dagger/templates/{template_id}",
                    "name": "Dagger Workflow Template",
                    "mimeType": "application/json",
                    "description": "Details of a specific workflow template",
                },
                {
                    "uriTemplate": "task-manager://dagger/templates/category/{category}",
                    "name": "Dagger Workflow Templates by Category",
                    "mimeType": "application/json",
                    "description": "List of workflow templates in a specific category",
                },
                {
                    "uriTemplate": "task-manager://dagger/containers/{container_id}",
                    "name": "Dagger Container Details",
                    "mimeType": "application/json",
                    "description": "Details of a specific Dagger container",
                },
                {
                    "uriTemplate": "task-manager://dagger/containers/{container_id}/logs",
                    "name": "Dagger Container Logs",
                    "mimeType": "text/plain",
                    "description": "Logs for a specific Dagger container",
                },
                {
                    "uriTemplate": "task-manager://dagger/workflows/{workflow_id}/containers",
                    "name": "Dagger Workflow Containers",
                    "mimeType": "application/json",
                    "description": "Containers for a specific Dagger workflow",
                },
            ]
            
            templates.extend(dagger_templates)
            return {"resourceTemplates": templates}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListResourceTemplatesRequestSchema, enhanced_list_templates)
        
        # Enhance the read_resource handler to handle Dagger workflow resources
        original_read_resource = self.server._request_handlers.get(ReadResourceRequestSchema.__name__)
        
        async def enhanced_read_resource(request):
            """Enhanced handler for reading resources that handles Dagger workflow resources."""
            uri = request.params.uri
            
            # Handle Dagger workflow resources
            if uri.startswith("task-manager://dagger/"):
                return await self._handle_dagger_workflow_resource(uri)
            
            # For other resources, use the original handler
            return await original_read_resource(request)
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ReadResourceRequestSchema, enhanced_read_resource)

    async def _handle_dagger_workflow_resource(self, uri):
        """Handle Dagger workflow resources.
        
        Args:
            uri: The resource URI
            
        Returns:
            The resource content
            
        Raises:
            McpError: If the resource is not found
        """
        try:
            # List of all Dagger workflows
            if uri == "task-manager://dagger/workflows":
                workflows = await self._get_all_workflows()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(workflows, indent=2),
                        }
                    ],
                }
            
            # Dagger workflow statistics
            elif uri == "task-manager://dagger/stats":
                stats = await self._get_workflow_stats()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(stats, indent=2),
                        }
                    ],
                }
            
            # List of all workflow templates
            elif uri == "task-manager://dagger/templates":
                templates = self.template_registry.list_templates()
                categories = self.template_registry.get_categories()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps({
                                "templates": templates,
                                "categories": categories,
                                "count": len(templates)
                            }, indent=2),
                        }
                    ],
                }
                
            # List of all Dagger containers
            elif uri == "task-manager://dagger/containers":
                containers = await self._get_all_containers()
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(containers, indent=2),
                        }
                    ],
                }
            
            # Dagger workflow for a specific task
            elif uri.startswith("task-manager://dagger/workflows/"):
                # Extract task_id from URI
                parts = uri.split("/")
                if len(parts) >= 5:
                    task_id = parts[4]
                    try:
                        # Use circuit breaker for this operation
                        workflow = await execute_with_circuit_breaker(
                            self.circuit_breaker,
                            lambda: self.workflow_integration.get_workflow_status(task_id)
                        )
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(workflow, indent=2),
                                }
                            ],
                        }
                    except ValueError as e:
                        # Task not found
                        raise McpError(ErrorCode.NotFound, str(e))
            
            # Dagger workflows for a project
            elif uri.startswith("task-manager://dagger/projects/") and uri.endswith("/workflows"):
                # Extract project_id from URI
                parts = uri.split("/")
                if len(parts) >= 5:
                    project_id = parts[4]
                    try:
                        workflows = await self._get_project_workflows(project_id)
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(workflows, indent=2),
                                }
                            ],
                        }
                    except ValueError as e:
                        # Project not found
                        raise McpError(ErrorCode.NotFound, str(e))
            
            # Specific workflow template
            elif uri.startswith("task-manager://dagger/templates/"):
                # Extract template_id from URI
                parts = uri.split("/")
                if len(parts) >= 5 and parts[3] == "templates" and parts[4] != "category":
                    template_id = parts[4]
                    template = self.template_registry.get_template(template_id)
                    if template:
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(template.to_dict(), indent=2),
                                }
                            ],
                        }
                    else:
                        raise McpError(ErrorCode.NotFound, f"Template not found: {template_id}")
            
            # Templates by category
            elif uri.startswith("task-manager://dagger/templates/category/"):
                # Extract category from URI
                parts = uri.split("/")
                if len(parts) >= 6 and parts[3] == "templates" and parts[4] == "category":
                    category = parts[5]
                    templates = self.template_registry.list_templates(category)
                    return {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps({
                                    "category": category,
                                    "templates": templates,
                                    "count": len(templates)
                                }, indent=2),
                            }
                        ],
                    }
                    
            # Dagger container details
            elif uri.startswith("task-manager://dagger/containers/") and not uri.endswith("/logs"):
                # Extract container_id from URI
                parts = uri.split("/")
                if len(parts) >= 5:
                    container_id = parts[4]
                    try:
                        container_info = await self._get_container_info(container_id)
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(container_info, indent=2),
                                }
                            ],
                        }
                    except ValueError as e:
                        # Container not found
                        raise McpError(ErrorCode.NotFound, str(e))
                        
            # Dagger container logs
            elif uri.startswith("task-manager://dagger/containers/") and uri.endswith("/logs"):
                # Extract container_id from URI
                parts = uri.split("/")
                if len(parts) >= 6 and parts[5] == "logs":
                    container_id = parts[4]
                    try:
                        logs = await self._get_container_logs(container_id)
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "text/plain",
                                    "text": logs,
                                }
                            ],
                        }
                    except ValueError as e:
                        # Container not found
                        raise McpError(ErrorCode.NotFound, str(e))
                        
            # Dagger workflow containers
            elif uri.startswith("task-manager://dagger/workflows/") and uri.endswith("/containers"):
                # Extract workflow_id from URI
                parts = uri.split("/")
                if len(parts) >= 6 and parts[5] == "containers":
                    workflow_id = parts[4]
                    try:
                        containers = await self._get_workflow_containers(workflow_id)
                        return {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(containers, indent=2),
                                }
                            ],
                        }
                    except ValueError as e:
                        # Workflow not found
                        raise McpError(ErrorCode.NotFound, str(e))
            
            # If we get here, the resource wasn't found
            raise McpError(ErrorCode.NotFound, f"Resource not found: {uri}")
        except Exception as e:
            if isinstance(e, McpError):
                raise
            logging.error(f"Error handling Dagger workflow resource: {e}")
            raise McpError(ErrorCode.InternalError, f"Internal error: {str(e)}")

    async def _get_all_containers(self):
        """Get all Dagger containers.
        
        Returns:
            Dict containing all containers
        """
        containers = {}
        
        # Get containers from the registry
        for container_id, container_info in self.container_registry.items():
            try:
                # Get container status from communication manager
                status = await self.communication_manager.get_container_capabilities(
                    container_id=container_id,
                    use_circuit_breaker=True
                )
                
                # Add status to container info
                container_info["status"] = status
                containers[container_id] = container_info
            except Exception as e:
                logging.warning(f"Error getting container status for {container_id}: {e}")
                containers[container_id] = {
                    "container_id": container_id,
                    "status": "unknown",
                    "error": str(e)
                }
        
        return containers
    
    async def _get_container_info(self, container_id):
        """Get information about a specific container.
        
        Args:
            container_id: ID of the container
            
        Returns:
            Dict containing container information
            
        Raises:
            ValueError: If the container is not found
        """
        # Check if container exists in registry
        if container_id not in self.container_registry:
            raise ValueError(f"Container not found: {container_id}")
        
        container_info = self.container_registry[container_id]
        
        try:
            # Get container status from communication manager
            status = await self.communication_manager.get_container_capabilities(
                container_id=container_id,
                use_circuit_breaker=True
            )
            
            # Add status to container info
            container_info["status"] = status
        except Exception as e:
            logging.warning(f"Error getting container status for {container_id}: {e}")
            container_info["status"] = "unknown"
            container_info["error"] = str(e)
        
        return container_info
    
    async def _get_container_logs(self, container_id):
        """Get logs for a specific container.
        
        Args:
            container_id: ID of the container
            
        Returns:
            String containing container logs
            
        Raises:
            ValueError: If the container is not found
        """
        # Check if container exists in registry
        if container_id not in self.container_registry:
            raise ValueError(f"Container not found: {container_id}")
        
        # Get container logs from workflow integration
        try:
            # Use circuit breaker for this operation
            logs = await execute_with_circuit_breaker(
                self.circuit_breaker,
                lambda: self.workflow_integration.get_container_logs(container_id)
            )
            return logs
        except Exception as e:
            logging.error(f"Error getting logs for container {container_id}: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def _get_workflow_containers(self, workflow_id):
        """Get containers for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict containing workflow containers
            
        Raises:
            ValueError: If the workflow is not found
        """
        containers = {}
        
        # Find containers for this workflow
        for container_id, container_info in self.container_registry.items():
            if container_info.get("workflow_id") == workflow_id:
                try:
                    # Get container status from communication manager
                    status = await self.communication_manager.get_container_capabilities(
                        container_id=container_id,
                        use_circuit_breaker=True
                    )
                    
                    # Add status to container info
                    container_info["status"] = status
                    containers[container_id] = container_info
                except Exception as e:
                    logging.warning(f"Error getting container status for {container_id}: {e}")
                    containers[container_id] = {
                        "container_id": container_id,
                        "workflow_id": workflow_id,
                        "status": "unknown",
                        "error": str(e)
                    }
        
        if not containers:
            raise ValueError(f"No containers found for workflow: {workflow_id}")
        
        return containers
    
    async def _get_all_workflows(self):
        """Get all Dagger workflows.
        
        Returns:
            Dict containing all workflows
        """
        workflows = {}
        
        # Check if task manager has projects
        if not hasattr(self.task_manager, 'projects') or not self.task_manager.projects:
            return workflows
        
        # Iterate through all projects and tasks
        for project_id, project in self.task_manager.projects.items():
            if not hasattr(project, 'tasks') or not project.tasks:
                continue
                
            for task_id, task in project.tasks.items():
                # Check if task has a workflow
                if hasattr(task, 'metadata') and task.metadata and "workflow_id" in task.metadata:
                    try:
                        # Use circuit breaker for this operation
                        workflow_status = await execute_with_circuit_breaker(
                            self.circuit_breaker,
                            lambda: self.workflow_integration.get_workflow_status(task_id)
                        )
                        if workflow_status["has_workflow"]:
                            workflows[task_id] = workflow_status
                    except Exception as e:
                        logging.warning(f"Error getting workflow status for task {task_id}: {e}")
        
        return workflows

    async def _get_workflow_stats(self):
        """Get Dagger workflow statistics.
        
        Returns:
            Dict containing workflow statistics
        """
        # Initialize counters
        total_workflows = 0
        completed_workflows = 0
        failed_workflows = 0
        in_progress_workflows = 0
        unknown_workflows = 0
        
        # Check if task manager has projects
        if not hasattr(self.task_manager, 'projects') or not self.task_manager.projects:
            return {
                "total_workflows": 0,
                "completed_workflows": 0,
                "failed_workflows": 0,
                "in_progress_workflows": 0,
                "unknown_workflows": 0,
                "success_rate": 0
            }
        
        # Iterate through all projects and tasks
        for project_id, project in self.task_manager.projects.items():
            if not hasattr(project, 'tasks') or not project.tasks:
                continue
                
            for task_id, task in project.tasks.items():
                # Check if task has a workflow
                if hasattr(task, 'metadata') and task.metadata and "workflow_id" in task.metadata:
                    total_workflows += 1
                    
                    # Count by status
                    workflow_status = task.metadata.get("workflow_status", "unknown")
                    if workflow_status == "completed":
                        completed_workflows += 1
                    elif workflow_status == "failed":
                        failed_workflows += 1
                    elif workflow_status == "in_progress":
                        in_progress_workflows += 1
                    else:
                        unknown_workflows += 1
        
        # Calculate success rate
        success_rate = (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0
        
        return {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "in_progress_workflows": in_progress_workflows,
            "unknown_workflows": unknown_workflows,
            "success_rate": success_rate
        }

    async def _get_project_workflows(self, project_id):
        """Get all workflows for a project.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dict containing all workflows for the project
            
        Raises:
            ValueError: If the project is not found
        """
        workflows = {}
        
        # Get the project
        project = self.task_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # Check if project has tasks
        if not hasattr(project, 'tasks') or not project.tasks:
            return workflows
        
        # Iterate through all tasks in the project
        for task_id, task in project.tasks.items():
            # Check if task has a workflow
            if hasattr(task, 'metadata') and task.metadata and "workflow_id" in task.metadata:
                try:
                    # Use circuit breaker for this operation
                    workflow_status = await execute_with_circuit_breaker(
                        self.circuit_breaker,
                        lambda: self.workflow_integration.get_workflow_status(task_id)
                    )
                    if workflow_status["has_workflow"]:
                        workflows[task_id] = workflow_status
                except Exception as e:
                    logging.warning(f"Error getting workflow status for task {task_id}: {e}")
        
        return workflows

    def setup_dagger_workflow_tools(self):
        """Set up Dagger workflow tools for the MCP server."""
        # Register the tools with the server
        original_list_tools = self.server._request_handlers.get(ListToolsRequestSchema.__name__)
        
        async def enhanced_list_tools(request):
            """Enhanced handler for listing tools that includes Dagger workflow tools."""
            # Get original tools
            original_response = await original_list_tools(request)
            tools = original_response.get("tools", [])
            
            # Add Dagger workflow tools
            dagger_tools = self._get_dagger_workflow_tools()
            tools.extend(dagger_tools)
            
            return {"tools": tools}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListToolsRequestSchema, enhanced_list_tools)
        
        # Register the tool handlers
        original_call_tool = self.server._request_handlers.get(CallToolRequestSchema.__name__)
        
        async def enhanced_call_tool(request):
            """Enhanced handler for calling tools that handles Dagger workflow tools."""
            tool_name = request.params.name
            args = request.params.arguments
            
            # Handle Dagger workflow tools
            if tool_name == "create_workflow_from_task":
                return await self._handle_create_workflow_from_task(args)
            elif tool_name == "execute_task_workflow":
                return await self._handle_execute_task_workflow(args)
            elif tool_name == "get_workflow_status":
                return await self._handle_get_workflow_status(args)
            elif tool_name == "create_workflows_for_project":
                return await self._handle_create_workflows_for_project(args)
            elif tool_name == "execute_workflows_for_project":
                return await self._handle_execute_workflows_for_project(args)
            elif tool_name == "list_workflow_templates":
                return await self._handle_list_workflow_templates(args)
            elif tool_name == "get_workflow_template":
                return await self._handle_get_workflow_template(args)
            elif tool_name == "create_workflow_from_template":
                return await self._handle_create_workflow_from_template(args)
            # Handle container management tools
            elif tool_name == "get_container_status":
                return await self._handle_get_container_status(args)
            elif tool_name == "get_container_logs":
                return await self._handle_get_container_logs_tool(args)
            elif tool_name == "restart_container":
                return await self._handle_restart_container(args)
            elif tool_name == "execute_container_command":
                return await self._handle_execute_container_command(args)
            
            # For other tools, use the original handler
            return await original_call_tool(request)
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(CallToolRequestSchema, enhanced_call_tool)

    def _get_dagger_workflow_tools(self):
        """Get the Dagger workflow tools."""
        return [
            {
                "name": "create_workflow_from_task",
                "description": "Create a Dagger workflow from a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to create a workflow for"
                        },
                        "workflow_name": {
                            "type": "string",
                            "description": "Optional name for the workflow"
                        },
                        "custom_inputs": {
                            "type": "object",
                            "description": "Optional custom inputs for the workflow"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_container_status",
                "description": "Get the status of a Dagger container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "ID of the container to get status for"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "get_container_logs",
                "description": "Get logs for a Dagger container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "ID of the container to get logs for"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "restart_container",
                "description": "Restart a Dagger container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "ID of the container to restart"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["container_id"]
                }
            },
            {
                "name": "execute_container_command",
                "description": "Execute a command in a Dagger container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "ID of the container to execute the command in"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["container_id", "command"]
                }
            },
            {
                "name": "execute_task_workflow",
                "description": "Execute a Dagger workflow for a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to execute the workflow for"
                        },
                        "workflow_type": {
                            "type": "string",
                            "description": "Type of workflow to execute",
                            "enum": ["containerized_workflow", "dagger_pipeline"]
                        },
                        "workflow_params": {
                            "type": "object",
                            "description": "Optional parameters for the workflow"
                        },
                        "skip_cache": {
                            "type": "boolean",
                            "description": "Whether to skip the cache"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_workflow_status",
                "description": "Get the status of a Dagger workflow for a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to get the workflow status for"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "create_workflows_for_project",
                "description": "Create Dagger workflows for all tasks in a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project to create workflows for"
                        },
                        "phase_id": {
                            "type": "string",
                            "description": "Optional ID of the phase to create workflows for"
                        },
                        "status": {
                            "type": "string",
                            "description": "Optional status of tasks to create workflows for"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "execute_workflows_for_project",
                "description": "Execute Dagger workflows for all tasks in a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID of the project to execute workflows for"
                        },
                        "phase_id": {
                            "type": "string",
                            "description": "Optional ID of the phase to execute workflows for"
                        },
                        "status": {
                            "type": "string",
                            "description": "Optional status of tasks to execute workflows for"
                        },
                        "workflow_type": {
                            "type": "string",
                            "description": "Type of workflow to execute",
                            "enum": ["containerized_workflow", "dagger_pipeline"]
                        },
                        "skip_cache": {
                            "type": "boolean",
                            "description": "Whether to skip the cache"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "list_workflow_templates",
                "description": "List available workflow templates",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional category to filter templates"
                        }
                    }
                }
            },
            {
                "name": "get_workflow_template",
                "description": "Get details of a specific workflow template",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "ID of the template to retrieve"
                        }
                    },
                    "required": ["template_id"]
                }
            },
            {
                "name": "create_workflow_from_template",
                "description": "Create a workflow from a template",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to create a workflow for"
                        },
                        "template_id": {
                            "type": "string",
                            "description": "ID of the template to use"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Custom parameters for the template"
                        },
                        "use_circuit_breaker": {
                            "type": "boolean",
                            "description": "Whether to use circuit breaker protection"
                        }
                    },
                    "required": ["task_id", "template_id"]
                }
            }
        ]

    async def _handle_create_workflow_from_task(self, args):
        """Handle the create_workflow_from_task tool."""
        task_id = args.get("task_id")
        if not task_id:
            raise McpError(ErrorCode.InvalidParams, "task_id is required")
        
        workflow_name = args.get("workflow_name")
        custom_inputs = args.get("custom_inputs")
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                workflow_info = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.workflow_integration.create_workflow_from_task(
                        task_id=task_id,
                        workflow_name=workflow_name,
                        custom_inputs=custom_inputs
                    )
                )
            else:
                workflow_info = await self.workflow_integration.create_workflow_from_task(
                    task_id=task_id,
                    workflow_name=workflow_name,
                    custom_inputs=custom_inputs
                )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(workflow_info, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating workflow: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def _handle_execute_task_workflow(self, args):
        """Handle the execute_task_workflow tool."""
        task_id = args.get("task_id")
        if not task_id:
            raise McpError(ErrorCode.InvalidParams, "task_id is required")
        
        workflow_type = args.get("workflow_type", "containerized_workflow")
        workflow_params = args.get("workflow_params", {})
        skip_cache = args.get("skip_cache", False)
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        # Add circuit breaker flag to workflow params
        workflow_params["use_circuit_breaker"] = use_circuit_breaker
        
        try:
            # Use circuit breaker at MCP level if enabled
            if use_circuit_breaker:
                execution_result = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.workflow_integration.execute_task_workflow(
                        task_id=task_id,
                        workflow_type=workflow_type,
                        workflow_params=workflow_params,
                        skip_cache=skip_cache
                    )
                )
            else:
                execution_result = await self.workflow_integration.execute_task_workflow(
                    task_id=task_id,
                    workflow_type=workflow_type,
                    workflow_params=workflow_params,
                    skip_cache=skip_cache
                )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(execution_result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing workflow: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def _handle_get_workflow_status(self, args):
        """Handle the get_workflow_status tool."""
        task_id = args.get("task_id")
        if not task_id:
            raise McpError(ErrorCode.InvalidParams, "task_id is required")
        
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                status = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.workflow_integration.get_workflow_status(task_id=task_id)
                )
            else:
                status = await self.workflow_integration.get_workflow_status(task_id=task_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(status, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting workflow status: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def _handle_create_workflows_for_project(self, args):
        """Handle the create_workflows_for_project tool."""
        project_id = args.get("project_id")
        if not project_id:
            raise McpError(ErrorCode.InvalidParams, "project_id is required")
        
        phase_id = args.get("phase_id")
        status = args.get("status")
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                result = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.workflow_integration.create_workflows_for_project(
                        project_id=project_id,
                        phase_id=phase_id,
                        status=status
                    )
                )
            else:
                result = await self.workflow_integration.create_workflows_for_project(
                    project_id=project_id,
                    phase_id=phase_id,
                    status=status
                )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating workflows for project: {str(e)}"
                    }
                ],
                "isError": True
            }
            
    async def _handle_execute_workflows_for_project(self, args):
        """Handle the execute_workflows_for_project tool."""
        project_id = args.get("project_id")
        if not project_id:
            raise McpError(ErrorCode.InvalidParams, "project_id is required")
        
        phase_id = args.get("phase_id")
        status = args.get("status")
        workflow_type = args.get("workflow_type", "containerized_workflow")
        skip_cache = args.get("skip_cache", False)
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                result = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.workflow_integration.execute_workflows_for_project(
                        project_id=project_id,
                        phase_id=phase_id,
                        status=status,
                        workflow_type=workflow_type,
                        skip_cache=skip_cache
                    )
                )
            else:
                result = await self.workflow_integration.execute_workflows_for_project(
                    project_id=project_id,
                    phase_id=phase_id,
                    status=status,
                    workflow_type=workflow_type,
                    skip_cache=skip_cache
                )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing workflows for project: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_list_workflow_templates(self, args):
        """Handle the list_workflow_templates tool."""
        category = args.get("category")
        
        try:
            templates = self.template_registry.list_templates(category)
            categories = self.template_registry.get_categories()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "templates": templates,
                            "categories": categories,
                            "count": len(templates)
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error listing workflow templates: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_get_workflow_template(self, args):
        """Handle the get_workflow_template tool."""
        template_id = args.get("template_id")
        if not template_id:
            raise McpError(ErrorCode.InvalidParams, "template_id is required")
        
        try:
            template = self.template_registry.get_template(template_id)
            if not template:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Template not found: {template_id}"
                        }
                    ],
                    "isError": True
                }
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(template.to_dict(), indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting workflow template: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def create_workflow_from_template(
        self,
        task_id: str,
        template: Any,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a workflow from a template.
        
        Args:
            task_id: ID of the task to create a workflow for
            template: The template to use
            parameters: Parameters for the template
            
        Returns:
            Dictionary with workflow information
            
        Raises:
            ValueError: If the task is not found
        """
        # Get the task
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Convert task to pipeline using the template
        pipeline = await self.workflow_integration.convert_task_to_pipeline(
            task_id=task_id,
            template_id=template.template_id,
            parameters=parameters
        )
        
        # Create a workflow from the task
        workflow_info = await self.workflow_integration.create_workflow_from_task(
            task_id=task_id,
            workflow_name=f"Template: {template.name}",
            custom_inputs={
                "pipeline": pipeline,
                "template_id": template.template_id,
                "parameters": parameters
            }
        )
        
        return workflow_info
    
    async def _handle_create_workflow_from_template(self, args):
        """Handle the create_workflow_from_template tool."""
        task_id = args.get("task_id")
        if not task_id:
            raise McpError(ErrorCode.InvalidParams, "task_id is required")
        
        template_id = args.get("template_id")
        if not template_id:
            raise McpError(ErrorCode.InvalidParams, "template_id is required")
        
        parameters = args.get("parameters", {})
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Get the template
            template = self.template_registry.get_template(template_id)
            if not template:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Template not found: {template_id}"
                        }
                    ],
                    "isError": True
                }
            
            # Create workflow from template with circuit breaker if enabled
            if use_circuit_breaker:
                workflow_info = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.create_workflow_from_template(
                        task_id=task_id,
                        template=template,
                        parameters=parameters
                    )
                )
            else:
                workflow_info = await self.create_workflow_from_template(
                    task_id=task_id,
                    template=template,
                    parameters=parameters
                )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(workflow_info, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error creating workflow from template: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_get_container_status(self, args):
        """Handle the get_container_status tool."""
        container_id = args.get("container_id")
        if not container_id:
            raise McpError(ErrorCode.InvalidParams, "container_id is required")
        
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Get container status with circuit breaker if enabled
            if use_circuit_breaker:
                container_info = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._get_container_info(container_id)
                )
            else:
                container_info = await self._get_container_info(container_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(container_info, indent=2)
                    }
                ]
            }
        except ValueError as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(e)
                    }
                ],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting container status: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_get_container_logs_tool(self, args):
        """Handle the get_container_logs tool."""
        container_id = args.get("container_id")
        if not container_id:
            raise McpError(ErrorCode.InvalidParams, "container_id is required")
        
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Get container logs with circuit breaker if enabled
            if use_circuit_breaker:
                logs = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._get_container_logs(container_id)
                )
            else:
                logs = await self._get_container_logs(container_id)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": logs
                    }
                ]
            }
        except ValueError as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(e)
                    }
                ],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error getting container logs: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_restart_container(self, args):
        """Handle the restart_container tool."""
        container_id = args.get("container_id")
        if not container_id:
            raise McpError(ErrorCode.InvalidParams, "container_id is required")
        
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Check if container exists
            if container_id not in self.container_registry:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Container not found: {container_id}"
                        }
                    ],
                    "isError": True
                }
            
            # Restart container with circuit breaker if enabled
            if use_circuit_breaker:
                # First unregister the container
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.unregister_container(
                        container_id=container_id,
                        use_circuit_breaker=True
                    )
                )
                
                # Then register it again with the same capabilities
                capabilities = self.container_registry[container_id].get("capabilities", {})
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.register_container(
                        container_id=container_id,
                        capabilities=capabilities,
                        use_circuit_breaker=True
                    )
                )
            else:
                # First unregister the container
                await self.communication_manager.unregister_container(
                    container_id=container_id,
                    use_circuit_breaker=False
                )
                
                # Then register it again with the same capabilities
                capabilities = self.container_registry[container_id].get("capabilities", {})
                await self.communication_manager.register_container(
                    container_id=container_id,
                    capabilities=capabilities,
                    use_circuit_breaker=False
                )
            
            # Update container status in registry
            self.container_registry[container_id]["restarted_at"] = datetime.now().isoformat()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Container {container_id} restarted successfully"
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error restarting container: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_execute_container_command(self, args):
        """Handle the execute_container_command tool."""
        container_id = args.get("container_id")
        if not container_id:
            raise McpError(ErrorCode.InvalidParams, "container_id is required")
        
        command = args.get("command")
        if not command:
            raise McpError(ErrorCode.InvalidParams, "command is required")
        
        use_circuit_breaker = args.get("use_circuit_breaker", True)
        
        try:
            # Check if container exists
            if container_id not in self.container_registry:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Container not found: {container_id}"
                        }
                    ],
                    "isError": True
                }
            
            # Execute command with circuit breaker if enabled
            if use_circuit_breaker:
                # Send a message to the container with the command
                message_id = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.send_message(
                        sender_id="dagger_workflow_integration",
                        message_type="direct",
                        content={"command": command},
                        recipient_id=container_id,
                        priority="high",
                        use_circuit_breaker=True
                    )
                )
                
                # Wait for a response (in a real implementation, this would be more sophisticated)
                await asyncio.sleep(1)
                
                # Get the response
                messages = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.get_messages(
                        container_id="dagger_workflow_integration",
                        use_circuit_breaker=True
                    )
                )
                
                # Find the response message
                response = None
                for message in messages:
                    if message.get("sender_id") == container_id and message.get("correlation_id") == message_id:
                        response = message.get("content", {}).get("result", "No result")
                        break
                
                if response is None:
                    response = f"Command executed, but no response received from container {container_id}"
            else:
                # Send a message to the container with the command
                message_id = await self.communication_manager.send_message(
                    sender_id="dagger_workflow_integration",
                    message_type="direct",
                    content={"command": command},
                    recipient_id=container_id,
                    priority="high",
                    use_circuit_breaker=False
                )
                
                # Wait for a response (in a real implementation, this would be more sophisticated)
                await asyncio.sleep(1)
                
                # Get the response
                messages = await self.communication_manager.get_messages(
                    container_id="dagger_workflow_integration",
                    use_circuit_breaker=False
                )
                
                # Find the response message
                response = None
                for message in messages:
                    if message.get("sender_id") == container_id and message.get("correlation_id") == message_id:
                        response = message.get("content", {}).get("result", "No result")
                        break
                
                if response is None:
                    response = f"Command executed, but no response received from container {container_id}"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing command in container: {str(e)}"
                    }
                ],
                "isError": True
            }
