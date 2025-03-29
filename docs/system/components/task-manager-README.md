# AI-Orchestration-Platform Task Management System

This task management system helps track progress on integration work between AI-Orchestrator and Fast-Agent. It provides tools for managing tasks, generating prompts, and maintaining context across development sessions.

## Setup

To initialize the task management system, run:

```bash
./scripts/init-task-system.sh
```

This will:
- Set up the necessary directories
- Create a symbolic link to the task command in the project root
- Make all task scripts executable
- Create initial configuration files if they don't exist

## Usage

After initialization, you can use the following commands:

### Basic Commands

- `./task status` - Show the current task status
- `./task next` - Generate the prompt for the next task
- `./task complete` - Mark the current task as completed and move to the next task
- `./task help` - Show help message with all available commands

### Advanced Commands

- `./task start [--browser]` - Prepare the task prompt for Claude and copy to clipboard. With the `--browser` flag, it will also open Claude in your default browser.
- `./task cline [options]` - Run the Cline workflow (optimized for VS Code)

### Template Options

When generating task prompts, you can specify a template to use:

```bash
./task next --template integration-task
```

Available templates:
- `default` - Standard task template
- `concise` - Minimal task information
- `detailed` - Comprehensive task details with context
- `integration-task` - Specialized for AI-Orchestrator and Fast-Agent integration
- `orchestrator-enhancement` - For enhancing the Orchestrator component
- `agent-integration` - For integrating with Fast-Agent
- `frontend-integration` - For frontend integration work

### Sub-tasks

For complex tasks, you can use sub-tasks:

```bash
./task complete --sub-task "API Endpoint Implementation"
```

## Project Structure

The task management system uses the following files:

- `docs/project-plan.md` - The main project plan with phases and tasks
- `docs/task-tracking.json` - Tracks the current task and completed tasks
- `docs/templates/task-prompt-templates.json` - Templates for task prompts
- `docs/context-cache.json` - Caches project context for task generation

## VS Code Integration

The task system includes VS Code tasks that can be accessed from the Command Palette (Ctrl+Shift+P or Cmd+Shift+P) by typing "Tasks: Run Task" and selecting one of the task options.

## Customization

You can customize the task templates by editing `docs/templates/task-prompt-templates.json`.

To add new tasks or phases, edit `docs/project-plan.md` and follow the existing format.
