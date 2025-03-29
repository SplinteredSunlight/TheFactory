# AI-Orchestration-Platform Frontend

This is the frontend component of the AI-Orchestration-Platform, providing a unified dashboard for monitoring and managing AI-Orchestrator and Fast-Agent integration.

## Features

### Unified Dashboard

The Unified Dashboard provides a comprehensive view of the AI-Orchestration-Platform, including:

- **System Overview**: Real-time metrics for CPU usage, memory usage, active agents, and active tasks.
- **Agent Status**: Distribution of agent types (AI-Orchestrator vs Fast-Agent) and a list of recent agents with their status.
- **Task Status**: Distribution of task statuses (completed, failed, in progress, created/assigned) and a list of recent tasks.
- **Performance Metrics**: Time-series charts for CPU usage, memory usage, active agents, and active tasks.
- **Recent Messages**: List of recent messages exchanged between agents.

### Agent Management

The Agents page allows users to:

- View a summary of all agents in the system
- See detailed information about each agent, including status, capabilities, and current load
- Filter and search for specific agents
- Add new agents to the system

### Task Management

The Tasks page allows users to:

- View a summary of all tasks in the system
- See detailed information about each task, including status, progress, and assigned agent
- Filter tasks by status (all, in progress, completed, failed)
- Create new tasks

### Communication

The Communication page allows users to:

- Send messages to specific agents or broadcast to all agents
- Set message type (direct, broadcast, task request, status update)
- Set message priority (high, medium, low)
- View message history

### Settings

The Settings page allows users to configure various aspects of the platform:

- API settings
- Integration settings
- Authentication and security
- Notification preferences
- Appearance (including dark mode)
- Cross-System Configuration
- Advanced settings (logging, data management)

#### Cross-System Configuration

The Cross-System Configuration UI allows users to:

- Configure and manage system endpoints for AI-Orchestrator and Fast-Agent
- Create and manage connections between systems
- Define data mappings for synchronization between systems
- Test connections and trigger manual synchronization
- View synchronization history and status

## Technology Stack

- **React**: Frontend library for building user interfaces
- **TypeScript**: Type-safe JavaScript
- **Redux**: State management
- **Redux Toolkit**: Simplified Redux development
- **Material UI**: Component library for consistent design
- **Chart.js**: Data visualization
- **Axios**: HTTP client for API requests
- **Socket.io**: Real-time communication

## Project Structure

```
src/
  ├── assets/           # Static assets (images, icons, etc.)
  ├── components/       # Reusable UI components
  ├── hooks/            # Custom React hooks
  ├── pages/            # Page components
  │   ├── Dashboard.tsx # Unified Dashboard
  │   ├── Agents.tsx    # Agent management
  │   ├── Tasks.tsx     # Task management
  │   ├── Communication.tsx # Communication management
  │   └── Settings.tsx  # Settings management
  ├── services/         # API services
  ├── store/            # Redux store
  │   ├── index.ts      # Store configuration
  │   └── slices/       # Redux slices
  │       ├── authSlice.ts        # Authentication state
  │       ├── agentsSlice.ts      # Agents state
  │       ├── tasksSlice.ts       # Tasks state
  │       ├── metricsSlice.ts     # Metrics state
  │       ├── communicationSlice.ts # Communication state
  │       └── uiSlice.ts          # UI state
  └── utils/            # Utility functions
```

## Getting Started

1. Install dependencies:
   ```
   cd src/frontend
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Build for production:
   ```
   npm run build
   ```

## Integration with Backend

The frontend communicates with the backend API to fetch data and perform actions. The API endpoints are defined in the `services/api.ts` file.

## Authentication

The frontend uses JWT authentication to secure API requests. The authentication flow is handled by the `authSlice.ts` file.

## Real-time Updates

The frontend uses Socket.io to receive real-time updates from the backend, such as agent status changes, task progress updates, and new messages.
