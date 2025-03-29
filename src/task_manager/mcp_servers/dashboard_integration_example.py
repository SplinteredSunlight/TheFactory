#!/usr/bin/env python3
"""
Dashboard UI Integration Example

This script demonstrates how to use the Dashboard UI Integration component
of the Task Management MCP Server.
"""

import asyncio
import json
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.client import Client


async def main():
    """Run the dashboard integration example."""
    print("Dashboard UI Integration Example")
    print("================================")
    
    # Connect to the Task Manager MCP Server
    client = Client()
    await client.connect()
    
    try:
        # Get dashboard statistics
        print("\n1. Getting dashboard statistics...")
        stats = await get_dashboard_stats(client)
        print(f"Total projects: {stats['total_projects']}")
        print(f"Active projects: {stats['active_projects']}")
        print(f"Completed projects: {stats['completed_projects']}")
        print(f"Total tasks: {stats['total_tasks']}")
        print(f"Completed tasks: {stats['completed_tasks']}")
        print(f"In-progress tasks: {stats['in_progress_tasks']}")
        print(f"Planned tasks: {stats['planned_tasks']}")
        print(f"Blocked tasks: {stats['blocked_tasks']}")
        
        # Get dashboard configuration
        print("\n2. Getting dashboard configuration...")
        config = await get_dashboard_config(client)
        print(f"API base URL: {config['api']['baseUrl']}")
        print(f"UI theme: {config['ui']['theme']}")
        print(f"Default view: {config['ui']['defaultView']}")
        
        # Get projects summary
        print("\n3. Getting projects summary...")
        summaries = await get_projects_summary(client)
        for project in summaries:
            print(f"\nProject: {project['name']}")
            print(f"Description: {project['description']}")
            print(f"Progress: {project['progress']}%")
            print(f"Tasks: {project['taskCount']} ({project['completedTasks']} completed)")
            print("Phases:")
            for phase in project['phases']:
                print(f"  - {phase['name']}: {phase['progress']}% ({phase['completedTasks']}/{phase['taskCount']})")
        
        # Get recent tasks
        print("\n4. Getting recent tasks...")
        tasks = await get_recent_tasks(client)
        print("Recent tasks:")
        for task in tasks:
            print(f"- {task['name']} ({task['status']})")
            print(f"  Project: {task['projectName']}")
            if 'updatedAt' in task and task['updatedAt']:
                print(f"  Updated: {task['updatedAt']}")
        
        # Scan a directory for project files
        print("\n5. Scanning directory for project files...")
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
        projects = await scan_directory(client, directory)
        print(f"Found {len(projects)} projects in {directory}")
        for project in projects:
            print(f"- {project['name']}")
        
        # Update dashboard configuration
        print("\n6. Updating dashboard configuration...")
        success = await update_dashboard_config(client, {
            "ui": {
                "theme": "dark" if config['ui']['theme'] == "light" else "light"
            }
        })
        print(f"Configuration updated: {success}")
        
        # Get updated configuration
        print("\n7. Getting updated configuration...")
        updated_config = await get_dashboard_config(client)
        print(f"UI theme: {updated_config['ui']['theme']}")
        
    finally:
        # Close the client connection
        await client.close()


async def get_dashboard_stats(client):
    """Get dashboard statistics.
    
    Args:
        client: The MCP client
        
    Returns:
        Dict containing dashboard statistics
    """
    response = await client.read_resource("task-manager://dashboard/stats")
    return json.loads(response.contents[0].text)


async def get_dashboard_config(client):
    """Get dashboard configuration.
    
    Args:
        client: The MCP client
        
    Returns:
        Dict containing dashboard configuration
    """
    response = await client.read_resource("task-manager://dashboard/config")
    return json.loads(response.contents[0].text)


async def get_projects_summary(client):
    """Get a summary of all projects.
    
    Args:
        client: The MCP client
        
    Returns:
        List of project summaries
    """
    response = await client.read_resource("task-manager://dashboard/projects/summary")
    return json.loads(response.contents[0].text)


async def get_recent_tasks(client, limit=5):
    """Get recently updated tasks.
    
    Args:
        client: The MCP client
        limit: Maximum number of tasks to return
        
    Returns:
        List of recent tasks
    """
    response = await client.call_tool("task-manager", "get_recent_tasks", {
        "limit": limit
    })
    return json.loads(response.content[0].text)


async def scan_directory(client, directory):
    """Scan a directory for project files.
    
    Args:
        client: The MCP client
        directory: Directory to scan
        
    Returns:
        List of projects found in the directory
    """
    response = await client.call_tool("task-manager", "scan_directory", {
        "directory": directory,
        "depth": 2,
        "include_patterns": ["*.json", "*.yaml", "*.md"],
        "exclude_patterns": ["node_modules", ".git", "dist", "build"]
    })
    result = json.loads(response.content[0].text)
    return result["projects"]


async def update_dashboard_config(client, config_updates):
    """Update the dashboard configuration.
    
    Args:
        client: The MCP client
        config_updates: Configuration updates to apply
        
    Returns:
        True if the configuration was updated successfully
    """
    # Get current configuration
    current_config = await get_dashboard_config(client)
    
    # Apply updates
    for key, value in config_updates.items():
        if key in current_config:
            if isinstance(value, dict) and isinstance(current_config[key], dict):
                # Merge dictionaries
                current_config[key].update(value)
            else:
                # Replace value
                current_config[key] = value
        else:
            # Add new key
            current_config[key] = value
    
    # Update configuration
    response = await client.call_tool("task-manager", "update_dashboard_config", {
        "config": current_config
    })
    result = json.loads(response.content[0].text)
    return result["success"]


if __name__ == "__main__":
    asyncio.run(main())
