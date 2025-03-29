#!/usr/bin/env python3
"""
Run Task Manager MCP Server

This script runs the Task Manager MCP server, which provides task management
capabilities as MCP tools and resources.
"""

import argparse
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "mock_modules"))

# Use absolute import
from src.task_manager.mcp_servers.task_manager_server import TaskManagerServer


def main():
    """Run the Task Manager MCP server."""
    parser = argparse.ArgumentParser(description="Task Manager MCP Server")
    parser.add_argument("--data-dir", help="Directory for task manager data")
    parser.add_argument("--auth-token", help="Authentication token for API calls")
    parser.add_argument("--dagger-config", help="Path to Dagger configuration file")
    parser.add_argument("--enable-dagger", action="store_true", help="Enable Dagger workflow integration")
    args = parser.parse_args()
    
    # Set environment variables
    if args.enable_dagger:
        os.environ["TASK_MANAGER_DAGGER_ENABLED"] = "1"
    if args.dagger_config:
        os.environ["TASK_MANAGER_DAGGER_CONFIG"] = args.dagger_config
    
    # Create and run the server
    server = TaskManagerServer(
        data_dir=args.data_dir, 
        auth_token=args.auth_token,
        dagger_config_path=args.dagger_config
    )
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
