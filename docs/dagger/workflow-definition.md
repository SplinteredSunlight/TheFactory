# Dagger Workflow Definition

This document provides detailed information about defining Dagger workflows in the AI-Orchestration-Platform.

## Workflow Structure

A Dagger workflow is defined in YAML format and consists of the following components:

- **Name**: The name of the workflow
- **Description**: Optional description of the workflow
- **Steps**: A list of steps to execute in the workflow
- **Container Configuration**: Optional default container configuration for all steps

Here's an example workflow definition:

```yaml
name: Example Workflow
description: A simple example workflow

steps:
  - id: step1
    name: Step 1
    image: python:3.9-slim
    command: ["python", "script.py"]
    environment:
      ENV_VAR: value
    volumes:
      - source: /tmp
        target: /data

  - id: step2
    name: Step 2
    image: node:18-alpine
    command: ["node", "script.js"]
    depends_on:
      - step1
```

## Step Definition

Each step in a workflow is defined with the following properties:

- **ID**: Unique identifier for the step
- **Name**: Human-readable name for the step
- **Image**: Container image to use for the step
- **Command**: Command to run in the container
- **Environment**: Environment variables to set in the container
- **Volumes**: Volumes to mount in the container
- **Depends On**: Steps that must complete before this step can run
- **Timeout**: Optional timeout for the step

Here's an example step definition:

```yaml
id: fetch-data
name: Fetch Data
image: python:3.9-slim
command: ["python", "fetch.py"]
environment:
  API_KEY: "${API_KEY}"
  BASE_URL: "https://api.example.com"
volumes:
  - source: /tmp
    target: /data
  - source: /config
    target: /config
depends_on:
  - init
timeout_seconds: 300
```

### Step Properties

#### Image

The `image` property specifies the container image to use for the step. This can be any Docker image, such as:

- `python:3.9-slim`: Python 3.9 image
- `node:18-alpine`: Node.js 18 image
- `ubuntu:22.04`: Ubuntu 22.04 image

You can also use custom images from a container registry:

```yaml
image: gcr.io/my-project/my-image:latest
```

#### Command

The `command` property specifies the command to run in the container. This is an array of strings, where the first element is the command and the remaining elements are arguments:

```yaml
command: ["python", "script.py", "--arg1", "value1", "--arg2", "value2"]
```

#### Environment

The `environment` property specifies environment variables to set in the container. This is a map of variable names to values:

```yaml
environment:
  API_KEY: "${API_KEY}"
  DEBUG: "true"
  LOG_LEVEL: "info"
```

Environment variables can reference other environment variables using the `${VAR}` syntax. For example, `${API_KEY}` will be replaced with the value of the `API_KEY` environment variable at runtime.

#### Volumes

The `volumes` property specifies volumes to mount in the container. This is a list of source-target pairs, where the source is a path on the host and the target is a path in the container:

```yaml
volumes:
  - source: /tmp
    target: /data
  - source: /config
    target: /config
```

#### Depends On

The `depends_on` property specifies steps that must complete before this step can run. This is a list of step IDs:

```yaml
depends_on:
  - step1
  - step2
```

The step will only run after all of its dependencies have completed successfully.

#### Timeout

The `timeout_seconds` property specifies the maximum time in seconds that the step is allowed to run. If the step exceeds this timeout, it will be terminated:

```yaml
timeout_seconds: 300  # 5 minutes
```

If not specified, the step will use the default timeout from the workflow configuration.

## Container Configuration

The `container_config` property specifies default container configuration for all steps in the workflow. This is useful for setting common configuration that applies to all steps:

```yaml
container_config:
  image: python:3.9-slim
  environment:
    DEBUG: "true"
    LOG_LEVEL: "info"
  volumes:
    - source: /tmp
      target: /data
```

Step-specific configuration overrides the workflow's container configuration.

## Dependencies Between Steps

You can define dependencies between steps using the `depends_on` property. This creates a directed acyclic graph (DAG) of steps, where each step can only run after all of its dependencies have completed successfully.

