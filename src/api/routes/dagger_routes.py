"""
API routes for Dagger integration.

This module provides API routes for Dagger workflows, agents, and pipelines.
"""

from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import (
    AgentExecutionConfig,
    DaggerContainerConfig,
    DaggerWorkflowConfig,
    DaggerWorkflowStep,
    DaggerPipelineConfig
)
from src.orchestrator.engine import OrchestrationEngine
from src.api.middlewares.validation import ValidatedAPIRoute

# Define API models
class WorkflowStepModel(BaseModel):
    """API model for a workflow step."""
    
    id: str = Field(..., description="Unique identifier for the step")
    name: str = Field(..., description="Name of the step")
    container: Dict[str, Any] = Field(..., description="Container configuration for the step")
    depends_on: List[str] = Field(default_factory=list, description="Steps this step depends on")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs for the step")
    outputs: List[str] = Field(default_factory=list, description="Outputs from the step")
    timeout_seconds: int = Field(default=300, description="Timeout for the step in seconds")


class WorkflowModel(BaseModel):
    """API model for a workflow."""
    
    id: UUID = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    steps: List[WorkflowStepModel] = Field(..., description="Steps in the workflow")
    container_config: Optional[Dict[str, Any]] = Field(None, description="Default container configuration for the workflow")
    status: str = Field(..., description="Status of the workflow")
    created_at: datetime = Field(..., description="When the workflow was created")
    updated_at: Optional[datetime] = Field(None, description="When the workflow was last updated")


