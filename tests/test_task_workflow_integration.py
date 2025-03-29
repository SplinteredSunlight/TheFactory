"""
Tests for the TaskWorkflowIntegration class.

This module contains tests for the TaskWorkflowIntegration class,
which integrates Dagger workflows with the task management system.
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.dagger_integration import (
    TaskWorkflowIntegration,
    get_task_workflow_integration,
    WorkflowState
)
from src.task_manager.manager import Task
from src.agent_manager.schemas import AgentExecutionResult


@pytest.fixture
def mock_task_manager():
    """Create a mock task manager."""
    mock = MagicMock()
    
    # Mock task
    task = MagicMock(spec=Task)
    task.id = "task-123"
    task.name = "Test Task"
    task.description = "Test task description"
    task.status = "pending"
    task.metadata = {}
    
    # Mock get_task method
    mock.get_task.return_value = task
    
    return mock


@pytest.fixture
def mock_dagger_adapter():
    """Create a mock Dagger adapter."""
    mock = MagicMock()
    
    # Mock execute method
    mock.execute.return_value = asyncio.Future()
    mock.execute.return_value.set_result(
        AgentExecutionResult(
            success=True,
            error=None,
            result={"message": "Workflow executed successfully"}
        )
    )
    
    return mock


@pytest.fixture
def mock_communication_manager():
    """Create a mock communication manager."""
    mock = MagicMock()
    
    # Mock register_agent method
    mock.register_agent.return_value = asyncio.Future()
    mock.register_agent.return_value.set_result(None)
    
    # Mock send_message method
    mock.send_message.return_value = asyncio.Future()
    mock.send_message.return_value.set_result("message-123")
    
    return mock


@pytest.fixture
def mock_pipeline_converter():
    """Create a mock pipeline converter."""
    mock = MagicMock()
    
    # Mock convert_task_to_pipeline method
    mock.convert_task_to_pipeline.return_value = {
        "task_id": "task-123",
        "task_name": "Test Task",
        "steps": [
            {"name": "step1", "command": "echo 'Hello, World!'"}
        ]
    }
    
    return mock


@pytest.fixture
def mock_workflow_status_manager():
    """Create a mock workflow status manager."""
    mock = MagicMock()
    
    # Mock create_workflow_status method
    mock.create_workflow_status.return_value = MagicMock()
    
    # Mock update_workflow_state method
    mock.update_workflow_state.return_value = asyncio.Future()
    mock.update_workflow_state.return_value.set_result(MagicMock())
    
    return mock


@pytest.fixture
def mock_result_processor():
    """Create a mock result processor."""
    mock = MagicMock()
    
    # Mock store_result method
    mock.store_result.return_value = asyncio.Future()
    mock.store_result.return_value.set_result("result-123")
    
    return mock


@pytest.fixture
def mock_workflow_cache():
    """Create a mock workflow cache."""
    mock = MagicMock()
    
    # Mock get method
    mock.get.return_value = asyncio.Future()
    mock.get.return_value.set_result(None)
    
    # Mock put method
    mock.put.return_value = asyncio.Future()
    mock.put.return_value.set_result(None)
    
    return mock


@pytest.fixture
def integration(
    mock_task_manager,
    mock_dagger_adapter,
    mock_communication_manager,
    mock_pipeline_converter,
    mock_workflow_status_manager,
    mock_result_processor,
    mock_workflow_cache
):
    """Create a TaskWorkflowIntegration instance with mocked dependencies."""
    with patch("src.task_manager.dagger_integration.get_task_manager") as mock_get_task_manager, \
         patch("src.task_manager.dagger_integration.DaggerAdapter") as MockDaggerAdapter, \
         patch("src.task_manager.dagger_integration.get_dagger_communication_manager") as mock_get_communication_manager, \
         patch("src.task_manager.dagger_integration.get_pipeline_converter") as mock_get_pipeline_converter, \
         patch("src.task_manager.dagger_integration.get_workflow_status_manager") as mock_get_workflow_status_manager, \
         patch("src.task_manager.dagger_integration.get_result_processor") as mock_get_result_processor, \
         patch("src.task_manager.dagger_integration.get_workflow_cache_manager") as mock_get_workflow_cache_manager:
        
        # Set up mocks
        mock_get_task_manager.return_value = mock_task_manager
        MockDaggerAdapter.return_value = mock_dagger_adapter
        mock_get_communication_manager.return_value = mock_communication_manager
        mock_get_pipeline_converter.return_value = mock_pipeline_converter
        mock_get_workflow_status_manager.return_value = mock_workflow_status_manager
        mock_get_result_processor.return_value = mock_result_processor
        
        # Mock workflow cache manager
        mock_workflow_cache_manager_instance = MagicMock()
        mock_workflow_cache_manager_instance.get_cache.return_value = mock_workflow_cache
        mock_get_workflow_cache_manager.return_value = mock_workflow_cache_manager_instance
        
        # Create integration
        integration = TaskWorkflowIntegration()
        
        # Initialize integration
        loop = asyncio.get_event_loop()
        loop.run_until_complete(integration.initialize())
        
        yield integration


@pytest.mark.asyncio
async def test_create_workflow_from_task(integration, mock_task_manager):
    """Test creating a workflow from a task."""
    # Call the method
    result = await integration.create_workflow_from_task("task-123")
    
    # Check the result
    assert result["task_id"] == "task-123"
    assert "workflow_id" in result
    assert result["name"] == "Test Task"
    assert result["description"] == "Test task description"
    
    # Check that the task manager was called
    mock_task_manager.update_task.assert_called()
    mock_task_manager.update_task_status.assert_called_with("task-123", "in_progress")


@pytest.mark.asyncio
async def test_execute_task_workflow(integration, mock_task_manager, mock_dagger_adapter):
    """Test executing a workflow for a task."""
    # Call the method
    result = await integration.execute_task_workflow("task-123")
    
    # Check the result
    assert result["success"] is True
    assert result["task_id"] == "task-123"
    assert "workflow_id" in result
    assert result["result"] == {"message": "Workflow executed successfully"}
    
    # Check that the task manager was called
    mock_task_manager.update_task.assert_called()
    mock_task_manager.update_task_status.assert_called_with("task-123", "in_progress")
    
    # Check that the Dagger adapter was called
    mock_dagger_adapter.execute.assert_called()


@pytest.mark.asyncio
async def test_create_container(integration, mock_communication_manager):
    """Test creating a container."""
    # Call the method
    result = await integration.create_container(
        workflow_id="workflow-123",
        container_image="alpine:latest",
        container_name="test-container",
        environment={"VAR1": "value1"},
        volumes=[{"source": "/tmp", "target": "/data"}],
        command=["echo", "Hello, World!"]
    )
    
    # Check the result
    assert result["workflow_id"] == "workflow-123"
    assert result["container_image"] == "alpine:latest"
    assert result["container_name"] == "test-container"
    assert result["environment"] == {"VAR1": "value1"}
    assert result["volumes"] == [{"source": "/tmp", "target": "/data"}]
    assert result["command"] == ["echo", "Hello, World!"]
    assert result["status"] == "created"
    
    # Check that the communication manager was called
    mock_communication_manager.register_container.assert_called()


@pytest.mark.asyncio
async def test_start_container(integration, mock_dagger_adapter):
    """Test starting a container."""
    # Create a container first
    container = await integration.create_container(
        workflow_id="workflow-123",
        container_image="alpine:latest"
    )
    
    # Call the method
    result = await integration.start_container(container["container_id"])
    
    # Check the result
    assert result["status"] == "running"
    assert "started_at" in result
    
    # Check that the Dagger adapter was called
    mock_dagger_adapter.execute.assert_called()


@pytest.mark.asyncio
async def test_stop_container(integration, mock_communication_manager):
    """Test stopping a container."""
    # Create a container first
    container = await integration.create_container(
        workflow_id="workflow-123",
        container_image="alpine:latest"
    )
    
    # Start the container
    await integration.start_container(container["container_id"])
    
    # Call the method
    result = await integration.stop_container(container["container_id"])
    
    # Check the result
    assert result["status"] == "stopped"
    assert "stopped_at" in result
    
    # Check that the communication manager was called
    mock_communication_manager.send_message.assert_called()


@pytest.mark.asyncio
async def test_convert_task_to_pipeline(integration, mock_task_manager, mock_pipeline_converter):
    """Test converting a task to a pipeline."""
    # Call the method
    result = await integration.convert_task_to_pipeline(
        task_id="task-123",
        template_id="template-123"
    )
    
    # Check the result
    assert result["task_id"] == "task-123"
    assert result["task_name"] == "Test Task"
    assert "steps" in result
    
    # Check that the pipeline converter was called
    mock_pipeline_converter.convert_task_to_pipeline.assert_called_with(
        task=mock_task_manager.get_task.return_value,
        template_id="template-123",
        parameters=None,
        skip_cache=False
    )
    
    # Check that the task manager was called
    mock_task_manager.update_task.assert_called()


@pytest.mark.asyncio
async def test_create_custom_pipeline(integration, mock_task_manager, mock_pipeline_converter):
    """Test creating a custom pipeline."""
    # Call the method
    pipeline_definition = {
        "steps": [
            {"name": "step1", "command": "echo 'Hello, World!'"}
        ]
    }
    
    result = await integration.create_custom_pipeline(
        task_id="task-123",
        pipeline_definition=pipeline_definition
    )
    
    # Check the result
    assert result["task_id"] == "task-123"
    assert result["task_name"] == "Test Task"
    assert "steps" in result
    
    # Check that the pipeline converter was called
    mock_pipeline_converter.create_custom_pipeline.assert_called_with(
        task=mock_task_manager.get_task.return_value,
        pipeline_definition=pipeline_definition,
        skip_cache=False
    )
    
    # Check that the task manager was called
    mock_task_manager.update_task.assert_called()


@pytest.mark.asyncio
async def test_get_workflow_status(integration, mock_task_manager):
    """Test getting workflow status."""
    # Set up mock task with workflow metadata
    task = mock_task_manager.get_task.return_value
    task.metadata = {
        "workflow_id": "workflow-123",
        "workflow_status": "running",
        "workflow_type": "containerized_workflow",
        "workflow_created_at": "2023-01-01T00:00:00",
        "workflow_started_at": "2023-01-01T00:01:00"
    }
    
    # Call the method
    result = await integration.get_workflow_status("task-123")
    
    # Check the result
    assert result["task_id"] == "task-123"
    assert result["has_workflow"] is True
    assert result["workflow_id"] == "workflow-123"
    assert result["workflow_status"] == "running"
    assert result["workflow_type"] == "containerized_workflow"
    assert result["workflow_created_at"] == "2023-01-01T00:00:00"
    assert result["workflow_started_at"] == "2023-01-01T00:01:00"


@pytest.mark.asyncio
async def test_shutdown(integration, mock_dagger_adapter, mock_communication_manager):
    """Test shutting down the integration."""
    # Call the method
    await integration.shutdown()
    
    # Check that the communication manager was called
    mock_communication_manager.unregister_agent.assert_called_with(
        agent_id="task_workflow_integration",
        use_circuit_breaker=True
    )
    
    # Check that the Dagger adapter was called
    mock_dagger_adapter.shutdown.assert_called()


def test_get_task_workflow_integration():
    """Test getting a TaskWorkflowIntegration instance."""
    with patch("src.task_manager.dagger_integration.TaskWorkflowIntegration") as MockIntegration, \
         patch("src.task_manager.dagger_integration.asyncio.new_event_loop") as mock_new_event_loop, \
         patch("src.task_manager.dagger_integration.asyncio.set_event_loop") as mock_set_event_loop:
        
        # Set up mocks
        mock_integration = MagicMock()
        MockIntegration.return_value = mock_integration
        
        mock_loop = MagicMock()
        mock_new_event_loop.return_value = mock_loop
        
        # Call the function
        result = get_task_workflow_integration("config.yaml")
        
        # Check the result
        assert result == mock_integration
        
        # Check that the event loop was set up
        mock_new_event_loop.assert_called()
        mock_set_event_loop.assert_called_with(mock_loop)
        mock_loop.run_until_complete.assert_called_with(mock_integration.initialize())
