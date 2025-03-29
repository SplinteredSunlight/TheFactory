"""
Unit tests for the DaggerAdapter.
"""
import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult


@pytest.mark.asyncio
async def test_initialize_creates_workflow_dir(temp_workflow_dir):
    """Test that initialize creates the workflow directory if it doesn't exist."""
    # Delete the temp directory to test that it gets created
    os.rmdir(temp_workflow_dir)
    
    config = DaggerAdapterConfig(
        workflow_directory=temp_workflow_dir
    )
    
    adapter = DaggerAdapter(config)
    
    with patch('src.agent_manager.dagger_adapter.Engine', return_value=MagicMock()):
        result = await adapter.initialize()
        
    assert result is True
    assert os.path.exists(temp_workflow_dir)


@pytest.mark.asyncio
async def test_initialize_handles_exception():
    """Test that initialize handles exceptions and returns False."""
    config = DaggerAdapterConfig()
    adapter = DaggerAdapter(config)
    
    with patch('src.agent_manager.dagger_adapter.Engine', side_effect=Exception("Test error")):
        result = await adapter.initialize()
        
    assert result is False


@pytest.mark.asyncio
async def test_get_capabilities(dagger_adapter):
    """Test that get_capabilities returns the correct capabilities."""
    capabilities = await dagger_adapter.get_capabilities()
    
    assert len(capabilities) == 2
    assert capabilities[0].name == "containerized_workflow"
    assert capabilities[1].name == "dagger_pipeline"
    
    # Check that parameters are defined for each capability
    assert "container_image" in capabilities[0].parameters
    assert "workflow_definition" in capabilities[0].parameters
    assert "pipeline_definition" in capabilities[1].parameters


@pytest.mark.asyncio
async def test_get_status(dagger_adapter):
    """Test that get_status returns the correct status."""
    # Add some active workflows
    dagger_adapter._active_workflows = {
        "workflow1": {"status": "running"},
        "workflow2": {"status": "running"}
    }
    
    status = await dagger_adapter.get_status()
    
    assert status.adapter_id == dagger_adapter.id
    assert status.is_ready is True
    assert status.current_load == 2
    assert status.max_load == dagger_adapter.config.max_concurrent_executions
    assert status.status == "running"
    assert "active_workflows" in status.details
    assert status.details["active_workflows"] == 2


@pytest.mark.asyncio
async def test_get_status_when_busy(dagger_adapter):
    """Test that get_status returns not ready when at max capacity."""
    # Fill the active workflows to max capacity
    max_workflows = dagger_adapter.config.max_concurrent_executions
    dagger_adapter._active_workflows = {
        f"workflow{i}": {"status": "running"} for i in range(max_workflows)
    }
    
    status = await dagger_adapter.get_status()
    
    assert status.is_ready is False
    assert status.status == "busy"


@pytest.mark.asyncio
async def test_execute_unsupported_workflow_type(dagger_adapter):
    """Test that execute returns an error for unsupported workflow types."""
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="unsupported_type",
        parameters={}
    )
    
    result = await dagger_adapter.execute(config)
    
    assert result.success is False
    assert "Unsupported workflow type" in result.error


@pytest.mark.asyncio
async def test_execute_containerized_workflow(dagger_adapter, execution_config, mock_dagger_connection):
    """Test executing a containerized workflow."""
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        result = await dagger_adapter.execute(execution_config)
    
    assert result.success is True
    assert result.error is None
    assert "stdout" in result.result


@pytest.mark.asyncio
async def test_execute_missing_container_image(dagger_adapter, execution_config):
    """Test that execute validates required parameters."""
    # Remove the container_image parameter
    execution_config.parameters.pop("container_image")
    
    with patch('dagger.Connection', return_value=AsyncMock()):
        result = await dagger_adapter.execute(execution_config)
    
    assert result.success is False
    assert "Container image is required" in result.error


