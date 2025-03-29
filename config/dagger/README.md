# Dagger Configuration

This directory contains configuration files for the Dagger integration in the AI Orchestration Platform.

## Configuration Files

- **dagger.yaml**: Main configuration file for Dagger integration

## Configuration Structure

The Dagger configuration file follows this structure:

```yaml
# General Dagger configuration
dagger:
  # Connection settings
  connection:
    endpoint: "http://localhost:8080"
    timeout: 30  # seconds
    max_retries: 3
  
  # Authentication settings
  auth:
    enabled: true
    token_path: "/path/to/token"
    
  # Container registry settings
  registry:
    url: "docker.io"
    username: "${REGISTRY_USERNAME}"
    password: "${REGISTRY_PASSWORD}"
    
  # Execution settings
  execution:
    concurrency: 5
    log_level: "info"
    cache_enabled: true
    cache_dir: "/path/to/cache"
    
  # Circuit breaker settings
  circuit_breaker:
    enabled: true
    failure_threshold: 5
    reset_timeout: 60  # seconds
    half_open_requests: 2
```

## Environment Variables

The configuration can reference environment variables using the `${VARIABLE_NAME}` syntax. This allows for secure storage of sensitive information like credentials.

## Usage

The Dagger configuration is used by the AI Orchestration Platform to connect to and interact with Dagger for containerized workflow execution. The configuration is loaded by the `DaggerAdapter` class in the `src/agent_manager/dagger_adapter.py` module.

```python
from src.agent_manager.dagger_adapter import DaggerAdapter

# Load configuration from file
adapter = DaggerAdapter.from_config("config/dagger/dagger.yaml")

# Use the adapter to execute workflows
result = adapter.execute_workflow(workflow_id, inputs)
```

## Customization

To customize the Dagger configuration for your environment:

1. Copy the default configuration file
2. Modify the settings as needed
3. Update environment variables or paths to match your system
4. Reference the custom configuration file in your code
