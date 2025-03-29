#!/bin/bash

# Project Master Dashboard Installation Script
# This script sets up the Project Master Dashboard for the AI-Orchestration-Platform

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${GREEN}"
echo "============================================================"
echo "  Project Master Dashboard - Installation Script"
echo "============================================================"
echo -e "${NC}"

# Check if running from the correct directory
if [ ! -f "$(dirname "$0")/README.md" ]; then
    echo -e "${RED}Error: Please run this script from the AI-Orchestration-Platform root directory.${NC}"
    echo "Example: ./project_master_dashboard/install.sh"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p project_master_dashboard/{css,js,views,lib}

# Copy the simple dashboard as a starting point
echo -e "${YELLOW}Copying dashboard files...${NC}"
cp src/frontend/simple-dashboard.html project_master_dashboard/index.html

# Create the configuration file
echo -e "${YELLOW}Creating configuration file...${NC}"
cat > project_master_dashboard/config.example.json << 'EOF'
{
  "api": {
    "baseUrl": "http://localhost:8000",
    "authToken": "",
    "refreshInterval": 30000
  },
  "scan": {
    "enabled": true,
    "directories": [
      "./src/task_manager/data/projects",
      "./tasks"
    ],
    "depth": 2,
    "includePatterns": ["*.json", "*.yaml", "*.md"],
    "excludePatterns": ["node_modules", ".git", "dist", "build"]
  },
  "ui": {
    "theme": "light",
    "defaultView": "projects",
    "refreshInterval": 30000,
    "showCompletedTasks": true
  }
}
EOF

# Copy the example config to the actual config
cp project_master_dashboard/config.example.json project_master_dashboard/config.json

# Create the API integration module
echo -e "${YELLOW}Creating API integration module...${NC}"
cat > project_master_dashboard/js/api.js << 'EOF'
/**
 * API Integration Module for Project Master Dashboard
 * Handles communication with the AI-Orchestration-Platform API
 */

class DashboardAPI {
  constructor(config) {
    this.baseUrl = config.api.baseUrl || 'http://localhost:8000';
    this.authToken = config.api.authToken || '';
    this.refreshInterval = config.api.refreshInterval || 30000;
    this.websockets = {};
    this.eventHandlers = {};
  }

  /**
   * Initialize the API connection
   */
  async init() {
    console.log('Initializing API connection to:', this.baseUrl);
    try {
      // Test connection
      await this.getProjects();
      console.log('API connection successful');
      return true;
    } catch (error) {
      console.error('API connection failed:', error);
      return false;
    }
  }

  /**
   * Get all projects
   */
  async getProjects() {
    const response = await this._fetch('/tasks/projects');
    return response;
  }

  /**
   * Get a specific project by ID
   */
  async getProject(projectId) {
    const response = await this._fetch(`/tasks/projects/${projectId}`);
    return response;
  }

  /**
   * Get tasks for a project
   */
  async getProjectTasks(projectId, phaseId = null, status = null) {
    let url = `/tasks/projects/${projectId}/tasks`;
    const params = [];
    
    if (phaseId) params.push(`phase_id=${phaseId}`);
    if (status) params.push(`status=${status}`);
    
    if (params.length > 0) {
      url += `?${params.join('&')}`;
    }
    
    const response = await this._fetch(url);
    return response;
  }

