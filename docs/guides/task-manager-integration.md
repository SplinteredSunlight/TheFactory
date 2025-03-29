# Task Manager Integration with Dagger

This guide explains how to use the Task Manager Integration with Dagger in the AI-Orchestration-Platform.

## Overview

The Task Manager Integration provides a bridge between the task management system and Dagger workflows. It allows tasks to be executed as containerized workflows and updates task status based on workflow results. The integration includes container management, pipeline conversion, and advanced status tracking.

## Features

- **Workflow Creation**: Create Dagger workflows from tasks
- **Workflow Execution**: Execute workflows for tasks
- **Container Management**: Create, start, stop, and delete containers
- **Pipeline Conversion**: Convert tasks to Dagger pipelines
- **Status Tracking**: Track workflow status with detailed state management
- **Result Handling**: Process and store workflow execution results
- **Caching**: Cache workflow executions for improved performance

## Architecture

The Task Manager Integration consists of several components:

1. **TaskWorkflowIntegration**: Main class that integrates Dagger workflows with the task management system
2. **PipelineConverter**: Converts tasks to Dagger pipelines
3. **WorkflowStatusManager**: Tracks workflow status with detailed state management
4. **ResultProcessor**: Processes and stores workflow execution results
5. **WorkflowCacheManager**: Caches workflow executions for improved performance

## Usage

### Initialization

```python
from src.task_manager.dagger_integration import get_task_workflow_integration

# Get a TaskWorkflowIntegration instance
integration = get_task_workflow_integration(
    dagger_config_path="config/dagger.yaml",
    templates_dir="templates/pipelines"
)
```

### Creating a Workflow from a Task

```python
# Create a workflow from a task
workflow_info = await integration.create_workflow_from_task(
    task_id="task-123",
    workflow_name="My Workflow",
    custom_inputs={"param1": "value1"}
)

print(f"Created workflow: {workflow_info['workflow_id']}")
```

### Executing a Workflow

```python
# Execute a workflow for a task
result = await integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={"param1": "value1"},
    skip_cache=False
)

if result["success"]:
    print(f"Workflow executed successfully: {result['result']}")
else:
    print(f"Workflow execution failed: {result['error']}")
```

### Container Management

```python
# Create a container
container = await integration.create_container(
    workflow_id="workflow-123",
    container_image="alpine:latest",
    container_name="my-container",
    environment={"VAR1": "value1"},
    volumes=[{"source": "/tmp", "target": "/data"}],
    command=["echo", "Hello, World!"]
)

# Start the container
await integration.start_container(container["container_id"])

# Get container logs
logs = await integration.get_container_logs(container["container_id"])
print(logs)

# Stop the container
await integration.stop_container(container["container_id"])

# Delete the container
await integration.delete_container(container["container_id"])
```

### Pipeline Conversion

```python
# Convert a task to a pipeline using a template
pipeline = await integration.convert_task_to_pipeline(
    task_id="task-123",
    template_id="template-123",
    parameters={"param1": "value1"}
)

# Create a custom pipeline
pipeline_definition = {
    "steps": [
        {"name": "step1", "command": "echo 'Hello, World!'"}
    ]
}

pipeline = await integration.create_custom_pipeline(
    task_id="task-123",
    pipeline_definition=pipeline_definition
)
```

### Workflow Status

```python
# Get workflow status
status = await integration.get_workflow_status("task-123")
print(f"Workflow status: {status['workflow_status']}")
```

## Advanced Features

### Batch Operations

```python
# Create workflows for all tasks in a project
workflow_ids = await integration.create_workflows_for_project(
    project_id="project-123",
    phase_id="phase-1",
    status="pending"
)

# Execute workflows for all tasks in a project
results = await integration.execute_workflows_for_project(
    project_id="project-123",
    phase_id="phase-1",
    status="pending",
    workflow_type="containerized_workflow"
)
```

### Pipeline Templates

The integration supports pipeline templates for common task types. Templates are stored in the `templates/pipelines` directory and can be used to generate pipelines for tasks.

```python
# List available pipeline templates
templates = await integration.list_pipeline_templates()

# Get a pipeline template
template = await integration.get_pipeline_template("template-123")

# Get pipeline template categories
categories = await integration.get_pipeline_template_categories()
```

### Caching

The integration supports caching of workflow executions for improved performance. Caching can be enabled or disabled for individual workflow executions.

```python
# Execute a workflow with caching
result = await integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={"param1": "value1"},
    skip_cache=False
)

# Execute a workflow without caching
result = await integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={"param1": "value1"},
    skip_cache=True
)
```

## Error Handling

The integration uses circuit breakers to protect against cascading failures. Circuit breakers can be enabled or disabled for individual operations.

```python
# Execute a workflow with circuit breaker protection
result = await integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={"use_circuit_breaker": True}
)

# Execute a workflow without circuit breaker protection
result = await integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={"use_circuit_breaker": False}
)
```

## Configuration

The integration can be configured using a YAML configuration file. The configuration file should be passed to the `get_task_workflow_integration` function.

Example configuration file:

```yaml
# Dagger configuration
container_registry: "docker.io"
container_credentials:
  username: "username"
  password: "password"
workflow_directory: "workflows"
workflow_defaults:
  timeout_seconds: 600
  max_retries: 3
  retry_backoff_factor: 0.5
  retry_jitter: true
  caching_enabled: true
  cache_directory: ".dagger_cache"
  cache_ttl_seconds: 3600
```

## Shutdown

When you're done using the integration, you should shut it down to release resources.

```python
await integration.shutdown()
```

## Troubleshooting

### Common Issues

- **Workflow Creation Fails**: Check that the task exists and has the required metadata.
- **Workflow Execution Fails**: Check the error message in the result. Common issues include missing dependencies or invalid parameters.
- **Container Creation Fails**: Check that the container image exists and is accessible.
- **Container Start Fails**: Check that the container was created successfully and that the Dagger adapter is initialized.
- **Pipeline Conversion Fails**: Check that the template exists and that the task has the required metadata.

### Logging

The integration uses Python's logging module to log information about its operations. You can configure the logging level to get more or less information.

```python
import logging

# Set logging level for the integration
logging.getLogger("src.task_manager.dagger_integration").setLevel(logging.DEBUG)
```

## API Reference

For a complete API reference, see the [API documentation](../api-contracts/dagger-api.yaml).
