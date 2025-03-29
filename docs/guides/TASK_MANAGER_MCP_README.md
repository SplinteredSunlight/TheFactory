# Task Manager MCP Server

This guide explains how to use the Task Manager MCP Server in the AI-Orchestration-Platform.

## Overview

The Task Manager MCP Server provides task management capabilities as MCP tools and resources. It acts as a bridge between the Task Manager and MCP clients (including AI agents). The server now integrates with the new Dagger-based Task Management System, providing enhanced workflow capabilities.

## Features

- **Project Management**: Create, update, and delete projects
- **Phase Management**: Create and manage phases within projects
- **Task Management**: Create, update, delete, and query tasks
- **Workflow Integration**: Create and execute Dagger workflows for tasks
- **Container Management**: Manage Dagger containers for workflows
- **Template Support**: Use workflow templates for common task types
- **Dashboard Integration**: Visualize task and workflow status

## Architecture

The Task Manager MCP Server consists of several components:

1. **TaskManagerServer**: Main MCP server that provides task management capabilities
2. **DaggerWorkflowIntegration**: Integration with Dagger for workflow execution
3. **DashboardIntegration**: Integration with the dashboard for visualization
4. **TaskWorkflowIntegration**: Integration between tasks and Dagger workflows

## Installation

The Task Manager MCP Server is part of the AI-Orchestration-Platform. To use it, you need to have the platform installed.

```bash
# Clone the repository
git clone https://github.com/example/AI-Orchestration-Platform.git
cd AI-Orchestration-Platform

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
# Start the server with Dagger integration enabled
python -m src.task_manager.mcp_servers.task_manager_server --enable-dagger --dagger-config config/dagger.yaml
```

### Command-line Options

- `--data-dir`: Directory for task manager data
- `--auth-token`: Authentication token for API calls
- `--dagger-config`: Path to Dagger configuration file
- `--enable-dagger`: Enable Dagger workflow integration

### Environment Variables

- `TASK_MANAGER_DAGGER_ENABLED`: Set to "1", "true", or "yes" to enable Dagger integration
- `TASK_MANAGER_DAGGER_CONFIG`: Path to Dagger configuration file
- `TASK_MANAGER_TEMPLATES_DIR`: Directory for workflow templates

## MCP Resources

The Task Manager MCP Server provides the following resources:

### Static Resources

- `task-manager://projects`: List of all projects
- `task-manager://status`: Current status of the task management system

### Resource Templates

- `task-manager://projects/{project_id}`: Information about a specific project
- `task-manager://projects/{project_id}/phases`: Phases in a specific project
- `task-manager://projects/{project_id}/tasks`: Tasks in a specific project
- `task-manager://tasks/{task_id}`: Information about a specific task

### Dagger Workflow Resources

- `task-manager://dagger/workflows`: List of all Dagger workflows
- `task-manager://dagger/stats`: Statistics for Dagger workflows
- `task-manager://dagger/templates`: List of available workflow templates
- `task-manager://dagger/containers`: List of all Dagger containers
- `task-manager://dagger/workflows/{task_id}`: Dagger workflow for a specific task
- `task-manager://dagger/projects/{project_id}/workflows`: Dagger workflows for a project
- `task-manager://dagger/templates/{template_id}`: Details of a specific workflow template
- `task-manager://dagger/templates/category/{category}`: Workflow templates by category
- `task-manager://dagger/containers/{container_id}`: Details of a specific container
- `task-manager://dagger/containers/{container_id}/logs`: Logs for a specific container
- `task-manager://dagger/workflows/{workflow_id}/containers`: Containers for a workflow

## MCP Tools

The Task Manager MCP Server provides the following tools:

### Project Management Tools

- `create_project`: Create a new project
- `update_project`: Update an existing project
- `delete_project`: Delete a project

### Phase Management Tools

- `create_phase`: Create a new phase in a project

### Task Management Tools

- `create_task`: Create a new task in a project
- `update_task`: Update an existing task
- `delete_task`: Delete a task
- `update_task_status`: Update the status of a task
- `update_task_progress`: Update the progress of a task

### Calculation Tools

- `calculate_project_progress`: Calculate the progress of a project
- `calculate_phase_progress`: Calculate the progress of a phase

### Query Tools

- `get_tasks_by_status`: Get all tasks with a specific status
- `get_tasks_by_assignee`: Get all tasks assigned to a specific assignee

