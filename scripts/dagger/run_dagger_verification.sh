#!/bin/bash
# Run Dagger Workflow Integration Verification
# This script runs the verification script with the necessary environment variables.

# Set up environment variables
export TASK_MANAGER_DAGGER_ENABLED=1
export TASK_MANAGER_DAGGER_CONFIG="$(pwd)/config/dagger.yaml"
export TASK_MANAGER_DATA_DIR="$(pwd)/.task-manager"

# Create data directory if it doesn't exist
mkdir -p "$TASK_MANAGER_DATA_DIR"

# Print environment variables
echo "Running verification with the following configuration:"
echo "TASK_MANAGER_DAGGER_ENABLED=$TASK_MANAGER_DAGGER_ENABLED"
echo "TASK_MANAGER_DAGGER_CONFIG=$TASK_MANAGER_DAGGER_CONFIG"
echo "TASK_MANAGER_DATA_DIR=$TASK_MANAGER_DATA_DIR"
echo

# Run the verification script
echo "Starting verification..."
python3 ./verify_dagger_workflow_integration.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Verification completed successfully!"
    exit 0
else
    echo "Verification failed!"
    exit 1
fi
