#!/bin/bash
# Run Task Manager MCP Server with Dagger Integration
# This script runs the Task Manager MCP Server with Dagger integration enabled.

# Set up environment variables
export TASK_MANAGER_DAGGER_ENABLED=1
export TASK_MANAGER_DAGGER_CONFIG="$(pwd)/config/dagger.yaml"
export TASK_MANAGER_DATA_DIR="$(pwd)/.task-manager"

# Create data directory if it doesn't exist
mkdir -p "$TASK_MANAGER_DATA_DIR"

# Print environment variables
echo "Running Task Manager MCP Server with the following configuration:"
echo "TASK_MANAGER_DAGGER_ENABLED=$TASK_MANAGER_DAGGER_ENABLED"
echo "TASK_MANAGER_DAGGER_CONFIG=$TASK_MANAGER_DAGGER_CONFIG"
echo "TASK_MANAGER_DATA_DIR=$TASK_MANAGER_DATA_DIR"
echo

# Run the Task Manager MCP Server
echo "Starting Task Manager MCP Server with Dagger integration..."
python3 -m src.task_manager.mcp_servers.task_manager_server --enable-dagger --dagger-config "$TASK_MANAGER_DAGGER_CONFIG" --data-dir "$TASK_MANAGER_DATA_DIR"
