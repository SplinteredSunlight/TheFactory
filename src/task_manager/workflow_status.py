"""
Workflow Status Tracking for Task Management

This module provides utilities for tracking the status of Dagger workflows.
It supports detailed state management, status transitions, and persistence.
"""

import os
import sys
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker

logger = logging.getLogger(__name__)


class WorkflowState:
    """Enum-like class for workflow states."""
    CREATED = "created"
    PREPARING = "preparing"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class WorkflowStatusTransition:
    """
    Represents a transition between workflow states.
    
    This class tracks the details of a state transition, including
    the source and target states, timestamp, and any additional details.
    """
    
    def __init__(
        self,
        source_state: str,
        target_state: str,
        timestamp: Optional[datetime] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow status transition.
        
        Args:
            source_state: The state before the transition
            target_state: The state after the transition
            timestamp: When the transition occurred (defaults to now)
            details: Additional details about the transition
        """
        self.source_state = source_state
        self.target_state = target_state
        self.timestamp = timestamp or datetime.now()
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transition to a dictionary."""
        return {
            "source_state": self.source_state,
            "target_state": self.target_state,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStatusTransition':
        """Create a transition from a dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        return cls(
            source_state=data["source_state"],
            target_state=data["target_state"],
            timestamp=timestamp,
            details=data.get("details", {})
        )


class WorkflowStatus:
    """
    Status of a workflow.
    
    This class tracks the current state of a workflow, its history,
    and provides methods for updating and querying the status.
    """
    
    def __init__(
        self,
        workflow_id: str,
        initial_state: str = WorkflowState.CREATED,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow status.
        
        Args:
            workflow_id: ID of the workflow
            initial_state: Initial state of the workflow
            metadata: Additional metadata about the workflow
        """
        self.workflow_id = workflow_id
        self.current_state = initial_state
        self.metadata = metadata or {}
        self.history = []
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
        # Add initial state to history
        self._add_transition(
            source_state=WorkflowState.UNKNOWN,
            target_state=initial_state,
            details={"action": "created"}
        )
    
    def _add_transition(
        self,
        source_state: str,
        target_state: str,
        details: Optional[Dict[str, Any]] = None
    ) -> WorkflowStatusTransition:
        """
        Add a transition to the history.
        
        Args:
            source_state: The state before the transition
            target_state: The state after the transition
            details: Additional details about the transition
            
        Returns:
            The created transition
        """
        transition = WorkflowStatusTransition(
            source_state=source_state,
            target_state=target_state,
            timestamp=datetime.now(),
            details=details
        )
        self.history.append(transition)
        self.updated_at = transition.timestamp
        return transition
    
    def update_state(
        self,
        new_state: str,
        details: Optional[Dict[str, Any]] = None
    ) -> WorkflowStatusTransition:
        """
        Update the workflow state.
        
        Args:
            new_state: New state for the workflow
            details: Additional details about the state change
            
        Returns:
            The created transition
        """
        old_state = self.current_state
        self.current_state = new_state
        
        # Add transition to history
        return self._add_transition(
            source_state=old_state,
            target_state=new_state,
            details=details
        )
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the workflow metadata.
        
        Args:
            metadata: New metadata to merge with existing metadata
        """
        self.metadata.update(metadata)
        self.updated_at = datetime.now()
    
    def get_state_duration(self, state: str) -> float:
        """
        Get the total duration spent in a specific state.
        
        Args:
            state: The state to calculate duration for
            
        Returns:
            Duration in seconds
        """
        duration = 0.0
        
        # Find all transitions to and from the state
        entries = []
        exits = []
        
        for transition in self.history:
            if transition.target_state == state:
                entries.append(transition.timestamp)
            elif transition.source_state == state:
                exits.append(transition.timestamp)
        
        # Calculate durations
        for i, entry in enumerate(entries):
            if i < len(exits):
                # Complete transition
                duration += (exits[i] - entry).total_seconds()
            else:
                # Still in this state
                duration += (datetime.now() - entry).total_seconds()
        
        return duration
    
    def get_total_duration(self) -> float:
        """
        Get the total duration of the workflow.
        
        Returns:
            Duration in seconds
        """
        if not self.history:
            return 0.0
        
        start = self.history[0].timestamp
        
        if self.current_state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
            # Use the last transition timestamp for completed workflows
            end = self.history[-1].timestamp
        else:
            # Use current time for active workflows
            end = datetime.now()
        
        return (end - start).total_seconds()
    
    def is_active(self) -> bool:
        """
        Check if the workflow is active.
        
        Returns:
            True if the workflow is active, False otherwise
        """
        return self.current_state not in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED
        ]
    
    def is_completed(self) -> bool:
        """
        Check if the workflow is completed.
        
        Returns:
            True if the workflow is completed, False otherwise
        """
        return self.current_state == WorkflowState.COMPLETED
    
    def is_failed(self) -> bool:
        """
        Check if the workflow has failed.
        
        Returns:
            True if the workflow has failed, False otherwise
        """
        return self.current_state == WorkflowState.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the workflow status to a dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "current_state": self.current_state,
            "metadata": self.metadata,
            "history": [transition.to_dict() for transition in self.history],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active(),
            "total_duration": self.get_total_duration()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStatus':
        """Create a workflow status from a dictionary."""
        status = cls(
            workflow_id=data["workflow_id"],
            initial_state=data["current_state"],
            metadata=data.get("metadata", {})
        )
        
        # Override created_at
        if "created_at" in data:
            status.created_at = datetime.fromisoformat(data["created_at"])
        
        # Override updated_at
        if "updated_at" in data:
            status.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Clear default history and add from data
        status.history = []
        for transition_data in data.get("history", []):
            status.history.append(WorkflowStatusTransition.from_dict(transition_data))
        
        return status


class WorkflowStatusManager:
    """
    Manager for workflow statuses.
    
    This class provides methods for creating, updating, and querying
    workflow statuses, as well as persistence and notification.
    """
    
    def __init__(
        self,
        status_dir: Optional[str] = None,
        communication_manager = None
    ):
        """
        Initialize the workflow status manager.
        
        Args:
            status_dir: Directory for persisting status data
            communication_manager: Communication manager for notifications
        """
        self.status_dir = status_dir or os.path.join(os.getcwd(), ".workflow_status")
        self.communication_manager = communication_manager
        self.statuses = {}
        self.circuit_breaker = get_circuit_breaker("workflow_status")
        
        # Create status directory if it doesn't exist
        if not os.path.exists(self.status_dir):
            os.makedirs(self.status_dir)
        
        # Load persisted statuses
        self._load_statuses()
    
    def _load_statuses(self) -> None:
        """Load workflow statuses from disk."""
        status_file = os.path.join(self.status_dir, "workflow_statuses.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, "r") as f:
                    data = json.load(f)
                
                for workflow_id, status_data in data.items():
                    self.statuses[workflow_id] = WorkflowStatus.from_dict(status_data)
                
                logger.info(f"Loaded {len(self.statuses)} workflow statuses")
            except Exception as e:
                logger.warning(f"Failed to load workflow statuses: {e}")
    
    async def _save_statuses(self) -> None:
        """Save workflow statuses to disk."""
        status_file = os.path.join(self.status_dir, "workflow_statuses.json")
        try:
            data = {
                workflow_id: status.to_dict()
                for workflow_id, status in self.statuses.items()
            }
            
            with open(status_file, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.statuses)} workflow statuses")
        except Exception as e:
            logger.warning(f"Failed to save workflow statuses: {e}")
    
    async def _send_status_update(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        use_circuit_breaker: bool = True
    ) -> None:
        """
        Send a status update notification.
        
        Args:
            workflow_id: ID of the workflow
            status: Current status of the workflow
            use_circuit_breaker: Whether to use circuit breaker protection
        """
        if not self.communication_manager:
            return
        
        try:
            message = {
                "workflow_id": workflow_id,
                "current_state": status.current_state,
                "updated_at": status.updated_at.isoformat(),
                "is_active": status.is_active(),
                "total_duration": status.get_total_duration(),
                "metadata": status.metadata
            }
            
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self.communication_manager.send_message(
                        sender_id="workflow_status_manager",
                        message_type="workflow_status_update",
                        content=message,
                        recipient_id="*",  # Broadcast to all agents
                        priority="normal",
                        use_circuit_breaker=True
                    )
                )
            else:
                await self.communication_manager.send_message(
                    sender_id="workflow_status_manager",
                    message_type="workflow_status_update",
                    content=message,
                    recipient_id="*",  # Broadcast to all agents
                    priority="normal",
                    use_circuit_breaker=False
                )
        except Exception as e:
            logger.warning(f"Failed to send status update for workflow {workflow_id}: {e}")
    
    def create_workflow_status(
        self,
        workflow_id: str,
        initial_state: str = WorkflowState.CREATED,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowStatus:
        """
        Create a new workflow status.
        
        Args:
            workflow_id: ID of the workflow
            initial_state: Initial state of the workflow
            metadata: Additional metadata about the workflow
            
        Returns:
            The created workflow status
        """
        status = WorkflowStatus(
            workflow_id=workflow_id,
            initial_state=initial_state,
            metadata=metadata
        )
        
        self.statuses[workflow_id] = status
        return status
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """
        Get the status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            The workflow status or None if not found
        """
        return self.statuses.get(workflow_id)
    
    async def update_workflow_state(
        self,
        workflow_id: str,
        new_state: str,
        details: Optional[Dict[str, Any]] = None,
        use_circuit_breaker: bool = True
    ) -> Optional[WorkflowStatus]:
        """
        Update the state of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            new_state: New state for the workflow
            details: Additional details about the state change
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            The updated workflow status or None if not found
        """
        status = self.get_workflow_status(workflow_id)
        if not status:
            return None
        
        # Update the state
        status.update_state(new_state, details)
        
        # Save statuses
        await self._save_statuses()
        
        # Send notification
        await self._send_status_update(workflow_id, status, use_circuit_breaker)
        
        return status
    
    async def update_workflow_metadata(
        self,
        workflow_id: str,
        metadata: Dict[str, Any],
        use_circuit_breaker: bool = True
    ) -> Optional[WorkflowStatus]:
        """
        Update the metadata of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            metadata: New metadata to merge with existing metadata
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            The updated workflow status or None if not found
        """
        status = self.get_workflow_status(workflow_id)
        if not status:
            return None
        
        # Update the metadata
        status.update_metadata(metadata)
        
        # Save statuses
        await self._save_statuses()
        
        # Send notification
        await self._send_status_update(workflow_id, status, use_circuit_breaker)
        
        return status
    
    def get_active_workflows(self) -> List[WorkflowStatus]:
        """
        Get all active workflows.
        
        Returns:
            List of active workflow statuses
        """
        return [
            status for status in self.statuses.values()
            if status.is_active()
        ]
    
    def get_completed_workflows(self) -> List[WorkflowStatus]:
        """
        Get all completed workflows.
        
        Returns:
            List of completed workflow statuses
        """
        return [
            status for status in self.statuses.values()
            if status.is_completed()
        ]
    
    def get_failed_workflows(self) -> List[WorkflowStatus]:
        """
        Get all failed workflows.
        
        Returns:
            List of failed workflow statuses
        """
        return [
            status for status in self.statuses.values()
            if status.is_failed()
        ]
    
    def get_workflows_by_state(self, state: str) -> List[WorkflowStatus]:
        """
        Get all workflows in a specific state.
        
        Args:
            state: The state to filter by
            
        Returns:
            List of workflow statuses in the specified state
        """
        return [
            status for status in self.statuses.values()
            if status.current_state == state
        ]
    
    def get_workflows_by_metadata(
        self,
        metadata_key: str,
        metadata_value: Any
    ) -> List[WorkflowStatus]:
        """
        Get all workflows with a specific metadata value.
        
        Args:
            metadata_key: The metadata key to filter by
            metadata_value: The metadata value to filter by
            
        Returns:
            List of workflow statuses with the specified metadata
        """
        return [
            status for status in self.statuses.values()
            if metadata_key in status.metadata and status.metadata[metadata_key] == metadata_value
        ]
    
    def get_workflow_count(self) -> Dict[str, int]:
        """
        Get the count of workflows by state.
        
        Returns:
            Dictionary mapping states to counts
        """
        counts = {}
        for status in self.statuses.values():
            state = status.current_state
            counts[state] = counts.get(state, 0) + 1
        return counts
    
    def clear_completed_workflows(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear completed workflows from memory.
        
        Args:
            older_than_days: Only clear workflows older than this many days
            
        Returns:
            Number of workflows cleared
        """
        to_remove = []
        now = datetime.now()
        
        for workflow_id, status in self.statuses.items():
            if not status.is_active():
                if older_than_days is not None:
                    age_days = (now - status.updated_at).total_seconds() / (24 * 60 * 60)
                    if age_days < older_than_days:
                        continue
                
                to_remove.append(workflow_id)
        
        # Remove workflows
        for workflow_id in to_remove:
            del self.statuses[workflow_id]
        
        return len(to_remove)
    
    async def shutdown(self) -> None:
        """Shutdown the workflow status manager."""
        await self._save_statuses()


def get_workflow_status_manager(
    status_dir: Optional[str] = None,
    communication_manager = None
) -> WorkflowStatusManager:
    """
    Get a WorkflowStatusManager instance.
    
    Args:
        status_dir: Directory for persisting status data
        communication_manager: Communication manager for notifications
        
    Returns:
        WorkflowStatusManager instance
    """
    return WorkflowStatusManager(status_dir, communication_manager)
