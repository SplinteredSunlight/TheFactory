# Task Manager Service

The Task Manager Service is a command-line tool for managing tasks in the AI Orchestration Platform. It provides functionality for finding the next task to work on, generating task prompts, marking tasks as complete, and automatically progressing to the next task.

## Installation

The Task Manager Service is included in the AI Orchestration Platform. No additional installation is required.

## Usage

The Task Manager Service provides the following commands:

### Get the Next Task

To get the next task to work on, run:

```bash
python3 scripts/task_manager_service.py next
```

This will display a detailed prompt for the next task, including:
- Task name and description
- Project and phase information
- Priority and status
- Progress
- Subtasks
- Estimated hours
- Acceptance criteria
- Instructions for completion

You can filter by project name:

```bash
python3 scripts/task_manager_service.py next --project "AI Orchestration Platform Enhancement"
```

You can also execute the task workflow automatically:

```bash
python3 scripts/task_manager_service.py next --execute
```

### Mark a Task as Complete

To mark a task as complete and get the next task, run:

```bash
python3 scripts/task_manager_service.py complete "Task Name"
```

This will:
1. Mark the specified task as complete
2. Set its progress to 100%
3. Record the completion timestamp
4. Display the next task to work on

### Get Task Details

To get details about a specific task, run:

```bash
python3 scripts/task_manager_service.py details "Task Name"
```

### List Tasks

To list all tasks, run:

```bash
python3 scripts/task_manager_service.py list
```

You can filter by project name and status:

```bash
python3 scripts/task_manager_service.py list --project "AI Orchestration Platform Enhancement" --status "planned"
```

## Task Prioritization

Tasks are prioritized based on:
1. Phase order (earlier phases first)
2. Priority (high, medium, low)

Only tasks with status "planned" are considered for the next task.

## Task Prompt Format

The task prompt includes:

- **Task Name**: The name of the task
- **Project**: The project the task belongs to
- **Phase**: The phase the task belongs to
- **Priority**: The priority of the task (high, medium, low)
- **Status**: The status of the task (planned, in_progress, completed)
- **Progress**: The progress of the task (0-100%)
- **Description**: A detailed description of the task
- **Subtasks**: A list of subtasks to complete
- **Estimated Hours**: The estimated time to complete the task
- **Acceptance Criteria**: Criteria for task completion
- **Instructions**: Step-by-step instructions for completing the task

## Integration with Dagger

The Task Manager Service integrates with Dagger for task workflow execution. When a task is executed, a workflow is created and run using the Dagger integration.

## Examples

### Example 1: Get the Next Task

```bash
$ python3 scripts/task_manager_service.py next
# Task: Standardize Directory Structure

**Project**: AI Orchestration Platform Enhancement
**Phase**: Cleanup and Organization
**Priority**: high
**Status**: planned
**Progress**: 0%

## Description

Implement the desired project structure as outlined in claude-prompt.md

## Subtasks

- [ ] Reorganize source code directories
- [ ] Consolidate configuration files
- [ ] Standardize documentation structure
- [ ] Organize test files

**Estimated Hours**: 8

## Acceptance Criteria

- All subtasks completed
- Code follows project standards
- Tests pass
- Documentation updated

## Instructions

1. Complete all subtasks
2. Run tests to ensure everything works
3. Update documentation if necessary
4. Mark the task as complete using the task manager service

To mark this task as complete, run:

```bash
python scripts/task_manager_service.py complete "Standardize Directory Structure"
```
```

### Example 2: Mark a Task as Complete

```bash
$ python3 scripts/task_manager_service.py complete "Test Task"
Task 'Test Task' marked as complete

Next task:
# Task: Standardize Directory Structure
...
```

### Example 3: List Tasks

```bash
$ python3 scripts/task_manager_service.py list --status "planned"
Found 20 tasks:
- Standardize Directory Structure (AI Orchestration Platform Enhancement, Cleanup and Organization, planned, high)
- Consolidate Similar Functionality (AI Orchestration Platform Enhancement, Cleanup and Organization, planned, medium)
...
```

## Workflow

The typical workflow for using the Task Manager Service is:

1. Run `python3 scripts/task_manager_service.py next` to get the next task
2. Complete the task
3. Run `python3 scripts/task_manager_service.py complete "Task Name"` to mark the task as complete and get the next task
4. Repeat

This workflow ensures that tasks are completed in the correct order and that progress is tracked accurately.
