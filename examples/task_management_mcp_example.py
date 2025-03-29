#!/usr/bin/env python3
"""
Task Management MCP Server Example

This example demonstrates how to use the Task Management MCP Server
with the new Dagger-based Task Management System.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.client import Client
from mcp.client.stdio import StdioClientTransport
from mcp.types import McpError


async def main():
    """Run the example."""
    # Create an MCP client
    client = Client()
    
    # Connect to the Task Management MCP Server
    # Note: This assumes the server is already running
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "src.task_manager.mcp_servers.task_manager_server",
        "--enable-dagger",
        "--dagger-config", "config/dagger.yaml",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    # Create a transport for the client
    transport = StdioClientTransport(process.stdin, process.stdout)
    
    # Connect the client to the server
    await client.connect(transport)
    print("Connected to Task Management MCP Server")
    
    try:
        # List available resources
        resources = await client.list_resources()
        print("\nAvailable Resources:")
        for resource in resources["resources"]:
            print(f"- {resource['name']}: {resource['uri']}")
        
        # List available tools
        tools = await client.list_tools()
        print("\nAvailable Tools:")
        for tool in tools["tools"]:
            print(f"- {tool['name']}: {tool['description']}")
        
        # Create a project
        print("\nCreating a project...")
        project_result = await client.call_tool(
            "create_project",
            {
                "name": "Example Project",
                "description": "A project created by the example script",
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "example_script",
                }
            }
        )
        project = json.loads(project_result["content"][0]["text"])
        project_id = project["id"]
        print(f"Created project with ID: {project_id}")
        
        # Create a phase
        print("\nCreating a phase...")
        phase_result = await client.call_tool(
            "create_phase",
            {
                "project_id": project_id,
                "name": "Example Phase",
                "description": "A phase created by the example script",
                "order": 0,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "example_script",
                }
            }
        )
        phase = json.loads(phase_result["content"][0]["text"])
        phase_id = phase["id"]
        print(f"Created phase with ID: {phase_id}")
        
        # Create a task
        print("\nCreating a task...")
        task_result = await client.call_tool(
            "create_task",
            {
                "name": "Example Task",
                "description": "A task created by the example script",
                "project_id": project_id,
                "phase_id": phase_id,
                "status": "planned",
                "priority": "medium",
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "example_script",
                }
            }
        )
        task = json.loads(task_result["content"][0]["text"])
        task_id = task["id"]
        print(f"Created task with ID: {task_id}")
        
        # List available Dagger workflow templates
        print("\nListing Dagger workflow templates...")
        templates_result = await client.call_tool(
            "list_workflow_templates",
            {}
        )
        templates = json.loads(templates_result["content"][0]["text"])
        print(f"Available templates: {', '.join([t['name'] for t in templates['templates']])}")
        
        # Create a workflow from the task
        print("\nCreating a workflow from the task...")
        workflow_result = await client.call_tool(
            "create_workflow_from_task",
            {
                "task_id": task_id,
                "workflow_name": "Example Workflow",
                "custom_inputs": {
                    "example_param": "example_value"
                }
            }
        )
        workflow = json.loads(workflow_result["content"][0]["text"])
        workflow_id = workflow["workflow_id"]
        print(f"Created workflow with ID: {workflow_id}")
        
        # Get workflow status
        print("\nGetting workflow status...")
        status_result = await client.call_tool(
            "get_workflow_status",
            {
                "task_id": task_id
            }
        )
        status = json.loads(status_result["content"][0]["text"])
        print(f"Workflow status: {status['workflow_status']}")
        
        # Execute the workflow
        print("\nExecuting the workflow...")
        execution_result = await client.call_tool(
            "execute_task_workflow",
            {
                "task_id": task_id,
                "workflow_type": "containerized_workflow",
                "workflow_params": {
                    "example_param": "example_value"
                }
            }
        )
        execution = json.loads(execution_result["content"][0]["text"])
        print(f"Workflow execution result: {execution['success']}")
        
        # Get workflow status again
        print("\nGetting workflow status after execution...")
        status_result = await client.call_tool(
            "get_workflow_status",
            {
                "task_id": task_id
            }
        )
        status = json.loads(status_result["content"][0]["text"])
        print(f"Workflow status: {status['workflow_status']}")
        
        # Get task status
        print("\nGetting task status...")
        task_status_result = await client.read_resource(f"task-manager://tasks/{task_id}")
        task_status = json.loads(task_status_result["contents"][0]["text"])
        print(f"Task status: {task_status['status']}")
        
        # Clean up
        print("\nCleaning up...")
        await client.call_tool(
            "delete_task",
            {
                "task_id": task_id
            }
        )
        await client.call_tool(
            "delete_project",
            {
                "project_id": project_id
            }
        )
        print("Cleanup complete")
        
    except McpError as e:
        print(f"MCP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from the server
        await client.close()
        
        # Terminate the server process
        process.terminate()
        await process.wait()
        
        print("\nDisconnected from Task Management MCP Server")


if __name__ == "__main__":
    asyncio.run(main())
