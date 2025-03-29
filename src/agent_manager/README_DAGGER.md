# Dagger Integration for AI-Orchestration-Platform

This module provides integration with Dagger.io's containerized workflow engine for the AI-Orchestration-Platform. It allows workflows to be executed in containers with dependency management, efficient caching, and reproducible builds.

## Features

- Execute containerized workflows with Dagger
- Run Dagger pipelines for CI/CD workflows
- Configure container registries and authentication
- Mount volumes and set environment variables
- Handle dependencies between workflow steps
- Limit concurrent workflow executions

## Installation

Dagger integration requires the following dependencies:

```bash
pip install dagger-io>=0.8.1 pydagger>=0.3.0
```

These dependencies are included in the main `requirements.txt` file of the AI-Orchestration-Platform.

## Configuration

Dagger integration is configured in the `config/dagger.yaml` file:

```yaml
# Container settings
container:
  registry: "${CONTAINER_REGISTRY:-docker.io}"
  credentials:
    username: "${CONTAINER_REGISTRY_USERNAME:-}"
    password: "${CONTAINER_REGISTRY_PASSWORD:-}"

# Workflow settings
workflow:
  directory: "workflows"
  max_concurrent_executions: 5
  default_timeout: 600  # seconds
```

## Usage

### Creating a Workflow

```python
from src.orchestrator.engine import OrchestrationEngine

# Create an orchestration engine
engine = OrchestrationEngine()

# Create a workflow
workflow = engine.create_workflow(
    name="example_workflow",
    description="Example workflow with Dagger"
)

# Add tasks to the workflow
task1_id = workflow.add_task(
    name="fetch_data",
    agent="data_fetcher",
    inputs={
        "url": "https://example.com/data",
        "format": "json"
    }
)

task2_id = workflow.add_task(
    name="process_data",
    agent="data_processor",
    inputs={
        "operation": "transform",
        "schema": {
            "fields": ["name", "value", "timestamp"]
        }
    },
    depends_on=[task1_id]
)

# Execute the workflow with Dagger
result = engine.execute_workflow(
    workflow_id=workflow.id,
    engine_type="dagger",
    container_registry="docker.io",
    workflow_directory="workflows"
)
```

### Using the Dagger Adapter Directly

```python
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig

# Create the adapter configuration
config = DaggerAdapterConfig(
    container_registry="docker.io",
    workflow_directory="workflows",
    max_concurrent_executions=5
)

# Create the adapter
adapter = DaggerAdapter(config)
await adapter.initialize()

# Execute a containerized workflow
execution_config = AgentExecutionConfig(
    task_id="example_task",
    execution_type="containerized_workflow",
    parameters={
        "container_image": "python:3.9",
        "workflow_definition": "example_workflow.yml",
        "inputs": {"param": "value"},
        "volumes": [{"source": "/tmp", "target": "/data"}],
        "environment": {"ENV_VAR": "value"}
    }
)

result = await adapter.execute(execution_config)
```

## Workflow Definition

Workflows are defined in YAML files in the `workflows` directory:

```yaml
name: Example Workflow
description: A simple example workflow

steps:
  - id: fetch-data
    name: Fetch Data
    image: python:3.9-slim
    command: ["python", "fetch.py"]
    environment:
      API_KEY: ${API_KEY}
    volumes:
      - source: /tmp
        target: /data

  - id: process-data
    name: Process Data
    image: python:3.9-slim
    command: ["python", "process.py"]
    depends_on:
      - fetch-data
```

## Testing

To run the tests for the Dagger integration:

```bash
# Run all Dagger tests
python tests/run_dagger_tests.py

# Run unit tests only
python tests/run_dagger_tests.py --type unit

# Run integration tests only
python tests/run_dagger_tests.py --type integration

# Run with coverage
python tests/run_dagger_tests.py --coverage
```