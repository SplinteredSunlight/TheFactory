"""
Tests for the retry mechanism in the Dagger integration.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult
from src.orchestrator.engine import OrchestrationEngine, Workflow
from src.orchestrator.error_handling import RetryHandler, IntegrationError


@pytest.fixture
def adapter_config():
    """Create a DaggerAdapterConfig for testing."""
    return DaggerAdapterConfig(
        adapter_id="test-dagger-adapter",
        name="Test Dagger Adapter",
        description="Test adapter for Dagger integration",
        container_registry="docker.io",
        workflow_directory="/tmp/workflows",
        max_concurrent_executions=3,
        timeout_seconds=30,
        max_retries=3,
        retry_backoff_factor=0.1,  # Small value for faster tests
        retry_jitter=False  # Disable jitter for predictable tests
    )


@pytest.fixture
def adapter(adapter_config):
    """Create a DaggerAdapter for testing."""
    adapter = DaggerAdapter(adapter_config)
    adapter._engine = MagicMock()
    return adapter


@pytest.mark.asyncio
async def test_adapter_retry_on_transient_failure(adapter):
    """Test that the adapter retries on transient failures."""
    # Create a mock for the _execute_containerized_workflow method
    mock_execute = AsyncMock()
    # First two calls raise an exception, third call succeeds
    mock_execute.side_effect = [
        IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED"),
        IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED"),
        {"result": "success"}
    ]
    
    # Replace the _execute_containerized_workflow method with our mock
    with patch.object(adapter, '_execute_containerized_workflow', mock_execute):
        # Create an execution config
        config = AgentExecutionConfig(
            task_id="test-task",
            execution_type="containerized_workflow",
            parameters={
                "container_image": "python:3.9",
                "enable_retry": True
            }
        )
        
        # Execute the task
        result = await adapter.execute(config)
        
        # Verify that the method was called 3 times
        assert mock_execute.call_count == 3
        # Verify that the result is successful
        assert result.success is True
        assert result.result == {"result": "success"}


@pytest.mark.asyncio
async def test_adapter_no_retry_when_disabled(adapter):
    """Test that the adapter doesn't retry when retries are disabled."""
    # Create a mock for the _execute_containerized_workflow method
    mock_execute = AsyncMock()
    # Method raises an exception
    mock_execute.side_effect = IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED")
    
    # Replace the _execute_containerized_workflow method with our mock
    with patch.object(adapter, '_execute_containerized_workflow', mock_execute):
        # Create an execution config with retries disabled
        config = AgentExecutionConfig(
            task_id="test-task",
            execution_type="containerized_workflow",
            parameters={
                "container_image": "python:3.9",
                "enable_retry": False
            }
        )
        
        # Execute the task
        result = await adapter.execute(config)
        
        # Verify that the method was called only once
        assert mock_execute.call_count == 1
        # Verify that the result is a failure
        assert result.success is False
        assert "Connection error" in result.error


@pytest.mark.asyncio
async def test_orchestrator_retry_on_transient_failure():
    """Test that the orchestrator retries on transient failures."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = Workflow(name="test-workflow", description="Test workflow")
    workflow.add_task(name="test-task", agent="test-agent")
    
    # Mock the execute_workflow method to simulate a transient failure
    mock_execute = AsyncMock()
    # First two calls raise an exception, third call succeeds
    mock_execute.side_effect = [
        IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED"),
        IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED"),
        {"workflow_id": workflow.id, "status": "success"}
    ]
    
    # Replace the _execute_with_dagger method with our mock
    with patch.object(workflow, '_execute_with_dagger', mock_execute):
        # Add the workflow to the engine
        engine.workflows[workflow.id] = workflow
        
        # Execute the workflow with Dagger
        result = await engine.execute_workflow(
            workflow_id=workflow.id,
            engine_type="dagger",
            max_retries=3,
            retry_backoff_factor=0.1,
            retry_jitter=False,
            enable_retry=True
        )
        
        # Verify that the method was called 3 times
        assert mock_execute.call_count == 3
        # Verify that the result is successful
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_orchestrator_no_retry_when_disabled():
    """Test that the orchestrator doesn't retry when retries are disabled."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = Workflow(name="test-workflow", description="Test workflow")
    workflow.add_task(name="test-task", agent="test-agent")
    
    # Mock the execute_workflow method to simulate a failure
    mock_execute = AsyncMock()
    # Method raises an exception
    mock_execute.side_effect = IntegrationError("Connection error", "INTEGRATION.CONNECTION_FAILED")
    
    # Replace the _execute_with_dagger method with our mock
    with patch.object(workflow, '_execute_with_dagger', mock_execute):
        # Add the workflow to the engine
        engine.workflows[workflow.id] = workflow
        
        # Execute the workflow with Dagger with retries disabled
        result = await engine.execute_workflow(
            workflow_id=workflow.id,
            engine_type="dagger",
            enable_retry=False
        )
        
        # Verify that the method was called only once
        assert mock_execute.call_count == 1
        # Verify that the result is a failure
        assert result["status"] == "error"
        assert "Connection error" in result["error"]
