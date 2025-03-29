# Result Reporting System

The Result Reporting System is a component of the AI-Orchestration-Platform that enables agents to report detailed results, progress updates, metrics, and logs back to the orchestrator. This system provides a standardized way for agents to communicate their status, progress, and outcomes, enhancing observability and enabling better monitoring and management of agent activities.

## Overview

The Result Reporting System consists of a client library that agents can use to report various types of results back to the orchestrator. The system handles authentication, error handling, and provides methods for reporting different types of results.

Key features of the Result Reporting System include:

- **Task Completion Reporting**: Report the successful completion of tasks with detailed result data.
- **Task Progress Updates**: Report progress updates during task execution.
- **Task Error Reporting**: Report errors encountered during task execution.
- **Agent Status Updates**: Report agent online/offline status and current load.
- **Agent Metrics Reporting**: Report performance metrics and other statistics.
- **Agent Log Reporting**: Report log messages with different severity levels.
- **Custom Result Reporting**: Report custom results for specialized use cases.

## Architecture

The Result Reporting System is built on top of the existing Orchestrator API Client and integrates with the Task Distribution and Agent Communication systems. It uses the following components:

```mermaid
graph TD
    subgraph "Agent"
        RRC[Result Reporting Client]
        Agent[Agent Implementation]
    end
    
    subgraph "Orchestrator"
        OE[Orchestration Engine]
        TD[Task Distributor]
        CM[Communication Manager]
        DB[Result Database]
    end
    
    Agent --> RRC
    RRC --> OE
    OE --> TD
    OE --> CM
    TD --> DB
    CM --> DB
```

## Client Library

The Result Reporting System provides a client library that agents can use to report results. The library is designed to be easy to use and provides a consistent interface for reporting different types of results.

### Getting Started

To use the Result Reporting System, you first need to get a client instance:

```python
from fast_agent_integration.result_reporting import get_result_reporting_client

# Get a client instance for an agent
result_reporter = await get_result_reporting_client(
    agent_id="my-agent-id",
    api_key="my-api-key"  # Optional, will use default if not provided
)
```

The `get_result_reporting_client` function returns a singleton instance for each agent ID, so you can call it multiple times without creating duplicate clients.

### Reporting Task Completion

To report the successful completion of a task:

```python
await result_reporter.report_task_completion(
    task_id="task-123",
    result_data={
        "summary": "Task completed successfully",
        "execution_time_ms": 1500,
        "output": {
            "processed_items": 100,
            "success_rate": 0.98
        }
    }
)
```

### Reporting Task Progress

To report progress during task execution:

```python
await result_reporter.report_task_progress(
    task_id="task-123",
    progress_data={
        "percent_complete": 50,
        "message": "Processing data",
        "stage": "data_processing"
    }
)
```

### Reporting Task Errors

To report an error encountered during task execution:

```python
await result_reporter.report_task_error(
    task_id="task-123",
    error_message="Failed to connect to external API",
    error_details={
        "service": "external-api",
        "status_code": 500,
        "retry_count": 3
    }
)
```

### Reporting Agent Status

To report agent status:

```python
await result_reporter.report_agent_status(
    is_online=True,
    current_load=5  # Number of active tasks
)
```

### Reporting Agent Metrics

To report agent metrics:

```python
await result_reporter.report_agent_metrics(
    metrics={
        "memory_usage_mb": 256,
        "cpu_usage_percent": 15,
        "requests_processed": 1000,
        "average_response_time_ms": 50
    }
)
```

### Reporting Agent Logs

To report agent logs:

```python
from fast_agent_integration.result_reporting import ResultSeverity

await result_reporter.report_agent_log(
    log_message="Processing started for task",
    severity=ResultSeverity.INFO,
    log_context={
        "task_id": "task-123",
        "timestamp": "2025-03-09T12:34:56Z"
    }
)
```

### Reporting Custom Results

To report custom results:

