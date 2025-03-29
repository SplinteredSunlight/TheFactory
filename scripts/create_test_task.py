#!/usr/bin/env python3
"""
Create Test Task Script

This script creates a test task for testing the task manager service.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the task manager
from src.task_manager.manager import get_task_manager


async def create_test_task():
    """Create a test task."""
    # Initialize task manager
    task_manager = get_task_manager("data/new")
    
    # Get the AI Orchestration Platform Enhancement project
    project = None
    for p in task_manager.projects.values():
        if p.name == "AI Orchestration Platform Enhancement":
            project = p
            break
    
    if not project:
        print("Project 'AI Orchestration Platform Enhancement' not found")
        return
    
    # Get the Documentation phase
    phase = None
    for p in project.phases.values():
        if p.name == "Documentation":
            phase = p
            break
    
    if not phase:
        print("Phase 'Documentation' not found")
        return
    
    # Create a test task
    task = task_manager.create_task(
        name="Test Task",
        description="A test task for testing the task manager service",
        project_id=project.id,
        phase_id=phase.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 1,
            "subtasks": [
                "Test subtask 1",
                "Test subtask 2",
                "Test subtask 3"
            ]
        }
    )
    
    # Save the data
    task_manager.save_data()
    
    print(f"Test task created with ID: {task.id}")
    
    return task.id


if __name__ == "__main__":
    task_id = asyncio.run(create_test_task())
