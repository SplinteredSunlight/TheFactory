# AI Orchestration Platform Dashboard

This directory contains the implementation of the dashboard for the AI Orchestration Platform. The dashboard provides a web-based interface for monitoring and managing the platform.

## Features

- **Project Status Monitoring**: View the status of projects and tasks
- **Agent Performance Metrics**: Monitor the performance of AI agents
- **Workflow Visualization**: Visualize workflow execution and dependencies
- **System Health Monitoring**: Monitor the health of the platform components
- **Configuration Management**: Configure platform settings and integrations

## Architecture

The dashboard is built using a modern web stack:

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Node.js server for API endpoints
- **Data Visualization**: Charts and graphs for metrics visualization
- **Real-time Updates**: WebSocket for real-time data updates

## Directory Structure

```
dashboard/
├── css/                  # CSS stylesheets
├── js/                   # JavaScript files
│   ├── api.js            # API client for backend communication
│   └── dashboard.js      # Dashboard functionality
├── lib/                  # Third-party libraries
├── views/                # HTML templates
├── config.example.json   # Example configuration
├── config.json           # Dashboard configuration
├── index.html            # Main dashboard page
├── install.sh            # Installation script
├── package.json          # Node.js package configuration
├── README.md             # This file
├── server.js             # Node.js server
└── simple-dashboard.html # Simplified dashboard version
```

## Setup

To set up the dashboard:

1. Install dependencies:
   ```bash
   cd dashboard
   npm install
   ```

2. Configure the dashboard:
   ```bash
   cp config.example.json config.json
   # Edit config.json to match your environment
   ```

3. Start the server:
   ```bash
   node server.js
   ```

4. Access the dashboard:
   Open `http://localhost:3000` in your web browser

## Development

To develop the dashboard:

1. Make changes to the HTML, CSS, or JavaScript files
2. Refresh the browser to see your changes
3. For server changes, restart the Node.js server

## Integration

The dashboard integrates with the AI Orchestration Platform through:

- **REST API**: For data retrieval and management operations
- **WebSockets**: For real-time updates
- **MCP Server**: For advanced functionality through the Model Context Protocol

## Configuration

The dashboard can be configured through the `config.json` file:

- **API Endpoints**: URLs for backend API endpoints
- **Refresh Intervals**: How often to refresh data
- **UI Settings**: Customization of the user interface
- **Authentication**: Authentication settings
