# Workflow Examples

This directory contains example workflow definitions for the AI Orchestration Platform. These examples demonstrate how to define and use workflows for various use cases.

## Available Examples

- **example_workflow.yml**: A basic example workflow
- **example_pipeline.yml**: An example data processing pipeline
- **test/**: Directory containing test workflows and supporting files

## Workflow Structure

Each workflow definition follows a standard YAML structure:

```yaml
name: Workflow Name
description: Workflow description
version: 1.0.0
inputs:
  input_name:
    type: string|number|boolean|array|object
    description: Input description
    required: true|false
    default: default_value (optional)
steps:
  - name: step_name
    description: Step description
    agent: agent_name
    inputs:
      input_name: input_value
    depends_on:
      - other_step_name (optional)
outputs:
  output_name:
    description: Output description
    value: ${step_name.output_name}
```

## Running Workflows

You can run these example workflows using the AI Orchestration Platform:

```python
from src.orchestrator.engine import OrchestrationEngine

# Initialize the orchestration engine
engine = OrchestrationEngine()

# Load a workflow from a file
workflow = engine.load_workflow("examples/workflows/example_workflow.yml")

# Execute the workflow with inputs
result = engine.execute_workflow(
    workflow_id=workflow.id,
    inputs={
        "input_name": "input_value"
    }
)

# Access the workflow outputs
output = result.outputs["output_name"]
print(f"Workflow output: {output}")
```

## Creating Your Own Workflows

To create your own workflow:

1. Create a new YAML file in this directory or a subdirectory
2. Follow the workflow structure defined above
3. Define inputs, steps, and outputs
4. Use the workflow in your code as shown in the example

You can also use the workflow templates in `config/templates/` as a starting point for creating your own workflows.
