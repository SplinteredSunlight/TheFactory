# Circuit Breaker Pattern Integration with Dagger

This document describes how the circuit breaker pattern is integrated with Dagger workflows in the AI-Orchestration-Platform.

## Overview

The circuit breaker pattern is a design pattern used to detect failures and prevent cascading failures in distributed systems. It works by "tripping" when a certain number of failures occur, preventing further requests to a failing service until it has had time to recover.

In the context of Dagger workflows, the circuit breaker pattern is used to prevent repeated attempts to execute workflows that are consistently failing, which can help to:

1. Reduce load on failing services
2. Prevent cascading failures
3. Allow for graceful degradation of service
4. Provide automatic recovery when the system stabilizes

## Implementation

The circuit breaker pattern is implemented in the `src/orchestrator/circuit_breaker.py` module, which provides:

- A `CircuitBreaker` class that implements the core circuit breaker functionality
- A `CircuitBreakerOpenError` exception that is raised when a circuit is open
- A `get_circuit_breaker` function that provides a singleton circuit breaker instance for a given name

The circuit breaker has three states:

1. **Closed**: The circuit is closed and requests are allowed to pass through
2. **Open**: The circuit is open and requests are blocked
3. **Half-Open**: The circuit is partially open and a limited number of requests are allowed to pass through to test if the service has recovered

## Integration with Dagger

The circuit breaker pattern is integrated with Dagger workflows at multiple levels:

### 1. Dagger Adapter Level

The `DaggerAdapter` class in `src/agent_manager/dagger_adapter.py` integrates with the circuit breaker pattern to protect Dagger workflow executions. When executing a workflow, the adapter checks if the `use_circuit_breaker` parameter is set to `true` in the execution config. If it is, the adapter will use the circuit breaker pattern to protect the execution.

```python
# Example of using the circuit breaker with the Dagger adapter
execution_config = AgentExecutionConfig(
    task_id="task-123",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "my-image",
        "workflow_definition": "my-workflow",
        "use_circuit_breaker": True  # Enable circuit breaker protection
    }
)
result = await dagger_adapter.execute(execution_config)
```

### 2. Task Workflow Integration Level

The `TaskWorkflowIntegration` class in `src/task_manager/dagger_integration.py` also integrates with the circuit breaker pattern. When executing a task workflow, the integration checks if the `use_circuit_breaker` parameter is set to `true` in the workflow parameters. If it is, the integration will use the circuit breaker pattern to protect the execution.

```python
# Example of using the circuit breaker with the task workflow integration
result = await task_workflow_integration.execute_task_workflow(
    task_id="task-123",
    workflow_type="containerized_workflow",
    workflow_params={
        "use_circuit_breaker": True  # Enable circuit breaker protection
    }
)
```

### 3. MCP Server Level

The `DaggerWorkflowIntegration` class in `src/task_manager/mcp_servers/dagger_workflow_integration.py` integrates with the circuit breaker pattern to protect MCP server operations. When handling MCP requests, the integration checks if the `use_circuit_breaker` parameter is set to `true` in the request parameters. If it is, the integration will use the circuit breaker pattern to protect the operation.

```python
# Example of using the circuit breaker with the MCP server
result = await execute_with_circuit_breaker(
    circuit_breaker,
    lambda: workflow_integration.execute_task_workflow(
        task_id="task-123",
        workflow_type="containerized_workflow",
        workflow_params={"use_circuit_breaker": True}
    )
)
```

## Configuration

The circuit breaker pattern can be configured at multiple levels:

### 1. Global Configuration

The global circuit breaker configuration is defined in the `config/dagger.yaml` file:

```yaml
circuit_breaker:
  failure_threshold: 5  # Number of failures before the circuit opens
  reset_timeout: 60     # Time in seconds before the circuit resets to half-open
  half_open_timeout: 30 # Time in seconds before the circuit resets to closed if no failures occur
```

### 2. Per-Workflow Configuration

The circuit breaker pattern can also be configured on a per-workflow basis by setting the `use_circuit_breaker` parameter to `true` or `false` in the workflow parameters:

```python
# Enable circuit breaker protection for a specific workflow
workflow_params = {
    "use_circuit_breaker": True
}

# Disable circuit breaker protection for a specific workflow
workflow_params = {
    "use_circuit_breaker": False
}
```

## Example Usage

Here's an example of how to use the circuit breaker pattern with Dagger workflows:

```python
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig

# Create a Dagger adapter
config = DaggerAdapterConfig(
    max_retries=2,
    retry_backoff_factor=0.5,
    retry_jitter=True,
    caching_enabled=True
)
adapter = DaggerAdapter(config)

# Create an execution config with circuit breaker protection
execution_config = AgentExecutionConfig(
    task_id="task-123",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "my-image",
        "workflow_definition": "my-workflow",
        "use_circuit_breaker": True  # Enable circuit breaker protection
    }
)

# Execute the workflow
result = await adapter.execute(execution_config)
if result.success:
    print("Workflow executed successfully")
else:
    print(f"Workflow execution failed: {result.error}")
```

## Testing

The circuit breaker pattern integration with Dagger is tested in the following test files:

- `tests/test_circuit_breaker.py`: Tests the core circuit breaker functionality
- `tests/test_dagger_circuit_breaker_integration.py`: Tests the integration of the circuit breaker pattern with Dagger

## Example Script

An example script demonstrating the circuit breaker pattern with Dagger is available at:

- `examples/dagger/circuit_breaker_dagger_example.py`: Demonstrates how the circuit breaker pattern can be used with Dagger to prevent cascading failures

To run the example script, use the following command:

```bash
./scripts/dagger/run_circuit_breaker_dagger_example.sh
```

## Benefits

Using the circuit breaker pattern with Dagger workflows provides several benefits:

1. **Improved Resilience**: The circuit breaker pattern helps to improve the resilience of the system by preventing cascading failures.

2. **Reduced Load**: By preventing repeated attempts to execute failing workflows, the circuit breaker pattern helps to reduce the load on failing services.

3. **Graceful Degradation**: The circuit breaker pattern allows for graceful degradation of service by blocking requests to failing services while allowing requests to healthy services to continue.

4. **Automatic Recovery**: The circuit breaker pattern provides automatic recovery when the system stabilizes by transitioning from the open state to the half-open state and eventually to the closed state.

5. **Visibility**: The circuit breaker pattern provides visibility into the health of the system by tracking the number of failures and the state of the circuit.

## Conclusion

The circuit breaker pattern is a powerful tool for improving the resilience of distributed systems. By integrating the circuit breaker pattern with Dagger workflows, we can prevent cascading failures and improve the overall reliability of the AI-Orchestration-Platform.
