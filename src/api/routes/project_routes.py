from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid

# Import authentication dependencies
from src.orchestrator.auth import get_token_manager, get_current_user

# Create router
router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

# Models
class ProjectProgressBase(BaseModel):
    progress: float
    completedTasks: int
    totalTasks: int
    status: str
    estimatedCompletion: Optional[str] = None
    lastUpdated: str

class ProjectProgressCreate(ProjectProgressBase):
    pass

class ProjectProgress(ProjectProgressBase):
    projectId: str

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    name: str
    description: str
    startDate: str
    endDate: Optional[str] = None
    status: str
    owner: str
    team: List[str] = []

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str
    createdAt: str
    updatedAt: str

    class Config:
        orm_mode = True

# In-memory storage (replace with database in production)
projects = {}
project_progress = {}

# Helper functions
def get_project(project_id: str):
    if project_id not in projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return projects[project_id]

# Routes
@router.get("/", response_model=List[Project])
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Get all projects"""
    return list(projects.values())

@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Create a new project"""
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    new_project = Project(
        id=project_id,
        name=project.name,
        description=project.description,
        startDate=project.startDate,
        endDate=project.endDate,
        status=project.status,
        owner=project.owner,
        team=project.team,
        createdAt=now,
        updatedAt=now
    )
    
    projects[project_id] = new_project.dict()
    
    # Initialize project progress
    project_progress[project_id] = ProjectProgress(
        projectId=project_id,
        progress=0.0,
        completedTasks=0,
        totalTasks=0,
        status="on_track",
        estimatedCompletion=None,
        lastUpdated=now
    ).dict()
    
    return new_project

@router.get("/{project_id}", response_model=Project)
async def get_project_by_id(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a project by ID"""
    return get_project(project_id)

@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str, 
    project_update: ProjectBase, 
    current_user: dict = Depends(get_current_user)
):
    """Update a project"""
    project = get_project(project_id)
    
    update_data = project_update.dict(exclude_unset=True)
    update_data["updatedAt"] = datetime.now().isoformat()
    
    for key, value in update_data.items():
        project[key] = value
    
    projects[project_id] = project
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project"""
    get_project(project_id)  # Check if project exists
    
    del projects[project_id]
    if project_id in project_progress:
        del project_progress[project_id]
    
    return None

@router.get("/{project_id}/progress", response_model=ProjectProgress)
async def get_project_progress(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get progress for a project"""
    get_project(project_id)  # Check if project exists
    
    if project_id not in project_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progress data for project {project_id} not found"
        )
    
    return project_progress[project_id]

@router.patch("/{project_id}/progress", response_model=ProjectProgress)
async def update_project_progress(
    project_id: str, 
    progress_update: ProjectProgressCreate, 
    current_user: dict = Depends(get_current_user)
):
    """Update progress for a project"""
    get_project(project_id)  # Check if project exists
    
    if project_id not in project_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Progress data for project {project_id} not found"
        )
    
    progress = project_progress[project_id]
    
    update_data = progress_update.dict(exclude_unset=True)
    update_data["lastUpdated"] = datetime.now().isoformat()
    
    for key, value in update_data.items():
        progress[key] = value
    
    project_progress[project_id] = progress
    return progress

# Demo data initialization
def init_demo_data():
    """Initialize demo data for testing"""
    # Create a demo project
    project_id = "demo-project-1"
    now = datetime.now().isoformat()
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = (datetime.now() + timedelta(days=60)).isoformat()
    
    projects[project_id] = Project(
        id=project_id,
        name="AI Orchestration Platform",
        description="A platform for orchestrating AI agents and workflows",
        startDate=start_date,
        endDate=end_date,
        status="active",
        owner="admin",
        team=["user1", "user2"],
        createdAt=now,
        updatedAt=now
    ).dict()
    
    # Create progress data
    project_progress[project_id] = ProjectProgress(
        projectId=project_id,
        progress=65.0,
        completedTasks=13,
        totalTasks=20,
        status="on_track",
        estimatedCompletion=end_date,
        lastUpdated=now
    ).dict()

# Initialize demo data
init_demo_data()
