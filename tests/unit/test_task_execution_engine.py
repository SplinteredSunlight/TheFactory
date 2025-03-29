"""
Tests for the Task Execution Engine.

This module contains tests for the TaskExecutionEngine class and related functionality.
"""

import asyncio
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.task_execution_engine import (
    TaskExecutionEngine,
    TaskExecution,
    TaskExecutionStatus,
    TaskExecutionPriority,
    RetryStrategy,
    get_task_execution_engine,
)
from src.task_manager.manager import Task, TaskStatus


class TestTaskExecution(unittest.TestCase):
    """Tests for the TaskExecution class."""

    def test_init(self):
        """Test initialization of TaskExecution."""
        task_id = "task_123"
        execution_id = "exec_123"
        execution = TaskExecution(task_id=task_id, execution_id=execution_id)
        
        self.assertEqual(execution.task_id, task_id)
        self.assertEqual(execution.execution_id, execution_id)
        self.assertEqual(execution.status, TaskExecutionStatus.PENDING)
        self.assertEqual(execution.priority, TaskExecutionPriority.MEDIUM)
        self.assertEqual(execution.retry_strategy, RetryStrategy.EXPONENTIAL_BACKOFF)
        self.assertEqual(execution.max_retries, 3)
        self.assertEqual(execution.retry_count, 0)
        self.assertIsNone(execution.result)
        self.assertIsNone(execution.error)
        self.assertIsNone(execution.workflow_id)
        self.assertIsNone(execution.container_id)
        self.assertEqual(len(execution.status_history), 1)
        self.assertEqual(execution.status_history[0]["status"], TaskExecutionStatus.PENDING)
    
    def test_update_status(self):
        """Test updating the status of a TaskExecution."""
        execution = TaskExecution(task_id="task_123", execution_id="exec_123")
        
        # Update to SCHEDULED
        execution.update_status(TaskExecutionStatus.SCHEDULED)
        self.assertEqual(execution.status, TaskExecutionStatus.SCHEDULED)
        self.assertIsNotNone(execution.scheduled_at)
        self.assertEqual(len(execution.status_history), 2)
        self.assertEqual(execution.status_history[1]["status"], TaskExecutionStatus.SCHEDULED)
        self.assertEqual(execution.status_history[1]["previous_status"], TaskExecutionStatus.PENDING)
        
        # Update to RUNNING
        execution.update_status(TaskExecutionStatus.RUNNING)
        self.assertEqual(execution.status, TaskExecutionStatus.RUNNING)
        self.assertIsNotNone(execution.started_at)
        self.assertEqual(len(execution.status_history), 3)
        
        # Update to COMPLETED
        execution.update_status(TaskExecutionStatus.COMPLETED)
        self.assertEqual(execution.status, TaskExecutionStatus.COMPLETED)
        self.assertIsNotNone(execution.completed_at)
        self.assertEqual(len(execution.status_history), 4)
    
    def test_to_dict_from_dict(self):
        """Test converting TaskExecution to and from a dictionary."""
        execution = TaskExecution(
            task_id="task_123",
            execution_id="exec_123",
            workflow_type="containerized_workflow",
            priority=TaskExecutionPriority.HIGH,
            workflow_params={"param1": "value1"},
            retry_strategy=RetryStrategy.FIXED_DELAY,
            max_retries=5,
            retry_delay=10,
            timeout=7200,
            dependencies=["exec_456"],
            metadata={"key1": "value1"},
        )
        
        # Update status to add some history
        execution.update_status(TaskExecutionStatus.SCHEDULED)
        execution.update_status(TaskExecutionStatus.RUNNING)
        
        # Add some result data
        execution.workflow_id = "workflow_123"
        execution.container_id = "container_123"
        execution.result = {"output": "test_output"}
        
        # Convert to dictionary
        execution_dict = execution.to_dict()
        
        # Check dictionary values
        self.assertEqual(execution_dict["task_id"], "task_123")
        self.assertEqual(execution_dict["execution_id"], "exec_123")
        self.assertEqual(execution_dict["workflow_type"], "containerized_workflow")
        self.assertEqual(execution_dict["priority"], TaskExecutionPriority.HIGH.value)
        self.assertEqual(execution_dict["workflow_params"], {"param1": "value1"})
        self.assertEqual(execution_dict["retry_strategy"], RetryStrategy.FIXED_DELAY.value)
        self.assertEqual(execution_dict["max_retries"], 5)
        self.assertEqual(execution_dict["retry_delay"], 10)
        self.assertEqual(execution_dict["timeout"], 7200)
        self.assertEqual(execution_dict["dependencies"], ["exec_456"])
        self.assertEqual(execution_dict["metadata"], {"key1": "value1"})
        self.assertEqual(execution_dict["status"], TaskExecutionStatus.RUNNING)
        self.assertEqual(execution_dict["workflow_id"], "workflow_123")
        self.assertEqual(execution_dict["container_id"], "container_123")
        self.assertEqual(execution_dict["result"], {"output": "test_output"})
        self.assertEqual(len(execution_dict["status_history"]), 3)
        
        # Convert back to TaskExecution
        new_execution = TaskExecution.from_dict(execution_dict)
        
        # Check values
        self.assertEqual(new_execution.task_id, "task_123")
        self.assertEqual(new_execution.execution_id, "exec_123")
        self.assertEqual(new_execution.workflow_type, "containerized_workflow")
        self.assertEqual(new_execution.priority, TaskExecutionPriority.HIGH)
        self.assertEqual(new_execution.workflow_params, {"param1": "value1"})
        self.assertEqual(new_execution.retry_strategy, RetryStrategy.FIXED_DELAY)
        self.assertEqual(new_execution.max_retries, 5)
        self.assertEqual(new_execution.retry_delay, 10)
        self.assertEqual(new_execution.timeout, 7200)
        self.assertEqual(new_execution.dependencies, ["exec_456"])
        self.assertEqual(new_execution.metadata, {"key1": "value1"})
        self.assertEqual(new_execution.status, TaskExecutionStatus.RUNNING)
        self.assertEqual(new_execution.workflow_id, "workflow_123")
        self.assertEqual(new_execution.container_id, "container_123")
        self.assertEqual(new_execution.result, {"output": "test_output"})
        self.assertEqual(len(new_execution.status_history), 3)
    
    def test_should_retry(self):
        """Test the should_retry method."""
        # Create execution with default retry strategy
        execution = TaskExecution(task_id="task_123", execution_id="exec_123")
        
        # Should not retry if status is not FAILED or TIMEOUT
        self.assertFalse(execution.should_retry())
        
        # Should retry if status is FAILED and retry count < max_retries
        execution.update_status(TaskExecutionStatus.FAILED)
        self.assertTrue(execution.should_retry())
        
        # Should retry if status is TIMEOUT and retry count < max_retries
        execution.update_status(TaskExecutionStatus.TIMEOUT)
        self.assertTrue(execution.should_retry())
        
        # Should not retry if retry count >= max_retries
        execution.retry_count = 3
        self.assertFalse(execution.should_retry())
        
        # Should not retry if retry strategy is NONE
        execution.retry_count = 0
        execution.retry_strategy = RetryStrategy.NONE
        self.assertFalse(execution.should_retry())
    
    def test_prepare_for_retry(self):
        """Test the prepare_for_retry method."""
        execution = TaskExecution(task_id="task_123", execution_id="exec_123")
        
        # Set status to FAILED
        execution.update_status(TaskExecutionStatus.FAILED)
        
        # Prepare for retry
        execution.prepare_for_retry()
        
        # Check values
        self.assertEqual(execution.retry_count, 1)
        self.assertIsNotNone(execution.next_retry_at)
        self.assertEqual(execution.status, TaskExecutionStatus.RETRYING)
        self.assertEqual(len(execution.status_history), 3)
        self.assertEqual(execution.status_history[2]["status"], TaskExecutionStatus.RETRYING)
    
    def test_is_timed_out(self):
        """Test the is_timed_out method."""
        execution = TaskExecution(task_id="task_123", execution_id="exec_123", timeout=1)
        
        # Should not be timed out if not started
        self.assertFalse(execution.is_timed_out())
        
        # Should not be timed out if status is not RUNNING or PREPARING
        execution.started_at = datetime.now() - timedelta(seconds=2)
        self.assertFalse(execution.is_timed_out())
        
        # Should be timed out if status is RUNNING and elapsed time > timeout
        execution.update_status(TaskExecutionStatus.RUNNING)
        self.assertTrue(execution.is_timed_out())
        
        # Should be timed out if status is PREPARING and elapsed time > timeout
        execution.update_status(TaskExecutionStatus.PREPARING)
        self.assertTrue(execution.is_timed_out())
    
    def test_can_execute(self):
        """Test the can_execute method."""
        execution = TaskExecution(task_id="task_123", execution_id="exec_123")
        
        # Should be executable if status is PENDING
        self.assertTrue(execution.can_execute())
        
        # Should be executable if status is SCHEDULED
        execution.update_status(TaskExecutionStatus.SCHEDULED)
        self.assertTrue(execution.can_execute())
        
        # Should be executable if status is RETRYING
        execution.update_status(TaskExecutionStatus.RETRYING)
        self.assertTrue(execution.can_execute())
        
        # Should not be executable if status is RUNNING
        execution.update_status(TaskExecutionStatus.RUNNING)
        self.assertFalse(execution.can_execute())
        
        # Should not be executable if status is COMPLETED
        execution.update_status(TaskExecutionStatus.COMPLETED)
        self.assertFalse(execution.can_execute())
    
    def test_is_complete(self):
        """Test the is_complete method."""
        execution = TaskExecution(task_id="task_123", execution_id="exec_123")
        
        # Should not be complete if status is PENDING
        self.assertFalse(execution.is_complete())
        
        # Should not be complete if status is RUNNING
        execution.update_status(TaskExecutionStatus.RUNNING)
        self.assertFalse(execution.is_complete())
        
        # Should be complete if status is COMPLETED
        execution.update_status(TaskExecutionStatus.COMPLETED)
        self.assertTrue(execution.is_complete())
        
        # Should be complete if status is FAILED
        execution.update_status(TaskExecutionStatus.FAILED)
        self.assertTrue(execution.is_complete())
        
        # Should be complete if status is CANCELLED
        execution.update_status(TaskExecutionStatus.CANCELLED)
        self.assertTrue(execution.is_complete())


