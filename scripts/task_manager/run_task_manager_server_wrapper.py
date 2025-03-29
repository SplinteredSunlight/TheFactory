#!/usr/bin/env python3
"""
Task Manager Server Wrapper

This script runs the Task Manager MCP server directly, without importing it as a module.
"""

import os
import sys
import subprocess

# Set up environment variables
os.environ["TASK_MANAGER_DAGGER_ENABLED"] = "1"
os.environ["TASK_MANAGER_DAGGER_CONFIG"] = os.path.join(os.getcwd(), "config/dagger.yaml")
os.environ["TASK_MANAGER_DATA_DIR"] = os.path.join(os.getcwd(), ".task-manager")
os.environ["PYTHONPATH"] = f"{os.getcwd()}:{os.path.join(os.getcwd(), 'mock_modules')}"

# Create data directory if it doesn't exist
os.makedirs(os.environ["TASK_MANAGER_DATA_DIR"], exist_ok=True)

# Print environment variables
print("Running Task Manager MCP Server with the following configuration:")
print(f"TASK_MANAGER_DAGGER_ENABLED={os.environ['TASK_MANAGER_DAGGER_ENABLED']}")
print(f"TASK_MANAGER_DAGGER_CONFIG={os.environ['TASK_MANAGER_DAGGER_CONFIG']}")
print(f"TASK_MANAGER_DATA_DIR={os.environ['TASK_MANAGER_DATA_DIR']}")
print(f"PYTHONPATH={os.environ['PYTHONPATH']}")
print()

# Run the Task Manager MCP Server
print("Starting Task Manager MCP Server with Mock Dagger integration...")

# Run the task_manager_server.py script directly
subprocess.run([
    "python3", 
    "src/task_manager/mcp_servers/task_manager_server.py",
    "--enable-dagger",
    "--dagger-config", os.environ["TASK_MANAGER_DAGGER_CONFIG"],
    "--data-dir", os.environ["TASK_MANAGER_DATA_DIR"]
])
