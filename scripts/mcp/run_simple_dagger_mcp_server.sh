#!/bin/bash
# Run Simple Dagger MCP Server
# This script runs the Simple Dagger MCP Server with Dagger integration enabled,
# using mock modules for testing.

# Set up environment variables
export TASK_MANAGER_DAGGER_ENABLED=1
export TASK_MANAGER_DAGGER_CONFIG="$(pwd)/config/dagger.yaml"
export TASK_MANAGER_DATA_DIR="$(pwd)/.task-manager"
export PYTHONPATH="$(pwd):$(pwd)/mock_modules"

# Create data directory if it doesn't exist
mkdir -p "$TASK_MANAGER_DATA_DIR"

# Print environment variables
echo "Running Simple Dagger MCP Server with the following configuration:"
echo "TASK_MANAGER_DAGGER_ENABLED=$TASK_MANAGER_DAGGER_ENABLED"
echo "TASK_MANAGER_DAGGER_CONFIG=$TASK_MANAGER_DAGGER_CONFIG"
echo "TASK_MANAGER_DATA_DIR=$TASK_MANAGER_DATA_DIR"
echo "PYTHONPATH=$PYTHONPATH"
echo

# Run the Simple Dagger MCP Server
echo "Starting Simple Dagger MCP Server..."
./simple_dagger_mcp_server.py
