#!/bin/bash

# Script to mark the current task as completed and move to the next task
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
      echo "  --template <n>    Use the specified template for the next task prompt"
      echo "  --sub-task <n>    Mark a specific sub-task as completed"
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

# Run the task-tracker.py script with the --complete flag to mark the current task as completed
if [ -n "$SUB_TASK" ]; then
  echo "Marking sub-task '$SUB_TASK' as completed..."
  python3 "$SCRIPT_DIR/task-tracker.py" --complete --sub-task "$SUB_TASK"
else
  echo "Marking current task as completed..."
  python3 "$SCRIPT_DIR/task-tracker.py" --complete
fi

echo "Task tracking data updated."

# Generate the prompt for the next task
"$SCRIPT_DIR/generate-next-task-prompt.sh" --template "$TEMPLATE"

echo "To view the current task status, run: ./task status"