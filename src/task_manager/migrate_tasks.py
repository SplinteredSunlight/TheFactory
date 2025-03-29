#!/usr/bin/env python3
"""
Migration script to convert the existing task tracking system to the new task management system.

This script reads the existing task tracking data from docs/task-tracking.json and
project plan from docs/project-plan.md, and creates a new project with phases and tasks
in the new task management system.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import the task manager
from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority


def extract_phases_from_project_plan(project_plan_path: str) -> List[str]:
    """Extract phase names from the project plan markdown file."""
    phases = []
    
    try:
        with open(project_plan_path, 'r') as f:
            plan_text = f.read()
            
            # Simple parsing of phases (looking for ### N. Phase Name format)
            phase_pattern = re.compile(r'###\s+\d+\.\s+(.*?)\s*$', re.MULTILINE)
            
            for match in phase_pattern.finditer(plan_text):
                phases.append(match.group(1))
    except Exception as e:
        print(f"Error extracting phases from project plan: {e}")
    
    return phases


def load_task_tracking_data(task_tracking_path: str) -> Dict[str, Any]:
    """Load the existing task tracking data from JSON file."""
    try:
        with open(task_tracking_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading task tracking data: {e}")
        return {"completed_tasks": [], "current_phase": "", "current_task": ""}


def migrate_tasks(
    task_tracking_path: str,
    project_plan_path: str,
    project_name: str = "AI-Orchestration-Platform",
    project_description: str = "Integration project between AI-Orchestrator and Fast-Agent frameworks.",
    project_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Migrate tasks from the old system to the new task management system.
    
    Args:
        task_tracking_path: Path to the task tracking JSON file
        project_plan_path: Path to the project plan markdown file
        project_name: Name of the project
        project_description: Description of the project
        project_metadata: Additional metadata for the project
        
    Returns:
        The ID of the created project
    """
    # Get the task manager
    task_manager = get_task_manager()
    
    # Load the existing task tracking data
    tracking_data = load_task_tracking_data(task_tracking_path)
    
    # Extract phases from the project plan
    phases = extract_phases_from_project_plan(project_plan_path)
    
    if not phases:
        print("No phases found in project plan. Using default phases.")
        phases = ["Integration Setup", "Orchestrator Enhancements", "Agent Integration", "Frontend Integration"]
    
    # Create a project
    project = task_manager.create_project(
        name=project_name,
        description=project_description,
        metadata=project_metadata or {
            "repository": "https://github.com/SplinteredSunlight/AI-Orchestration-Platform"
        },
    )
    
    # Add phases to the project
    phase_map = {}  # Map of phase names to phase IDs
    for i, phase_name in enumerate(phases):
        phase_id = f"phase_{i+1}"
        project.add_phase(
            phase_id=phase_id,
            name=phase_name,
            description=f"Phase {i+1} of the project",
            order=i+1,
        )
        phase_map[phase_name] = phase_id
    
    # Add completed tasks from the task tracking data
    for task_data in tracking_data.get("completed_tasks", []):
        phase_name = task_data.get("phase")
        task_name = task_data.get("task")
        completed_at = task_data.get("completed_at")
        
        if not phase_name or not task_name:
            continue
        
        # Find the phase ID
        phase_id = None
        for p_name, p_id in phase_map.items():
            if phase_name.lower() in p_name.lower() or p_name.lower() in phase_name.lower():
                phase_id = p_id
                break
        
        if not phase_id:
            print(f"Could not find phase for task: {task_name} (phase: {phase_name})")
            continue
        
        # Create the task
        task = task_manager.create_task(
            name=task_name,
            description=f"Task from phase {phase_name}",
            project_id=project.id,
            phase_id=phase_id,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            progress=100.0,
        )
        
        # Set the completion time
        if completed_at:
            try:
                task.completed_at = datetime.fromisoformat(completed_at)
                task.started_at = task.completed_at  # Assume started at same time for completed tasks
                task.status_history.append({
                    "status": "completed",
                    "timestamp": completed_at,
                    "previous_status": "in_progress",
                })
            except Exception as e:
                print(f"Error setting completion time for task {task_name}: {e}")
    
    # Add current task
    current_phase = tracking_data.get("current_phase")
    current_task = tracking_data.get("current_task")
    
    if current_phase and current_task:
        # Find the phase ID
        phase_id = None
        for p_name, p_id in phase_map.items():
            if current_phase.lower() in p_name.lower() or p_name.lower() in current_phase.lower():
                phase_id = p_id
                break
        
        if phase_id:
            task = task_manager.create_task(
                name=current_task,
                description=f"Current task in phase {current_phase}",
                project_id=project.id,
                phase_id=phase_id,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                progress=50.0,  # Assuming 50% progress for current task
            )
            
            # Set the start time
            task.started_at = datetime.now()
            task.status_history.append({
                "status": "in_progress",
                "timestamp": task.started_at.isoformat(),
                "previous_status": "planned",
            })
        else:
            print(f"Could not find phase for current task: {current_task} (phase: {current_phase})")
    
    # Save the data
    task_manager.save_data()
    
    print(f"Migration complete. Created project '{project.name}' with ID '{project.id}'")
    print(f"Added {len(phases)} phases and {len(tracking_data.get('completed_tasks', [])) + (1 if current_task else 0)} tasks")
    
    return project.id


if __name__ == "__main__":
    # Paths to the existing task tracking file and project plan
    TASK_TRACKING_PATH = os.path.join(os.getcwd(), "docs", "task-tracking.json")
    PROJECT_PLAN_PATH = os.path.join(os.getcwd(), "docs", "project-plan.md")
    
    # Check if files exist
    if not os.path.exists(TASK_TRACKING_PATH):
        print(f"Task tracking file not found: {TASK_TRACKING_PATH}")
        exit(1)
    
    if not os.path.exists(PROJECT_PLAN_PATH):
        print(f"Project plan file not found: {PROJECT_PLAN_PATH}")
        # Try to find a similar file
        docs_dir = os.path.join(os.getcwd(), "docs")
        if os.path.exists(docs_dir):
            for filename in os.listdir(docs_dir):
                if "plan" in filename.lower() and filename.endswith(".md"):
                    PROJECT_PLAN_PATH = os.path.join(docs_dir, filename)
                    print(f"Using alternative project plan file: {PROJECT_PLAN_PATH}")
                    break
    
    # Run the migration
    project_id = migrate_tasks(
        task_tracking_path=TASK_TRACKING_PATH,
        project_plan_path=PROJECT_PLAN_PATH,
    )
    
    print(f"Project ID: {project_id}")
    print("You can now use the new task management system to manage your tasks.")
    print("To view the project progress, add the ProgressTracker component to your Dashboard.")
