# Task Manager MCP Server - Dagger Workflow Integration

This directory contains the implementation of the Dagger Workflow Integration for the Task Manager MCP Server component of the AI-Orchestration-Platform.

## Overview

The Dagger Workflow Integration provides a way to define, manage, and execute workflows using Dagger. It allows users to:

- Define workflow templates with customizable parameters
- Create workflows from templates
- Execute workflows using Dagger
- Monitor workflow execution status
- Retry failed workflows or individual stages
- Import and export workflow templates

## Components

### Workflow Templates (`workflow_templates.py`)

The `workflow_templates.py` module provides functionality for managing workflow templates. It includes:

- `WorkflowTemplate` class for defining workflow templates
- `WorkflowTemplateRegistry` class for registering and retrieving templates
- Built-in templates for common workflows (CI/CD, data processing, ML training, etc.)
- Support for loading templates from YAML or JSON files

### Dagger Workflow Integration (`dagger_workflow_integration.py`)

The `dagger_workflow_integration.py` module provides integration between the Task Manager MCP Server and Dagger for workflow execution. It includes:

- `DaggerWorkflowIntegration` class for creating and executing workflows
- Support for executing workflows with or without a Dagger client
- Topological sorting of workflow stages based on dependencies
- Parameter substitution in workflow stages
- Workflow status tracking and reporting

### Example Usage (`dagger_workflow_example.py`)

The `dagger_workflow_example.py` script demonstrates how to use the Dagger Workflow Integration. It includes:

- Creating a custom workflow template
- Creating a workflow from a template
- Executing a workflow
- Monitoring workflow status
- Handling workflow results

## Usage

### Creating a Workflow Template

```python
from workflow_templates import WorkflowTemplate

template = WorkflowTemplate(
    template_id="example_workflow",
    name="Example Workflow",
    description="An example workflow",
    category="example",
    version="1.0.0",
    parameters={
        "input_file": "data.csv",
        "output_dir": "/tmp/output",
    },
    stages=[
        {
            "id": "stage1",
            "name": "Stage 1",
            "description": "First stage",
            "agent": "agent1",
            "inputs": {
                "input_file": "${parameters.input_file}",
            }
        },
        {
            "id": "stage2",
            "name": "Stage 2",
            "description": "Second stage",
            "agent": "agent2",
            "depends_on": ["stage1"],
            "inputs": {
                "input_file": "${stages.stage1.outputs.result}",
                "output_dir": "${parameters.output_dir}",
            }
        }
    ],
    metadata={
        "tags": ["example"],
        "complexity": "low",
    }
)
```

### Creating and Executing a Workflow

```python
from dagger_workflow_integration import DaggerWorkflowIntegration

# Initialize the integration
integration = DaggerWorkflowIntegration(dagger_client=None)  # Use mock execution mode

# Register a template
integration.save_workflow_template(template)

# Create a workflow from the template
workflow = integration.create_workflow(
    template_id="example_workflow",
    task_id="task_001",
    parameters={
        "input_file": "custom.csv",
    }
)

# Execute the workflow
result = integration.execute_workflow(workflow["workflow_id"])

# Get workflow status
status = integration.get_workflow_status(workflow["workflow_id"])
```

## Running the Example

To run the example script:

```bash
# Set up the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create templates directory if it doesn't exist
mkdir -p src/task_manager/mcp_servers/templates

# Run the example
src/task_manager/mcp_servers/dagger_workflow_example.py
```

Or use the provided script:

```bash
./run_dagger_workflow_example.sh
```

## Testing

The implementation includes tests to verify the functionality of the workflow templates and Dagger workflow integration. To run the tests:

```bash
# Run the workflow templates test
./run_workflow_templates_test.sh

# Run the standalone test
./run_standalone_test.sh
```

## Integration with Task Manager MCP Server

The Dagger Workflow Integration is designed to be integrated with the Task Manager MCP Server. It provides a way to define, manage, and execute workflows using Dagger, which can be used to automate tasks in the AI-Orchestration-Platform.

To integrate with the Task Manager MCP Server, the `task_manager_server.py` module should import and use the `DaggerWorkflowIntegration` class to provide workflow management functionality to MCP clients.
