# Task Management System for AI-Orchestration-Platform

This package provides a comprehensive task management system for tracking projects, phases, and tasks with hierarchical relationships.

## Features

- **Hierarchical Task Management**: Create projects, phases, milestones, and tasks with parent-child relationships
- **Real-time Progress Tracking**: Visual representation of project progress with interactive components
- **Task Assignment**: Assign tasks to agents or users
- **Status Tracking**: Monitor task status and progress
- **API Integration**: Comprehensive API for integrating with other components
- **WebSocket Updates**: Real-time updates via WebSocket connections

## Components

### Backend

- `manager.py`: Core task management functionality
- `migrate_tasks.py`: Script to migrate from the old task tracking system

### API

- `src/api/routes/task_routes.py`: FastAPI endpoints for task management

### Frontend

- `src/frontend/src/components/progress/ProgressTracker.tsx`: Progress tracking component
- `src/frontend/src/components/ProjectProgressBar.tsx`: Simple progress bar component

## Usage

### Backend Usage

```python
from src.task_manager.manager import get_task_manager, TaskStatus

# Get the task manager singleton
task_manager = get_task_manager()

# Create a project
project = task_manager.create_project(
    name="My Project",
    description="This is my project",
    metadata={"key": "value"}
)

# Add a phase to the project
phase = project.add_phase(
    phase_id="phase_1",
    name="Phase 1",
    description="This is phase 1",
    order=1
)

# Create a task
task = task_manager.create_task(
    name="My Task",
    description="This is my task",
    project_id=project.id,
    phase_id=phase.id,
    status=TaskStatus.PLANNED,
    priority="medium",
    progress=0.0
)

# Update task status
task_manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)

# Update task progress
task_manager.update_task_progress(task.id, 50.0)  # 50%

# Get project progress
progress = task_manager.calculate_project_progress(project.id)
```

### Frontend Usage

#### Using the ProgressTracker Component

```tsx
import ProgressTracker from '../components/progress/ProgressTracker';

// In your component:
return (
  <div>
    {/* Other content */}
    
    {/* Embedded mode */}
    <ProgressTracker
      projectId="your_project_id"
      mode="embedded"
      showTitle={true}
      height={400}
    />
    
    {/* Or as a popup */}
    <ProgressTracker
      projectId="your_project_id"
      mode="popup"
    />
  </div>
);
```

#### Using the ProjectProgressBar Component

```tsx
import { ProjectProgressBar } from '../components/ProjectProgressBar';

// In your component:
return (
  <div>
    {/* Other content */}
    
    <ProjectProgressBar
      projectId="your_project_id"
      showDetails={true}
      variant="linear"
      size="medium"
    />
  </div>
);
```

## API Endpoints

The task management system provides the following API endpoints:

### Projects

- `GET /tasks/projects`: Get all projects
- `POST /tasks/projects`: Create a new project
- `GET /tasks/projects/{project_id}`: Get a project by ID
- `PUT /tasks/projects/{project_id}`: Update a project
- `DELETE /tasks/projects/{project_id}`: Delete a project
- `GET /tasks/projects/{project_id}/progress`: Get project progress

### Phases

- `GET /tasks/projects/{project_id}/phases`: Get all phases in a project
- `POST /tasks/projects/{project_id}/phases`: Create a new phase in a project
- `GET /tasks/projects/{project_id}/phases/{phase_id}`: Get a phase by ID

### Tasks

- `GET /tasks/projects/{project_id}/tasks`: Get all tasks in a project
- `POST /tasks/tasks`: Create a new task
- `GET /tasks/tasks/{task_id}`: Get a task by ID
- `PUT /tasks/tasks/{task_id}`: Update a task
- `DELETE /tasks/tasks/{task_id}`: Delete a task
- `PUT /tasks/tasks/{task_id}/status`: Update a task's status
- `PUT /tasks/tasks/{task_id}/progress`: Update a task's progress
- `GET /tasks/assignee/{assignee_id}/tasks`: Get all tasks assigned to a specific assignee

### WebSocket

- `WebSocket /tasks/ws/{project_id}`: WebSocket endpoint for real-time updates

## Migration

To migrate from the old task tracking system to the new task management system, run the migration script:

```bash
./migrate-tasks.sh
```

This will:

1. Read the existing task tracking data from `docs/task-tracking.json`
2. Extract phases from the project plan in `docs/project-plan.md`
3. Create a new project with phases and tasks in the new task management system
4. Save the data to disk

After migration, you can use the new task management system to manage your tasks.

## Integration with Agent System

The task management system is designed to work with the agent system. You can assign tasks to agents and execute tasks with agents.

```python
from src.agent_manager.manager import get_agent_manager
from src.task_manager.manager import get_task_manager

# Get managers
agent_manager = get_agent_manager()
task_manager = get_task_manager()

# Get an agent
agent = agent_manager.get_agent(agent_id)

# Assign a task to the agent
task = task_manager.update_task(
    task_id="your_task_id",
    assignee_id=agent.id,
    assignee_type="agent"
)

# Execute a task with an agent
def execute_task_with_agent(task_id, agent_id):
    # Get task and agent
    task = task_manager.get_task(task_id)
    agent = agent_manager.get_agent(agent_id)
    
    # Update task status to in progress
    task_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
    try:
        # Execute the agent with task parameters
        result = agent.execute(
            task_id=task_id,
            task_name=task.name,
            **task.metadata  # Pass any additional parameters
        )
        
        # Update task with result
        task_manager.update_task(task_id, result=result)
        task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        task_manager.update_task_progress(task_id, 100.0)
        
        return result
    except Exception as e:
        # Handle failure
        task_manager.update_task(task_id, error=str(e))
        task_manager.update_task_status(task_id, TaskStatus.FAILED)
        raise
