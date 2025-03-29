"""
Progress tracking routes for the AI-Orchestration-Platform.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional

from src.monitoring.progress_tracking import (
    get_progress_service,
    ProgressTrackingService,
    ProgressUpdate,
    ProgressEstimate,
    ProgressSubscription
)

router = APIRouter(
    prefix="/progress",
    tags=["progress"],
    responses={404: {"description": "Not found"}},
)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    workflow_id: Optional[str] = None,
    include_completed: bool = False,
    include_failed: bool = True
):
    """
    WebSocket endpoint for progress updates.
    
    Args:
        websocket: WebSocket connection
        workflow_id: Optional workflow ID to filter by
        include_completed: Whether to include completed workflows/steps
        include_failed: Whether to include failed workflows/steps
    """
    progress_service = get_progress_service()
    
    # Create subscription
    subscription = ProgressSubscription(
        workflow_id=workflow_id,
        include_completed=include_completed,
        include_failed=include_failed
    )
    
    # Connect client
    await progress_service.connect(websocket, subscription)
    
    try:
        # Keep connection alive
        while True:
            # Wait for messages (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Disconnect client
        await progress_service.disconnect(websocket)


@router.post("/update", response_model=Dict[str, Any])
async def update_progress(
    update: ProgressUpdate,
    progress_service: ProgressTrackingService = Depends(get_progress_service)
):
    """
    Update progress for a workflow or step.
    
    Args:
        update: Progress update
        progress_service: Progress tracking service
        
    Returns:
        Updated progress data
    """
    return await progress_service.update_progress(update)


@router.get("/{workflow_id}", response_model=Dict[str, Any])
async def get_progress(
    workflow_id: str,
    progress_service: ProgressTrackingService = Depends(get_progress_service)
):
    """
    Get progress for a workflow.
    
    Args:
        workflow_id: Workflow ID
        progress_service: Progress tracking service
        
    Returns:
        Progress data
    """
    progress = await progress_service.get_progress(workflow_id)
    if progress is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return progress


@router.get("/{workflow_id}/history", response_model=List[Dict[str, Any]])
async def get_progress_history(
    workflow_id: str,
    progress_service: ProgressTrackingService = Depends(get_progress_service)
):
    """
    Get progress history for a workflow.
    
    Args:
        workflow_id: Workflow ID
        progress_service: Progress tracking service
        
    Returns:
        Progress history
    """
    return await progress_service.get_progress_history(workflow_id)


@router.get("/{workflow_id}/estimate", response_model=ProgressEstimate)
async def estimate_completion(
    workflow_id: str,
    progress_service: ProgressTrackingService = Depends(get_progress_service)
):
    """
    Estimate completion time for a workflow.
    
    Args:
        workflow_id: Workflow ID
        progress_service: Progress tracking service
        
    Returns:
        Progress estimate
    """
    estimate = await progress_service.estimate_completion(workflow_id)
    if estimate is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return estimate
