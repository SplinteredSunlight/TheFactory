"""
Progress tracking service for Dagger integration.

This module provides a progress tracking service for Dagger integration with real-time updates.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set, Callable, Awaitable
from datetime import datetime
import uuid

# Import FastAPI and WebSocket modules
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy classes for type hints
    class BaseModel: pass

from src.monitoring.dagger_logging import DaggerLogger
from src.monitoring.dagger_tracing import trace_function

# Configure logging
logger = DaggerLogger("progress_tracking")

# Progress tracking models
class ProgressUpdate(BaseModel):
    """Progress update model."""
    workflow_id: str
    step_id: Optional[str] = None
    percent_complete: float
    status: str
    message: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProgressEstimate(BaseModel):
    """Progress estimate model."""
    workflow_id: str
    percent_complete: float
    estimated_completion_time: Optional[str] = None
    estimated_remaining_seconds: Optional[int] = None
    steps_total: int
    steps_completed: int
    steps_in_progress: int
    steps_failed: int
    steps_pending: int


class ProgressSubscription(BaseModel):
    """Progress subscription model."""
    workflow_id: Optional[str] = None
    include_completed: bool = False
    include_failed: bool = True


# Progress tracking service
class ProgressTrackingService:
    """Progress tracking service for Dagger integration."""
    
    def __init__(self):
        """Initialize the progress tracking service."""
        self.progress_updates: Dict[str, Dict[str, Any]] = {}
        self.progress_history: Dict[str, List[Dict[str, Any]]] = {}
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, ProgressSubscription] = {}
        self.workflow_metadata: Dict[str, Dict[str, Any]] = {}
        self.step_metadata: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.last_update_time: Dict[str, float] = {}
        
        # Initialize the database connection
        self.db_connection = None
        
        # Start the cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_progress())
    
    async def connect(self, websocket: WebSocket, subscription: ProgressSubscription):
        """
        Connect a WebSocket client.
        
        Args:
            websocket: WebSocket connection
            subscription: Progress subscription
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = subscription
        
        # Send initial progress updates for the subscription
        await self._send_initial_updates(websocket, subscription)
    
    async def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    @trace_function(name="progress_tracking.update_progress")
    async def update_progress(self, update: ProgressUpdate) -> Dict[str, Any]:
        """
        Update progress for a workflow or step.
        
        Args:
            update: Progress update
            
        Returns:
            Updated progress data
        """
        # Set timestamp if not provided
        if not update.timestamp:
            update.timestamp = datetime.now().isoformat()
        
        # Get workflow ID
        workflow_id = update.workflow_id
        
        # Initialize workflow progress if not exists
        if workflow_id not in self.progress_updates:
            self.progress_updates[workflow_id] = {
                "workflow_id": workflow_id,
                "percent_complete": 0.0,
                "status": "in_progress",
                "steps": {},
                "start_time": update.timestamp,
                "last_update_time": update.timestamp,
                "metadata": update.metadata or {}
            }
            self.progress_history[workflow_id] = []
        
        # Update workflow metadata if provided
        if update.metadata:
            self.workflow_metadata.setdefault(workflow_id, {}).update(update.metadata)
        
        # Update step progress if step_id is provided
        if update.step_id:
            step_id = update.step_id
            
            # Initialize step progress if not exists
            if step_id not in self.progress_updates[workflow_id]["steps"]:
                self.progress_updates[workflow_id]["steps"][step_id] = {
                    "step_id": step_id,
                    "percent_complete": 0.0,
                    "status": "pending",
                    "start_time": update.timestamp,
                    "last_update_time": update.timestamp,
                    "metadata": update.metadata or {}
                }
            
            # Update step progress
            step_progress = self.progress_updates[workflow_id]["steps"][step_id]
            step_progress["percent_complete"] = update.percent_complete
            step_progress["status"] = update.status
            step_progress["last_update_time"] = update.timestamp
            if update.message:
                step_progress["message"] = update.message
            
            # Update step metadata if provided
            if update.metadata:
                self.step_metadata.setdefault(workflow_id, {}).setdefault(step_id, {}).update(update.metadata)
            
            # Calculate workflow progress based on steps
            self._calculate_workflow_progress(workflow_id)
        else:
            # Update workflow progress directly
            workflow_progress = self.progress_updates[workflow_id]
            workflow_progress["percent_complete"] = update.percent_complete
            workflow_progress["status"] = update.status
            workflow_progress["last_update_time"] = update.timestamp
            if update.message:
                workflow_progress["message"] = update.message
        
        # Add to history
        self.progress_history[workflow_id].append(update.dict())
        
        # Update last update time
        self.last_update_time[workflow_id] = time.time()
        
        # Save to database if available
        if self.db_connection:
            await self._save_to_database(workflow_id, update)
        
        # Broadcast update to subscribers
        await self._broadcast_update(update)
        
        return self.progress_updates[workflow_id]
    
    @trace_function(name="progress_tracking.get_progress")
    async def get_progress(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Progress data or None if not found
        """
        if workflow_id not in self.progress_updates:
            return None
        
        return self.progress_updates[workflow_id]
    
    @trace_function(name="progress_tracking.get_progress_history")
    async def get_progress_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get progress history for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Progress history
        """
        if workflow_id not in self.progress_history:
            return []
        
        return self.progress_history[workflow_id]
    
    @trace_function(name="progress_tracking.estimate_completion")
    async def estimate_completion(self, workflow_id: str) -> Optional[ProgressEstimate]:
        """
        Estimate completion time for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Progress estimate or None if not found
        """
        if workflow_id not in self.progress_updates:
            return None
        
        workflow_progress = self.progress_updates[workflow_id]
        
        # Count steps by status
        steps = workflow_progress["steps"]
        steps_total = len(steps)
        steps_completed = sum(1 for s in steps.values() if s["status"] == "completed")
        steps_in_progress = sum(1 for s in steps.values() if s["status"] == "in_progress")
        steps_failed = sum(1 for s in steps.values() if s["status"] == "failed")
        steps_pending = sum(1 for s in steps.values() if s["status"] == "pending")
        
        # Calculate estimated completion time
        estimated_completion_time = None
        estimated_remaining_seconds = None
        
        if steps_completed > 0 and workflow_progress["percent_complete"] > 0:
            # Parse start time
            start_time = datetime.fromisoformat(workflow_progress["start_time"])
            now = datetime.now()
            
            # Calculate elapsed time
            elapsed_seconds = (now - start_time).total_seconds()
            
            # Estimate remaining time
            if workflow_progress["percent_complete"] < 100:
                estimated_remaining_seconds = int(elapsed_seconds * (100 - workflow_progress["percent_complete"]) / workflow_progress["percent_complete"])
                estimated_completion_time = (now + asyncio.timedelta(seconds=estimated_remaining_seconds)).isoformat()
        
        return ProgressEstimate(
            workflow_id=workflow_id,
            percent_complete=workflow_progress["percent_complete"],
            estimated_completion_time=estimated_completion_time,
            estimated_remaining_seconds=estimated_remaining_seconds,
            steps_total=steps_total,
            steps_completed=steps_completed,
            steps_in_progress=steps_in_progress,
            steps_failed=steps_failed,
            steps_pending=steps_pending
        )
    
    async def _calculate_workflow_progress(self, workflow_id: str):
        """
        Calculate workflow progress based on steps.
        
        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.progress_updates:
            return
        
        workflow_progress = self.progress_updates[workflow_id]
        steps = workflow_progress["steps"]
        
        if not steps:
            return
        
        # Calculate average progress
        total_progress = sum(step["percent_complete"] for step in steps.values())
        avg_progress = total_progress / len(steps)
        
        # Update workflow progress
        workflow_progress["percent_complete"] = avg_progress
        
        # Update workflow status
        if all(step["status"] == "completed" for step in steps.values()):
            workflow_progress["status"] = "completed"
        elif any(step["status"] == "failed" for step in steps.values()):
            workflow_progress["status"] = "failed"
        else:
            workflow_progress["status"] = "in_progress"
    
    async def _broadcast_update(self, update: ProgressUpdate):
        """
        Broadcast progress update to subscribers.
        
        Args:
            update: Progress update
        """
        for websocket, subscription in list(self.subscriptions.items()):
            try:
                # Check if the client is subscribed to this workflow
                if subscription.workflow_id and subscription.workflow_id != update.workflow_id:
                    continue
                
                # Check if the client wants to receive completed/failed updates
                if update.status == "completed" and not subscription.include_completed:
                    continue
                
                if update.status == "failed" and not subscription.include_failed:
                    continue
                
                # Send update
                await websocket.send_text(json.dumps(update.dict()))
            except Exception as e:
                logger.error(f"Error broadcasting update: {e}")
                await self.disconnect(websocket)
    
    async def _send_initial_updates(self, websocket: WebSocket, subscription: ProgressSubscription):
        """
        Send initial progress updates for a subscription.
        
        Args:
            websocket: WebSocket connection
            subscription: Progress subscription
        """
        try:
            # Get workflows to send
            if subscription.workflow_id:
                # Send updates for a specific workflow
                if subscription.workflow_id in self.progress_updates:
                    workflow_progress = self.progress_updates[subscription.workflow_id]
                    
                    # Check if the client wants to receive completed/failed updates
                    if workflow_progress["status"] == "completed" and not subscription.include_completed:
                        return
                    
                    if workflow_progress["status"] == "failed" and not subscription.include_failed:
                        return
                    
                    # Send workflow update
                    await websocket.send_text(json.dumps(workflow_progress))
                    
                    # Send step updates
                    for step_id, step_progress in workflow_progress["steps"].items():
                        # Check if the client wants to receive completed/failed updates
                        if step_progress["status"] == "completed" and not subscription.include_completed:
                            continue
                        
                        if step_progress["status"] == "failed" and not subscription.include_failed:
                            continue
                        
                        await websocket.send_text(json.dumps(step_progress))
            else:
                # Send updates for all workflows
                for workflow_id, workflow_progress in self.progress_updates.items():
                    # Check if the client wants to receive completed/failed updates
                    if workflow_progress["status"] == "completed" and not subscription.include_completed:
                        continue
                    
                    if workflow_progress["status"] == "failed" and not subscription.include_failed:
                        continue
                    
                    # Send workflow update
                    await websocket.send_text(json.dumps(workflow_progress))
        except Exception as e:
            logger.error(f"Error sending initial updates: {e}")
            await self.disconnect(websocket)
    
    async def _save_to_database(self, workflow_id: str, update: ProgressUpdate):
        """
        Save progress update to database.
        
        Args:
            workflow_id: Workflow ID
            update: Progress update
        """
        # This is a placeholder for database integration
        # In a real implementation, this would save the update to a database
        pass
    
    async def _cleanup_old_progress(self):
        """Clean up old progress data."""
        while True:
            try:
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
                # Get current time
                now = time.time()
                
                # Find workflows to clean up (older than 7 days)
                workflows_to_clean = []
                for workflow_id, last_update in self.last_update_time.items():
                    if now - last_update > 7 * 24 * 3600:  # 7 days
                        workflows_to_clean.append(workflow_id)
                
                # Clean up old workflows
                for workflow_id in workflows_to_clean:
                    logger.info(f"Cleaning up old progress data for workflow {workflow_id}")
                    self.progress_updates.pop(workflow_id, None)
                    self.progress_history.pop(workflow_id, None)
                    self.workflow_metadata.pop(workflow_id, None)
                    self.step_metadata.pop(workflow_id, None)
                    self.last_update_time.pop(workflow_id, None)
            except Exception as e:
                logger.error(f"Error cleaning up old progress data: {e}")


# Create a singleton instance
_progress_service = None


def get_progress_service() -> ProgressTrackingService:
    """
    Get the progress tracking service.
    
    Returns:
        Progress tracking service
    """
    global _progress_service
    
    if _progress_service is None:
        _progress_service = ProgressTrackingService()
    
    return _progress_service


# FastAPI router for progress tracking
if FASTAPI_AVAILABLE:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
    
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