### Dagger Workflow Tools

- `create_workflow_from_task`: Create a Dagger workflow from a task
- `execute_task_workflow`: Execute a Dagger workflow for a task
- `get_workflow_status`: Get the status of a Dagger workflow for a task
- `create_workflows_for_project`: Create Dagger workflows for all tasks in a project
- `execute_workflows_for_project`: Execute Dagger workflows for all tasks in a project
- `list_workflow_templates`: List available workflow templates
- `get_workflow_template`: Get details of a specific workflow template
- `create_workflow_from_template`: Create a workflow from a template

### Container Management Tools

- `get_container_status`: Get the status of a Dagger container
- `get_container_logs`: Get logs for a Dagger container
- `restart_container`: Restart a Dagger container
- `execute_container_command`: Execute a command in a Dagger container

## Example

Here's a simple example of how to use the Task Manager MCP Server:

```python
import asyncio
import json
from mcp.client import Client
from mcp.client.stdio import StdioClientTransport

async def main():
    # Create an MCP client
    client = Client()
    
    # Connect to the Task Management MCP Server
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "src.task_manager.mcp_servers.task_manager_server",
        "--enable-dagger",
        "--dagger-config", "config/dagger.yaml",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    
    # Create a transport for the client
    transport = StdioClientTransport(process.stdin, process.stdout)
    
    # Connect the client to the server
    await client.connect(transport)
    
    try:
        # Create a project
        project_result = await client.call_tool(
            "create_project",
            {
                "name": "Example Project",
                "description": "A project created by the example script",
            }
        )
        project = json.loads(project_result["content"][0]["text"])
        project_id = project["id"]
        
        # Create a task
        task_result = await client.call_tool(
            "create_task",
            {
                "name": "Example Task",
                "description": "A task created by the example script",
                "project_id": project_id,
                "status": "planned",
                "priority": "medium",
            }
        )
        task = json.loads(task_result["content"][0]["text"])
        task_id = task["id"]
        
        # Create a workflow from the task
        workflow_result = await client.call_tool(
            "create_workflow_from_task",
            {
                "task_id": task_id,
                "workflow_name": "Example Workflow",
            }
        )
        workflow = json.loads(workflow_result["content"][0]["text"])
        workflow_id = workflow["workflow_id"]
        
        # Execute the workflow
        execution_result = await client.call_tool(
            "execute_task_workflow",
            {
                "task_id": task_id,
                "workflow_type": "containerized_workflow",
            }
        )
        
    finally:
        # Disconnect from the server
        await client.close()
        
        # Terminate the server process
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(main())
```

For a more complete example, see `examples/task_management_mcp_example.py`.

## Integration with Dagger

The Task Manager MCP Server integrates with Dagger to provide workflow capabilities. This integration allows tasks to be executed as containerized workflows using Dagger.io.

### Workflow Creation

```python
# Create a workflow from a task
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
```

### Workflow Execution

```python
# Execute a workflow for a task
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
```

### Workflow Status

```python
# Get workflow status
status_result = await client.call_tool(
    "get_workflow_status",
    {
        "task_id": task_id
    }
)
```

### Workflow Templates

```python
# List available workflow templates
templates_result = await client.call_tool(
    "list_workflow_templates",
    {}
)

# Create a workflow from a template
workflow_result = await client.call_tool(
    "create_workflow_from_template",
    {
        "task_id": task_id,
        "template_id": template_id,
        "parameters": {
            "example_param": "example_value"
        }
    }
)
```

## Troubleshooting

### Common Issues

- **Server Fails to Start**: Check that the Dagger configuration file exists and is valid.
- **Workflow Creation Fails**: Check that the task exists and has the required metadata.
- **Workflow Execution Fails**: Check the error message in the result. Common issues include missing dependencies or invalid parameters.
- **Container Creation Fails**: Check that the container image exists and is accessible.
- **Container Start Fails**: Check that the container was created successfully and that the Dagger adapter is initialized.
- **Pipeline Conversion Fails**: Check that the template exists and that the task has the required metadata.

### Logging

The Task Manager MCP Server uses Python's logging module to log information about its operations. You can configure the logging level to get more or less information.

```python
import logging

# Set logging level for the server
logging.getLogger("src.task_manager.mcp_servers").setLevel(logging.DEBUG)
```

## API Reference

For a complete API reference, see the [API documentation](../api-contracts/dagger-api.yaml).