```python
await result_reporter.report_custom_result(
    result_id="custom-result-123",
    data={
        "key": "value",
        "nested": {
            "field": 42
        }
    },
    recipient_id="another-agent",  # Optional, defaults to orchestrator
    correlation_id="correlation-123",  # Optional
    priority="high"  # Optional, defaults to "medium"
)
```

### Offline Operation

The Result Reporting System supports offline operation by caching results when the orchestrator is unavailable. Results are automatically retried when the connection is restored.

To add a result to the cache without sending it immediately:

```python
await result_reporter.report_task_completion(
    task_id="task-123",
    result_data={"output": "Task completed successfully"},
    send_immediately=False  # Add to cache but don't send immediately
)
```

To manually flush the cache:

```python
await result_reporter.flush_cache()
```

### Shutting Down

When you're done with the client, you should shut it down to flush any cached results and release resources:

```python
await result_reporter.shutdown()
```

## Integration with Fast-Agent Adapter

The Result Reporting System is integrated with the Fast-Agent Adapter, which automatically reports agent creation, deletion, and task execution results. This integration provides enhanced visibility into agent activities without requiring changes to existing agent implementations.

## Error Handling

The Result Reporting System includes robust error handling with circuit breaker functionality to prevent cascading failures. If the orchestrator is unavailable, results are cached and retried when the connection is restored.

## Examples

For complete examples of how to use the Result Reporting System, see the [Result Reporting Example](../src/fast_agent_integration/examples/result_reporting_example.py).

## API Reference

### ResultType

Constants for different types of results:

- `ResultType.TASK_COMPLETION`: Task completion result
- `ResultType.TASK_PROGRESS`: Task progress update
- `ResultType.TASK_ERROR`: Task error
- `ResultType.AGENT_STATUS`: Agent status update
- `ResultType.AGENT_METRICS`: Agent metrics
- `ResultType.AGENT_LOG`: Agent log message
- `ResultType.CUSTOM`: Custom result

### ResultSeverity

Constants for different severity levels:

- `ResultSeverity.INFO`: Informational message
- `ResultSeverity.WARNING`: Warning message
- `ResultSeverity.ERROR`: Error message
- `ResultSeverity.CRITICAL`: Critical error message
- `ResultSeverity.DEBUG`: Debug message

### ResultReportingClient

The main client class for reporting results:

- `report_task_completion(task_id, result_data, send_immediately=True)`: Report task completion
- `report_task_progress(task_id, progress_data, send_immediately=True)`: Report task progress
- `report_task_error(task_id, error_message, error_details=None, send_immediately=True)`: Report task error
- `report_agent_status(is_online, current_load=None, send_immediately=True)`: Report agent status
- `report_agent_metrics(metrics, send_immediately=True)`: Report agent metrics
- `report_agent_log(log_message, severity=ResultSeverity.INFO, log_context=None, send_immediately=True)`: Report agent log
- `report_custom_result(result_id, data, recipient_id=None, correlation_id=None, priority="medium", send_immediately=True)`: Report custom result
- `flush_cache()`: Flush the result cache
- `shutdown()`: Shutdown the client

### get_result_reporting_client

Factory function to get a ResultReportingClient instance:

```python
async def get_result_reporting_client(
    agent_id: str,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ResultReportingClient:
    """Get a ResultReportingClient instance for an agent."""
```

## Best Practices

1. **Use Appropriate Result Types**: Choose the appropriate result type for the information you're reporting.
2. **Include Relevant Context**: Include relevant context in your results to make them more useful for debugging and analysis.
3. **Report Progress Updates**: For long-running tasks, report progress updates to provide visibility into task execution.
4. **Handle Errors Gracefully**: Report errors with detailed information to help diagnose and resolve issues.
5. **Use Severity Levels**: Use appropriate severity levels for log messages to help filter and prioritize them.
6. **Shutdown Properly**: Always call `shutdown()` when you're done with the client to flush any cached results and release resources.
