"""
Task Execution Engine for AI-Orchestration-Platform.

This module provides a comprehensive task execution engine for scheduling,
executing, and managing tasks with dependencies using Dagger workflows.
"""

import asyncio
import logging
import os
import sys
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable
from enum import Enum
import heapq
import time
import traceback

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.manager import get_task_manager, TaskStatus, Task
from src.task_manager.dagger_integration import get_task_workflow_integration, TaskWorkflowIntegration
from src.task_manager.workflow_status import WorkflowState, get_workflow_status_manager
from src.task_manager.result_processor import get_result_processor, ResultProcessor
from src.task_manager.workflow_cache import get_workflow_cache, WorkflowCache
from src.task_manager.pipeline_converter import get_pipeline_converter, PipelineConverter
from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker
from src.orchestrator.dagger_communication import get_dagger_communication_manager, DaggerCommunicationManager

logger = logging.getLogger(__name__)


class TaskExecutionStatus(str, Enum):
    """Enum representing the status of a task execution."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


class TaskExecutionPriority(int, Enum):
    """Enum representing the priority of a task execution."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class RetryStrategy(str, Enum):
    """Enum representing retry strategies for failed tasks."""
    NONE = "none"
    IMMEDIATE = "immediate"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"


class TaskExecution:
    """Class representing a task execution."""
    
    def __init__(
        self,
        task_id: str,
        execution_id: str,
        workflow_type: str = "containerized_workflow",
        priority: Union[TaskExecutionPriority, int] = TaskExecutionPriority.MEDIUM,
        workflow_params: Optional[Dict[str, Any]] = None,
        retry_strategy: Union[RetryStrategy, str] = RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries: int = 3,
        retry_delay: int = 5,  # seconds
        timeout: int = 3600,  # seconds
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a task execution."""
        self.task_id = task_id
        self.execution_id = execution_id
        self.workflow_type = workflow_type
        self.priority = priority if isinstance(priority, TaskExecutionPriority) else TaskExecutionPriority(priority)
        self.workflow_params = workflow_params or {}
        self.retry_strategy = retry_strategy if isinstance(retry_strategy, RetryStrategy) else RetryStrategy(retry_strategy)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        
        self.status = TaskExecutionStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.scheduled_at = None
        self.started_at = None
        self.completed_at = None
        self.next_retry_at = None
        
        self.retry_count = 0
        self.result = None
        self.error = None
        self.workflow_id = None
        self.container_id = None
        
        self.status_history = [
            {
                "status": self.status,
                "timestamp": self.created_at.isoformat(),
                "previous_status": None,
            }
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task execution to a dictionary."""
        return {
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "workflow_type": self.workflow_type,
            "priority": self.priority.value,
            "workflow_params": self.workflow_params,
            "retry_strategy": self.retry_strategy.value,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "retry_count": self.retry_count,
            "result": self.result,
            "error": self.error,
            "workflow_id": self.workflow_id,
            "container_id": self.container_id,
            "status_history": self.status_history,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecution":
        """Create a task execution from a dictionary."""
        execution = cls(
            task_id=data["task_id"],
            execution_id=data["execution_id"],
            workflow_type=data["workflow_type"],
            priority=data["priority"],
            workflow_params=data["workflow_params"],
            retry_strategy=data["retry_strategy"],
            max_retries=data["max_retries"],
            retry_delay=data["retry_delay"],
            timeout=data["timeout"],
            dependencies=data["dependencies"],
            metadata=data["metadata"],
        )
        
        execution.status = TaskExecutionStatus(data["status"])
        execution.created_at = datetime.fromisoformat(data["created_at"])
        execution.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if data.get("scheduled_at"):
            execution.scheduled_at = datetime.fromisoformat(data["scheduled_at"])
        if data.get("started_at"):
            execution.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            execution.completed_at = datetime.fromisoformat(data["completed_at"])
        if data.get("next_retry_at"):
            execution.next_retry_at = datetime.fromisoformat(data["next_retry_at"])
        
        execution.retry_count = data["retry_count"]
        execution.result = data["result"]
        execution.error = data["error"]
        execution.workflow_id = data["workflow_id"]
        execution.container_id = data["container_id"]
        execution.status_history = data["status_history"]
        
        return execution
    
    def update_status(self, status: Union[TaskExecutionStatus, str]) -> None:
        """
        Update the status of the task execution.
        
        Args:
            status: New status
        """
        previous_status = self.status
        self.status = status if isinstance(status, TaskExecutionStatus) else TaskExecutionStatus(status)
        self.updated_at = datetime.now()
        
        # Update timestamps based on status
        if self.status == TaskExecutionStatus.SCHEDULED and not self.scheduled_at:
            self.scheduled_at = self.updated_at
        elif self.status == TaskExecutionStatus.RUNNING and not self.started_at:
            self.started_at = self.updated_at
        elif self.status in (TaskExecutionStatus.COMPLETED, TaskExecutionStatus.FAILED, TaskExecutionStatus.CANCELLED):
            self.completed_at = self.updated_at
        
        # Add to status history
        self.status_history.append({
            "status": self.status,
            "timestamp": self.updated_at.isoformat(),
            "previous_status": previous_status,
        })
    
    def calculate_next_retry_time(self) -> datetime:
        """
        Calculate the next retry time based on the retry strategy.
        
        Returns:
            Next retry time
        """
        now = datetime.now()
        
        if self.retry_strategy == RetryStrategy.NONE:
            return now  # No retry
        
        if self.retry_strategy == RetryStrategy.IMMEDIATE:
            return now
        
        if self.retry_strategy == RetryStrategy.FIXED_DELAY:
            return now + timedelta(seconds=self.retry_delay)
        
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # Exponential backoff with jitter: delay * 2^retry_count + random(0, 1)
            import random
            delay = self.retry_delay * (2 ** self.retry_count) + random.random()
            return now + timedelta(seconds=delay)
        
        if self.retry_strategy == RetryStrategy.FIBONACCI_BACKOFF:
            # Fibonacci backoff: delay * fibonacci(retry_count)
            def fibonacci(n: int) -> int:
                if n <= 0:
                    return 0
                elif n == 1:
                    return 1
                else:
                    a, b = 0, 1
                    for _ in range(2, n + 1):
                        a, b = b, a + b
                    return b
            
            delay = self.retry_delay * fibonacci(self.retry_count + 1)
            return now + timedelta(seconds=delay)
        
        # Default to fixed delay
        return now + timedelta(seconds=self.retry_delay)
    
    def should_retry(self) -> bool:
        """
        Check if the task execution should be retried.
        
        Returns:
            True if the task should be retried, False otherwise
        """
        if self.retry_strategy == RetryStrategy.NONE:
            return False
        
        if self.retry_count >= self.max_retries:
            return False
        
        if self.status not in (TaskExecutionStatus.FAILED, TaskExecutionStatus.TIMEOUT):
            return False
        
        return True
    
    def prepare_for_retry(self) -> None:
        """Prepare the task execution for retry."""
        self.retry_count += 1
        self.next_retry_at = self.calculate_next_retry_time()
        self.update_status(TaskExecutionStatus.RETRYING)
    
    def is_timed_out(self) -> bool:
        """
        Check if the task execution has timed out.
        
        Returns:
            True if the task has timed out, False otherwise
        """
        if not self.started_at or self.status not in (TaskExecutionStatus.RUNNING, TaskExecutionStatus.PREPARING):
            return False
        
        elapsed = (datetime.now() - self.started_at).total_seconds()
        return elapsed > self.timeout
    
    def can_execute(self) -> bool:
        """
        Check if the task execution can be executed.
        
        Returns:
            True if the task can be executed, False otherwise
        """
        return self.status in (TaskExecutionStatus.PENDING, TaskExecutionStatus.SCHEDULED, TaskExecutionStatus.RETRYING)
    
    def is_complete(self) -> bool:
        """
        Check if the task execution is complete.
        
        Returns:
            True if the task is complete, False otherwise
        """
        return self.status in (TaskExecutionStatus.COMPLETED, TaskExecutionStatus.FAILED, TaskExecutionStatus.CANCELLED)


class TaskExecutionEngine:
    """
    Engine for scheduling and executing tasks.
    
    This class provides methods for scheduling, executing, and managing tasks
    with dependencies using Dagger workflows.
    """
    
    def __init__(
        self,
        max_concurrent_executions: int = 10,
        scheduler_interval: int = 5,  # seconds
        data_dir: Optional[str] = None,
        dagger_config_path: Optional[str] = None,
        templates_dir: Optional[str] = None,
    ):
        """
        Initialize the task execution engine.
        
        Args:
            max_concurrent_executions: Maximum number of concurrent task executions
            scheduler_interval: Interval in seconds for the scheduler loop
            data_dir: Directory for storing task execution data
            dagger_config_path: Path to the Dagger configuration file
            templates_dir: Directory containing pipeline templates
        """
        self.max_concurrent_executions = max_concurrent_executions
        self.scheduler_interval = scheduler_interval
        
        # Set up data directory
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "data", "executions")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Get dependencies
        self.task_manager = get_task_manager()
        self.workflow_integration = get_task_workflow_integration(dagger_config_path, templates_dir)
        self.workflow_status_manager = get_workflow_status_manager()
        self.result_processor = get_result_processor()
        self.workflow_cache = get_workflow_cache()
        self.pipeline_converter = get_pipeline_converter(templates_dir)
        
        # Get circuit breaker for task executions
        self.circuit_breaker = get_circuit_breaker("task_executions")
        
        # Get the Dagger communication manager
        self.communication_manager = get_dagger_communication_manager()
        
        # Task execution registry
        self.executions: Dict[str, TaskExecution] = {}
        
        # Priority queue for scheduled executions
        self.execution_queue: List[Tuple[int, datetime, str]] = []  # (priority, scheduled_time, execution_id)
        
        # Set of currently running executions
        self.running_executions: Set[str] = set()
        
        # Dependency graph for executions
        self.dependency_graph: Dict[str, Set[str]] = {}  # execution_id -> set of dependent execution_ids
        
        # Scheduler task
        self._scheduler_task = None
        self._initialized = False
        
        # Execution hooks
        self.pre_execution_hooks: List[Callable[[TaskExecution], None]] = []
        self.post_execution_hooks: List[Callable[[TaskExecution], None]] = []
        
        # Statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "retried_executions": 0,
            "cancelled_executions": 0,
            "timed_out_executions": 0,
        }
    
    async def initialize(self) -> None:
        """Initialize the task execution engine."""
        if not self._initialized:
            # Initialize dependencies
            await self.workflow_integration.initialize()
            
            # Load persisted executions
            await self._load_executions()
            
            # Register with the communication manager
            await self.communication_manager.register_agent(
                agent_id="task_execution_engine",
                capabilities={
                    "task_execution": True,
                    "task_scheduling": True,
                    "dependency_management": True
                },
                use_circuit_breaker=True
            )
            
            # Start the scheduler
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            self._initialized = True
            logger.info("Task Execution Engine initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the task execution engine."""
        if self._initialized:
            # Save executions
            await self._save_executions()
            
            # Cancel the scheduler task
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass
            
            # Unregister from communication manager
            try:
                await self.communication_manager.unregister_agent(
                    agent_id="task_execution_engine",
                    use_circuit_breaker=True
                )
            except Exception as e:
                logger.warning(f"Failed to unregister from communication manager: {e}")
            
            # Shutdown dependencies
            await self.workflow_integration.shutdown()
            
            self._initialized = False
            logger.info("Task Execution Engine shut down successfully")
    
    async def _load_executions(self) -> None:
        """Load executions from disk."""
        executions_dir = os.path.join(self.data_dir, "executions")
        if not os.path.exists(executions_dir):
            os.makedirs(executions_dir, exist_ok=True)
            return
        
        for filename in os.listdir(executions_dir):
            if filename.endswith(".json"):
                execution_id = filename[:-5]  # Remove .json extension
                execution_path = os.path.join(executions_dir, filename)
                try:
                    with open(execution_path, "r") as f:
                        execution_data = json.load(f)
                    
                    execution = TaskExecution.from_dict(execution_data)
                    self.executions[execution_id] = execution
                    
                    # Add to queue if not complete
                    if not execution.is_complete():
                        if execution.status == TaskExecutionStatus.RUNNING:
                            # Add to running executions
                            self.running_executions.add(execution_id)
                        elif execution.status == TaskExecutionStatus.RETRYING:
                            # Add to queue with next retry time
                            heapq.heappush(
                                self.execution_queue,
                                (-execution.priority.value, execution.next_retry_at, execution_id)
                            )
                        else:
                            # Add to queue with current time
                            heapq.heappush(
                                self.execution_queue,
                                (-execution.priority.value, datetime.now(), execution_id)
                            )
                    
                    # Update dependency graph
                    for dep_id in execution.dependencies:
                        if dep_id not in self.dependency_graph:
                            self.dependency_graph[dep_id] = set()
                        self.dependency_graph[dep_id].add(execution_id)
                    
                    # Update statistics
                    self.stats["total_executions"] += 1
                    if execution.status == TaskExecutionStatus.COMPLETED:
                        self.stats["successful_executions"] += 1
                    elif execution.status == TaskExecutionStatus.FAILED:
                        self.stats["failed_executions"] += 1
                    elif execution.status == TaskExecutionStatus.CANCELLED:
                        self.stats["cancelled_executions"] += 1
                    elif execution.status == TaskExecutionStatus.TIMEOUT:
                        self.stats["timed_out_executions"] += 1
                    
                    if execution.retry_count > 0:
                        self.stats["retried_executions"] += 1
                except Exception as e:
                    logger.error(f"Error loading execution {execution_id}: {e}")
        
        logger.info(f"Loaded {len(self.executions)} executions")
    
    async def _save_executions(self) -> None:
        """Save executions to disk."""
        executions_dir = os.path.join(self.data_dir, "executions")
        os.makedirs(executions_dir, exist_ok=True)
        
        for execution_id, execution in self.executions.items():
            execution_path = os.path.join(executions_dir, f"{execution_id}.json")
            try:
                with open(execution_path, "w") as f:
                    json.dump(execution.to_dict(), f, indent=2)
            except Exception as e:
                logger.error(f"Error saving execution {execution_id}: {e}")
    
    async def _save_execution(self, execution_id: str) -> None:
        """
        Save a single execution to disk.
        
        Args:
            execution_id: ID of the execution to save
        """
        if execution_id not in self.executions:
            return
        
        execution = self.executions[execution_id]
        execution_path = os.path.join(self.data_dir, "executions", f"{execution_id}.json")
        
        try:
            os.makedirs(os.path.dirname(execution_path), exist_ok=True)
            with open(execution_path, "w") as f:
                json.dump(execution.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving execution {execution_id}: {e}")
    
    async def _scheduler_loop(self) -> None:
        """Background task for scheduling and executing tasks."""
        while True:
            try:
                # Check for timed out executions
                timed_out = []
                for execution_id in self.running_executions:
                    execution = self.executions.get(execution_id)
                    if execution and execution.is_timed_out():
                        timed_out.append(execution_id)
                
                # Handle timed out executions
                for execution_id in timed_out:
                    await self._handle_timeout(execution_id)
                
                # Check if we can execute more tasks
                if len(self.running_executions) < self.max_concurrent_executions:
                    # Get the next execution from the queue
                    while self.execution_queue and len(self.running_executions) < self.max_concurrent_executions:
                        # Get the highest priority execution that is ready to run
                        now = datetime.now()
                        if not self.execution_queue:
                            break
                        
                        priority, scheduled_time, execution_id = self.execution_queue[0]
                        
                        # Check if it's time to execute
                        if scheduled_time > now:
                            # Not yet time to execute
                            break
                        
                        # Remove from queue
                        heapq.heappop(self.execution_queue)
                        
                        # Check if execution exists and can be executed
                        execution = self.executions.get(execution_id)
                        if not execution or not execution.can_execute():
                            continue
                        
                        # Check if dependencies are satisfied
                        dependencies_satisfied = True
                        for dep_id in execution.dependencies:
                            dep_execution = self.executions.get(dep_id)
                            if not dep_execution or dep_execution.status != TaskExecutionStatus.COMPLETED:
                                dependencies_satisfied = False
                                break
                        
                        if not dependencies_satisfied:
                            # Reschedule for later
                            heapq.heappush(
                                self.execution_queue,
                                (priority, now + timedelta(seconds=self.scheduler_interval), execution_id)
                            )
                            continue
                        
                        # Execute the task
                        asyncio.create_task(self._execute_task(execution_id))
                
                # Wait for the next scheduler interval
                await asyncio.sleep(self.scheduler_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(self.scheduler_interval)
    
    async def _execute_task(self, execution_id: str) -> None:
        """
        Execute a task.
        
        Args:
            execution_id: ID of the execution to run
        """
        if execution_id not in self.executions:
            logger.warning(f"Execution {execution_id} not found")
            return
        
        execution = self.executions[execution_id]
        
        # Add to running executions
        self.running_executions.add(execution_id)
        
        # Update status
        execution.update_status(TaskExecutionStatus.PREPARING)
        await self._save_execution(execution_id)
        
        # Run pre-execution hooks
        for hook in self.pre_execution_hooks:
            try:
                hook(execution)
            except Exception as e:
                logger.error(f"Error in pre-execution hook: {e}")
        
        try:
            # Get the task
            task = self.task_manager.get_task(execution.task_id)
            if not task:
                raise ValueError(f"Task not found: {execution.task_id}")
            
            # Update task status
            self.task_manager.update_task_status(execution.task_id, TaskStatus.IN_PROGRESS)
            
            # Create workflow if needed
            if not execution.workflow_id:
                workflow_info = await self.workflow_integration.create_workflow_from_task(
                    task_id=execution.task_id,
                    workflow_name=f"Execution {execution.execution_id}",
                    custom_inputs=execution.workflow_params.get("inputs"),
                )
                execution.workflow_id = workflow_info["workflow_id"]
                execution.metadata["workflow_info"] = workflow_info
                await self._save_execution(execution_id)
            
            # Update status
            execution.update_status(TaskExecutionStatus.RUNNING)
            await self._save_execution(execution_id)
            
            # Execute the workflow
            result = await self.workflow_integration.execute_task_workflow(
                task_id=execution.task_id,
                workflow_type=execution.workflow_type,
                workflow_params={
                    **execution.workflow_params,
                    "execution_id": execution.execution_id,
                },
                skip_cache=execution.metadata.get("skip_cache", False),
            )
            
            # Process the result
            processed_result = await self.result_processor.process_result(
                task_id=execution.task_id,
                workflow_id=execution.workflow_id,
                result=result,
            )
            
            # Update execution with result
            if result.get("success", False):
                execution.result = processed_result
                execution.update_status(TaskExecutionStatus.COMPLETED)
                self.stats["successful_executions"] += 1
            else:
                execution.error = result.get("error")
                execution.update_status(TaskExecutionStatus.FAILED)
                self.stats["failed_executions"] += 1
                
                # Check if we should retry
                if execution.should_retry():
                    execution.prepare_for_retry()
                    
                    # Add to queue with next retry time
                    heapq.heappush(
                        self.execution_queue,
                        (-execution.priority.value, execution.next_retry_at, execution_id)
                    )
                    
                    self.stats["retried_executions"] += 1
            
            # Update task status
            if execution.status == TaskExecutionStatus.COMPLETED:
                self.task_manager.update_task(
                    task_id=execution.task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100.0,
                    result=processed_result,
                )
            elif execution.status == TaskExecutionStatus.FAILED and not execution.should_retry():
                self.task_manager.update_task(
                    task_id=execution.task_id,
                    status=TaskStatus.FAILED,
                    error=execution.error,
                )
        except Exception as e:
            logger.error(f"Error executing task {execution.task_id}: {e}")
            logger.error(traceback.format_exc())
            
            # Update execution with error
            execution.error = str(e)
            execution.update_status(TaskExecutionStatus.FAILED)
            self.stats["failed_executions"] += 1
            
            # Check if we should retry
            if execution.should_retry():
                execution.prepare_for_retry()
                
                # Add to queue with next retry time
                heapq.heappush(
                    self.execution_queue,
                    (-execution.priority.value, execution.next_retry_at, execution_id)
                )
                
                self.stats["retried_executions"] += 1
            else:
                # Update task status
                self.task_manager.update_task(
                    task_id=execution.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                )
        finally:
            # Remove from running executions
            self.running_executions.discard(execution_id)
            
            # Run post-execution hooks
            for hook in self.post_execution_hooks:
                try:
                    hook(execution)
                except Exception as e:
                    logger.error(f"Error in post-execution hook: {e}")
            
            # Save execution
            await self._save_execution(execution_id)
            
            # Check if there are dependent executions that can now be executed
            await self._check_dependent_executions(execution_id)
    
    async def _handle_timeout(self, execution_id: str) -> None:
        """
        Handle a timed out execution.
        
        Args:
            execution_id: ID of the execution that timed out
        """
        if execution_id not in self.executions:
            return
        
        execution = self.executions[execution_id]
        
        # Update status
        execution.update_status(TaskExecutionStatus.TIMEOUT)
        self.stats["timed_out_executions"] += 1
        
        # Remove from running executions
        self.running_executions.discard(execution_id)
        
        # Check if we should retry
        if execution.should_retry():
            execution.prepare_for_retry()
            
            # Add to queue with next retry time
            heapq.heappush(
                self.execution_queue,
                (-execution.priority.value, execution.next_retry_at, execution_id)
            )
            
            self.stats["retried_executions"] += 1
        else:
            # Update task status
            self.task_manager.update_task(
                task_id=execution.task_id,
                status=TaskStatus.FAILED,
                error="Task execution timed out",
            )
        
        # Save execution
        await self._save_execution(execution_id)
    
    async def _check_dependent_executions(self, execution_id: str) -> None:
        """
        Check if there are dependent executions that can now be executed.
        
        Args:
            execution_id: ID of the execution that completed
        """
        # Check if there are dependent executions
        if execution_id not in self.dependency_graph:
            return
        
        # Get the execution
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        # Only check dependents if the execution completed successfully
        if execution.status != TaskExecutionStatus.COMPLETED:
            return
        
        # Check each dependent execution
        for dependent_id in self.dependency_graph.get(execution_id, set()):
            dependent = self.executions.get(dependent_id)
            if not dependent or not dependent.can_execute():
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = True
            for dep_id in dependent.dependencies:
                dep_execution = self.executions.get(dep_id)
                if not dep_execution or dep_execution.status != TaskExecutionStatus.COMPLETED:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                # Add to queue with current time and priority
                heapq.heappush(
                    self.execution_queue,
                    (-dependent.priority.value, datetime.now(), dependent_id)
                )
    
    async def schedule_task(
        self,
        task_id: str,
        workflow_type: str = "containerized_workflow",
        priority: Union[TaskExecutionPriority, int] = TaskExecutionPriority.MEDIUM,
        workflow_params: Optional[Dict[str, Any]] = None,
        retry_strategy: Union[RetryStrategy, str] = RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries: int = 3,
        retry_delay: int = 5,
        timeout: int = 3600,
        dependencies: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a task for execution.
        
        Args:
            task_id: ID of the task to execute
            workflow_type: Type of workflow to execute
            priority: Priority of the execution
            workflow_params: Parameters for the workflow
            retry_strategy: Strategy for retrying failed executions
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            timeout: Timeout for the execution in seconds
            dependencies: List of execution IDs that must complete before this execution
            scheduled_time: Time to schedule the execution for
            metadata: Additional metadata for the execution
            
        Returns:
            Dictionary with execution information
        """
        # Check if the task exists
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        # Create execution
        execution = TaskExecution(
            task_id=task_id,
            execution_id=execution_id,
            workflow_type=workflow_type,
            priority=priority,
            workflow_params=workflow_params,
            retry_strategy=retry_strategy,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        # Add to registry
        self.executions[execution_id] = execution
        
        # Update dependency graph
        for dep_id in execution.dependencies:
            if dep_id not in self.dependency_graph:
                self.dependency_graph[dep_id] = set()
            self.dependency_graph[dep_id].add(execution_id)
        
        # Update status
        if scheduled_time and scheduled_time > datetime.now():
            execution.update_status(TaskExecutionStatus.SCHEDULED)
            execution.scheduled_at = scheduled_time
        else:
            scheduled_time = datetime.now()
            execution.update_status(TaskExecutionStatus.PENDING)
        
        # Add to queue
        heapq.heappush(
            self.execution_queue,
            (-execution.priority.value, scheduled_time, execution_id)
        )
        
        # Update statistics
        self.stats["total_executions"] += 1
        
        # Save execution
        await self._save_execution(execution_id)
        
        return {
            "execution_id": execution_id,
            "task_id": task_id,
            "status": execution.status,
            "scheduled_time": scheduled_time.isoformat(),
            "priority": execution.priority.value,
        }
    
    async def schedule_task_batch(
        self,
        task_ids: List[str],
        workflow_type: str = "containerized_workflow",
        priority: Union[TaskExecutionPriority, int] = TaskExecutionPriority.MEDIUM,
        workflow_params: Optional[Dict[str, Any]] = None,
        retry_strategy: Union[RetryStrategy, str] = RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries: int = 3,
        retry_delay: int = 5,
        timeout: int = 3600,
        dependencies: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Schedule multiple tasks for execution.
        
        Args:
            task_ids: List of task IDs to execute
            workflow_type: Type of workflow to execute
            priority: Priority of the executions
            workflow_params: Parameters for the workflows
            retry_strategy: Strategy for retrying failed executions
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            timeout: Timeout for the executions in seconds
            dependencies: List of execution IDs that must complete before these executions
            scheduled_time: Time to schedule the executions for
            metadata: Additional metadata for the executions
            
        Returns:
            Dictionary with execution information for each task
        """
        results = {
            "successful": [],
            "failed": []
        }
        
        for task_id in task_ids:
            try:
                result = await self.schedule_task(
                    task_id=task_id,
                    workflow_type=workflow_type,
                    priority=priority,
                    workflow_params=workflow_params,
                    retry_strategy=retry_strategy,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    timeout=timeout,
                    dependencies=dependencies,
                    scheduled_time=scheduled_time,
                    metadata=metadata,
                )
                results["successful"].append(result)
            except Exception as e:
                results["failed"].append({
                    "task_id": task_id,
                    "error": str(e)
                })
        
        return results
    
    async def schedule_task_graph(
        self,
        task_graph: Dict[str, List[str]],
        workflow_type: str = "containerized_workflow",
        priority: Union[TaskExecutionPriority, int] = TaskExecutionPriority.MEDIUM,
        workflow_params: Optional[Dict[str, Dict[str, Any]]] = None,
        retry_strategy: Union[RetryStrategy, str] = RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries: int = 3,
        retry_delay: int = 5,
        timeout: int = 3600,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a graph of tasks for execution.
        
        Args:
            task_graph: Dictionary mapping task IDs to lists of dependent task IDs
            workflow_type: Type of workflow to execute
            priority: Priority of the executions
            workflow_params: Parameters for the workflows, keyed by task ID
            retry_strategy: Strategy for retrying failed executions
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            timeout: Timeout for the executions in seconds
            scheduled_time: Time to schedule the executions for
            metadata: Additional metadata for the executions, keyed by task ID
            
        Returns:
            Dictionary with execution information for each task
        """
        # Validate the task graph
        for task_id, dependencies in task_graph.items():
            task = self.task_manager.get_task(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            
            for dep_id in dependencies:
                if dep_id not in task_graph:
                    raise ValueError(f"Dependency task not in graph: {dep_id}")
        
        # Topologically sort the task graph
        sorted_tasks = self._topological_sort(task_graph)
        
        # Schedule tasks in topological order
        execution_map = {}  # task_id -> execution_id
        results = {
            "executions": [],
            "task_order": sorted_tasks
        }
        
        for task_id in sorted_tasks:
            # Get dependencies
            task_deps = task_graph.get(task_id, [])
            execution_deps = [execution_map[dep_id] for dep_id in task_deps if dep_id in execution_map]
            
            # Get task-specific parameters
            task_params = workflow_params.get(task_id, {}) if workflow_params else {}
            task_metadata = metadata.get(task_id, {}) if metadata else {}
            
            # Schedule the task
            result = await self.schedule_task(
                task_id=task_id,
                workflow_type=workflow_type,
                priority=priority,
                workflow_params=task_params,
                retry_strategy=retry_strategy,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                dependencies=execution_deps,
                scheduled_time=scheduled_time,
                metadata=task_metadata,
            )
            
            # Add to results
            results["executions"].append(result)
            execution_map[task_id] = result["execution_id"]
        
        return results
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Topologically sort a directed acyclic graph.
        
        Args:
            graph: Dictionary mapping nodes to lists of dependent nodes
            
        Returns:
            List of nodes in topological order
        """
        # Create a reversed graph (dependencies -> node)
        reversed_graph = {}
        for node, deps in graph.items():
            if node not in reversed_graph:
                reversed_graph[node] = []
            
            for dep in deps:
                if dep not in reversed_graph:
                    reversed_graph[dep] = []
                reversed_graph[dep].append(node)
        
        # Find nodes with no dependencies
        no_deps = [node for node, deps in graph.items() if not deps]
        
        # Topological sort
        sorted_nodes = []
        while no_deps:
            node = no_deps.pop(0)
            sorted_nodes.append(node)
            
            # Remove node from graph
            for dependent in reversed_graph.get(node, []):
                graph[dependent].remove(node)
                if not graph[dependent]:
                    no_deps.append(dependent)
        
        # Check for cycles
        if any(deps for deps in graph.values()):
            raise ValueError("Graph contains cycles")
        
        return sorted_nodes
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Cancel a task execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            Dictionary with cancellation result
        """
        # Check if execution exists
        if execution_id not in self.executions:
            raise ValueError(f"Execution not found: {execution_id}")
        
        execution = self.executions[execution_id]
        
        # Check if execution can be cancelled
        if execution.is_complete():
            return {
                "execution_id": execution_id,
                "success": False,
                "message": f"Execution already completed with status: {execution.status}"
            }
        
        # Cancel the execution
        if execution.status == TaskExecutionStatus.RUNNING:
            # Remove from running executions
            self.running_executions.discard(execution_id)
            
            # Cancel the workflow if it has one
            if execution.workflow_id:
                try:
                    # Get workflow status
                    workflow_status = await self.workflow_integration.get_workflow_status(execution.task_id)
                    
                    # Cancel containers if any
                    if workflow_status.get("container_id"):
                        await self.workflow_integration.stop_container(
                            container_id=workflow_status["container_id"],
                            use_circuit_breaker=True
                        )
                except Exception as e:
                    logger.warning(f"Error cancelling workflow: {e}")
        elif execution.status in (TaskExecutionStatus.PENDING, TaskExecutionStatus.SCHEDULED, TaskExecutionStatus.RETRYING):
            # Remove from queue
            self.execution_queue = [
                (p, t, e) for p, t, e in self.execution_queue if e != execution_id
            ]
            heapq.heapify(self.execution_queue)
        
        # Update status
        execution.update_status(TaskExecutionStatus.CANCELLED)
        self.stats["cancelled_executions"] += 1
        
        # Update task status
        self.task_manager.update_task_status(execution.task_id, TaskStatus.CANCELLED)
        
        # Save execution
        await self._save_execution(execution_id)
        
        return {
            "execution_id": execution_id,
            "success": True,
            "message": "Execution cancelled successfully"
        }
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a task execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Dictionary with execution information or None if not found
        """
        # Check if execution exists
        if execution_id not in self.executions:
            return None
        
        execution = self.executions[execution_id]
        
        # Get task information
        task = self.task_manager.get_task(execution.task_id)
        task_info = task.to_dict() if task else {"id": execution.task_id, "not_found": True}
        
        # Get workflow status if available
        workflow_status = None
        if execution.workflow_id:
            try:
                workflow_status = await self.workflow_integration.get_workflow_status(execution.task_id)
            except Exception as e:
                logger.warning(f"Error getting workflow status: {e}")
        
        # Return execution information
        return {
            **execution.to_dict(),
            "task": task_info,
            "workflow_status": workflow_status
        }
    
    async def list_executions(
        self,
        status: Optional[Union[TaskExecutionStatus, str]] = None,
        task_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List task executions.
        
        Args:
            status: Filter by execution status
            task_id: Filter by task ID
            limit: Maximum number of executions to return
            offset: Number of executions to skip
            
        Returns:
            Dictionary with execution information
        """
        # Filter executions
        filtered_executions = []
        for execution_id, execution in self.executions.items():
            # Filter by status
            if status:
                status_value = status.value if isinstance(status, TaskExecutionStatus) else status
                if execution.status != status_value:
                    continue
            
            # Filter by task ID
            if task_id and execution.task_id != task_id:
                continue
            
            filtered_executions.append(execution)
        
        # Sort by creation time (newest first)
        filtered_executions.sort(key=lambda e: e.created_at, reverse=True)
        
        # Apply pagination
        paginated_executions = filtered_executions[offset:offset + limit]
        
        # Convert to dictionaries
        execution_dicts = [execution.to_dict() for execution in paginated_executions]
        
        return {
            "executions": execution_dicts,
            "total": len(filtered_executions),
            "limit": limit,
            "offset": offset
        }
    
    async def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get statistics about task executions.
        
        Returns:
            Dictionary with execution statistics
        """
        # Count executions by status
        status_counts = {}
        for execution in self.executions.values():
            status = execution.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Get queue length
        queue_length = len(self.execution_queue)
        
        # Get running count
        running_count = len(self.running_executions)
        
        return {
            **self.stats,
            "status_counts": status_counts,
            "queue_length": queue_length,
            "running_count": running_count,
            "total_count": len(self.executions)
        }
    
    def add_pre_execution_hook(self, hook: Callable[[TaskExecution], None]) -> None:
        """
        Add a hook to run before executing a task.
        
        Args:
            hook: Function to call with the task execution
        """
        self.pre_execution_hooks.append(hook)
    
    def add_post_execution_hook(self, hook: Callable[[TaskExecution], None]) -> None:
        """
        Add a hook to run after executing a task.
        
        Args:
            hook: Function to call with the task execution
        """
        self.post_execution_hooks.append(hook)


# Singleton instance
_task_execution_engine_instance = None


def get_task_execution_engine(
    max_concurrent_executions: int = 10,
    scheduler_interval: int = 5,
    data_dir: Optional[str] = None,
    dagger_config_path: Optional[str] = None,
    templates_dir: Optional[str] = None,
) -> TaskExecutionEngine:
    """
    Get the singleton instance of the task execution engine.
    
    Args:
        max_concurrent_executions: Maximum number of concurrent task executions
        scheduler_interval: Interval in seconds for the scheduler loop
        data_dir: Directory for storing task execution data
        dagger_config_path: Path to the Dagger configuration file
        templates_dir: Directory containing pipeline templates
        
    Returns:
        TaskExecutionEngine instance
    """
    global _task_execution_engine_instance
    if _task_execution_engine_instance is None:
        _task_execution_engine_instance = TaskExecutionEngine(
            max_concurrent_executions=max_concurrent_executions,
            scheduler_interval=scheduler_interval,
            data_dir=data_dir,
            dagger_config_path=dagger_config_path,
            templates_dir=templates_dir,
        )
        
        # Initialize the engine
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(_task_execution_engine_instance.initialize())
        except RuntimeError:
            # Create and run a new event loop if the current one is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_task_execution_engine_instance.initialize())
    
    return _task_execution_engine_instance
