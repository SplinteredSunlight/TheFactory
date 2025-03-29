# Dagger Workflow Integration for Task Management MCP Server

This document provides an overview of the Dagger Workflow Integration feature for the Task Management MCP Server component of the AI-Orchestration-Platform.

## Overview

The Dagger Workflow Integration extends the Task Management MCP Server with Dagger workflow capabilities, allowing tasks to be executed as containerized workflows using Dagger.io. This integration enables:

- Creating and executing Dagger workflows for tasks
- Managing workflow templates
- Monitoring workflow execution status
- Executing workflows for entire projects

## Architecture

The integration consists of the following components:

1. **DaggerWorkflowIntegration**: Main class that integrates with the MCP server
2. **WorkflowTemplateRegistry**: Manages workflow templates
3. **TaskWorkflowIntegration**: Handles the interaction with Dagger

## Features

### MCP Resources

The integration exposes the following MCP resources:

- `task-manager://dagger/workflows`: List of all Dagger workflows
- `task-manager://dagger/stats`: Statistics for Dagger workflows
- `task-manager://dagger/templates`: List of available workflow templates
- `task-manager://dagger/workflows/{task_id}`: Dagger workflow information for a specific task
- `task-manager://dagger/projects/{project_id}/workflows`: Dagger workflows for all tasks in a project
- `task-manager://dagger/templates/{template_id}`: Details of a specific workflow template
- `task-manager://dagger/templates/category/{category}`: List of workflow templates in a specific category

### MCP Tools

The integration provides the following MCP tools:

- `create_workflow_from_task`: Create a Dagger workflow from a task
- `execute_task_workflow`: Execute a Dagger workflow for a task
- `get_workflow_status`: Get the status of a Dagger workflow for a task
- `create_workflows_for_project`: Create Dagger workflows for all tasks in a project
- `execute_workflows_for_project`: Execute Dagger workflows for all tasks in a project
- `list_workflow_templates`: List available workflow templates
- `get_workflow_template`: Get details of a specific workflow template
- `create_workflow_from_template`: Create a workflow from a template

## Usage Examples

### Creating a Workflow from a Task

```python
result = await mcp_client.call_tool(
    server_name="task_manager",
    tool_name="create_workflow_from_task",
    arguments={
        "task_id": "task-123",
        "workflow_name": "My Workflow"
    }
)
```

### Executing a Workflow

```python
result = await mcp_client.call_tool(
    server_name="task_manager",
    tool_name="execute_task_workflow",
    arguments={
        "task_id": "task-123",
        "workflow_type": "containerized_workflow",
        "skip_cache": False
    }
)
```

### Creating a Workflow from a Template

```python
result = await mcp_client.call_tool(
    server_name="task_manager",
    tool_name="create_workflow_from_template",
    arguments={
        "task_id": "task-123",
        "template_id": "ml-training",
        "parameters": {
            "epochs": 10,
            "batch_size": 32
        }
    }
)
```

## Workflow Templates

Workflow templates provide reusable workflow definitions that can be applied to tasks. Templates can be categorized and parameterized to support different use cases.

### Template Structure

A workflow template includes:

- ID: Unique identifier
- Name: Human-readable name
- Description: Detailed description
- Category: Optional category for organization
- Parameters: Definition of parameters that can be customized
- Definition: The actual workflow definition

## Integration with Dashboard

The Dagger Workflow Integration includes integration with the dashboard, allowing users to:

- View workflow status
- Start/stop workflows
- Monitor workflow execution
- View workflow statistics

## Configuration

The integration can be configured through the following settings:

- `dagger_config_path`: Path to the Dagger configuration file
- `templates_dir`: Directory to load workflow templates from

## Testing

The integration includes comprehensive tests to ensure reliability:

- Unit tests for individual components
- Integration tests for the entire workflow
- Mock tests for testing without actual Dagger execution

## Future Enhancements

Planned enhancements for the Dagger Workflow Integration include:

- Enhanced caching mechanisms
- Parallel workflow execution
- Workflow dependency management
- Advanced workflow monitoring and visualization
- Integration with external CI/CD systems
