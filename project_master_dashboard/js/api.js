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