  /**
   * Create a new task
   */
  async createTask(taskData) {
    const response = await this._fetch('/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    });
    return response;
  }

  /**
   * Update a task
   */
  async updateTask(taskId, taskData) {
    const response = await this._fetch(`/tasks/${taskId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    });
    return response;
  }

  /**
   * Update a task's status
   */
  async updateTaskStatus(taskId, status) {
    const response = await this._fetch(`/tasks/${taskId}/status?status=${status}`, {
      method: 'PUT'
    });
    return response;
  }

  /**
   * Update a task's progress
   */
  async updateTaskProgress(taskId, progress) {
    const response = await this._fetch(`/tasks/${taskId}/progress?progress=${progress}`, {
      method: 'PUT'
    });
    return response;
  }

  /**
   * Delete a task
   */
  async deleteTask(taskId) {
    const response = await this._fetch(`/tasks/${taskId}`, {
      method: 'DELETE'
    });
    return response;
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket(projectId, onMessage) {
    if (this.websockets[projectId]) {
      this.disconnectWebSocket(projectId);
    }
    
    const wsUrl = `${this.baseUrl.replace('http', 'ws')}/tasks/ws/${projectId}`;
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log(`WebSocket connection established for project ${projectId}`);
      // Send a ping every 30 seconds to keep the connection alive
      this.websockets[projectId].pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type !== 'pong') {
        onMessage(data);
      }
    };
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for project ${projectId}:`, error);
    };
    
    ws.onclose = () => {
      console.log(`WebSocket connection closed for project ${projectId}`);
      clearInterval(this.websockets[projectId].pingInterval);
      delete this.websockets[projectId];
      
      // Try to reconnect after a delay
      setTimeout(() => {
        if (!this.websockets[projectId]) {
          this.connectWebSocket(projectId, onMessage);
        }
      }, 5000);
    };
    
    this.websockets[projectId] = { socket: ws };
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket(projectId) {
    if (this.websockets[projectId]) {
      clearInterval(this.websockets[projectId].pingInterval);
      this.websockets[projectId].socket.close();
      delete this.websockets[projectId];
    }
  }

  /**
   * Register an event handler
   */
  on(event, handler) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  /**
   * Trigger an event
   */
  trigger(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }

  /**
   * Helper method for making API requests
   */
  async _fetch(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Add authorization header if token is available
    if (this.authToken) {
      options.headers = options.headers || {};
      options.headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    try {
      const response = await fetch(url, options);
      
      // Handle 204 No Content responses
      if (response.status === 204) {
        return null;
      }
      
      // Handle error responses
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error (${response.status}): ${errorText}`);
      }
      
      // Parse JSON response
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
}

// Export the API class
window.DashboardAPI = DashboardAPI;
EOF

# Create the dashboard main module
echo -e "${YELLOW}Creating dashboard main module...${NC}"
cat > project_master_dashboard/js/dashboard.js << 'EOF'
/**
 * Main Dashboard Module for Project Master Dashboard
 * Handles the core dashboard functionality
 */

class Dashboard {
  constructor(config) {
    this.config = config;
    this.api = new DashboardAPI(config);
    this.projects = [];
    this.currentProject = null;
    this.initialized = false;
  }

  /**
   * Initialize the dashboard
   */
  async init() {
    console.log('Initializing dashboard with config:', this.config);
    
    // Initialize API
    const apiConnected = await this.api.init();
    if (!apiConnected) {
      this.showError('Failed to connect to API. Please check your configuration.');
      return false;
    }
    
    // Load projects
    await this.loadProjects();
    
    // Set up refresh interval
    this.startRefreshInterval();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Apply theme
    this.applyTheme(this.config.ui.theme);
    
    this.initialized = true;
    return true;
  }

  /**
   * Load projects from the API
   */
  async loadProjects() {
    try {
      const projects = await this.api.getProjects();
      this.projects = projects;
      
      // Render projects
      this.renderProjects();
      
      return projects;
    } catch (error) {
      console.error('Failed to load projects:', error);
      this.showError('Failed to load projects. Please try again later.');
      return [];
    }
  }

  /**
   * Render projects in the UI
   */
  renderProjects() {
    const phasesContainer = document.getElementById('phases-container');
    const progressStats = document.getElementById('progress-stats');
    const overallProgress = document.getElementById('overall-progress');
    
    if (!phasesContainer || !progressStats || !overallProgress) {
      console.error('Required DOM elements not found');
      return;
    }
    
    // Clear container
    phasesContainer.innerHTML = '';
    
    if (this.projects.length === 0) {
      phasesContainer.innerHTML = '<p>No projects found. Create a project to get started.</p>';
      progressStats.innerHTML = 'No projects available';
      overallProgress.style.width = '0%';
      return;
    }
    
    // Use the first project or the current project
    const project = this.currentProject || this.projects[0];
    this.currentProject = project;
    
    // Calculate project progress
    const tasks = Object.values(project.tasks);
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(task => task.status === 'completed').length;
    const inProgressTasks = tasks.filter(task => task.status === 'in_progress').length;
    
    // Calculate overall progress percentage
    const progressPercentage = Math.round((completedTasks / totalTasks) * 100) || 0;
    
    // Update progress bar
    overallProgress.style.width = `${progressPercentage}%`;
    
    // Update progress stats
    progressStats.innerHTML = `
      <p>Project: ${project.name}</p>
      <p>Completed: ${completedTasks}/${totalTasks} tasks (${progressPercentage}%)</p>
      <p>In Progress: ${inProgressTasks} tasks</p>
    `;
    
    // Sort phases by order
    const phases = Object.values(project.phases).sort((a, b) => a.order - b.order);
    
    // Render each phase
    phases.forEach(phase => {
      const phaseElement = document.createElement('div');
      phaseElement.className = 'phase';
      
      // Get tasks for this phase
      const phaseTasks = phase.tasks
        .map(taskId => project.tasks[taskId])
        .filter(task => task); // Filter out undefined tasks
      
      // Calculate phase progress
      const totalPhaseTasks = phaseTasks.length;
      const completedPhaseTasks = phaseTasks.filter(task => task.status === 'completed').length;
      const phaseProgressPercentage = totalPhaseTasks > 0 
        ? Math.round((completedPhaseTasks / totalPhaseTasks) * 100) 
        : 0;
      
      phaseElement.innerHTML = `
        <div class="phase-header">
          <h3>${phase.name}</h3>
          <span>${completedPhaseTasks}/${totalPhaseTasks} completed</span>
        </div>
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width: ${phaseProgressPercentage}%"></div>
        </div>
        <div class="phase-actions">
          <button class="add-task-btn" data-phase-id="${phase.id}">Add Task</button>
        </div>
        <ul class="tasks">
          ${this.renderTasks(phaseTasks)}
        </ul>
      `;
      
      phasesContainer.appendChild(phaseElement);
    });
    
    // Set up event listeners for task actions
    this.setupTaskEventListeners();
    
    // Connect to WebSocket for real-time updates
    this.connectToWebSocket(project.id);
  }

  /**
   * Render tasks in a phase
   */
  renderTasks(tasks) {
    if (tasks.length === 0) {
      return '<li class="no-tasks">No tasks in this phase</li>';
    }
    
    // Filter out completed tasks if configured
    const filteredTasks = this.config.ui.showCompletedTasks 
      ? tasks 
      : tasks.filter(task => task.status !== 'completed');
    
    if (filteredTasks.length === 0) {
      return '<li class="no-tasks">All tasks completed</li>';
    }
    
    return filteredTasks.map(task => `
      <li class="task" data-task-id="${task.id}">
        <div class="task-header">
          <span class="task-name">${task.name}</span>
          <span class="task-status status-${task.status}">${task.status.replace('_', ' ')}</span>
        </div>
        <div class="task-description">${task.description}</div>
        <div class="task-progress">
          <div class="task-progress-fill" style="width: ${task.progress}%"></div>
        </div>
        <div class="task-actions">
          <button class="edit-task-btn" data-task-id="${task.id}">Edit</button>
          <button class="delete-task-btn" data-task-id="${task.id}">Delete</button>
        </div>
      </li>
    `).join('');
  }

  /**
   * Set up event listeners for the dashboard
   */
  setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadProjects());
    }
    
    // Project selector (if multiple projects)
    const projectSelector = document.getElementById('project-selector');
    if (projectSelector) {
      projectSelector.addEventListener('change', (event) => {
        const projectId = event.target.value;
        this.currentProject = this.projects.find(p => p.id === projectId);
        this.renderProjects();
      });
    }
  }

  /**
   * Set up event listeners for task actions
   */
  setupTaskEventListeners() {
    // Add task buttons
    document.querySelectorAll('.add-task-btn').forEach(button => {
      button.addEventListener('click', (event) => {
        const phaseId = event.target.dataset.phaseId;
        this.showAddTaskDialog(phaseId);
      });
    });
    
    // Edit task buttons
    document.querySelectorAll('.edit-task-btn').forEach(button => {
      button.addEventListener('click', (event) => {
        const taskId = event.target.dataset.taskId;
        this.showEditTaskDialog(taskId);
      });
    });
    
    // Delete task buttons
    document.querySelectorAll('.delete-task-btn').forEach(button => {
      button.addEventListener('click', (event) => {
        const taskId = event.target.dataset.taskId;
        this.confirmDeleteTask(taskId);
      });
    });
    
    // Task click (for details)
    document.querySelectorAll('.task').forEach(taskElement => {
      taskElement.addEventListener('click', (event) => {
        // Only handle clicks on the task itself, not on buttons
        if (!event.target.closest('button')) {
          const taskId = taskElement.dataset.taskId;
          this.showTaskDetails(taskId);
        }
      });
    });
  }

  /**
   * Show add task dialog
   */
  showAddTaskDialog(phaseId) {
    // Implementation will be added in the tasks.js module
    console.log('Add task dialog for phase:', phaseId);
    alert('Add task functionality will be implemented in the full version.');
  }

  /**
   * Show edit task dialog
   */
  showEditTaskDialog(taskId) {
    // Implementation will be added in the tasks.js module
    console.log('Edit task dialog for task:', taskId);
    alert('Edit task functionality will be implemented in the full version.');
  }

  /**
   * Confirm delete task
   */
  confirmDeleteTask(taskId) {
    // Implementation will be added in the tasks.js module
    console.log('Confirm delete task:', taskId);
    alert('Delete task functionality will be implemented in the full version.');
  }

  /**
   * Show task details
   */
  showTaskDetails(taskId) {
    // Implementation will be added in the tasks.js module
    console.log('Show task details for task:', taskId);
    alert('Task details functionality will be implemented in the full version.');
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectToWebSocket(projectId) {
    this.api.connectWebSocket(projectId, (data) => {
      console.log('WebSocket message received:', data);
      
      // Handle different message types
      switch (data.type) {
        case 'initial_data':
          // Update project data
          if (this.currentProject && this.currentProject.id === projectId) {
            this.currentProject = data.data;
            this.renderProjects();
          }
          break;
          
        case 'task_created':
        case 'task_updated':
        case 'task_deleted':
          // Refresh project data
          this.loadProjects();
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    });
  }

  /**
   * Start the refresh interval
   */
  startRefreshInterval() {
    // Clear any existing interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    // Set up new interval
    this.refreshInterval = setInterval(() => {
      this.loadProjects();
    }, this.config.ui.refreshInterval);
  }

  /**
   * Apply theme to the dashboard
   */
  applyTheme(theme) {
    document.body.classList.remove('theme-light', 'theme-dark');
    document.body.classList.add(`theme-${theme}`);
  }

  /**
   * Show error message
   */
  showError(message) {
    console.error(message);
    
    // Create error element if it doesn't exist
    let errorElement = document.getElementById('dashboard-error');
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.id = 'dashboard-error';
      errorElement.className = 'error-message';
      
      // Insert at the top of the container
      const container = document.querySelector('.container');
      if (container) {
        container.insertBefore(errorElement, container.firstChild);
      } else {
        document.body.insertBefore(errorElement, document.body.firstChild);
      }
    }
    
    // Set error message
    errorElement.textContent = message;
    errorElement.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
      errorElement.style.display = 'none';
    }, 5000);
  }
}

// Initialize dashboard when the page loads
window.addEventListener('DOMContentLoaded', async () => {
  try {
    // Load configuration
    const configResponse = await fetch('config.json');
    const config = await configResponse.json();
    
    // Create and initialize dashboard
    const dashboard = new Dashboard(config);
    window.dashboard = dashboard;
    
    const initialized = await dashboard.init();
    if (!initialized) {
      console.error('Failed to initialize dashboard');
    }
  } catch (error) {
    console.error('Error initializing dashboard:', error);
    alert('Failed to initialize dashboard. Please check the console for details.');
  }
});
EOF

# Create CSS file
echo -e "${YELLOW}Creating CSS styles...${NC}"
cat > project_master_dashboard/css/dashboard.css << 'EOF'
/* Dashboard Styles */
:root {
  --primary-color: #4caf50;
  --secondary-color: #2196f3;
  --warning-color: #ff9800;
  --danger-color: #f44336;
  --success-color: #4caf50;
  --info-color: #2196f3;
  --light-bg: #f5f5f5;
  --dark-bg: #333;
  --light-text: #333;
  --dark-text: #f5f5f5;
  --border-color: #ddd;
  --shadow-color: rgba(0, 0, 0, 0.1);
}

/* Theme: Light */
body.theme-light {
  --bg-color: var(--light-bg);
  --text-color: var(--light-text);
  --card-bg: white;
}

/* Theme: Dark */
body.theme-dark {
  --bg-color: var(--dark-bg);
  --text-color: var(--dark-text);
  --card-bg: #444;
  --border-color: #555;
}

body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 20px;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  background-color: var(--card-bg);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px var(--shadow-color);
}

.error-message {
  background-color: var(--danger-color);
  color: white;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  display: none;
}

/* Add more styles as needed */
EOF

# Update the index.html file to use the new modules
echo -e "${YELLOW}Updating index.html...${NC}"
cat > project_master_dashboard/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Master Dashboard</title>
    <link rel="stylesheet" href="css/dashboard.css">
    <style>
        /* Inline styles from simple-dashboard.html */
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3 {
            color: #333;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .progress-bar {
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background-color: #4caf50;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .phases {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
        }
        .phase {
            flex: 1;
            min-width: 300px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .phase-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .tasks {
            list-style-type: none;
            padding: 0;
        }
        .task {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            cursor: pointer;
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .task-name {
            font-weight: bold;
        }
        .task-status {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            color: white;
        }
        .status-completed {
            background-color: #4caf50;
        }
        .status-in_progress {
            background-color: #ff9800;
        }
        .status-planned {
            background-color: #2196f3;
        }
        .status-failed {
            background-color: #f44336;
        }
        .status-blocked {
            background-color: #9c27b0;
        }
        .task-progress {
            height: 6px;
            background-color: #e0e0e0;
            border-radius: 3px;
            margin-top: 5px;
        }
        .task-progress-fill {
            height: 100%;
            background-color: #4caf50;
            border-radius: 3px;
        }
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border-left-color: #09f;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .phase-actions, .task-actions {
            margin-top: 10px;
            display: flex;
            gap: 5px;
        }
        button {
            padding: 5px 10px;
            border: none;
            border-radius: 4px;
            background-color: #2196f3;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #0b7dda;
        }
        .delete-task-btn {
            background-color: #f44336;
        }
        .delete-task-btn:hover {
            background-color: #d32f2f;
        }
        .no-tasks {
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body class="theme-light">
    <div class="container">
        <div class="header">
            <h1>Project Master Dashboard</h1>
            <div>
                <button id="refresh-btn">Refresh</button>
            </div>
        </div>
        
        <div id="project-info">
            <h2>Project Progress</h2>
            <div class="progress-bar">
                <div class="progress-bar-fill" id="overall-progress" style="width: 0%"></div>
            </div>
            <div id="progress-stats">Loading project stats...</div>
        </div>
        
        <div id="phases-container" class="phases">
            <div class="loading">
                <div class="spinner"></div>
            </div>
        </div>
    </div>

    <!-- Load JavaScript modules -->
    <script src="js/api.js"></script>
    <script src="js/dashboard.js"></script>
</body>
</html>
EOF

# Create a simple package.json for optional server features
echo -e "${YELLOW}Creating package.json for optional server features...${NC}"
cat > project_master_dashboard/package.json << 'EOF'
{
  "name": "project-master-dashboard",
  "version": "1.0.0",
  "description": "A standalone dashboard for the AI-Orchestration-Platform",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.0.3"
  }
}
EOF

# Create a simple server.js for optional
