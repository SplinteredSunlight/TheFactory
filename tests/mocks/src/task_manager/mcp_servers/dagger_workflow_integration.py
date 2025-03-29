#!/usr/bin/env python3
"""
Dagger Workflow Integration for Task Management MCP Server (Mock Module)

This module extends the Task Manager MCP Server with Dagger workflow capabilities,
allowing tasks to be executed as containerized workflows using Dagger.io.
"""

import asyncio
import json
import os
import sys
import logging
from typing import Dict, List, Optional, Any, Union

# Mock MCP types
class ErrorCode:
    InvalidRequest = "InvalidRequest"
    NotFound = "NotFound"
    InvalidParams = "InvalidParams"
    MethodNotFound = "MethodNotFound"
    InternalError = "InternalError"

class McpError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

# Mock classes for testing
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60, half_open_timeout=30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = None

class CircuitBreakerOpenError(Exception):
    pass

def get_circuit_breaker(name, failure_threshold=5, reset_timeout=60, half_open_timeout=30):
    return CircuitBreaker(failure_threshold, reset_timeout, half_open_timeout)

async def execute_with_circuit_breaker(circuit_breaker, func):
    if circuit_breaker.state == "open":
        raise CircuitBreakerOpenError("Circuit breaker is open")
    try:
        result = await func()
        return result
    except Exception as e:
        circuit_breaker.failures += 1
        if circuit_breaker.failures >= circuit_breaker.failure_threshold:
            circuit_breaker.state = "open"
        raise e

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
        self.workflow_integration = self._mock_workflow_integration()
        self.template_registry = self._mock_template_registry()
        
        # Get circuit breaker for MCP operations
        self.circuit_breaker = get_circuit_breaker("mcp_dagger_operations")
        
        # Set up Dagger workflow resources and tools
        self.setup_dagger_workflow_resources()
        self.setup_dagger_workflow_tools()
        
        # Log initialization
        logging.info("Dagger Workflow Integration initialized with config path: %s", dagger_config_path)

    def _mock_workflow_integration(self):
        """Create a mock workflow integration for testing."""
        class MockWorkflowIntegration:
            async def create_workflow_from_task(self, task_id, workflow_name=None, custom_inputs=None):
                return {
                    "workflow_id": f"workflow-{task_id}",
                    "task_id": task_id,
                    "name": workflow_name or f"Workflow for task {task_id}",
                    "status": "created",
                    "created_at": "2025-03-22T12:00:00Z"
                }
                
            async def execute_task_workflow(self, task_id, workflow_type="containerized_workflow", workflow_params=None, skip_cache=False):
                return {
                    "workflow_id": f"workflow-{task_id}",
                    "task_id": task_id,
                    "status": "completed",
                    "result": {"message": "Workflow executed successfully"},
                    "execution_time": 1.5
                }
                
            async def get_workflow_status(self, task_id):
                return {
                    "workflow_id": f"workflow-{task_id}",
                    "task_id": task_id,
                    "status": "completed",
                    "has_workflow": True,
                    "execution_time": 1.5
                }
                
            async def create_workflows_for_project(self, project_id, phase_id=None, status=None):
                return {
                    "project_id": project_id,
                    "workflows_created": 5,
                    "phase_id": phase_id,
                    "status": status
                }
                
            async def execute_workflows_for_project(self, project_id, phase_id=None, status=None, workflow_type="containerized_workflow", skip_cache=False):
                return {
                    "project_id": project_id,
                    "workflows_executed": 5,
                    "successful": 4,
                    "failed": 1,
                    "phase_id": phase_id,
                    "status": status
                }
                
            async def create_workflow_from_template(self, task_id, template, parameters=None):
                return {
                    "workflow_id": f"workflow-{task_id}",
                    "task_id": task_id,
                    "template_id": template.id if hasattr(template, "id") else "unknown",
                    "status": "created",
                    "created_at": "2025-03-22T12:00:00Z"
                }
        
        return MockWorkflowIntegration()
    
    def _mock_template_registry(self):
        """Create a mock template registry for testing."""
        class MockTemplate:
            def __init__(self, id, name, category, description):
                self.id = id
                self.name = name
                self.category = category
                self.description = description
                
            def to_dict(self):
                return {
                    "id": self.id,
                    "name": self.name,
                    "category": self.category,
                    "description": self.description
                }
        
        class MockTemplateRegistry:
            def __init__(self):
                self.templates = {
                    "template1": MockTemplate("template1", "Basic Workflow", "general", "A basic workflow template"),
                    "template2": MockTemplate("template2", "ML Training", "machine-learning", "A machine learning training workflow template"),
                    "template3": MockTemplate("template3", "Data Processing", "data", "A data processing workflow template")
                }
                
            def list_templates(self, category=None):
                if category:
                    return [t.to_dict() for t in self.templates.values() if t.category == category]
                return [t.to_dict() for t in self.templates.values()]
                
            def get_template(self, template_id):
                return self.templates.get(template_id)
                
            def get_categories(self):
                return list(set(t.category for t in self.templates.values()))
        
        return MockTemplateRegistry()

    def setup_dagger_workflow_resources(self):
        """Set up Dagger workflow resources for the MCP server."""
        # Mock implementation
        pass

    def setup_dagger_workflow_tools(self):
        """Set up Dagger workflow tools for the MCP server."""
        # Mock implementation
        pass
        
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
            
            # If we get here, the resource wasn't found
            raise McpError(ErrorCode.NotFound, f"Resource not found: {uri}")
        except Exception as e:
            if isinstance(e, McpError):
                raise
            logging.error(f"Error handling Dagger workflow resource: {e}")
            raise McpError(ErrorCode.InternalError, f"Internal error: {str(e)}")
        
    async def _get_all_workflows(self):
        """Get all Dagger workflows.
        
        Returns:
            Dict containing all workflows
        """
        workflows = {}
        
        # Mock implementation
        workflows["task-1"] = {
            "workflow_id": "workflow-task-1",
            "task_id": "task-1",
            "status": "completed",
            "has_workflow": True,
            "execution_time": 1.5
        }
        
        workflows["task-2"] = {
            "workflow_id": "workflow-task-2",
            "task_id": "task-2",
            "status": "in_progress",
            "has_workflow": True,
            "execution_time": 0.5
        }
        
        return workflows
        
    async def _get_workflow_stats(self):
        """Get Dagger workflow statistics.
        
        Returns:
            Dict containing workflow statistics
        """
        return {
            "total_workflows": 2,
            "completed_workflows": 1,
            "failed_workflows": 0,
            "in_progress_workflows": 1,
            "unknown_workflows": 0,
            "success_rate": 50.0
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
        if project_id not in ["project-1", "project-2"]:
            raise ValueError(f"Project not found: {project_id}")
            
        workflows = {}
        
        # Mock implementation
        if project_id == "project-1":
            workflows["task-1"] = {
                "workflow_id": "workflow-task-1",
                "task_id": "task-1",
                "status": "completed",
                "has_workflow": True,
                "execution_time": 1.5
            }
            
            workflows["task-2"] = {
                "workflow_id": "workflow-task-2",
                "task_id": "task-2",
                "status": "in_progress",
                "has_workflow": True,
                "execution_time": 0.5
            }
        else:
            workflows["task-3"] = {
                "workflow_id": "workflow-task-3",
                "task_id": "task-3",
                "status": "completed",
                "has_workflow": True,
                "execution_time": 2.0
            }
            
        return workflows

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
                    lambda: self.workflow_integration.create_workflow_from_template(
                        task_id=task_id,
                        template=template,
                        parameters=parameters
                    )
                )
            else:
                workflow_info = await self.workflow_integration.create_workflow_from_template(
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
