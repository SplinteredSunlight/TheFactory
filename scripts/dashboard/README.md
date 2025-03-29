# Dashboard Scripts

This directory contains scripts and utilities for working with the dashboard in the AI-Orchestration-Platform.

## Files

### Dashboard HTML

- **dashboard.html**: The main dashboard HTML file that provides a visual interface for monitoring the AI-Orchestration-Platform.

### Server Scripts

- **mock-api-server.js**: A mock API server that provides data for the dashboard during development and testing.

### Utility Scripts

- **open-dashboard**: Script to open the dashboard in a web browser.

## Usage

### Opening the Dashboard

```bash
./scripts/dashboard/open-dashboard
```

### Running the Mock API Server

```bash
node ./scripts/dashboard/mock-api-server.js
```

## Dashboard Features

The dashboard provides a visual interface for monitoring the AI-Orchestration-Platform, including:

- Task status and progress
- Agent performance metrics
- System health monitoring
- Workflow execution status
- Project progress tracking

## Related Components

The dashboard is related to the following components:

- **Project Master Dashboard**: A more comprehensive dashboard implementation in the `project_master_dashboard` directory.
- **Frontend Dashboard**: React-based dashboard components in the `src/frontend/src/components/dashboard` directory.
- **Dashboard Integration**: Integration with the Task Management system in the `src/task_manager/mcp_servers/dashboard_integration.py` file.

For more information about the dashboard, see the [Dashboard Documentation](../../docs/dashboard-documentation-section.html).
