"""
Dashboard API Routes for AI-Orchestration-Platform.

This module provides FastAPI routes for the Project Master Dashboard integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import os
import glob

from src.task_manager.manager import (
    get_task_manager,
    TaskManager,
    TaskStatus,
    TaskPriority,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Pydantic models for request/response validation
class ScanDirectoryRequest(BaseModel):
    directory: str
    depth: int = 2
    include_patterns: List[str] = ["*.json", "*.yaml", "*.md"]
    exclude_patterns: List[str] = ["node_modules", ".git", "dist", "build"]

class ScanDirectoryResponse(BaseModel):
    projects: List[Dict[str, Any]]

class DashboardConfigRequest(BaseModel):
    api: Dict[str, Any]
    scan: Dict[str, Any]
    ui: Dict[str, Any]
    dashboard: Optional[Dict[str, Any]] = None
    integration: Optional[Dict[str, Any]] = None

class DashboardConfigResponse(BaseModel):
    config: Dict[str, Any]

class DashboardStatsResponse(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    planned_tasks: int
    blocked_tasks: int

# Routes
@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(task_manager: TaskManager = Depends(get_task_manager)):
    """Get dashboard statistics."""
    projects = list(task_manager.projects.values())
    
    # Count projects by status
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if any(
        t.status == TaskStatus.IN_PROGRESS for t in p.tasks.values()
    ))
    completed_projects = sum(1 for p in projects if all(
        t.status == TaskStatus.COMPLETED for t in p.tasks.values()
    ) and len(p.tasks) > 0)
    
    # Count tasks by status
    all_tasks = [task for p in projects for task in p.tasks.values()]
    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
    in_progress_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
    planned_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.PLANNED)
    blocked_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.BLOCKED)
    
    return DashboardStatsResponse(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        planned_tasks=planned_tasks,
        blocked_tasks=blocked_tasks
    )

@router.post("/scan", response_model=ScanDirectoryResponse)
async def scan_directory(request: ScanDirectoryRequest):
    """Scan a directory for project files."""
    try:
        # Validate directory
        if not os.path.isdir(request.directory):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Directory not found: {request.directory}"
            )
        
        projects = []
        
        # Scan for JSON files
        pattern = os.path.join(request.directory, "**", "*.json")
        json_files = glob.glob(pattern, recursive=True)
        
        # Filter out excluded patterns
        for exclude in request.exclude_patterns:
            json_files = [f for f in json_files if exclude not in f]
        
        # Process JSON files
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check if it's a project file
                if isinstance(data, dict) and "tasks" in data and "name" in data:
                    projects.append(data)
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        # Scan for YAML files if needed
        # (Implementation would be similar to JSON files)
        
        # Scan for Markdown files if needed
        # (Implementation would extract project info from markdown)
        
        return ScanDirectoryResponse(projects=projects)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning directory: {str(e)}"
        )

@router.get("/config", response_model=DashboardConfigResponse)
async def get_dashboard_config():
    """Get dashboard configuration."""
    # Default configuration
    config = {
        "api": {
            "baseUrl": "http://localhost:8000",
            "authToken": "",
            "refreshInterval": 30000
        },
        "scan": {
            "enabled": True,
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
            "showCompletedTasks": True
        },
        "dashboard": {
            "title": "Project Master Dashboard",
            "logo": "",
            "showProjectSelector": True,
            "defaultProjectId": "",
            "enableTaskManagement": True,
            "enableRealTimeUpdates": True
        },
        "integration": {
            "aiOrchestrationPlatform": {
                "enabled": True,
                "apiEndpoint": "http://localhost:8000",
                "authToken": "",
                "projectId": "project_6d186b44"
            }
        }
    }
    
    # Try to load configuration from file
    config_path = os.path.join("dashboard", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                # Merge saved config with default config
                for key, value in saved_config.items():
                    if key in config:
                        config[key].update(value)
                    else:
                        config[key] = value
        except Exception as e:
            # Use default config if there's an error
            pass
    
    return DashboardConfigResponse(config=config)

@router.post("/config", response_model=DashboardConfigResponse)
async def update_dashboard_config(request: DashboardConfigRequest):
    """Update dashboard configuration."""
    try:
        # Create config directory if it doesn't exist
        os.makedirs("dashboard", exist_ok=True)
        
        # Save configuration to file
        config_path = os.path.join("dashboard", "config.json")
        with open(config_path, 'w') as f:
            json.dump(request.dict(), f, indent=2)
        
        return DashboardConfigResponse(config=request.dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}"
        )

@router.get("/projects/summary", response_model=List[Dict[str, Any]])
async def get_projects_summary(task_manager: TaskManager = Depends(get_task_manager)):
    """Get a summary of all projects."""
    projects = list(task_manager.projects.values())
    
    summaries = []
    for project in projects:
        # Calculate project progress
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks.values() if t.status == TaskStatus.COMPLETED)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get phase information
        phases = []
        for phase_id, phase in project.phases.items():
            phase_tasks = [project.tasks[task_id] for task_id in phase.tasks if task_id in project.tasks]
            phase_total = len(phase_tasks)
            phase_completed = sum(1 for t in phase_tasks if t.status == TaskStatus.COMPLETED)
            phase_progress = (phase_completed / phase_total * 100) if phase_total > 0 else 0
            
            phases.append({
                "id": phase_id,
                "name": phase.name,
                "order": phase.order,
                "taskCount": phase_total,
                "completedTasks": phase_completed,
                "progress": phase_progress
            })
        
        # Sort phases by order
        phases.sort(key=lambda p: p["order"])
        
        # Create project summary
        summary = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "taskCount": total_tasks,
            "completedTasks": completed_tasks,
            "progress": progress,
            "phases": phases,
            "createdAt": project.created_at.isoformat() if hasattr(project, 'created_at') else None,
            "updatedAt": project.updated_at.isoformat() if hasattr(project, 'updated_at') else None
        }
        
        summaries.append(summary)
    
    return summaries

@router.get("/tasks/recent", response_model=List[Dict[str, Any]])
async def get_recent_tasks(
    limit: int = Query(10, ge=1, le=100),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """Get recently updated tasks."""
    # Collect all tasks from all projects
    all_tasks = []
    for project in task_manager.projects.values():
        for task_id, task in project.tasks.items():
            # Add project information to task
            task_dict = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status.value,
                "progress": task.progress,
                "projectId": project.id,
                "projectName": project.name,
                "phaseId": task.phase_id,
                "phaseName": project.phases[task.phase_id].name if task.phase_id in project.phases else None,
                "updatedAt": task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
            }
            all_tasks.append(task_dict)
    
    # Sort by updated_at (most recent first)
    all_tasks.sort(key=lambda t: t["updatedAt"] if t["updatedAt"] else "", reverse=True)
    
    # Return limited number of tasks
    return all_tasks[:limit]
