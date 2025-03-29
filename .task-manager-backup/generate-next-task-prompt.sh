#!/bin/bash

# Script to generate the next task prompt based on the task-tracking.json file
# Supports hierarchical tasks (parent tasks with child sub-tasks)

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse command line arguments
TEMPLATE="default"
SUB_TASK=""

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --template)
      TEMPLATE="$2"
      shift 2
      ;;
    --sub-task)
      SUB_TASK="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--template <template_name>] [--sub-task <sub_task_name>]"
      echo "Available templates: default, concise, detailed, integration-task, etc."
      echo "Options:"
      echo "  --template <name>    Use the specified template for the task prompt"
      echo "  --sub-task <name>    Generate a prompt for a specific sub-task"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--template <template_name>] [--sub-task <sub_task_name>]"
      echo "Use --help for more information"
      exit 1
      ;;
  esac
done

# Update the context cache first to ensure it's current
echo "Updating context cache..."
python3 "$SCRIPT_DIR/context-manager.py" --update

# If a sub-task is specified and the template is not explicitly set to something else,
# use the subtask template by default
if [ -n "$SUB_TASK" ] && [ "$TEMPLATE" = "default" ]; then
  TEMPLATE="subtask"
fi

# Run the task-tracker.py script with the --next flag to generate the prompt
if [ -n "$SUB_TASK" ]; then
  echo "Generating prompt for sub-task '$SUB_TASK' using the '$TEMPLATE' template..."
  python3 "$SCRIPT_DIR/task-tracker.py" --next --template "$TEMPLATE" --sub-task "$SUB_TASK" > "$PROJECT_ROOT/docs/next-task-prompt.md"
else
  echo "Generating prompt for the next task using the '$TEMPLATE' template..."
  python3 "$SCRIPT_DIR/task-tracker.py" --next --template "$TEMPLATE" > "$PROJECT_ROOT/docs/next-task-prompt.md"
fi

echo "Next task prompt generated at docs/next-task-prompt.md"

# Display the prompt
echo "====================== NEXT TASK PROMPT ======================"
cat "$PROJECT_ROOT/docs/next-task-prompt.md"
echo "=============================================================="

echo "To use this prompt, copy and paste it into your next task request."
echo "Available templates: default, concise, detailed, integration-task, orchestrator-enhancement, agent-integration, frontend-integration"
echo "For hierarchical tasks, use --sub-task to generate prompts for specific sub-tasks"
