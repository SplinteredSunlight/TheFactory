# Getting Started with Dagger Integration

This guide will help you get started with the Dagger integration in the AI-Orchestration-Platform.

## What is Dagger?

Dagger is a powerful tool for creating and executing containerized workflows. It allows you to define and run complex workflows in containers, making it easier to manage dependencies and ensure reproducibility.

## Prerequisites

- AI-Orchestration-Platform installed and configured
- Docker installed and running
- Dagger SDK installed (`pip install dagger-io>=0.8.1 pydagger>=0.3.0`)

## Installation

The Dagger integration is included in the AI-Orchestration-Platform. To enable it, make sure you have the required dependencies installed:

```bash
pip install dagger-io>=0.8.1 pydagger>=0.3.0
```

## Configuration

The Dagger integration is configured in the `config/dagger.yaml` file. Here's an example configuration:

```yaml
# Workflow execution settings
workflow:
  directory: "workflows"
  max_concurrent_executions: 5
  default_timeout: 600  # seconds

# Container settings
container:
  registry: "${CONTAINER_REGISTRY:-docker.io}"
  credentials:
    username: "${CONTAINER_REGISTRY_USERNAME:-}"
    password: "${CONTAINER_REGISTRY_PASSWORD:-}"
  
  # Default images for common operations
  default_images:
    python: "python:3.9-slim"
    node: "node:18-alpine"
    go: "golang:1.20-alpine"
    base: "ubuntu:22.04"

# Pipeline settings
pipeline:
  caching_enabled: true
  default_timeout: 1800  # seconds
  source_directory: "src"
```

You can configure the following settings:

- **Workflow directory**: The directory where workflow definitions are stored
- **Maximum concurrent executions**: The maximum number of workflows that can be executed concurrently
- **Default timeout**: The default timeout for workflow executions in seconds
- **Container registry**: The registry to use for container images
- **Container credentials**: Credentials for the container registry
- **Default images**: Default images to use for common operations
- **Pipeline settings**: Settings for Dagger pipelines

## Creating a Workflow

Let's create a simple workflow that fetches data, processes it, and generates a report:

```yaml
name: Example Workflow
description: A simple example workflow

steps:
  - id: fetch-data
    name: Fetch Data
    image: python:3.9-slim
    command: ["python", "-c", "import json; print(json.dumps({'data': [1, 2, 3, 4, 5]}))" ]
    environment:
      API_KEY: "${API_KEY}"
    volumes:
      - source: /tmp
        target: /data

  - id: process-data
    name: Process Data
    image: python:3.9-slim
    command: ["python", "-c", "import json, sys; data = json.loads(sys.stdin.read()); print(json.dumps({'result': sum(data['data'])}))"]
    depends_on:
      - fetch-data

  - id: generate-report
    name: Generate Report
    image: python:3.9-slim
    command: ["python", "-c", "import json, sys; data = json.loads(sys.stdin.read()); print(f'Report: The sum is {data[\"result\"]}')"]
    depends_on:
      - process-data
```

Save this workflow to a file in the `workflows` directory, for example `workflows/example.yaml`.

## Executing a Workflow

You can execute a workflow using the API or directly with the Dagger adapter. Here's an example using the API:

```python
import requests

# Create a workflow
workflow_data = {
    "name": "example-workflow",
    "description": "Example workflow",
    "steps": [
        {
            "id": "step1",
            "name": "Step 1",
            "container": {
                "image": "python:3.9-slim"
            }
        }
    ]
}

response = requests.post("http://localhost:8000/dagger/workflows", json=workflow_data)
workflow_id = response.json()["id"]

# Execute the workflow
execution_data = {
    "inputs": {"param": "value"},
    "container_registry": "docker.io",
    "workflow_defaults": {"inputs": {"default_timeout": 30}}
}

response = requests.post(f"http://localhost:8000/dagger/workflows/{workflow_id}/execute", json=execution_data)
execution_id = response.json()["execution_id"]

# Check the execution status
response = requests.get(f"http://localhost:8000/dagger/executions/{execution_id}")
status = response.json()["status"]
```

## Using the Dagger Adapter Directly

You can also use the Dagger adapter directly:

```python
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig

# Create a Dagger adapter config
config = DaggerAdapterConfig(
    container_registry="docker.io",
    workflow_directory="workflows",
    max_concurrent_executions=5
)

# Create a Dagger adapter
adapter = DaggerAdapter(config)
await adapter.initialize()

# Execute a workflow
execution_config = AgentExecutionConfig(
    task_id="example-task",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "python:3.9",
        "workflow_definition": "example.yaml",
        "inputs": {"param": "value"},
        "volumes": [{"source": "/tmp", "target": "/data"}],
        "environment": {"ENV_VAR": "value"}
    }
)

result = await adapter.execute(execution_config)
```

## Creating a Dagger Pipeline

Dagger also supports pipelines, which are more complex workflows with multiple stages. Here's an example pipeline definition:

```yaml
name: Example Pipeline
description: A simple example pipeline

source: src

steps:
  - name: lint
    image: python:3.9-slim
    command: ["pip", "install", "flake8", "&&", "flake8", "${source}"]

  - name: test
    image: python:3.9-slim
    command: ["pip", "install", "pytest", "&&", "pytest", "${source}"]
    depends_on:
      - lint

  - name: build
    image: python:3.9-slim
    command: ["pip", "install", "build", "&&", "python", "-m", "build"]
    depends_on:
      - test

outputs:
  - name: build-output
    path: /dist
    step: build
```

Save this pipeline to a file in the `workflows` directory, for example `workflows/pipeline.yaml`.

## Executing a Dagger Pipeline

You can execute a Dagger pipeline using the API or directly with the Dagger adapter:

```python
# Execute a pipeline
execution_config = AgentExecutionConfig(
    task_id="example-pipeline",
    execution_type="dagger_pipeline",
    parameters={
        "pipeline_definition": "pipeline.yaml",
        "inputs": {"param": "value"},
        "source_directory": "src"
    }
)

result = await adapter.execute(execution_config)
```

## Monitoring Dagger Workflows

The AI-Orchestration-Platform includes monitoring and observability features for Dagger workflows. You can access the monitoring dashboard at:

```
http://localhost:8000/monitoring/dagger/status
```

This provides real-time information about active workflows, resource usage, and errors.

For more detailed metrics, you can use the Prometheus endpoint:

```
http://localhost:8000/monitoring/dagger/metrics
```

This endpoint provides Prometheus metrics for workflows, steps, resource usage, and errors.

## Next Steps

- Learn more about [Dagger workflow definitions](workflow-definition.md)
- Explore [advanced features](advanced-features.md) of the Dagger integration
- Check out the [API reference](api-reference.md) for the Dagger integration