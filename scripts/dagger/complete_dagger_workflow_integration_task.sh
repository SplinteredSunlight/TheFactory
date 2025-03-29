#!/bin/bash
# Script to mark the Dagger Workflow Integration task as completed

set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Run the verification script to ensure everything is working
echo "Running verification script..."
python3 scripts/dagger/verify_dagger_workflow_with_mock.py

# If verification passed, mark the task as completed
if [ $? -eq 0 ]; then
    echo "Verification passed! Marking task as completed..."
    
    # Update the task status in the task tracking system
    if [ -f ".task-manager/complete-current-task.sh" ]; then
        echo "Updating task status..."
        bash .task-manager/complete-current-task.sh
        echo "Task marked as completed!"
    else
        echo "Task completion script not found. Please mark the task as completed manually."
    fi
    
    echo "Dagger Workflow Integration has been successfully implemented!"
    echo "Documentation: docs/guides/DAGGER_WORKFLOW_INTEGRATION_README.md"
    echo "Implementation: src/task_manager/mcp_servers/dagger_workflow_integration.py"
    echo "Tests: tests/test_dagger_workflow_integration.py"
    echo "Verification: scripts/dagger/verify_dagger_workflow_with_mock.py"
else
    echo "Verification failed! Please fix the issues before marking the task as completed."
    exit 1
fi
