"""
Task Management API Routes for AI-Orchestration-Platform.

This module provides FastAPI routes for the task management system.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import asyncio
from enum import Enum

from src.task_manager.manager import (
    get_task_manager,
    TaskManager,
    TaskStatus,
    TaskPriority,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


# Pydantic models for request/response validation
class TaskBase(BaseModel):
    name: str
    description: str
    phase_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = TaskStatus.PLANNED.value
    priority: Optional[str] = TaskPriority.MEDIUM.value
    progress: Optional[float] = 0.0
    assignee_id: Optional[str] = None
    assignee_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    project_id: str


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phase_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[float] = None
    assignee_id: Optional[str] = None
    assignee_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    children: List[str] = []
    status_history: List[Dict[str, Any]] = []
    result: Optional[Any] = None
    error: Optional[str] = None

    class Config:
        orm_mode = True


class PhaseBase(BaseModel):
    name: str
    description: Optional[str] = ""
    order: int = 0
    metadata: Optional[Dict[str, Any]] = None


class PhaseCreate(PhaseBase):
    project_id: str
    phase_id: str


class PhaseResponse(PhaseBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    tasks: List[str] = []

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    phases: Dict[str, PhaseResponse] = {}
    tasks: Dict[str, TaskResponse] = {}

    class Config:
        orm_mode = True


class ProjectProgressResponse(BaseModel):
    project_id: str
    progress: float
    phase_progress: Dict[str, float] = {}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast(self, project_id: str, message: Dict[str, Any]):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                await connection.send_json(message)


# Singleton connection manager
manager = ConnectionManager()


def get_manager():
    return manager


# Helper function to convert task to response model
def task_to_response(task):
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        project_id=task.project_id,
        phase_id=task.phase_id,
        parent_id=task.parent_id,
        status=task.status.value,
        priority=task.priority.value,
        progress=task.progress,
        assignee_id=task.assignee_id,
        assignee_type=task.assignee_type,
        metadata=task.metadata,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        children=task.children,
        status_history=task.status_history,
        result=task.result,
        error=task.error,
    )


# Helper function to convert phase to response model
def phase_to_response(phase):
    return PhaseResponse(
        id=phase.id,
        name=phase.name,
        description=phase.description,
        project_id=phase.project_id,
        order=phase.order,
        metadata=phase.metadata,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
        tasks=phase.tasks,
    )


# Helper function to convert project to response model
def project_to_response(project):
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        metadata=project.metadata,
        created_at=project.created_at,
        updated_at=project.updated_at,
        phases={
            phase_id: phase_to_response(phase)
            for phase_id, phase in project.phases.items()
        },
        tasks={
            task_id: task_to_response(task)
            for task_id, task in project.tasks.items()
        },
    )


# Project routes
@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate, task_manager: TaskManager = Depends(get_task_manager)
):
    """Create a new project."""
    new_project = task_manager.create_project(
        name=project.name,
        description=project.description,
        metadata=project.metadata,
    )
    return project_to_response(new_project)


@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(task_manager: TaskManager = Depends(get_task_manager)):
    """Get all projects."""
    return [
        project_to_response(project) for project in task_manager.projects.values()
    ]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str, task_manager: TaskManager = Depends(get_task_manager)
):
    """Get a project by ID."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    return project_to_response(project)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Update a project."""
    updated_project = task_manager.update_project(
        project_id=project_id,
        name=project.name,
        description=project.description,
        metadata=project.metadata,
    )
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    # Broadcast update
    await connection_manager.broadcast(
        project_id,
        {
            "type": "project_updated",
            "data": project_to_response(updated_project).dict(),
        },
    )
    
    return project_to_response(updated_project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Delete a project."""
    success = task_manager.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    # Broadcast deletion
    await connection_manager.broadcast(
        project_id,
        {
            "type": "project_deleted",
            "data": {"project_id": project_id},
        },
    )
    
    return None


@router.get("/projects/{project_id}/progress", response_model=ProjectProgressResponse)
async def get_project_progress(
    project_id: str, task_manager: TaskManager = Depends(get_task_manager)
):
    """Get the progress of a project."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    progress = task_manager.calculate_project_progress(project_id)
    phase_progress = {
        phase_id: task_manager.calculate_phase_progress(project_id, phase_id)
        for phase_id in project.phases
    }
    
    return ProjectProgressResponse(
        project_id=project_id,
        progress=progress,
        phase_progress=phase_progress,
    )


# Phase routes
@router.post("/projects/{project_id}/phases", response_model=PhaseResponse, status_code=status.HTTP_201_CREATED)
async def create_phase(
    project_id: str,
    phase: PhaseCreate,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Create a new phase in a project."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    new_phase = project.add_phase(
        phase_id=phase.phase_id,
        name=phase.name,
        description=phase.description,
        order=phase.order,
        metadata=phase.metadata,
    )
    
    task_manager.save_data()
    
    # Broadcast creation
    await connection_manager.broadcast(
        project_id,
        {
            "type": "phase_created",
            "data": phase_to_response(new_phase).dict(),
        },
    )
    
    return phase_to_response(new_phase)


@router.get("/projects/{project_id}/phases", response_model=List[PhaseResponse])
async def get_phases(
    project_id: str, task_manager: TaskManager = Depends(get_task_manager)
):
    """Get all phases in a project."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    return [phase_to_response(phase) for phase in project.phases.values()]


@router.get("/projects/{project_id}/phases/{phase_id}", response_model=PhaseResponse)
async def get_phase(
    project_id: str,
    phase_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Get a phase by ID."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    if phase_id not in project.phases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase with ID {phase_id} not found in project {project_id}",
        )
    
    return phase_to_response(project.phases[phase_id])


# Task routes
@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Create a new task."""
    new_task = task_manager.create_task(
        name=task.name,
        description=task.description,
        project_id=task.project_id,
        phase_id=task.phase_id,
        parent_id=task.parent_id,
        status=task.status,
        priority=task.priority,
        progress=task.progress,
        assignee_id=task.assignee_id,
        assignee_type=task.assignee_type,
        metadata=task.metadata,
    )
    
    if not new_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create task. Check project_id, phase_id, and parent_id.",
        )
    
    # Broadcast creation
    await connection_manager.broadcast(
        task.project_id,
        {
            "type": "task_created",
            "data": task_to_response(new_task).dict(),
        },
    )
    
    return task_to_response(new_task)


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def get_tasks(
    project_id: str,
    phase_id: Optional[str] = None,
    status: Optional[str] = None,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Get tasks in a project, optionally filtered by phase or status."""
    project = task_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )
    
    if phase_id:
        tasks = task_manager.get_tasks_by_phase(project_id, phase_id)
    elif status:
        tasks = task_manager.get_tasks_by_status(project_id, status)
    else:
        tasks = list(project.tasks.values())
    
    return [task_to_response(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, task_manager: TaskManager = Depends(get_task_manager)
):
    """Get a task by ID."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    return task_to_response(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Update a task."""
    updated_task = task_manager.update_task(
        task_id=task_id,
        name=task.name,
        description=task.description,
        phase_id=task.phase_id,
        parent_id=task.parent_id,
        status=task.status,
        priority=task.priority,
        progress=task.progress,
        assignee_id=task.assignee_id,
        assignee_type=task.assignee_type,
        metadata=task.metadata,
        result=task.result,
        error=task.error,
    )
    
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Broadcast update
    await connection_manager.broadcast(
        updated_task.project_id,
        {
            "type": "task_updated",
            "data": task_to_response(updated_task).dict(),
        },
    )
    
    return task_to_response(updated_task)


@router.put("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status: str,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Update a task's status."""
    updated_task = task_manager.update_task_status(task_id, status)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Broadcast update
    await connection_manager.broadcast(
        updated_task.project_id,
        {
            "type": "task_updated",
            "data": task_to_response(updated_task).dict(),
        },
    )
    
    return task_to_response(updated_task)


@router.put("/tasks/{task_id}/progress", response_model=TaskResponse)
async def update_task_progress(
    task_id: str,
    progress: float,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Update a task's progress."""
    updated_task = task_manager.update_task_progress(task_id, progress)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Broadcast update
    await connection_manager.broadcast(
        updated_task.project_id,
        {
            "type": "task_updated",
            "data": task_to_response(updated_task).dict(),
        },
    )
    
    return task_to_response(updated_task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
    connection_manager: ConnectionManager = Depends(get_manager),
):
    """Delete a task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    project_id = task.project_id
    success = task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task with ID {task_id}",
        )
    
    # Broadcast deletion
    await connection_manager.broadcast(
        project_id,
        {
            "type": "task_deleted",
            "data": {"task_id": task_id},
        },
    )
    
    return None


@router.get("/assignee/{assignee_id}/tasks", response_model=List[TaskResponse])
async def get_tasks_by_assignee(
    assignee_id: str,
    assignee_type: Optional[str] = None,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Get all tasks assigned to a specific assignee."""
    tasks = task_manager.get_tasks_by_assignee(assignee_id, assignee_type)
    return [task_to_response(task) for task in tasks]


# WebSocket endpoint for real-time updates
@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    connection_manager: ConnectionManager = Depends(get_manager),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """WebSocket endpoint for real-time updates."""
    # Check if project exists
    project = task_manager.get_project(project_id)
    if not project:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await connection_manager.connect(websocket, project_id)
    try:
        # Send initial project data
        await websocket.send_json({
            "type": "initial_data",
            "data": project_to_response(project).dict(),
        })
        
        # Keep connection alive
        while True:
            # Wait for any message (ping)
            await websocket.receive_text()
            # Send a pong message
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, project_id)
