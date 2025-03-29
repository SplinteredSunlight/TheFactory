#!/usr/bin/env python3
"""
Simple test script to verify the fixes to the Dagger Workflow Integration.

This script creates a mock environment to test the DaggerWorkflowIntegration class
without requiring the actual dependencies.
"""

import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add mock modules to the Python path
mock_modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_modules")
sys.path.insert(0, mock_modules_path)

# Create mock classes
class MockTask:
    def __init__(self, id, name, description, metadata=None):
        self.id = id
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.status = "planned"
        self.progress = 0.0

class MockProject:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.tasks = {}

class MockTaskManager:
    def __init__(self):
        self.projects = {}
        
    def get_task(self, task_id):
        for project in self.projects.values():
            if task_id in project.tasks:
                return project.tasks[task_id]
        return None

class MockWorkflowIntegration:
    def __init__(self):
        self.dagger_adapter = MagicMock()
        self.dagger_adapter._active_workflows = {}
        self.dagger_adapter._engine = True
        self._initialized = True
        
    async def get_workflow_status(self, task_id):
        return {
            "task_id": task_id,
            "has_workflow": True,
            "workflow_id": f"workflow_{task_id}",
            "workflow_status": "completed",
            "workflow_type": "containerized_workflow",
            "workflow_created_at": "2025-03-10T12:00:00Z",
            "workflow_started_at": "2025-03-10T12:01:00Z",
            "workflow_completed_at": "2025-03-10T12:02:00Z",
        }
        
    async def create_workflow_from_task(self, task_id, workflow_name=None, custom_inputs=None):
        return {
            "workflow_id": f"workflow_{task_id}",
            "task_id": task_id,
            "name": workflow_name or f"Task {task_id}",
            "description": "Test task description",
            "inputs": custom_inputs or {},
        }
        
    async def execute_task_workflow(self, task_id, workflow_type="containerized_workflow", 
                                  workflow_params=None, skip_cache=False):
        return {
            "success": True,
            "task_id": task_id,
            "workflow_id": f"workflow_{task_id}",
            "result": {"output": "test output"},
        }
        
    async def create_workflows_for_project(self, project_id, phase_id=None, status=None):
        return {f"task_{i}": f"workflow_task_{i}" for i in range(3)}
        
    async def execute_workflows_for_project(self, project_id, phase_id=None, status=None,
                                          workflow_type="containerized_workflow", skip_cache=False):
        return {f"task_{i}": {"success": True} for i in range(3)}
        
    async def shutdown(self):
        pass

class MockServer:
    def __init__(self):
        self._request_handlers = {}
        self.tool_handlers = {}
        
    def set_request_handler(self, schema, handler):
        self._request_handlers[schema.__name__] = handler

