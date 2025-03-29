# AI Orchestration Platform Task Manager

This README provides information on how to use the Task Manager system for the AI Orchestration Platform.

## Overview

The Task Manager is a system for organizing and tracking tasks for the AI Orchestration Platform. It provides a hierarchical structure of projects, phases, and tasks, and integrates with Dagger for containerized workflow execution.

## Project Structure

The project structure in the Task Manager is organized as follows:

- **Project**: AI Orchestration Platform Enhancement
  - **Phase 1**: Cleanup and Organization
    - Task 1.1: Remove Legacy Migration Files
    - Task 1.2: Standardize Directory Structure
    - Task 1.3: Consolidate Similar Functionality
    - Task 1.4: Standardize Naming Conventions
  - **Phase 2**: Core Improvements
    - Task 2.1: Enhance Workflow Templates
    - Task 2.2: Improve Parameter Substitution
    - Task 2.3: Add Workflow Validation
    - Task 2.4: Extend Dagger Integration
    - Task 2.5: Improve Error Handling
  - **Phase 3**: Testing Implementation
    - Task 3.1: Create Unit Tests
    - Task 3.2: Implement Integration Tests
    - Task 3.3: Develop End-to-End Tests
    - Task 3.4: Add Performance Tests
  - **Phase 4**: Dashboard Development
    - Task 4.1: Design Dashboard UI
    - Task 4.2: Implement Task Status Visualization
    - Task 4.3: Add Agent Performance Monitoring
    - Task 4.4: Create Metrics and Analytics
    - Task 4.5: Integrate with Task Management
  - **Phase 5**: Documentation
    - Task 5.1: Create Developer Documentation
    - Task 5.2: Develop User Guides
    - Task 5.3: Document API Endpoints
    - Task 5.4: Update README Files

## Scripts

The following scripts are available for working with the Task Manager:

### Setup Project Structure

The `scripts/setup_project_structure.py` script sets up the project structure in the Task Manager. It creates the project, phases, and tasks with their metadata.

```bash
python3 scripts/setup_project_structure.py
```

### Execute Task Workflow

The `scripts/execute_task_workflow.py` script demonstrates how to execute a workflow for a task using the Dagger integration. It finds a task by name, executes a workflow for it, and updates the task with the workflow result.

```bash
python3 scripts/execute_task_workflow.py
```

## Task Manager API

The Task Manager provides a Python API for working with tasks. Here's an example of how to use it:

```python
from src.task_manager.manager import get_task_manager

# Initialize task manager
task_manager = get_task_manager("data/new")

# Get a project
project = task_manager.get_project("project-4cbf0807-b2d4-4563-9425-f456b3d6dd0e")

# Create a new task
task = task_manager.create_task(
    name="New Task",
    description="A new task",
    project_id=project.id,
    phase_id=list(project.phases.keys())[0],
    status="planned",
    priority="medium",
    progress=0.0,
    metadata={
        "estimated_hours": 8,
        "subtasks": [
            "Subtask 1",
            "Subtask 2",
            "Subtask 3"
        ]
    }
)

# Update a task
task_manager.update_task(
    task_id=task.id,
    status="in_progress",
    progress=25.0
)

# Save the data
task_manager.save_data()
```

## Dagger Integration

The Task Manager integrates with Dagger for containerized workflow execution. Here's an example of how to use it:

```python
from src.task_manager.dagger_integration import get_task_workflow_integration

# Initialize task workflow integration
workflow_integration = get_task_workflow_integration(
    dagger_config_path="config/dagger.yaml",
    templates_dir="templates"
)

# Execute a workflow
result = await workflow_integration.execute_task_workflow(
    task_id="task-id",
    workflow_type="basic_task",
    workflow_params={
        "task_name": "Task Name",
        "task_description": "Task Description",
        "task_command": "echo 'Hello, World!'",
        "task_timeout": 3600,
        "task_image": "alpine:latest",
        "task_environment": {},
        "task_working_dir": "/app",
        "task_mounts": []
    },
    skip_cache=True
)
```

## Workflow Templates

The Task Manager supports the following workflow templates:

### Basic Task

The `basic_task` template is a simple workflow template for executing a command in a container. It requires the following parameters:

- `task_name`: The name of the task
- `task_description`: The description of the task
- `task_command`: The command to execute
- `task_timeout`: The timeout for the task in seconds (default: 3600)
- `task_image`: The container image to use (default: alpine:latest)
- `task_environment`: Environment variables for the task (default: {})
- `task_working_dir`: The working directory for the task (default: /app)
- `task_mounts`: Mounts for the task (default: [])

### Data Processing

The `data_processing` template is a workflow template for processing data. It requires the following parameters:

- `input_data`: The input data to process
- `output_path`: The path to save the processed data
- `processing_type`: The type of processing to perform (filter, transform, aggregate, analyze)
- `filter_criteria`: Criteria for filtering data (default: {})
- `transform_function`: Function to transform data (default: "")
- `aggregate_function`: Function to aggregate data (default: "")
- `analysis_type`: Type of analysis to perform (default: "")
- `timeout`: The timeout for the processing in seconds (default: 3600)
- `image`: The container image to use (default: python:3.9-slim)

## Next Steps

1. Start working on the tasks in the Task Manager, beginning with the "Remove Legacy Migration Files" task in the "Cleanup and Organization" phase.
2. Use the Dagger integration to execute workflows for tasks.
3. Update task status and progress as you complete tasks.
4. Create additional workflow templates as needed for specific tasks.
