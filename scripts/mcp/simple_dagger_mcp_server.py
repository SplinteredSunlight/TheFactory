#!/usr/bin/env python3
"""
Simple Dagger MCP Server

This script creates a simple MCP server that provides the Dagger Workflow Integration tools.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the project root and mock modules to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
mock_modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_modules")
sys.path.insert(0, mock_modules_path)

# Import MCP server components
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListToolsRequestSchema,
    McpError,
)

# Import the task manager and workflow integration
from mock_modules.src.task_manager.manager import get_task_manager, TaskManager
from mock_modules.src.task_manager.dagger_integration import get_task_workflow_integration, TaskWorkflowIntegration


class SimpleDaggerMcpServer:
    """Simple MCP server that provides Dagger Workflow Integration tools."""
    
    def __init__(self, data_dir=None, dagger_config_path=None):
        """Initialize the server."""
        self.server = Server(
            {
                "name": "dagger-workflow",
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
        self.task_manager = TaskManager(data_dir)
        
        # Initialize the workflow integration
        self.workflow_integration = TaskWorkflowIntegration(dagger_config_path)
        self.workflow_integration.task_manager = self.task_manager
        
        # Set up request handlers
        self.server.set_request_handler(ListToolsRequestSchema, self._handle_list_tools)
        self.server.set_request_handler(CallToolRequestSchema, self._handle_call_tool)
        
        # Error handling
        self.server.onerror = lambda error: print(f"[MCP Error] {error}", file=sys.stderr)
    
    async def _handle_list_tools(self, request):
        """Handle listing available tools."""
        return {
            "tools": [
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
                },
                # Task management tools for testing
                {
                    "name": "create_project",
                    "description": "Create a new project for testing",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the project"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the project"
                            }
                        },
                        "required": ["name"]
                    }
                },
                {
                    "name": "create_task",
                    "description": "Create a new task for testing",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the task"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the task"
                            },
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project"
                            }
                        },
                        "required": ["name", "description", "project_id"]
                    }
                }
            ]
        }
    
    async def _handle_call_tool(self, request):
        """Handle calling tools."""
        tool_name = request.params.name
        args = request.params.arguments
        
        try:
            # Dagger Workflow Integration tools
            if tool_name == "create_workflow_from_task":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                
                # Call the workflow integration
                result = await self.workflow_integration.create_workflow_from_task(
                    task_id=args["task_id"],
                    workflow_name=args.get("workflow_name"),
                    custom_inputs=args.get("custom_inputs"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "execute_task_workflow":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                
                # Call the workflow integration
                result = await self.workflow_integration.execute_task_workflow(
                    task_id=args["task_id"],
                    workflow_type=args.get("workflow_type", "containerized_workflow"),
                    workflow_params=args.get("workflow_params"),
                    skip_cache=args.get("skip_cache", False),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "get_workflow_status":
                # Validate required arguments
                if "task_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: task_id",
                    )
                
                # Call the workflow integration
                result = await self.workflow_integration.get_workflow_status(
                    task_id=args["task_id"],
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "create_workflows_for_project":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                
                # Call the workflow integration
                result = await self.workflow_integration.create_workflows_for_project(
                    project_id=args["project_id"],
                    phase_id=args.get("phase_id"),
                    status=args.get("status"),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            elif tool_name == "execute_workflows_for_project":
                # Validate required arguments
                if "project_id" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: project_id",
                    )
                
                # Call the workflow integration
                result = await self.workflow_integration.execute_workflows_for_project(
                    project_id=args["project_id"],
                    phase_id=args.get("phase_id"),
                    status=args.get("status"),
                    workflow_type=args.get("workflow_type", "containerized_workflow"),
                    skip_cache=args.get("skip_cache", False),
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                }
            
            # Task management tools for testing
            elif tool_name == "create_project":
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
        print("Simple Dagger MCP server running on stdio", file=sys.stderr)
    
    async def shutdown(self):
        """Shutdown the MCP server."""
        # Shutdown the workflow integration
        await self.workflow_integration.shutdown()
        
        # Close the server
        await self.server.close()


async def main():
    """Run the Simple Dagger MCP server."""
    # Set up environment variables
    data_dir = os.environ.get("TASK_MANAGER_DATA_DIR")
    dagger_config_path = os.environ.get("TASK_MANAGER_DAGGER_CONFIG")
    
    # Create and run the server
    server = SimpleDaggerMcpServer(
        data_dir=data_dir,
        dagger_config_path=dagger_config_path,
    )
    
    try:
        await server.run()
    except KeyboardInterrupt:
        print("Shutting down...", file=sys.stderr)
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
