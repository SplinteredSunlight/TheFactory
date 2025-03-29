#!/usr/bin/env python3
"""
Task Manager API Server

This script provides a simple API server for the Task Manager Web Interface.
It serves the web interface and provides API endpoints for interacting with the task manager.
"""

import os
import sys
import json
import subprocess
from flask import Flask, request, jsonify, send_file

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the task manager
from src.task_manager.manager import get_task_manager

app = Flask(__name__)

# Initialize task manager
task_manager = get_task_manager("data/new")


@app.route('/')
def index():
    """Serve the web interface."""
    return send_file('task_manager_web.html')


@app.route('/api/next-task')
def next_task():
    """Get the next task to work on."""
    # Find all planned tasks
    planned_tasks = []
    for project in task_manager.projects.values():
        for task in project.tasks.values():
            if task.status == "planned":
                # Get phase name
                phase_name = ""
                if task.phase_id and task.phase_id in project.phases:
                    phase_name = project.phases[task.phase_id].name
                
                # Get subtasks
                subtasks = []
                if task.metadata and "subtasks" in task.metadata:
                    subtasks = task.metadata["subtasks"]
                
                planned_tasks.append({
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "progress": task.progress or 0,
                    "project": project.name,
                    "phase": phase_name,
                    "subtasks": subtasks
                })
    
    # Sort tasks by priority
    def get_priority_value(task):
        if task["priority"] == "high":
            return 0
        elif task["priority"] == "medium":
            return 1
        elif task["priority"] == "low":
            return 2
        return 3
    
    planned_tasks.sort(key=get_priority_value)
    
    if not planned_tasks:
        return jsonify({"error": "No planned tasks found"}), 404
    
    return jsonify(planned_tasks[0])


@app.route('/api/tasks')
def get_tasks():
    """Get all tasks."""
    tasks = []
    for project in task_manager.projects.values():
        for task in project.tasks.values():
            # Get phase name
            phase_name = ""
            if task.phase_id and task.phase_id in project.phases:
                phase_name = project.phases[task.phase_id].name
            
            # Get subtasks
            subtasks = []
            if task.metadata and "subtasks" in task.metadata:
                subtasks = task.metadata["subtasks"]
            
            tasks.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "progress": task.progress or 0,
                "project": project.name,
                "phase": phase_name,
                "subtasks": subtasks
            })
    
    return jsonify(tasks)


@app.route('/api/complete-task/<task_id>', methods=['POST'])
def complete_task(task_id):
    """Mark a task as complete."""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    
    # Update task status and progress
    task_manager.update_task(
        task_id=task_id,
        status="completed",
        progress=100.0,
        metadata={
            **task.metadata,
            "completed_at": "now"  # We'll use a placeholder since we don't need the actual timestamp
        }
    )
    
    # Save the data
    task_manager.save_data()
    
    # Run the task_manager_service.py script to get the next task
    try:
        subprocess.run(
            ["python3", "scripts/task_manager_service.py", "complete", task.name],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running task_manager_service.py: {e}")
        print(f"stdout: {e.stdout.decode()}")
        print(f"stderr: {e.stderr.decode()}")
    
    return jsonify({"success": True})


@app.route('/api/task/<task_id>')
def get_task(task_id):
    """Get a task by ID."""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    
    # Get project and phase
    project = task_manager.get_project(task.project_id)
    if not project:
        return jsonify({"error": f"Project with ID {task.project_id} not found"}), 404
    
    # Get phase name
    phase_name = ""
    if task.phase_id and task.phase_id in project.phases:
        phase_name = project.phases[task.phase_id].name
    
    # Get subtasks
    subtasks = []
    if task.metadata and "subtasks" in task.metadata:
        subtasks = task.metadata["subtasks"]
    
    return jsonify({
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "progress": task.progress or 0,
        "project": project.name,
        "phase": phase_name,
        "subtasks": subtasks
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
