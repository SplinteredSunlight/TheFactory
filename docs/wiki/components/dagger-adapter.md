# Dagger Adapter

## Purpose
The Dagger Adapter provides integration between the AI-Orchestration-Platform and Dagger.io's containerized workflow engine. It enables the execution of workflows in isolated containers with caching, error handling, and observability capabilities.

## Responsibilities
- Translate between AI-Orchestration-Platform task definitions and Dagger workflows
- Manage containerized execution of workflows
- Handle container registry authentication
- Implement caching for workflow results
- Provide error handling and retry mechanisms
- Monitor and report workflow execution status

## Architecture
The Dagger Adapter follows the Adapter pattern to provide a consistent interface between the AI-Orchestration-Platform's Orchestration Engine and Dagger's workflow API.

```
┌─────────────────────┐      ┌─────────────────┐      ┌───────────────┐
│                     │      │                 │      │               │
│ Orchestration       │─────▶│ Dagger Adapter  │─────▶│ Dagger API    │
│ Engine              │      │                 │      │               │
│                     │◀─────│                 │◀─────│               │
└─────────────────────┘      └─────────────────┘      └───────────────┘
```

Key components:
- **DaggerAdapter**: Main adapter class that implements the AgentAdapter interface
- **DaggerAdapterConfig**: Configuration class for the adapter
- **RetryHandler**: Handles transient failures with exponential backoff
- **CacheManager**: Manages caching of workflow results

## Dependencies
- **Dagger SDK**: Used to interact with Dagger's API
- **Agent Manager**: The adapter is registered with the Agent Manager
- **Error Handling Framework**: Provides error categorization and retry logic
- **Configuration System**: Provides adapter configuration

## API
### Key Methods

#### `execute(config: AgentExecutionConfig) -> AgentExecutionResult`
Executes a workflow using Dagger.

Parameters:
- `config`: Configuration for the execution, including:
  - `execution_type`: Type of workflow to execute ("containerized_workflow" or "dagger_pipeline")
  - `parameters`: Parameters for the workflow execution
  - `task_id`: ID of the task to execute

Returns:
- `AgentExecutionResult`: Result of the execution, including:
  - `success`: Whether the execution was successful
  - `error`: Error message if execution failed
  - `result`: Result data from the execution

#### `get_capabilities() -> List[AgentCapability]`
Gets the capabilities of this adapter.

Returns:
- List of agent capabilities, including "containerized_workflow" and "dagger_pipeline"

#### `get_status() -> AgentStatus`
Gets the current status of the adapter.

Returns:
- Status information including readiness, current load, and capacity

## Configuration
The Dagger Adapter is configured through the `DaggerAdapterConfig` class:

```python
config = DaggerAdapterConfig(
    container_registry="docker.io",
    container_credentials={
        "username": "your-username",
        "password": "your-password"
    },
    workflow_directory="/path/to/workflows",
    max_concurrent_executions=5,
    timeout_seconds=600,
    max_retries=3,
    retry_backoff_factor=0.5,
    retry_jitter=True,
    caching_enabled=True,
    cache_directory="/path/to/cache",
    cache_ttl_seconds=3600
)
```

## Usage Examples

### Basic Workflow Execution
```python
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig

# Create adapter configuration
config = DaggerAdapterConfig(
    container_registry="docker.io",
    workflow_directory="./workflows"
)

# Create and initialize the adapter
adapter = DaggerAdapter(config)
await adapter.initialize()

# Execute a workflow
result = await adapter.execute(AgentExecutionConfig(
    task_id="task-123",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "python:3.9",
        "workflow_definition": "./workflows/data_processing.yml",
        "inputs": {
            "data_file": "data.csv",
            "output_file": "results.json"
        },
        "volumes": [
            {
                "source": "./data",
                "target": "/data"
            }
        ],
        "environment": {
            "DEBUG": "true"
        }
    }
))

# Check the result
if result.success:
    print(f"Workflow executed successfully: {result.result}")
else:
    print(f"Workflow execution failed: {result.error}")
```

### With Retry Configuration
```python
# Configure with custom retry parameters
config = DaggerAdapterConfig(
    # ... other parameters ...
    max_retries=5,
    retry_backoff_factor=1.0,
    retry_jitter=True
)

# The adapter will automatically retry transient failures
adapter = DaggerAdapter(config)
await adapter.initialize()

# Execute with retry for transient failures
result = await adapter.execute(AgentExecutionConfig(
    # ... execution parameters ...
    parameters={
        # ... other parameters ...
        "enable_retry": True  # Can be disabled for specific executions
    }
))
```

## Notes and Limitations
- The adapter currently supports two types of workflow execution: containerized workflows and Dagger pipelines
- Caching is based on input parameters and is not content-aware
- For large workflows, consider increasing the timeout_seconds configuration
- Circuit breaker functionality prevents overloading systems during outages
- Registry authentication supports username/password only; token-based auth will be added in a future version