class WorkflowCreateModel(BaseModel):
    """API model for creating a workflow."""
    
    name: str = Field(..., description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    steps: List[WorkflowStepModel] = Field(..., description="Steps in the workflow")
    container_config: Optional[Dict[str, Any]] = Field(None, description="Default container configuration for the workflow")


class WorkflowUpdateModel(BaseModel):
    """API model for updating a workflow."""
    
    name: Optional[str] = Field(None, description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    steps: Optional[List[WorkflowStepModel]] = Field(None, description="Steps in the workflow")
    container_config: Optional[Dict[str, Any]] = Field(None, description="Default container configuration for the workflow")


class WorkflowSummaryModel(BaseModel):
    """API model for a workflow summary."""
    
    id: UUID = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    status: str = Field(..., description="Status of the workflow")
    created_at: datetime = Field(..., description="When the workflow was created")
    updated_at: Optional[datetime] = Field(None, description="When the workflow was last updated")


class WorkflowExecutionModel(BaseModel):
    """API model for a workflow execution."""
    
    id: UUID = Field(..., description="Unique identifier for the execution")
    workflow_id: UUID = Field(..., description="ID of the workflow that was executed")
    status: str = Field(..., description="Status of the execution")
    steps: Dict[str, Dict[str, Any]] = Field(..., description="Status of each step in the execution")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs for the execution")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Outputs from the execution")
    started_at: datetime = Field(..., description="When the execution started")
    completed_at: Optional[datetime] = Field(None, description="When the execution completed")
    error: Optional[str] = Field(None, description="Error message if the execution failed")
    logs: Optional[str] = Field(None, description="Logs from the execution")


class PipelineModel(BaseModel):
    """API model for a pipeline."""
    
    id: UUID = Field(..., description="Unique identifier for the pipeline")
    name: str = Field(..., description="Name of the pipeline")
    description: Optional[str] = Field(None, description="Description of the pipeline")
    source_directory: str = Field(..., description="Source directory for the pipeline")
    pipeline_definition: Any = Field(..., description="Definition of the pipeline")
    caching_enabled: bool = Field(default=True, description="Whether to enable caching for the pipeline")
    timeout_seconds: int = Field(default=1800, description="Timeout for the pipeline in seconds")
    created_at: datetime = Field(..., description="When the pipeline was created")
    updated_at: Optional[datetime] = Field(None, description="When the pipeline was last updated")


class PipelineCreateModel(BaseModel):
    """API model for creating a pipeline."""
    
    name: str = Field(..., description="Name of the pipeline")
    description: Optional[str] = Field(None, description="Description of the pipeline")
    source_directory: str = Field(..., description="Source directory for the pipeline")
    pipeline_definition: Any = Field(..., description="Definition of the pipeline")
    caching_enabled: bool = Field(default=True, description="Whether to enable caching for the pipeline")
    timeout_seconds: int = Field(default=1800, description="Timeout for the pipeline in seconds")


class AgentModel(BaseModel):
    """API model for an agent."""
    
    id: UUID = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    capabilities: List[str] = Field(..., description="Capabilities of the agent")
    status: str = Field(..., description="Status of the agent")
    current_load: int = Field(default=0, description="Current load of the agent")
    max_load: int = Field(default=0, description="Maximum load of the agent")
    container_registry: Optional[str] = Field(None, description="Container registry for the agent")
    workflow_directory: Optional[str] = Field(None, description="Workflow directory for the agent")
    created_at: datetime = Field(..., description="When the agent was created")
    updated_at: Optional[datetime] = Field(None, description="When the agent was last updated")


class AgentCreateModel(BaseModel):
    """API model for creating an agent."""
    
    name: str = Field(..., description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities of the agent")
    container_registry: Optional[str] = Field(None, description="Container registry for the agent")
    workflow_directory: Optional[str] = Field(None, description="Workflow directory for the agent")
    max_concurrent_executions: int = Field(default=5, description="Maximum number of concurrent workflow executions")
    timeout_seconds: int = Field(default=600, description="Default timeout for workflow executions in seconds")


class ErrorModel(BaseModel):
    """API model for an error."""
    
    status: int = Field(..., description="HTTP status code")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Create API router
router = APIRouter(
    prefix="/dagger",
    tags=["dagger"],
    route_class=ValidatedAPIRoute
)

# Dependables
async def get_orchestration_engine() -> OrchestrationEngine:
    """Get the orchestration engine."""
    # In a real implementation, this would be a singleton
    return OrchestrationEngine()


@router.get(
    "/workflows",
    response_model=Dict[str, Any],
    summary="List all Dagger workflows",
    description="Returns a list of all Dagger workflows",
    responses={
        200: {"description": "A list of workflows"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def list_workflows(
    engine: OrchestrationEngine = Depends(get_orchestration_engine),
    status: Optional[str] = Query(None, description="Filter workflows by status"),
    limit: int = Query(20, description="Maximum number of workflows to return"),
    offset: int = Query(0, description="Number of workflows to skip")
) -> Dict[str, Any]:
    """
    List all Dagger workflows.
    
    Args:
        engine: Orchestration engine
        status: Filter workflows by status
        limit: Maximum number of workflows to return
        offset: Number of workflows to skip
        
    Returns:
        Dictionary containing workflows and pagination info
    """
    workflows = await engine.list_workflows()
    
    # Filter workflows by engine type and status
    filtered_workflows = [
        wf for wf in workflows
        if getattr(wf, "engine_type", "default") == "dagger"
        and (status is None or wf.get("status") == status)
    ]
    
    # Apply pagination
    paginated_workflows = filtered_workflows[offset:offset + limit]
    
    # Convert workflows to summary models
    workflow_summaries = [
        WorkflowSummaryModel(
            id=wf["id"],
            name=wf["name"],
            description=wf.get("description"),
            status=wf["status"],
            created_at=wf["created_at"],
            updated_at=wf.get("updated_at")
        ).dict()
        for wf in paginated_workflows
    ]
    
    return {
        "workflows": workflow_summaries,
        "total": len(filtered_workflows),
        "limit": limit,
        "offset": offset
    }


@router.post(
    "/workflows",
    response_model=WorkflowModel,
    status_code=201,
    summary="Create a new Dagger workflow",
    description="Creates a new Dagger workflow",
    responses={
        201: {"description": "Workflow created successfully"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def create_workflow(
    workflow: WorkflowCreateModel = Body(...),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> WorkflowModel:
    """
    Create a new Dagger workflow.
    
    Args:
        workflow: Workflow to create
        engine: Orchestration engine
        
    Returns:
        Created workflow
    """
    # Create the workflow
    created_workflow = engine.create_workflow(
        name=workflow.name,
        description=workflow.description
    )
    
    # Add steps
    for step in workflow.steps:
        created_workflow.add_task(
            name=step.name,
            agent=step.container.get("image", "default"),
            inputs=step.inputs,
            depends_on=step.depends_on
        )
    
    # Update workflow attributes
    created_workflow.container_config = workflow.container_config
    created_workflow.engine_type = "dagger"
    created_workflow.updated_at = datetime.now()
    
    # Return the workflow
    return WorkflowModel(
        id=created_workflow.id,
        name=created_workflow.name,
        description=created_workflow.description,
        steps=[WorkflowStepModel(**step.to_dict()) for step in created_workflow.tasks.values()],
        container_config=created_workflow.container_config,
        status=created_workflow.status,
        created_at=created_workflow.created_at,
        updated_at=created_workflow.updated_at
    )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowModel,
    summary="Get a specific Dagger workflow",
    description="Returns details for a specific Dagger workflow",
    responses={
        200: {"description": "Workflow details"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def get_workflow(
    workflow_id: UUID = Path(..., description="ID of the workflow to retrieve"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> WorkflowModel:
    """
    Get a specific Dagger workflow.
    
    Args:
        workflow_id: ID of the workflow to retrieve
        engine: Orchestration engine
        
    Returns:
        Workflow details
        
    Raises:
        HTTPException: If the workflow doesn't exist
    """
    try:
        workflow = engine.get_workflow(str(workflow_id))
        
        # Check if it's a Dagger workflow
        if getattr(workflow, "engine_type", "default") != "dagger":
            raise HTTPException(status_code=404, detail="Dagger workflow not found")
        
        return WorkflowModel(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            steps=[WorkflowStepModel(**step.to_dict()) for step in workflow.tasks.values()],
            container_config=getattr(workflow, "container_config", None),
            status=workflow.status,
            created_at=workflow.created_at,
            updated_at=getattr(workflow, "updated_at", None)
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.patch(
    "/workflows/{workflow_id}",
    response_model=WorkflowModel,
    summary="Update a Dagger workflow",
    description="Updates an existing Dagger workflow",
    responses={
        200: {"description": "Workflow updated successfully"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def update_workflow(
    workflow_id: UUID = Path(..., description="ID of the workflow to update"),
    workflow_update: WorkflowUpdateModel = Body(...),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> WorkflowModel:
    """
    Update a Dagger workflow.
    
    Args:
        workflow_id: ID of the workflow to update
        workflow_update: Workflow updates
        engine: Orchestration engine
        
    Returns:
        Updated workflow
        
    Raises:
        HTTPException: If the workflow doesn't exist
    """
    try:
        workflow = engine.get_workflow(str(workflow_id))
        
        # Check if it's a Dagger workflow
        if getattr(workflow, "engine_type", "default") != "dagger":
            raise HTTPException(status_code=404, detail="Dagger workflow not found")
        
        # Update workflow attributes
        if workflow_update.name is not None:
            workflow.name = workflow_update.name
        if workflow_update.description is not None:
            workflow.description = workflow_update.description
        if workflow_update.container_config is not None:
            workflow.container_config = workflow_update.container_config
        if workflow_update.steps is not None:
            # Clear existing tasks
            workflow.tasks = {}
            
            # Add steps
            for step in workflow_update.steps:
                workflow.add_task(
                    name=step.name,
                    agent=step.container.get("image", "default"),
                    inputs=step.inputs,
                    depends_on=step.depends_on
                )
        
        workflow.updated_at = datetime.now()
        
        return WorkflowModel(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            steps=[WorkflowStepModel(**step.to_dict()) for step in workflow.tasks.values()],
            container_config=getattr(workflow, "container_config", None),
            status=workflow.status,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.delete(
    "/workflows/{workflow_id}",
    status_code=204,
    summary="Delete a Dagger workflow",
    description="Deletes a Dagger workflow",
    responses={
        204: {"description": "Workflow deleted successfully"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def delete_workflow(
    workflow_id: UUID = Path(..., description="ID of the workflow to delete"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> None:
    """
    Delete a Dagger workflow.
    
    Args:
        workflow_id: ID of the workflow to delete
        engine: Orchestration engine
        
    Raises:
        HTTPException: If the workflow doesn't exist
    """
    try:
        workflow = engine.get_workflow(str(workflow_id))
        
        # Check if it's a Dagger workflow
        if getattr(workflow, "engine_type", "default") != "dagger":
            raise HTTPException(status_code=404, detail="Dagger workflow not found")
        
        # Delete the workflow
        engine.workflows.pop(str(workflow_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=Dict[str, Any],
    status_code=202,
    summary="Execute a Dagger workflow",
    description="Executes a Dagger workflow",
    responses={
        202: {"description": "Workflow execution started"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def execute_workflow(
    workflow_id: UUID = Path(..., description="ID of the workflow to execute"),
    inputs: Dict[str, Any] = Body(default={}),
    container_registry: Optional[str] = Body(None),
    container_credentials: Optional[Dict[str, str]] = Body(None),
    workflow_defaults: Optional[Dict[str, Any]] = Body(None),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Execute a Dagger workflow.
    
    Args:
        workflow_id: ID of the workflow to execute
        inputs: Input parameters for the workflow
        container_registry: Container registry to use
        container_credentials: Credentials for the container registry
        workflow_defaults: Default parameters for the workflow
        engine: Orchestration engine
        
    Returns:
        Execution details
        
    Raises:
        HTTPException: If the workflow doesn't exist
    """
    try:
        # Execute the workflow
        execution_id = str(uuid4())
        
        # Start workflow execution asynchronously
        engine.execute_workflow(
            workflow_id=str(workflow_id),
            engine_type="dagger",
            inputs=inputs,
            container_registry=container_registry,
            container_credentials=container_credentials,
            workflow_defaults=workflow_defaults,
            execution_id=execution_id
        )
        
        return {
            "execution_id": execution_id,
            "status": "pending",
            "workflow_id": str(workflow_id)
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Workflow Execution Endpoints

@router.get(
    "/workflows/{workflow_id}/executions",
    response_model=Dict[str, Any],
    summary="List executions for a workflow",
    description="Returns a list of executions for a specific workflow",
    responses={
        200: {"description": "A list of workflow executions"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def list_workflow_executions(
    workflow_id: UUID = Path(..., description="ID of the workflow"),
    status: Optional[str] = Query(None, description="Filter executions by status"),
    limit: int = Query(20, description="Maximum number of executions to return"),
    offset: int = Query(0, description="Number of executions to skip"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    List executions for a workflow.
    
    Args:
        workflow_id: ID of the workflow
        status: Filter executions by status
        limit: Maximum number of executions to return
        offset: Number of executions to skip
        engine: Orchestration engine
        
    Returns:
        Dictionary containing executions and pagination info
        
    Raises:
        HTTPException: If the workflow doesn't exist
    """
    try:
        # Check if the workflow exists
        workflow = engine.get_workflow(str(workflow_id))
        
        # Get executions for the workflow
        # In a real implementation, this would query a database
        executions = []
        
        # Filter by status if provided
        if status:
            executions = [ex for ex in executions if ex.get("status") == status]
            
        # Apply pagination
        paginated_executions = executions[offset:offset + limit]
        
        # Convert to API models
        execution_models = [
            WorkflowExecutionModel(
                id=ex["id"],
                workflow_id=workflow_id,
                status=ex["status"],
                steps=ex["steps"],
                inputs=ex.get("inputs", {}),
                outputs=ex.get("outputs", {}),
                started_at=ex["started_at"],
                completed_at=ex.get("completed_at"),
                error=ex.get("error"),
                logs=ex.get("logs")
            ).dict()
            for ex in paginated_executions
        ]
        
        return {
            "executions": execution_models,
            "total": len(executions),
            "limit": limit,
            "offset": offset
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionModel,
    summary="Get a specific workflow execution",
    description="Returns details for a specific workflow execution",
    responses={
        200: {"description": "Execution details"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def get_execution(
    execution_id: UUID = Path(..., description="ID of the execution to retrieve"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> WorkflowExecutionModel:
    """
    Get a specific workflow execution.
    
    Args:
        execution_id: ID of the execution to retrieve
        engine: Orchestration engine
        
    Returns:
        Execution details
        
    Raises:
        HTTPException: If the execution doesn't exist
    """
    # In a real implementation, this would query a database
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Execution not found")


@router.delete(
    "/executions/{execution_id}",
    status_code=204,
    summary="Cancel a workflow execution",
    description="Cancels a running workflow execution",
    responses={
        204: {"description": "Execution cancelled successfully"},
        400: {"model": ErrorModel, "description": "Execution cannot be cancelled"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def cancel_execution(
    execution_id: UUID = Path(..., description="ID of the execution to cancel"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> None:
    """
    Cancel a workflow execution.
    
    Args:
        execution_id: ID of the execution to cancel
        engine: Orchestration engine
        
    Raises:
        HTTPException: If the execution doesn't exist or cannot be cancelled
    """
    # In a real implementation, this would cancel the execution
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Execution not found")


# Agent Endpoints

@router.get(
    "/agents",
    response_model=Dict[str, Any],
    summary="List all Dagger agents",
    description="Returns a list of all Dagger agents",
    responses={
        200: {"description": "A list of agents"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def list_agents(
    status: Optional[str] = Query(None, description="Filter agents by status"),
    capability: Optional[str] = Query(None, description="Filter agents by capability"),
    limit: int = Query(20, description="Maximum number of agents to return"),
    offset: int = Query(0, description="Number of agents to skip"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    List all Dagger agents.
    
    Args:
        status: Filter agents by status
        capability: Filter agents by capability
        limit: Maximum number of agents to return
        offset: Number of agents to skip
        engine: Orchestration engine
        
    Returns:
        Dictionary containing agents and pagination info
    """
    # Get all agents
    agents = await engine.list_agents()
    
    # Filter by status if provided
    if status:
        agents = [agent for agent in agents if agent.get("status") == status]
        
    # Filter by capability if provided
    if capability:
        agents = [
            agent for agent in agents 
            if capability in agent.get("capabilities", [])
        ]
        
    # Apply pagination
    paginated_agents = agents[offset:offset + limit]
    
    # Convert to API models
    agent_models = [
        AgentModel(
            id=agent.get("id", uuid4()),
            name=agent["name"],
            description=agent.get("description"),
            capabilities=agent.get("capabilities", []),
            status=agent.get("status", "idle"),
            current_load=agent.get("current_load", 0),
            max_load=agent.get("max_load", 0),
            container_registry=agent.get("container_registry"),
            workflow_directory=agent.get("workflow_directory"),
            created_at=agent.get("created_at", datetime.now()),
            updated_at=agent.get("updated_at")
        ).dict()
        for agent in paginated_agents
    ]
    
    return {
        "agents": agent_models,
        "total": len(agents),
        "limit": limit,
        "offset": offset
    }


@router.post(
    "/agents",
    response_model=AgentModel,
    status_code=201,
    summary="Create a new Dagger agent",
    description="Creates a new Dagger agent",
    responses={
        201: {"description": "Agent created successfully"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def create_agent(
    agent: AgentCreateModel = Body(...),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> AgentModel:
    """
    Create a new Dagger agent.
    
    Args:
        agent: Agent to create
        engine: Orchestration engine
        
    Returns:
        Created agent
    """
    # Register the agent
    agent_id = str(uuid4())
    
    # Create agent info
    agent_info = {
        "agent_id": agent_id,
        "name": agent.name,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "container_registry": agent.container_registry,
        "workflow_directory": agent.workflow_directory,
        "max_concurrent_executions": agent.max_concurrent_executions,
        "timeout_seconds": agent.timeout_seconds,
        "created_at": datetime.now().isoformat(),
        "status": "idle",
        "current_load": 0,
        "max_load": agent.max_concurrent_executions
    }
    
    # Register the agent with the orchestration engine
    await engine.register_agent(
        agent_id=agent_id,
        name=agent.name,
        capabilities={
            "dagger": True,
            "container_registry": agent.container_registry is not None,
            "workflow_directory": agent.workflow_directory is not None,
            "max_concurrent_executions": agent.max_concurrent_executions,
            "timeout_seconds": agent.timeout_seconds,
            "user_defined": {cap: True for cap in agent.capabilities}
        }
    )
    
    # Return the agent model
    return AgentModel(
        id=agent_id,
        name=agent.name,
        description=agent.description,
        capabilities=agent.capabilities,
        status="idle",
        current_load=0,
        max_load=agent.max_concurrent_executions,
        container_registry=agent.container_registry,
        workflow_directory=agent.workflow_directory,
        created_at=datetime.now(),
        updated_at=None
    )


# Pipeline Endpoints

@router.get(
    "/pipelines",
    response_model=Dict[str, Any],
    summary="List all Dagger pipelines",
    description="Returns a list of all Dagger pipelines",
    responses={
        200: {"description": "A list of pipelines"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def list_pipelines(
    limit: int = Query(20, description="Maximum number of pipelines to return"),
    offset: int = Query(0, description="Number of pipelines to skip"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    List all Dagger pipelines.
    
    Args:
        limit: Maximum number of pipelines to return
        offset: Number of pipelines to skip
        engine: Orchestration engine
        
    Returns:
        Dictionary containing pipelines and pagination info
    """
    # In a real implementation, this would query a database
    # For now, return an empty list
    return {
        "pipelines": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.post(
    "/pipelines",
    response_model=PipelineModel,
    status_code=201,
    summary="Create a new Dagger pipeline",
    description="Creates a new Dagger pipeline",
    responses={
        201: {"description": "Pipeline created successfully"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def create_pipeline(
    pipeline: PipelineCreateModel = Body(...),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> PipelineModel:
    """
    Create a new Dagger pipeline.
    
    Args:
        pipeline: Pipeline to create
        engine: Orchestration engine
        
    Returns:
        Created pipeline
    """
    # Generate a pipeline ID
    pipeline_id = uuid4()
    
    # Create the pipeline
    # In a real implementation, this would store the pipeline in a database
    
    # Return the pipeline model
    return PipelineModel(
        id=pipeline_id,
        name=pipeline.name,
        description=pipeline.description,
        source_directory=pipeline.source_directory,
        pipeline_definition=pipeline.pipeline_definition,
        caching_enabled=pipeline.caching_enabled,
        timeout_seconds=pipeline.timeout_seconds,
        created_at=datetime.now(),
        updated_at=None
    )


@router.post(
    "/pipelines/{pipeline_id}/execute",
    response_model=Dict[str, Any],
    status_code=202,
    summary="Execute a Dagger pipeline",
    description="Executes a Dagger pipeline",
    responses={
        202: {"description": "Pipeline execution started"},
        400: {"model": ErrorModel, "description": "Bad request"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def execute_pipeline(
    pipeline_id: UUID = Path(..., description="ID of the pipeline to execute"),
    inputs: Dict[str, Any] = Body(default={}),
    source_directory: Optional[str] = Body(None),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Execute a Dagger pipeline.
    
    Args:
        pipeline_id: ID of the pipeline to execute
        inputs: Input parameters for the pipeline
        source_directory: Source directory for the pipeline
        engine: Orchestration engine
        
    Returns:
        Execution details
        
    Raises:
        HTTPException: If the pipeline doesn't exist
    """
    # In a real implementation, this would execute the pipeline
    # For now, return a placeholder
    execution_id = uuid4()
    
    return {
        "execution_id": str(execution_id),
        "status": "pending",
        "pipeline_id": str(pipeline_id)
    }


# Container Management Endpoints

@router.get(
    "/containers",
    response_model=Dict[str, Any],
    summary="List all containers",
    description="Returns a list of all containers",
    responses={
        200: {"description": "A list of containers"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"}
    }
)
async def list_containers(
    workflow_id: Optional[UUID] = Query(None, description="Filter containers by workflow ID"),
    status: Optional[str] = Query(None, description="Filter containers by status"),
    limit: int = Query(20, description="Maximum number of containers to return"),
    offset: int = Query(0, description="Number of containers to skip"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    List all containers.
    
    Args:
        workflow_id: Filter containers by workflow ID
        status: Filter containers by status
        limit: Maximum number of containers to return
        offset: Number of containers to skip
        engine: Orchestration engine
        
    Returns:
        Dictionary containing containers and pagination info
    """
    # In a real implementation, this would query a database
    # For now, return an empty list
    return {
        "containers": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get(
    "/containers/{container_id}",
    response_model=Dict[str, Any],
    summary="Get container details",
    description="Returns details for a specific container",
    responses={
        200: {"description": "Container details"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def get_container(
    container_id: str = Path(..., description="ID of the container to retrieve"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Get container details.
    
    Args:
        container_id: ID of the container to retrieve
        engine: Orchestration engine
        
    Returns:
        Container details
        
    Raises:
        HTTPException: If the container doesn't exist
    """
    # In a real implementation, this would query a database
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Container not found")


@router.post(
    "/containers/{container_id}/start",
    response_model=Dict[str, Any],
    summary="Start a container",
    description="Starts a container",
    responses={
        200: {"description": "Container started successfully"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def start_container(
    container_id: str = Path(..., description="ID of the container to start"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Start a container.
    
    Args:
        container_id: ID of the container to start
        engine: Orchestration engine
        
    Returns:
        Container status
        
    Raises:
        HTTPException: If the container doesn't exist
    """
    # In a real implementation, this would start the container
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Container not found")


@router.post(
    "/containers/{container_id}/stop",
    response_model=Dict[str, Any],
    summary="Stop a container",
    description="Stops a container",
    responses={
        200: {"description": "Container stopped successfully"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def stop_container(
    container_id: str = Path(..., description="ID of the container to stop"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Stop a container.
    
    Args:
        container_id: ID of the container to stop
        engine: Orchestration engine
        
    Returns:
        Container status
        
    Raises:
        HTTPException: If the container doesn't exist
    """
    # In a real implementation, this would stop the container
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Container not found")


@router.get(
    "/containers/{container_id}/logs",
    response_model=Dict[str, Any],
    summary="Get container logs",
    description="Returns logs for a specific container",
    responses={
        200: {"description": "Container logs"},
        401: {"model": ErrorModel, "description": "Unauthorized"},
        403: {"model": ErrorModel, "description": "Forbidden"},
        404: {"model": ErrorModel, "description": "Not found"}
    }
)
async def get_container_logs(
    container_id: str = Path(..., description="ID of the container to get logs for"),
    engine: OrchestrationEngine = Depends(get_orchestration_engine)
) -> Dict[str, Any]:
    """
    Get container logs.
    
    Args:
        container_id: ID of the container to get logs for
        engine: Orchestration engine
        
    Returns:
        Container logs
        
    Raises:
        HTTPException: If the container doesn't exist
    """
    # In a real implementation, this would get the container logs
    # For now, return a placeholder
    raise HTTPException(status_code=404, detail="Container not found")


# Export router
dagger_router = router
