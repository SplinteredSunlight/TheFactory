#!/usr/bin/env python3
"""
Execute Task Workflow Script

This script demonstrates how to execute a workflow for a task using the Dagger integration.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the task manager and dagger integration
from src.task_manager.manager import get_task_manager
from src.task_manager.dagger_integration import get_task_workflow_integration


async def execute_task_workflow(task_id: str):
    """Execute a workflow for a task."""
    # Initialize task manager
    task_manager = get_task_manager("data/new")
    
    # Get the task
    task = task_manager.get_task(task_id)
    if not task:
        print(f"Task with ID {task_id} not found")
        return
    
    print(f"Executing workflow for task: {task.name}")
    
    # Initialize task workflow integration
    workflow_integration = get_task_workflow_integration(
        dagger_config_path="config/dagger.yaml",
        templates_dir="templates"
    )
    
    # Create workflow parameters based on task metadata
    workflow_params = {
        "task_name": task.name,
        "task_description": task.description,
        "task_command": f"echo 'Executing task: {task.name}'",
        "task_timeout": 3600,
        "task_image": "alpine:latest",
        "task_environment": {},
        "task_working_dir": "/app",
        "task_mounts": []
    }
    
    # Execute the workflow
    result = await workflow_integration.execute_task_workflow(
        task_id=task.id,
        workflow_type="basic_task",
        workflow_params=workflow_params,
        skip_cache=True
    )
    
    print(f"Workflow execution result: {json.dumps(result, indent=2)}")
    
    # Update the task with the workflow result
    task_manager.update_task(
        task_id=task.id,
        status="in_progress",
        progress=25.0,
        result=result
    )
    
    # Save the data
    task_manager.save_data()
    
    print(f"Task {task.name} updated with workflow result")
    
    return result


async def find_task_by_name(name: str):
    """Find a task by name."""
    # Initialize task manager
    task_manager = get_task_manager("data/new")
    
    # Find the task
    for project in task_manager.projects.values():
        for task in project.tasks.values():
            if task.name == name:
                return task
    
    return None


async def main():
    """Main function."""
    # Find the task by name
    task = await find_task_by_name("Remove Legacy Migration Files")
    if not task:
        print("Task 'Remove Legacy Migration Files' not found")
        return
    
    # Execute the workflow
    await execute_task_workflow(task.id)


if __name__ == "__main__":
    asyncio.run(main())