@pytest.mark.asyncio
async def test_execute_dagger_pipeline(dagger_adapter, pipeline_execution_config, mock_dagger_connection):
    """Test executing a Dagger pipeline."""
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        result = await dagger_adapter.execute(pipeline_execution_config)
    
    assert result.success is True
    assert result.error is None
    assert "result" in result.result
    assert "inputs" in result.result


@pytest.mark.asyncio
async def test_execute_missing_pipeline_definition(dagger_adapter, pipeline_execution_config):
    """Test that execute validates required pipeline parameters."""
    # Remove the pipeline_definition parameter
    pipeline_execution_config.parameters.pop("pipeline_definition")
    
    with patch('dagger.Connection', return_value=AsyncMock()):
        result = await dagger_adapter.execute(pipeline_execution_config)
    
    assert result.success is False
    assert "Pipeline definition is required" in result.error


@pytest.mark.asyncio
async def test_execution_semaphore(dagger_adapter, execution_config, mock_dagger_connection):
    """Test that the execution semaphore limits concurrent executions."""
    # Setup to track execution order
    execution_order = []
    
    async def delayed_execution(delay, index):
        await asyncio.sleep(delay)
        execution_order.append(index)
        return AgentExecutionResult(success=True, result={"index": index})
    
    # Mock the _execute_containerized_workflow method
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        with patch.object(dagger_adapter, '_execute_containerized_workflow') as mock_execute:
            # Set up mock to delay execution
            mock_execute.side_effect = [
                delayed_execution(0.3, 1),  # Task 1: Delay 0.3s
                delayed_execution(0.1, 2),  # Task 2: Delay 0.1s
                delayed_execution(0.2, 3),  # Task 3: Delay 0.2s
                delayed_execution(0.1, 4),  # Task 4: Delay 0.1s
            ]
            
            # Execute multiple tasks concurrently
            tasks = [
                dagger_adapter.execute(execution_config),
                dagger_adapter.execute(execution_config),
                dagger_adapter.execute(execution_config),
                dagger_adapter.execute(execution_config),
            ]
            
            results = await asyncio.gather(*tasks)
    
    # Check that all executions were successful
    assert all(result.success for result in results)
    
    # With max_concurrent_executions=3, task 4 should be executed after any of tasks 1-3 completes
    # The actual order depends on which task completes first
    # But we know task 2 should complete before task 1 and task 3
    assert 2 in execution_order[:3]  # Task 2 should be in the first 3 tasks to complete


@pytest.mark.asyncio
async def test_shutdown(dagger_adapter):
    """Test that shutdown cleans up resources."""
    # Add some active workflows
    dagger_adapter._active_workflows = {
        "workflow1": {"status": "running"},
        "workflow2": {"status": "running"}
    }
    
    result = await dagger_adapter.shutdown()
    
    assert result is True
    assert dagger_adapter._engine is None


@pytest.mark.asyncio
async def test_shutdown_handles_exception(dagger_adapter):
    """Test that shutdown handles exceptions."""
    # Make the engine raise an exception when accessed
    dagger_adapter._engine = MagicMock(side_effect=Exception("Test error"))
    
    result = await dagger_adapter.shutdown()
    
    assert result is False


def test_from_config():
    """Test creating an adapter from a configuration dictionary."""
    config_dict = {
        "adapter_id": "test-adapter",
        "name": "Test Adapter",
        "description": "Test description",
        "container_registry": "docker.io",
        "workflow_directory": "/tmp/workflows",
        "max_concurrent_executions": 5,
        "timeout_seconds": 60
    }
    
    adapter = DaggerAdapter.from_config(config_dict)
    
    assert adapter.id == "test-adapter"
    assert adapter.name == "Test Adapter"
    assert adapter.description == "Test description"
    assert adapter.config.container_registry == "docker.io"
    assert adapter.config.workflow_directory == "/tmp/workflows"
    assert adapter.config.max_concurrent_executions == 5
    assert adapter.config.timeout_seconds == 60