@pytest.mark.asyncio
class TestTaskExecutionEngine:
    """Tests for the TaskExecutionEngine class."""
    
    @pytest.fixture
    async def mock_dependencies(self):
        """Set up mock dependencies for the TaskExecutionEngine."""
        with patch("src.task_manager.task_execution_engine.get_task_manager") as mock_get_task_manager, \
             patch("src.task_manager.task_execution_engine.get_task_workflow_integration") as mock_get_workflow_integration, \
             patch("src.task_manager.task_execution_engine.get_workflow_status_manager") as mock_get_workflow_status_manager, \
             patch("src.task_manager.task_execution_engine.get_result_processor") as mock_get_result_processor, \
             patch("src.task_manager.task_execution_engine.get_workflow_cache") as mock_get_workflow_cache, \
             patch("src.task_manager.task_execution_engine.get_pipeline_converter") as mock_get_pipeline_converter, \
             patch("src.task_manager.task_execution_engine.get_circuit_breaker") as mock_get_circuit_breaker, \
             patch("src.task_manager.task_execution_engine.get_dagger_communication_manager") as mock_get_communication_manager:
            
            # Create mock instances
            mock_task_manager = MagicMock()
            mock_workflow_integration = AsyncMock()
            mock_workflow_status_manager = MagicMock()
            mock_result_processor = AsyncMock()
            mock_workflow_cache = MagicMock()
            mock_pipeline_converter = MagicMock()
            mock_circuit_breaker = MagicMock()
            mock_communication_manager = AsyncMock()
            
            # Configure mocks
            mock_get_task_manager.return_value = mock_task_manager
            mock_get_workflow_integration.return_value = mock_workflow_integration
            mock_get_workflow_status_manager.return_value = mock_workflow_status_manager
            mock_get_result_processor.return_value = mock_result_processor
            mock_get_workflow_cache.return_value = mock_workflow_cache
            mock_get_pipeline_converter.return_value = mock_pipeline_converter
            mock_get_circuit_breaker.return_value = mock_circuit_breaker
            mock_get_communication_manager.return_value = mock_communication_manager
            
            # Configure workflow_integration.initialize to be awaitable
            mock_workflow_integration.initialize = AsyncMock()
            
            # Configure communication_manager.register_agent to be awaitable
            mock_communication_manager.register_agent = AsyncMock()
            
            yield {
                "task_manager": mock_task_manager,
                "workflow_integration": mock_workflow_integration,
                "workflow_status_manager": mock_workflow_status_manager,
                "result_processor": mock_result_processor,
                "workflow_cache": mock_workflow_cache,
                "pipeline_converter": mock_pipeline_converter,
                "circuit_breaker": mock_circuit_breaker,
                "communication_manager": mock_communication_manager,
            }
    
    @pytest.fixture
    async def engine(self, mock_dependencies, tmp_path):
        """Create a TaskExecutionEngine instance with mocked dependencies."""
        # Create a temporary directory for the engine
        data_dir = tmp_path / "executions"
        data_dir.mkdir()
        
        # Create the engine
        engine = TaskExecutionEngine(
            max_concurrent_executions=5,
            scheduler_interval=1,
            data_dir=str(data_dir),
        )
        
        # Initialize the engine
        await engine.initialize()
        
        # Patch the _scheduler_loop method to prevent it from running
        engine._scheduler_loop = AsyncMock()
        engine._scheduler_task = asyncio.create_task(asyncio.sleep(0))
        
        yield engine
        
        # Clean up
        await engine.shutdown()
    
    async def test_initialize(self, mock_dependencies, engine):
        """Test initializing the TaskExecutionEngine."""
        # Check that dependencies were initialized
        mock_dependencies["workflow_integration"].initialize.assert_called_once()
        mock_dependencies["communication_manager"].register_agent.assert_called_once_with(
            agent_id="task_execution_engine",
            capabilities={
                "task_execution": True,
                "task_scheduling": True,
                "dependency_management": True
            },
            use_circuit_breaker=True
        )
        
        # Check that the scheduler task was started
        assert engine._initialized is True
    
    async def test_shutdown(self, mock_dependencies, engine):
        """Test shutting down the TaskExecutionEngine."""
        # Set up mocks
        mock_dependencies["workflow_integration"].shutdown = AsyncMock()
        mock_dependencies["communication_manager"].unregister_agent = AsyncMock()
        
        # Shutdown the engine
        await engine.shutdown()
        
        # Check that dependencies were shut down
        mock_dependencies["workflow_integration"].shutdown.assert_called_once()
        mock_dependencies["communication_manager"].unregister_agent.assert_called_once_with(
            agent_id="task_execution_engine",
            use_circuit_breaker=True
        )
        
        # Check that the scheduler task was cancelled
        assert engine._initialized is False
    
    async def test_schedule_task(self, mock_dependencies, engine):
        """Test scheduling a task for execution."""
        # Set up mock task
        task_id = "task_123"
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        # Schedule the task
        result = await engine.schedule_task(
            task_id=task_id,
            workflow_type="containerized_workflow",
            priority=TaskExecutionPriority.HIGH,
            workflow_params={"param1": "value1"},
            retry_strategy=RetryStrategy.FIXED_DELAY,
            max_retries=5,
            retry_delay=10,
            timeout=7200,
            dependencies=["exec_456"],
            metadata={"key1": "value1"},
        )
        
        # Check that the task was scheduled
        assert result["task_id"] == task_id
        assert result["status"] == TaskExecutionStatus.PENDING
        assert result["priority"] == TaskExecutionPriority.HIGH.value
        
        # Check that the execution was added to the registry
        execution_id = result["execution_id"]
        assert execution_id in engine.executions
        execution = engine.executions[execution_id]
        assert execution.task_id == task_id
        assert execution.workflow_type == "containerized_workflow"
        assert execution.priority == TaskExecutionPriority.HIGH
        assert execution.workflow_params == {"param1": "value1"}
        assert execution.retry_strategy == RetryStrategy.FIXED_DELAY
        assert execution.max_retries == 5
        assert execution.retry_delay == 10
        assert execution.timeout == 7200
        assert execution.dependencies == ["exec_456"]
        assert execution.metadata == {"key1": "value1"}
        
        # Check that the execution was added to the queue
        assert len(engine.execution_queue) == 1
        priority, _, queue_execution_id = engine.execution_queue[0]
        assert queue_execution_id == execution_id
        assert priority == -TaskExecutionPriority.HIGH.value  # Negative for max-heap
    
    async def test_schedule_task_batch(self, mock_dependencies, engine):
        """Test scheduling multiple tasks for execution."""
        # Set up mock tasks
        task_ids = ["task_1", "task_2", "task_3"]
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        # Schedule the tasks
        result = await engine.schedule_task_batch(
            task_ids=task_ids,
            workflow_type="containerized_workflow",
            priority=TaskExecutionPriority.HIGH,
        )
        
        # Check that all tasks were scheduled
        assert len(result["successful"]) == 3
        assert all(r["task_id"] in task_ids for r in result["successful"])
        assert len(result["failed"]) == 0
        
        # Check that all executions were added to the registry
        assert len(engine.executions) == 3
        
        # Check that all executions were added to the queue
        assert len(engine.execution_queue) == 3
    
    async def test_schedule_task_graph(self, mock_dependencies, engine):
        """Test scheduling a graph of tasks for execution."""
        # Set up mock tasks
        task_graph = {
            "task_1": [],
            "task_2": ["task_1"],
            "task_3": ["task_1", "task_2"],
        }
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        # Schedule the task graph
        result = await engine.schedule_task_graph(
            task_graph=task_graph,
            workflow_type="containerized_workflow",
            priority=TaskExecutionPriority.HIGH,
        )
        
        # Check that all tasks were scheduled
        assert len(result["executions"]) == 3
        assert set(result["task_order"]) == {"task_1", "task_2", "task_3"}
        
        # Check that the tasks were scheduled in topological order
        task_order = result["task_order"]
        assert task_order.index("task_1") < task_order.index("task_2")
        assert task_order.index("task_1") < task_order.index("task_3")
        assert task_order.index("task_2") < task_order.index("task_3")
        
        # Check that all executions were added to the registry
        assert len(engine.executions) == 3
        
        # Check that all executions were added to the queue
        assert len(engine.execution_queue) == 3
        
        # Check that dependencies were set correctly
        execution_map = {e["task_id"]: e["execution_id"] for e in result["executions"]}
        task_3_execution = engine.executions[execution_map["task_3"]]
        assert len(task_3_execution.dependencies) == 2
        assert execution_map["task_1"] in task_3_execution.dependencies
        assert execution_map["task_2"] in task_3_execution.dependencies
    
    async def test_cancel_execution(self, mock_dependencies, engine):
        """Test cancelling a task execution."""
        # Schedule a task
        task_id = "task_123"
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        result = await engine.schedule_task(task_id=task_id)
        execution_id = result["execution_id"]
        
        # Cancel the execution
        cancel_result = await engine.cancel_execution(execution_id)
        
        # Check that the execution was cancelled
        assert cancel_result["success"] is True
        assert cancel_result["execution_id"] == execution_id
        
        # Check that the execution status was updated
        execution = engine.executions[execution_id]
        assert execution.status == TaskExecutionStatus.CANCELLED
        
        # Check that the task status was updated
        mock_dependencies["task_manager"].update_task_status.assert_called_with(
            task_id, TaskStatus.CANCELLED
        )
    
    async def test_get_execution(self, mock_dependencies, engine):
        """Test getting information about a task execution."""
        # Schedule a task
        task_id = "task_123"
        mock_task = MagicMock(spec=Task)
        mock_task.to_dict.return_value = {"id": task_id, "name": "Test Task"}
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        result = await engine.schedule_task(task_id=task_id)
        execution_id = result["execution_id"]
        
        # Get the execution
        execution_info = await engine.get_execution(execution_id)
        
        # Check that the execution information was returned
        assert execution_info["task_id"] == task_id
        assert execution_info["execution_id"] == execution_id
        assert execution_info["status"] == TaskExecutionStatus.PENDING
        assert execution_info["task"]["id"] == task_id
        assert execution_info["task"]["name"] == "Test Task"
    
    async def test_list_executions(self, mock_dependencies, engine):
        """Test listing task executions."""
        # Schedule multiple tasks
        task_ids = ["task_1", "task_2", "task_3"]
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        for task_id in task_ids:
            await engine.schedule_task(task_id=task_id)
        
        # List all executions
        result = await engine.list_executions()
        
        # Check that all executions were returned
        assert result["total"] == 3
        assert len(result["executions"]) == 3
        assert all(e["task_id"] in task_ids for e in result["executions"])
        
        # List executions with pagination
        result = await engine.list_executions(limit=2, offset=1)
        
        # Check that pagination works
        assert result["total"] == 3
        assert len(result["executions"]) == 2
        assert result["limit"] == 2
        assert result["offset"] == 1
    
    async def test_get_execution_stats(self, mock_dependencies, engine):
        """Test getting statistics about task executions."""
        # Schedule multiple tasks with different statuses
        mock_task = MagicMock(spec=Task)
        mock_dependencies["task_manager"].get_task.return_value = mock_task
        
        # Schedule 3 tasks
        for i in range(3):
            await engine.schedule_task(task_id=f"task_{i}")
        
        # Update status of one execution to RUNNING
        execution_id = list(engine.executions.keys())[0]
        engine.executions[execution_id].update_status(TaskExecutionStatus.RUNNING)
        engine.running_executions.add(execution_id)
        
        # Update status of another execution to COMPLETED
        execution_id = list(engine.executions.keys())[1]
        engine.executions[execution_id].update_status(TaskExecutionStatus.COMPLETED)
        engine.stats["successful_executions"] += 1
        
        # Get execution stats
        stats = await engine.get_execution_stats()
        
        # Check that stats were returned
        assert stats["total_count"] == 3
        assert stats["successful_executions"] == 1
        assert stats["queue_length"] == 3  # All executions are still in the queue in this test
        assert stats["running_count"] == 1
        assert len(stats["status_counts"]) == 3
        assert stats["status_counts"][TaskExecutionStatus.PENDING] == 1
        assert stats["status_counts"][TaskExecutionStatus.RUNNING] == 1
        assert stats["status_counts"][TaskExecutionStatus.COMPLETED] == 1


@pytest.mark.asyncio
async def test_get_task_execution_engine():
    """Test the get_task_execution_engine function."""
    # Patch the TaskExecutionEngine class
    with patch("src.task_manager.task_execution_engine.TaskExecutionEngine") as MockTaskExecutionEngine, \
         patch("asyncio.get_event_loop"), \
         patch("asyncio.new_event_loop"), \
         patch("asyncio.set_event_loop"):
        
        # Configure the mock
        mock_engine = AsyncMock()
        MockTaskExecutionEngine.return_value = mock_engine
        mock_engine.initialize = AsyncMock()
        
        # Get the engine
        engine1 = get_task_execution_engine()
        
        # Check that the engine was created with default parameters
        MockTaskExecutionEngine.assert_called_once()
        mock_engine.initialize.assert_called_once()
        
        # Get the engine again
        engine2 = get_task_execution_engine()
        
        # Check that the same instance was returned
        assert engine1 is engine2
        assert MockTaskExecutionEngine.call_count == 1