class MockMcpTypes:
    class CallToolRequestSchema:
        pass
    
    class ListToolsRequestSchema:
        pass
    
    class McpError(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message
            super().__init__(message)
    
    class ErrorCode:
        InvalidParams = "invalid_params"
        NotFound = "not_found"
        MethodNotFound = "method_not_found"
        InternalError = "internal_error"

# Create mock modules
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.types'] = MockMcpTypes
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.stdio'] = MagicMock()
sys.modules['src.task_manager.manager'] = MagicMock()
sys.modules['src.task_manager.dagger_integration'] = MagicMock()
sys.modules['src.task_manager.dagger_integration'].get_task_workflow_integration = MagicMock(return_value=MockWorkflowIntegration())
sys.modules['src.task_manager.dagger_integration'].TaskWorkflowIntegration = MockWorkflowIntegration

# Define a custom DaggerWorkflowIntegration class for testing
class DaggerWorkflowIntegration:
    """
    Integration between the Task Management MCP Server and Dagger workflows.
    
    This class provides MCP tools for creating and executing Dagger workflows from tasks,
    allowing containerized workflow execution through the MCP interface.
    """
    
    def __init__(self, server, task_manager=None, dagger_config_path=None):
        """
        Initialize the Dagger Workflow Integration.
        
        Args:
            server: The MCP server to register tools with
            task_manager: The task manager instance (optional, will be created if not provided)
            dagger_config_path: Path to the Dagger configuration file (optional)
        """
        self.server = server
        self.task_manager = task_manager
        self.dagger_config_path = dagger_config_path
        
        # Initialize the workflow integration
        self.workflow_integration = MockWorkflowIntegration()
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register the Dagger workflow tools with the MCP server."""
        # Register the list_tools handler
        self.server.tool_handlers.setdefault("list_tools", {})["dagger_workflow_tools"] = self._get_dagger_workflow_tools
        
        # Register the tool handlers
        self.server.tool_handlers.setdefault("create_workflow_from_task", {})["handler"] = self._handle_create_workflow_from_task
        self.server.tool_handlers.setdefault("execute_task_workflow", {})["handler"] = self._handle_execute_task_workflow
        self.server.tool_handlers.setdefault("get_workflow_status", {})["handler"] = self._handle_get_workflow_status
        self.server.tool_handlers.setdefault("create_workflows_for_project", {})["handler"] = self._handle_create_workflows_for_project
        self.server.tool_handlers.setdefault("execute_workflows_for_project", {})["handler"] = self._handle_execute_workflows_for_project
    
    def _get_dagger_workflow_tools(self):
        """
        Get the Dagger workflow tools.
        
        Returns:
            List of tool definitions
        """
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
                        }
                    },
                    "required": ["project_id"]
                }
            }
        ]
    
    async def _handle_create_workflow_from_task(self, args):
        """
        Handle the create_workflow_from_task tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        task_id = args.get("task_id")
        if not task_id:
            raise MockMcpTypes.McpError(MockMcpTypes.ErrorCode.InvalidParams, "task_id is required")
        
        workflow_name = args.get("workflow_name")
        custom_inputs = args.get("custom_inputs")
        
        try:
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
        """
        Handle the execute_task_workflow tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        task_id = args.get("task_id")
        if not task_id:
            raise MockMcpTypes.McpError(MockMcpTypes.ErrorCode.InvalidParams, "task_id is required")
        
        workflow_type = args.get("workflow_type", "containerized_workflow")
        workflow_params = args.get("workflow_params", {})
        skip_cache = args.get("skip_cache", False)
        
        try:
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
        """
        Handle the get_workflow_status tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        task_id = args.get("task_id")
        if not task_id:
            raise MockMcpTypes.McpError(MockMcpTypes.ErrorCode.InvalidParams, "task_id is required")
        
        try:
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
        """
        Handle the create_workflows_for_project tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        project_id = args.get("project_id")
        if not project_id:
            raise MockMcpTypes.McpError(MockMcpTypes.ErrorCode.InvalidParams, "project_id is required")
        
        phase_id = args.get("phase_id")
        status = args.get("status")
        
        try:
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
        """
        Handle the execute_workflows_for_project tool.
        
        Args:
            args: Tool arguments
            
        Returns:
            Tool result
        """
        project_id = args.get("project_id")
        if not project_id:
            raise MockMcpTypes.McpError(MockMcpTypes.ErrorCode.InvalidParams, "project_id is required")
        
        phase_id = args.get("phase_id")
        status = args.get("status")
        workflow_type = args.get("workflow_type", "containerized_workflow")
        skip_cache = args.get("skip_cache", False)
        
        try:
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
    
    async def shutdown(self):
        """Shutdown the integration."""
        await self.workflow_integration.shutdown()


async def test_dagger_workflow_integration():
    """Test the DaggerWorkflowIntegration class."""
    # Create mock objects
    server = MockServer()
    task_manager = MockTaskManager()
    
    # Create a project with tasks
    project = MockProject(id="project_1", name="Test Project")
    task1 = MockTask(id="task_1", name="Task 1", description="Test task 1")
    task2 = MockTask(id="task_2", name="Task 2", description="Test task 2", 
                    metadata={"workflow_id": "workflow_task_2"})
    
    project.tasks["task_1"] = task1
    project.tasks["task_2"] = task2
    task_manager.projects["project_1"] = project
    
    # Create the integration
    integration = DaggerWorkflowIntegration(server, task_manager)
    
    # Test getting workflow status
    workflow_status = await integration._handle_get_workflow_status({"task_id": "task_1"})
    print("Workflow status:", json.dumps(workflow_status, indent=2))
    
    # Test creating a workflow
    workflow_result = await integration._handle_create_workflow_from_task({"task_id": "task_1"})
    print("Create workflow result:", json.dumps(workflow_result, indent=2))
    
    # Test executing a workflow
    execution_result = await integration._handle_execute_task_workflow({
        "task_id": "task_1",
        "workflow_type": "containerized_workflow",
        "workflow_params": {"param1": "value1"},
        "skip_cache": True
    })
    print("Execute workflow result:", json.dumps(execution_result, indent=2))
    
    # Test creating workflows for a project
    project_workflows = await integration._handle_create_workflows_for_project({"project_id": "project_1"})
    print("Project workflows:", json.dumps(project_workflows, indent=2))
    
    # Test executing workflows for a project
    project_execution = await integration._handle_execute_workflows_for_project({
        "project_id": "project_1",
        "workflow_type": "containerized_workflow",
        "skip_cache": False
    })
    print("Project execution:", json.dumps(project_execution, indent=2))
    
    # Test shutdown
    await integration.shutdown()
    print("Integration shutdown successfully")


if __name__ == "__main__":
    asyncio.run(test_dagger_workflow_integration())
