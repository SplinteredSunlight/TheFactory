# Task Management CLI Tool

This command-line interface (CLI) tool provides a convenient way to interact with the Task Management system from the terminal. It allows you to create, update, and manage projects, phases, and tasks without needing to use the web interface or MCP server.

## Installation

The CLI tool is already installed as part of the AI-Orchestration-Platform. You can run it using the `task-cli` command from the project root directory.

## Usage

```bash
./task-cli <command> [options]
```

### Global Options

- `--data-dir <directory>`: Specify a custom data directory for the task manager

### Commands

#### Project Management

- **list-projects**: List all projects
  ```bash
  ./task-cli list-projects
  ```

- **create-project**: Create a new project
  ```bash
  ./task-cli create-project --name "My Project" --description "A sample project"
  ```

- **get-project**: Get project details
  ```bash
  ./task-cli get-project --project-id project_123
  ```

- **update-project**: Update a project
  ```bash
  ./task-cli update-project --project-id project_123 --name "New Name" --description "New description"
  ```

- **delete-project**: Delete a project
  ```bash
  ./task-cli delete-project --project-id project_123
  ```

#### Phase Management

- **create-phase**: Create a new phase in a project
  ```bash
  ./task-cli create-phase --project-id project_123 --name "Phase 1" --description "First phase" --order 1
  ```

- **list-phases**: List phases in a project
  ```bash
  ./task-cli list-phases --project-id project_123
  ```

#### Task Management

- **create-task**: Create a new task
  ```bash
  ./task-cli create-task --name "Task 1" --description "A sample task" --project-id project_123 --phase-id phase_123
  ```

- **get-task**: Get task details
  ```bash
  ./task-cli get-task --task-id task_123
  ```

- **list-tasks**: List tasks in a project
  ```bash
  ./task-cli list-tasks --project-id project_123
  ```

- **update-task**: Update a task
  ```bash
  ./task-cli update-task --task-id task_123 --name "New Name" --description "New description" --status in_progress
  ```

- **update-task-status**: Update task status
  ```bash
  ./task-cli update-task-status --task-id task_123 --status in_progress
  ```

- **update-task-progress**: Update task progress
  ```bash
  ./task-cli update-task-progress --task-id task_123 --progress 50
  ```

- **delete-task**: Delete a task
  ```bash
  ./task-cli delete-task --task-id task_123
  ```

#### Calculation Commands

- **calculate-project-progress**: Calculate project progress
  ```bash
  ./task-cli calculate-project-progress --project-id project_123
  ```

- **calculate-phase-progress**: Calculate phase progress
  ```bash
  ./task-cli calculate-phase-progress --project-id project_123 --phase-id phase_123
  ```

#### Query Commands

- **get-tasks-by-status**: Get tasks by status
  ```bash
  ./task-cli get-tasks-by-status --project-id project_123 --status in_progress
  ```

- **get-tasks-by-assignee**: Get tasks by assignee
  ```bash
  ./task-cli get-tasks-by-assignee --assignee-id user_123
  ```

## Examples

### Creating a Project and Tasks

```bash
# Create a new project
./task-cli create-project --name "Website Redesign" --description "Redesign the company website"

# Create phases for the project
./task-cli create-phase --project-id project_abc123 --name "Planning" --description "Planning phase" --order 1
./task-cli create-phase --project-id project_abc123 --name "Design" --description "Design phase" --order 2
./task-cli create-phase --project-id project_abc123 --name "Development" --description "Development phase" --order 3
./task-cli create-phase --project-id project_abc123 --name "Testing" --description "Testing phase" --order 4

# Create tasks in the phases
./task-cli create-task --name "Define Requirements" --description "Define website requirements" --project-id project_abc123 --phase-id phase_123 --status in_progress
./task-cli create-task --name "Create Mockups" --description "Create website mockups" --project-id project_abc123 --phase-id phase_456
```

### Tracking Progress

```bash
# Update task status
./task-cli update-task-status --task-id task_123 --status completed

# Update task progress
./task-cli update-task-progress --task-id task_456 --progress 75

# Calculate project progress
./task-cli calculate-project-progress --project-id project_abc123
```

### Querying Tasks

```bash
# Get all tasks in a project
./task-cli list-tasks --project-id project_abc123

# Get tasks in a specific phase
./task-cli list-tasks --project-id project_abc123 --phase-id phase_123

# Get tasks with a specific status
./task-cli get-tasks-by-status --project-id project_abc123 --status in_progress

# Get tasks assigned to a specific user
./task-cli get-tasks-by-assignee --assignee-id user_123
```

## Integration with Other Tools

The Task Management CLI Tool can be easily integrated with other tools and scripts. For example, you can use it in shell scripts to automate task management:

```bash
#!/bin/bash

# Create a new project
PROJECT_ID=$(./task-cli create-project --name "Automated Project" --description "Created by script" | grep "Project created with ID" | awk '{print $5}')

# Create phases
PLANNING_PHASE_ID=$(./task-cli create-phase --project-id "$PROJECT_ID" --name "Planning" --order 1 | grep "Phase created with ID" | awk '{print $5}')
EXECUTION_PHASE_ID=$(./task-cli create-phase --project-id "$PROJECT_ID" --name "Execution" --order 2 | grep "Phase created with ID" | awk '{print $5}')

# Create tasks
./task-cli create-task --name "Task 1" --description "First task" --project-id "$PROJECT_ID" --phase-id "$PLANNING_PHASE_ID"
./task-cli create-task --name "Task 2" --description "Second task" --project-id "$PROJECT_ID" --phase-id "$EXECUTION_PHASE_ID"

# Calculate project progress
./task-cli calculate-project-progress --project-id "$PROJECT_ID"
```

## Troubleshooting

If you encounter any issues with the Task Management CLI Tool, try the following:

1. **Check the data directory**: Make sure the data directory exists and is writable
2. **Check the project and task IDs**: Verify that you're using the correct IDs
3. **Check the command syntax**: Make sure you're using the correct command syntax and options
4. **Check the Python environment**: Make sure Python is installed and in your PATH

## Contributing

If you'd like to contribute to the Task Management CLI Tool, please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
