#!/usr/bin/env node
/**
 * Mock API Server for Task Management MCP Server
 * 
 * This is a simple Express server that mocks the Task Management MCP Server API
 * for testing and development purposes.
 */

const express = require('express');
const cors = require('cors');
const app = express();
const port = process.env.PORT || 8080;

// Enable CORS
app.use(cors());

// Parse JSON request body
app.use(express.json());

// Sample data
const projects = {
  'project-1': {
    id: 'project-1',
    name: 'AI Orchestration Platform',
    description: 'A platform for orchestrating AI agents',
    phases: {
      'phase-1': {
        id: 'phase-1',
        name: 'Planning',
        order: 0,
        tasks: ['task-1', 'task-2']
      },
      'phase-2': {
        id: 'phase-2',
        name: 'Implementation',
        order: 1,
        tasks: ['task-3', 'task-4', 'task-5']
      },
      'phase-3': {
        id: 'phase-3',
        name: 'Testing',
        order: 2,
        tasks: ['task-6', 'task-7']
      }
    },
    tasks: {
      'task-1': {
        id: 'task-1',
        name: 'Define requirements',
        description: 'Define the requirements for the AI Orchestration Platform',
        status: 'completed',
        progress: 100,
        phase_id: 'phase-1'
      },
      'task-2': {
        id: 'task-2',
        name: 'Create architecture diagram',
        description: 'Create an architecture diagram for the AI Orchestration Platform',
        status: 'completed',
        progress: 100,
        phase_id: 'phase-1'
      },
      'task-3': {
        id: 'task-3',
        name: 'Implement core components',
        description: 'Implement the core components of the AI Orchestration Platform',
        status: 'in_progress',
        progress: 75,
        phase_id: 'phase-2'
      },
      'task-4': {
        id: 'task-4',
        name: 'Implement Dagger integration',
        description: 'Implement the Dagger workflow integration for the Task Management MCP Server',
        status: 'in_progress',
        progress: 90,
        phase_id: 'phase-2'
      },
      'task-5': {
        id: 'task-5',
        name: 'Implement dashboard',
        description: 'Implement the dashboard UI for the AI Orchestration Platform',
        status: 'planned',
        progress: 0,
        phase_id: 'phase-2'
      },
      'task-6': {
        id: 'task-6',
        name: 'Write tests',
        description: 'Write tests for the AI Orchestration Platform',
        status: 'planned',
        progress: 0,
        phase_id: 'phase-3'
      },
      'task-7': {
        id: 'task-7',
        name: 'Run integration tests',
        description: 'Run integration tests for the AI Orchestration Platform',
        status: 'planned',
        progress: 0,
        phase_id: 'phase-3'
      }
    }
  }
};

// MCP resource endpoint
app.get('/mcp/resource', (req, res) => {
  const uri = req.query.uri;
  
  if (!uri) {
    return res.status(400).json({ error: 'Missing uri parameter' });
  }
  
  // Handle different resource URIs
  if (uri === 'task-manager://projects') {
    return res.json(projects);
  }
  
  if (uri === 'task-manager://dashboard/projects/summary') {
    const summaries = Object.values(projects).map(project => {
      const totalTasks = Object.keys(project.tasks).length;
      const completedTasks = Object.values(project.tasks).filter(task => task.status === 'completed').length;
      const progress = totalTasks > 0 ? (completedTasks / totalTasks * 100) : 0;
      
      const phases = Object.values(project.phases).map(phase => {
        const phaseTasks = phase.tasks.map(taskId => project.tasks[taskId]).filter(Boolean);
        const phaseTotal = phaseTasks.length;
        const phaseCompleted = phaseTasks.filter(task => task.status === 'completed').length;
        const phaseProgress = phaseTotal > 0 ? (phaseCompleted / phaseTotal * 100) : 0;
        
        return {
          id: phase.id,
          name: phase.name,
          order: phase.order,
          taskCount: phaseTotal,
          completedTasks: phaseCompleted,
          progress: phaseProgress
        };
      });
      
      return {
        id: project.id,
        name: project.name,
        description: project.description,
        taskCount: totalTasks,
        completedTasks: completedTasks,
        progress: progress,
        phases: phases,
        createdAt: '2025-03-01T00:00:00Z',
        updatedAt: '2025-03-10T00:00:00Z'
      };
    });
    
    return res.json(summaries);
  }
  
  // Handle project tasks
  const projectTasksMatch = uri.match(/^task-manager:\/\/projects\/([^\/]+)\/tasks$/);
  if (projectTasksMatch) {
    const projectId = projectTasksMatch[1];
    const project = projects[projectId];
    
    if (!project) {
      return res.status(404).json({ error: `Project not found: ${projectId}` });
    }
    
    return res.json(project.tasks);
  }
  
  // Handle other URIs
  res.status(404).json({ error: `Resource not found: ${uri}` });
});

// MCP tool endpoint
app.post('/mcp/tool', (req, res) => {
  const { name, arguments: args } = req.body;
  
  if (!name) {
    return res.status(400).json({ error: 'Missing tool name' });
  }
  
  // Handle different tools
  if (name === 'create_workflow_from_task') {
    const taskId = args?.task_id;
    
    if (!taskId) {
      return res.status(400).json({ error: 'Missing task_id parameter' });
    }
    
    // Find the task
    let task = null;
    let projectId = null;
    
    for (const pid in projects) {
      if (taskId in projects[pid].tasks) {
        task = projects[pid].tasks[taskId];
        projectId = pid;
        break;
      }
    }
    
    if (!task) {
      return res.status(404).json({ error: `Task not found: ${taskId}` });
    }
    
    // Create a workflow
    const workflowId = `workflow-${taskId}`;
    const workflowName = args?.workflow_name || `Workflow for ${task.name}`;
    
    const workflow = {
      workflow_id: workflowId,
      task_id: taskId,
      name: workflowName,
      description: task.description,
      inputs: args?.custom_inputs || {},
    };
    
    return res.json(workflow);
  }
  
  if (name === 'execute_task_workflow') {
    const taskId = args?.task_id;
    
    if (!taskId) {
      return res.status(400).json({ error: 'Missing task_id parameter' });
    }
    
    // Find the task
    let task = null;
    let projectId = null;
    
    for (const pid in projects) {
      if (taskId in projects[pid].tasks) {
        task = projects[pid].tasks[taskId];
        projectId = pid;
        break;
      }
    }
    
    if (!task) {
      return res.status(404).json({ error: `Task not found: ${taskId}` });
    }
    
    // Execute the workflow
    const workflowId = `workflow-${taskId}`;
    const workflowType = args?.workflow_type || 'containerized_workflow';
    
    const result = {
      success: true,
      task_id: taskId,
      workflow_id: workflowId,
      result: {
        output: `Executed ${workflowType} workflow for task ${taskId}`,
        logs: [
          `[INFO] Starting workflow execution`,
          `[INFO] Workflow type: ${workflowType}`,
          `[INFO] Task: ${task.name}`,
          `[INFO] Workflow completed successfully`
        ]
      }
    };
    
    return res.json(result);
  }
  
  // Handle other tools
  res.status(404).json({ error: `Tool not found: ${name}` });
});

// Start the server
app.listen(port, () => {
  console.log(`Mock API Server running at http://localhost:${port}`);
});