For example:

```yaml
steps:
  - id: step1
    name: Step 1
    image: python:3.9-slim
    command: ["python", "step1.py"]

  - id: step2
    name: Step 2
    image: python:3.9-slim
    command: ["python", "step2.py"]
    depends_on:
      - step1

  - id: step3
    name: Step 3
    image: python:3.9-slim
    command: ["python", "step3.py"]
    depends_on:
      - step1

  - id: step4
    name: Step 4
    image: python:3.9-slim
    command: ["python", "step4.py"]
    depends_on:
      - step2
      - step3
```

In this example, `step1` runs first, then `step2` and `step3` run in parallel, and finally `step4` runs after both `step2` and `step3` have completed.

## Environment Variables

You can use environment variables in your workflow definition:

```yaml
environment:
  API_KEY: "${API_KEY}"
  BASE_URL: "${BASE_URL:-https://api.example.com}"
```

Variables referenced with `${VAR}` will be replaced with the value of the environment variable at runtime. You can also specify a default value using the `${VAR:-default}` syntax, which will be used if the environment variable is not set.

## Workflow Inputs

You can pass inputs to a workflow when you execute it:

```python
execution_data = {
    "inputs": {
        "api_key": "your_api_key",
        "base_url": "https://api.example.com"
    }
}

response = requests.post(f"http://localhost:8000/dagger/workflows/{workflow_id}/execute", json=execution_data)
```

These inputs can be accessed in the workflow using the `${inputs.VAR}` syntax:

```yaml
environment:
  API_KEY: "${inputs.api_key}"
  BASE_URL: "${inputs.base_url}"
```

## Workflow Outputs

You can define outputs for a workflow in the API:

```yaml
outputs:
  - name: result
    description: The result of the workflow
    value: "${steps.process-data.outputs.result}"
```

These outputs can be retrieved from the workflow execution result.

## Advanced Features

### Conditional Execution

You can conditionally execute steps based on inputs or the outputs of previous steps:

```yaml
steps:
  - id: check-condition
    name: Check Condition
    image: python:3.9-slim
    command: ["python", "-c", "import sys; sys.exit(0 if '${inputs.run_tests}' == 'true' else 1)"]

  - id: run-tests
    name: Run Tests
    image: python:3.9-slim
    command: ["python", "run_tests.py"]
    depends_on:
      - check-condition
```

In this example, the `run-tests` step will only run if the `check-condition` step exits with a zero status code, which happens if the `run_tests` input is `true`.

### Retries

You can configure retries for steps that may fail transiently:

```yaml
steps:
  - id: fetch-data
    name: Fetch Data
    image: python:3.9-slim
    command: ["python", "fetch.py"]
    retries: 3
    retry_delay: 5  # seconds
```

This step will be retried up to 3 times with a 5-second delay between retries if it fails.

### Resource Limits

You can set resource limits for steps:

```yaml
steps:
  - id: heavy-computation
    name: Heavy Computation
    image: python:3.9-slim
    command: ["python", "compute.py"]
    resources:
      cpu: "2"
      memory: "4G"
```

This step will be allocated 2 CPU cores and 4 GB of memory.

## Best Practices

### Keep Steps Small and Focused

Each step should do one thing and do it well. This makes workflows easier to understand, test, and maintain.

### Use Explicit Dependencies

Always explicitly define dependencies between steps using the `depends_on` property. Don't rely on implicit dependencies.

### Use Environment Variables for Configuration

Use environment variables for configuration that may change between environments or runs.

### Handle Errors Gracefully

Design your workflows to handle errors gracefully. Use retries for transient failures and set appropriate timeouts.

### Use Version Control for Workflow Definitions

Store your workflow definitions in version control to track changes and collaborate with others.

### Use Container Images from Trusted Sources

Use container images from trusted sources, such as official images from Docker Hub or your organization's container registry.

### Validate Inputs and Outputs

Validate inputs and outputs to ensure they meet your expectations and fail fast if they don't.