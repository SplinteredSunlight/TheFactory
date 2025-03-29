# Dashboard UI Integration for Task Management MCP Server

This component extends the Task Manager MCP Server with dashboard-specific tools and resources to enable integration with the Project Master Dashboard.

## Overview

The Dashboard UI Integration component provides:

1. **Dashboard-specific MCP resources** for accessing dashboard data
2. **Dashboard-specific MCP tools** for interacting with the dashboard
3. **Integration with the Project Master Dashboard** for a unified view of tasks and projects

## Resources

The Dashboard UI Integration adds the following MCP resources:

### Static Resources

- `task-manager://dashboard/stats`: Statistics for the Project Master Dashboard
- `task-manager://dashboard/config`: Configuration for the Project Master Dashboard
- `task-manager://dashboard/projects/summary`: Summary of all projects for the dashboard
- `task-manager://dashboard/tasks/recent`: Recently updated tasks for the dashboard

### Resource Templates

- `task-manager://dashboard/projects/{project_id}/summary`: Dashboard summary for a specific project
- `task-manager://dashboard/projects/{project_id}/phases/{phase_id}/tasks`: Tasks in a specific phase for the dashboard

## Tools

The Dashboard UI Integration adds the following MCP tools:

- `update_dashboard_config`: Update the dashboard configuration
- `scan_directory`: Scan a directory for project files
- `get_dashboard_stats`: Get dashboard statistics
- `get_projects_summary`: Get a summary of all projects for the dashboard
- `get_recent_tasks`: Get recently updated tasks for the dashboard

## Usage

### Accessing Dashboard Statistics

To get dashboard statistics, use the `task-manager://dashboard/stats` resource:

```python
from mcp.client import Client

async def get_dashboard_stats(client):
    response = await client.read_resource("task-manager://dashboard/stats")
    stats = json.loads(response.contents[0].text)
    print(f"Total projects: {stats['total_projects']}")
    print(f"Active projects: {stats['active_projects']}")
    print(f"Total tasks: {stats['total_tasks']}")
    print(f"Completed tasks: {stats['completed_tasks']}")
```

### Updating Dashboard Configuration

To update the dashboard configuration, use the `update_dashboard_config` tool:

```python
from mcp.client import Client

async def update_dashboard_config(client):
    config = {
        "api": {
            "baseUrl": "http://localhost:8000",
            "refreshInterval": 30000
        },
        "ui": {
            "theme": "dark",
            "defaultView": "projects",
            "showCompletedTasks": True
        }
    }
    
    response = await client.call_tool("task-manager", "update_dashboard_config", {
        "config": config
    })
    
    result = json.loads(response.content[0].text)
    print(f"Configuration updated: {result['success']}")
```

### Scanning for Project Files

To scan a directory for project files, use the `scan_directory` tool:

```python
from mcp.client import Client

async def scan_directory(client, directory):
    response = await client.call_tool("task-manager", "scan_directory", {
        "directory": directory,
        "depth": 3,
        "include_patterns": ["*.json", "*.yaml", "*.md"],
        "exclude_patterns": ["node_modules", ".git"]
    })
    
    result = json.loads(response.content[0].text)
    print(f"Found {len(result['projects'])} projects")
    
    for project in result['projects']:
        print(f"Project: {project['name']}")
```

### Getting Project Summaries

To get a summary of all projects, use the `task-manager://dashboard/projects/summary` resource:

```python
from mcp.client import Client

async def get_projects_summary(client):
    response = await client.read_resource("task-manager://dashboard/projects/summary")
    summaries = json.loads(response.contents[0].text)
    
    for project in summaries:
        print(f"Project: {project['name']}")
        print(f"Progress: {project['progress']}%")
        print(f"Tasks: {project['taskCount']} ({project['completedTasks']} completed)")
        print("Phases:")
        
        for phase in project['phases']:
            print(f"  - {phase['name']}: {phase['progress']}%")
```

### Getting Recent Tasks

To get recently updated tasks, use the `task-manager://dashboard/tasks/recent` resource:

```python
from mcp.client import Client

async def get_recent_tasks(client):
    response = await client.read_resource("task-manager://dashboard/tasks/recent")
    tasks = json.loads(response.contents[0].text)
    
    print("Recent tasks:")
    for task in tasks:
        print(f"- {task['name']} ({task['status']})")
        print(f"  Project: {task['projectName']}")
        print(f"  Updated: {task['updatedAt']}")
```

## Integration with Project Master Dashboard

The Dashboard UI Integration component is designed to work seamlessly with the Project Master Dashboard. The dashboard can be configured to connect to the Task Manager MCP Server by updating the configuration:

```json
{
  "integration": {
    "mcp": {
      "enabled": true,
      "serverName": "task-manager",
      "refreshInterval": 30000
    }
  }
}
```

This allows the dashboard to:

1. Fetch project and task data from the Task Manager MCP Server
2. Display real-time updates of task progress
3. Provide a unified view of all projects and tasks

## Implementation Details

The Dashboard UI Integration component is implemented in `dashboard_integration.py`. It extends the Task Manager MCP Server by:

1. Enhancing the resource handlers to include dashboard-specific resources
2. Enhancing the tool handlers to include dashboard-specific tools
3. Providing methods for calculating dashboard statistics and summaries

The integration is initialized in the `TaskManagerServer` class constructor:

```python
def __init__(self, data_dir=None, auth_token=None):
    # ... existing initialization code ...
    
    # Initialize the Dashboard Integration
    self.dashboard_integration = DashboardIntegration(self.server, self.task_manager)
```

This ensures that all dashboard-specific functionality is available when the Task Manager MCP Server is running.
