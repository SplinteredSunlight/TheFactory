# Dagger Task Management User Guide

This guide provides instructions for using the new Dagger-based Task Management System.

## Introduction

The Dagger Task Management System is a powerful tool for managing tasks, projects, and workflows. It provides a seamless integration with Dagger for workflow execution, enabling you to automate complex task pipelines.

## Getting Started

### Installation

The Dagger Task Management System is installed as part of the AI Orchestration Platform. To install it, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/example/ai-orchestration-platform.git
   ```

2. Install dependencies:
   ```bash
   cd ai-orchestration-platform
   pip install -r requirements.txt
   ```

3. Configure Dagger:
   ```bash
   cp config/example.env config/.env
   # Edit config/.env with your settings
   ```

4. Start the system:
   ```bash
   python src/api/main.py
   ```

### Configuration

The Dagger Task Management System is configured using the following files:

- `config/dagger.yaml`: Dagger configuration
- `config/default.yaml`: Default system configuration
- `config/.env`: Environment variables

## Core Concepts

### Projects

Projects are the top-level organizational units in the Task Management System. They contain phases and tasks.

### Phases

Phases represent stages in a project's lifecycle. They help organize tasks into logical groups.

### Tasks

Tasks are the individual units of work. They can be assigned to users or agents, have dependencies, and be part of workflows.

### Workflows

Workflows are automated sequences of tasks. They are executed using Dagger and can include complex logic, dependencies, and conditions.

## Basic Usage

### Creating a Project

To create a project:

1. Navigate to the Projects page
2. Click "New Project"
3. Enter the project details:
   - Name
   - Description
   - Metadata (optional)
4. Click "Create"

### Creating a Phase

To create a phase:

1. Navigate to the project
2. Click "New Phase"
3. Enter the phase details:
   - Name
   - Description
   - Order
4. Click "Create"

### Creating a Task

To create a task:

1. Navigate to the project or phase
2. Click "New Task"
3. Enter the task details:
   - Name
   - Description
   - Status
   - Priority
   - Assignee (optional)
   - Metadata (optional)
4. Click "Create"

### Creating a Workflow

To create a workflow:

1. Navigate to the task
2. Click "Create Workflow"
3. Select a workflow template
4. Configure the workflow parameters
5. Click "Create"

### Executing a Workflow

To execute a workflow:

1. Navigate to the task
2. Click "Execute Workflow"
3. Configure the execution parameters (optional)
4. Click "Execute"

## Advanced Usage

### Custom Workflow Templates

You can create custom workflow templates to automate specific types of tasks. Templates are defined in YAML format and stored in the `templates` directory.

Example template:

```yaml
# Basic Task Workflow Template
metadata:
  name: basic_task
  description: A basic task workflow template
  version: 1.0.0
  category: general
  tags:
    - basic
    - task

parameters:
  task_name:
    type: string
    description: The name of the task
    required: true
  task_command:
    type: string
    description: The command to execute
    required: true

steps:
  - name: execute_task
    description: Execute the task
    container:
      image: alpine:latest
      command: ${task_command}
      workdir: /app

outputs:
  result:
    description: The result of the task
    value: ${steps.execute_task.output}
```

### Task Dependencies

Tasks can have dependencies on other tasks. To create a dependency:

1. Navigate to the task
2. Click "Edit"
3. In the "Dependencies" section, select the tasks that must be completed before this task
4. Click "Save"

### Task Metadata

Tasks can have metadata associated with them. This metadata can be used by workflows and integrations.

To add metadata to a task:

1. Navigate to the task
2. Click "Edit"
3. In the "Metadata" section, add key-value pairs
4. Click "Save"

## Integration with Other Systems

### API Integration

The Dagger Task Management System provides a RESTful API for integration with other systems. The API is documented in the [API Reference](../dagger/api-reference.md).

### Webhook Integration

You can configure webhooks to notify external systems when tasks or workflows are created, updated, or completed.

To configure a webhook:

1. Navigate to the Settings page
2. Click "Webhooks"
3. Click "New Webhook"
4. Enter the webhook details:
   - URL
   - Events to trigger the webhook
   - Secret (optional)
5. Click "Create"

## Troubleshooting

### Common Issues

1. **Workflow execution fails**
   - Check the workflow logs
   - Verify that the workflow parameters are correct
   - Check that the required dependencies are installed

2. **Task creation fails**
   - Check that the required fields are provided
   - Verify that the project and phase exist

3. **API requests fail**
   - Check that the API key is valid
   - Verify that the request format is correct
   - Check the API logs for errors

### Getting Help

If you encounter issues that are not covered in this guide, please contact support:

- Email: support@example.com
- Slack: #dagger-task-management
- GitHub Issues: https://github.com/example/ai-orchestration-platform/issues

## Reference

### Task Statuses

- `planned`: Task is planned but not started
- `in_progress`: Task is in progress
- `completed`: Task is completed
- `blocked`: Task is blocked by a dependency or issue
- `cancelled`: Task is cancelled

### Task Priorities

- `low`: Low priority
- `medium`: Medium priority
- `high`: High priority
- `critical`: Critical priority

### Workflow Types

- `containerized_workflow`: Workflow that runs in a container
- `script_workflow`: Workflow that runs a script
- `api_workflow`: Workflow that calls an API
- `composite_workflow`: Workflow that combines multiple workflows

## Glossary

- **Dagger**: A workflow engine for containerized applications
- **Project**: A top-level organizational unit
- **Phase**: A stage in a project's lifecycle
- **Task**: An individual unit of work
- **Workflow**: An automated sequence of tasks
- **Template**: A reusable workflow definition
- **Metadata**: Additional data associated with a task or project
- **Webhook**: A mechanism for notifying external systems of events
