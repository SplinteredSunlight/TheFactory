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
