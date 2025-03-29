# Project Master Dashboard

The Project Master Dashboard is a standalone application that provides a unified view of multiple projects using the AI task management system. It integrates seamlessly with the AI-Orchestration-Platform to provide real-time updates on project progress, tasks, and phases.

## Features

- **Unified Project View**: Monitor multiple projects in a single dashboard
- **Real-time Updates**: See task and project changes as they happen
- **Progress Tracking**: Visual progress bars for projects and phases
- **Task Management**: Create, update, and delete tasks directly from the dashboard
- **Custom Scan Directories**: Configure the dashboard to scan specific directories for projects
- **API Integration**: Connect to the AI-Orchestration-Platform API for data synchronization
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites

- Node.js 16+ (for optional server features)
- Modern web browser
- Running instance of AI-Orchestration-Platform API

### Quick Installation

Use the provided installation script to set up the dashboard:

```bash
# Make the script executable
chmod +x ./project_master_dashboard/install.sh

# Run the installation script
./project_master_dashboard/install.sh
```

The installation script will:
1. Copy necessary files to the correct locations
2. Create a default configuration file
3. Set up API connections
4. Provide instructions for starting the dashboard

### Manual Installation

If you prefer to install manually:

1. Copy the dashboard files to your preferred location:
   ```bash
   cp -r project_master_dashboard /path/to/destination
   ```

2. Create a configuration file:
   ```bash
   cp project_master_dashboard/config.example.json project_master_dashboard/config.json
   ```

3. Edit the configuration file to match your environment:
   ```bash
   nano project_master_dashboard/config.json
   ```

4. Start the dashboard:
   ```bash
   # If using the built-in server
   cd project_master_dashboard
   npm start
   
   # Or simply open the HTML file in a browser
   open project_master_dashboard/index.html
   ```

## Configuration

The dashboard can be configured through the `config.json` file:

```json
{
  "api": {
    "baseUrl": "http://localhost:8000",
    "authToken": "",
    "refreshInterval": 30000
  },
  "scan": {
    "enabled": true,
    "directories": [
      "/path/to/projects",
      "/another/path/to/projects"
    ],
    "depth": 2,
    "includePatterns": ["*.json", "*.yaml"],
    "excludePatterns": ["node_modules", ".git"]
  },
  "ui": {
    "theme": "light",
    "defaultView": "projects",
    "refreshInterval": 30000,
    "showCompletedTasks": true
  }
}
```

### API Configuration

- **baseUrl**: The base URL of the AI-Orchestration-Platform API
- **authToken**: Authentication token for API access (leave empty for unauthenticated access)
- **refreshInterval**: How often to refresh data from the API (in milliseconds)

### Custom Scan Directories

The dashboard can scan directories for project files:

- **enabled**: Enable or disable directory scanning
- **directories**: List of directories to scan for project files
- **depth**: How deep to scan in the directory structure
- **includePatterns**: File patterns to include in the scan
- **excludePatterns**: File patterns to exclude from the scan

### UI Configuration

- **theme**: UI theme ('light' or 'dark')
- **defaultView**: Default view to show when opening the dashboard
- **refreshInterval**: How often to refresh the UI (in milliseconds)
- **showCompletedTasks**: Whether to show completed tasks in the dashboard

## Usage

### Opening the Dashboard

You can open the dashboard in several ways:

1. If using the built-in server:
   ```bash
   cd project_master_dashboard
   npm start
   ```
   Then open http://localhost:3000 in your browser

2. Open the HTML file directly:
   ```bash
   open project_master_dashboard/index.html
   ```

3. Serve with any static file server:
   ```bash
   cd project_master_dashboard
   python -m http.server 8080
   ```
   Then open http://localhost:8080 in your browser

### Viewing Projects

The dashboard shows all projects from the connected AI-Orchestration-Platform. For each project, you can see:

- Overall progress
- Phases and their progress
- Tasks within each phase
- Task status and details

### Managing Tasks

You can manage tasks directly from the dashboard:

1. **Create a Task**: Click the "Add Task" button in a phase
2. **Update a Task**: Click on a task to open the edit dialog
3. **Change Task Status**: Use the status dropdown in the task edit dialog
4. **Delete a Task**: Click the delete button in the task edit dialog

### Real-time Updates

The dashboard uses WebSocket connections to receive real-time updates from the AI-Orchestration-Platform. When tasks are updated, the dashboard will automatically refresh to show the latest data.

## API Integration

The dashboard integrates with the following AI-Orchestration-Platform API endpoints:

- `GET /tasks/projects`: Get all projects
- `GET /tasks/projects/{project_id}`: Get a specific project
- `GET /tasks/projects/{project_id}/tasks`: Get tasks for a project
- `POST /tasks`: Create a new task
- `PUT /tasks/{task_id}`: Update a task
- `DELETE /tasks/{task_id}`: Delete a task
- `WebSocket /tasks/ws/{project_id}`: Real-time updates for a project

## Troubleshooting

### Dashboard Not Loading

1. Check that the AI-Orchestration-Platform API is running
2. Verify the API URL in the configuration file
3. Check browser console for JavaScript errors
4. Ensure you have network connectivity to the API server

### No Projects Showing

1. Verify that projects exist in the AI-Orchestration-Platform
2. Check the API connection settings
3. Look for error messages in the browser console
4. Try manually refreshing the dashboard

### Custom Scan Not Working

1. Ensure the scan configuration is correct
2. Verify the directories exist and are accessible
3. Check file permissions on the directories
4. Try increasing the scan depth

### API Connection Issues

1. Verify the API server is running
2. Check the API URL in the configuration
3. Ensure any required authentication is configured
4. Check network connectivity and firewall settings

### WebSocket Connection Failing

1. Ensure the API server supports WebSockets
2. Check for proxy or firewall issues
3. Verify the WebSocket URL is correct
4. Try disabling and re-enabling real-time updates

## Extending the Dashboard

### Adding Custom Views

You can add custom views to the dashboard by creating new HTML files in the `views` directory and updating the navigation menu.

### Customizing the UI

The dashboard uses standard HTML, CSS, and JavaScript. You can customize the appearance by editing the CSS files in the `css` directory.

### Adding New Features

To add new features:

1. Create new JavaScript modules in the `js` directory
2. Update the main application to use your new modules
3. Add any required HTML elements to the appropriate views
4. Update the configuration file if needed

## Developer Documentation

For developers looking to extend or modify the dashboard, please refer to the code comments and the following structure:

```
project_master_dashboard/
├── index.html              # Main dashboard HTML
├── config.json             # Configuration file
├── install.sh              # Installation script
├── css/                    # CSS styles
├── js/                     # JavaScript modules
│   ├── api.js              # API integration
│   ├── dashboard.js        # Main dashboard logic
│   ├── projects.js         # Project management
│   ├── tasks.js            # Task management
│   └── utils.js            # Utility functions
├── views/                  # Additional views
└── lib/                    # Third-party libraries
```

### API Integration

The dashboard uses the `api.js` module to communicate with the AI-Orchestration-Platform API. This module provides methods for:

- Fetching projects and tasks
- Creating, updating, and deleting tasks
- Establishing WebSocket connections for real-time updates

### Event System

The dashboard uses a custom event system to handle updates and user interactions. Events are triggered when:

- Data is loaded from the API
- Tasks are created, updated, or deleted
- User interface elements are interacted with

### Data Flow

1. Configuration is loaded from `config.json`
2. API connection is established
3. Projects and tasks are fetched from the API
4. Data is rendered to the UI
5. WebSocket connections are established for real-time updates
6. User interactions trigger API calls and UI updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
