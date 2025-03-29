# Dagger Caching

This document provides a comprehensive guide to the caching mechanism implemented in the Dagger integration for the AI-Orchestration-Platform.

## Overview

The caching mechanism allows the Dagger adapter to store and reuse the results of workflow executions, significantly improving performance for repeated or similar operations. By caching the results of expensive computations, the system can avoid redundant work and respond more quickly to requests.

## How Caching Works

1. **Cache Key Generation**: When a workflow or pipeline is executed, a unique cache key is generated based on the execution parameters. This key is a hash of the parameters, ensuring that identical operations will have the same key.

2. **Cache Storage**: Results are stored in a local cache directory as JSON files. Each cache entry includes:
   - The result data
   - An expiry timestamp
   - A creation timestamp

3. **Cache Lookup**: Before executing a workflow, the system checks if a valid cache entry exists for the given parameters. If found and not expired, the cached result is returned immediately.

4. **Cache Invalidation**: Cache entries automatically expire after a configurable time-to-live (TTL) period. Expired entries are removed from the cache when encountered.

## Configuration

The caching mechanism can be configured through the `DaggerAdapterConfig` class with the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `caching_enabled` | `bool` | `True` | Whether to enable caching |
| `cache_directory` | `str` | `./.dagger_cache` | Directory to store cache files |
| `cache_ttl_seconds` | `int` | `3600` (1 hour) | Time-to-live for cache entries in seconds |

Example configuration:

```python
config = DaggerAdapterConfig(
    adapter_id="dagger-adapter",
    name="Dagger Adapter",
    caching_enabled=True,
    cache_directory="/path/to/cache",
    cache_ttl_seconds=7200  # 2 hours
)
```

## Cache Control

Individual workflow executions can control caching behavior through the `skip_cache` parameter:

```python
# Skip cache for this execution
result = await adapter.execute(AgentExecutionConfig(
    task_id="task-1",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "python:3.9",
        "workflow_definition": "workflow.yml",
        "inputs": {"param1": "value1"},
        "skip_cache": True  # Force execution, don't use cache
    }
))
```

## Performance Considerations

- **Cache Size**: The cache can grow large if many different workflows are executed. Consider periodically cleaning the cache directory.
- **Cache TTL**: Choose an appropriate TTL based on how frequently your data changes. Shorter TTLs ensure fresher data but may reduce cache effectiveness.
- **Memory Usage**: The cache is loaded into memory on adapter initialization. For very large caches, this may impact memory usage.

## Implementation Details

The caching mechanism is implemented in the `DaggerAdapter` class with the following key methods:

- `_get_cache_key(params)`: Generates a unique cache key for the given parameters
- `_get_from_cache(cache_key)`: Retrieves a result from the cache if available
- `_add_to_cache(cache_key, result)`: Adds a result to the cache
- `_load_cache()`: Loads the cache from disk on initialization
- `_save_cache()`: Saves the cache to disk

The cache is stored in a file named `cache.json` in the configured cache directory. This file contains a JSON object mapping cache keys to cache entries.

## Example Usage

Here's a complete example of using the caching mechanism:

```python
from src.orchestrator.engine import OrchestrationEngine

# Create an orchestration engine
engine = OrchestrationEngine()

# Create a workflow
workflow = engine.create_workflow(
    name="example_workflow",
    description="Example workflow with caching"
)

# Add tasks to the workflow
workflow.add_task(
    name="data_process",
    agent="data_processor",
    inputs={
        "data": [1, 2, 3, 4, 5]
    }
)

# Execute with caching enabled
result = await engine.execute_workflow(
    workflow_id=workflow.id,
    engine_type="dagger",
    caching_enabled=True,
    cache_directory="./.dagger_cache",
    cache_ttl_seconds=3600
)
```

## Troubleshooting

If you encounter issues with caching:

1. **Cache Not Being Used**: Ensure `caching_enabled` is set to `True` and `skip_cache` is not set in the execution parameters.
2. **Stale Results**: Check the `cache_ttl_seconds` setting. If it's too long, you may be getting outdated results.
3. **Missing Cache Directory**: The system will create the cache directory if it doesn't exist, but ensure the parent directory exists and is writable.
4. **Cache File Corruption**: If the cache file becomes corrupted, delete it and the adapter will create a new one.

## Future Improvements

Potential improvements to the caching mechanism include:

1. **Distributed Caching**: Support for distributed cache backends like Redis or Memcached
2. **Cache Versioning**: Version-based cache invalidation to handle schema changes
3. **Partial Caching**: Caching intermediate results for multi-step workflows
4. **Cache Analytics**: Tools to analyze cache hit rates and effectiveness
5. **Cache Prewarming**: Mechanisms to prewarm the cache for common operations
