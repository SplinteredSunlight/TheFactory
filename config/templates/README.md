# Workflow Templates

This directory contains YAML template files for defining workflows in the AI Orchestration Platform.

## Available Templates

- **basic_task.yaml**: A simple template for basic task execution
- **data_processing.yaml**: A template for data processing workflows

## Template Structure

Each template follows a standard structure:

```yaml
name: Template Name
description: Template description
version: 1.0.0
parameters:
  - name: parameter_name
    type: string|number|boolean|array|object
    description: Parameter description
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
```

## Using Templates

Templates can be used to create workflows in the AI Orchestration Platform. They provide a standardized way to define common workflow patterns.

### Example Usage

```python
from src.task_manager.workflow_templates import WorkflowTemplate

# Load a template
template = WorkflowTemplate.from_file("config/templates/basic_task.yaml")

# Create a workflow from the template with parameter values
workflow = template.create_workflow({
    "task_name": "My Task",
    "input_data": "path/to/data.json",
    "output_path": "path/to/output"
})

# Execute the workflow
result = workflow.execute()
```

## Creating New Templates

To create a new template:

1. Create a new YAML file in this directory
2. Follow the template structure defined above
3. Define parameters for customization
4. Define steps with their dependencies

Templates should be designed to be reusable across different use cases by parameterizing the variable parts of the workflow.
