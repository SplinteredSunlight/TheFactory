"""
Test the integration of the circuit breaker pattern with Dagger.

This module tests the integration of the circuit breaker pattern with the Dagger adapter
and workflow integration components.
"""

import asyncio
import pytest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig
from src.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from src.task_manager.dagger_integration import TaskWorkflowIntegration


@pytest.fixture
def dagger_adapter():
    """Create a DaggerAdapter instance for testing."""
    config = DaggerAdapterConfig(
        max_retries=2,
        retry_backoff_factor=0.1,
        retry_jitter=False,
        caching_enabled=False
    )
    adapter = DaggerAdapter(config)
    # Mock the initialize method to avoid actual initialization
    adapter.initialize = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def task_workflow_integration():
    """Create a TaskWorkflowIntegration instance for testing."""
    integration = TaskWorkflowIntegration()
    # Mock the task manager
    integration.task_manager = MagicMock()
    integration.task_manager.get_task = MagicMock(return_value=MagicMock(
        id="test-task-1",
        name="Test Task",
        description="Test task for circuit breaker",
        metadata={}
    ))
    integration.task_manager.update_task = MagicMock()
    integration.task_manager.update_task_status = MagicMock()
    
    # Mock the workflow integration
    integration.workflow_integration = MagicMock()
    integration.dagger_adapter = MagicMock()
    
    # Set up the circuit breaker
    integration.circuit_breaker = CircuitBreaker(
        failure_threshold=2,
        reset_timeout=1,
        half_open_timeout=0.5
    )
    
    return integration


@pytest.mark.asyncio
async def test_circuit_breaker_with_dagger_adapter(dagger_adapter):
    """Test that the circuit breaker works with the Dagger adapter."""
    # Mock the _execute_containerized_workflow method to fail
    dagger_adapter._execute_containerized_workflow = AsyncMock(side_effect=Exception("Test failure"))
    
    # Create an execution config
    execution_config = AgentExecutionConfig(
        task_id="test-task-1",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "test-image",
            "workflow_definition": "test-workflow",
            "use_circuit_breaker": True
        }
    )
    
    # Execute the workflow and expect it to fail
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "Test failure" in result.error
    
    # Execute again and expect it to fail
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "Test failure" in result.error
    
    # Execute a third time and expect the circuit breaker to be open
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "circuit breaker is open" in result.error.lower()
    
    # Wait for the circuit breaker to reset
    await asyncio.sleep(1.5)
    
    # Mock the _execute_containerized_workflow method to succeed
    dagger_adapter._execute_containerized_workflow = AsyncMock(return_value={"result": "success"})
    
    # Execute again and expect it to succeed (circuit breaker should be half-open)
    result = await dagger_adapter.execute(execution_config)
    assert result.success
    assert result.result == {"result": "success"}


@pytest.mark.asyncio
async def test_circuit_breaker_with_task_workflow_integration(task_workflow_integration):
    """Test that the circuit breaker works with the TaskWorkflowIntegration."""
    # Mock the execute_task_workflow method to fail
    task_workflow_integration.workflow_integration.execute_task_workflow = AsyncMock(side_effect=Exception("Test failure"))
    
    # Execute the workflow and expect it to fail
    with pytest.raises(Exception) as excinfo:
        await task_workflow_integration.execute_task_workflow(
            task_id="test-task-1",
            workflow_type="containerized_workflow",
            workflow_params={"use_circuit_breaker": True}
        )
    assert "Test failure" in str(excinfo.value)
    
    # Execute again and expect it to fail
    with pytest.raises(Exception) as excinfo:
        await task_workflow_integration.execute_task_workflow(
            task_id="test-task-1",
            workflow_type="containerized_workflow",
            workflow_params={"use_circuit_breaker": True}
        )
    assert "Test failure" in str(excinfo.value)
    
    # Execute a third time and expect the circuit breaker to be open
    with pytest.raises(CircuitBreakerOpenError) as excinfo:
        await task_workflow_integration.execute_task_workflow(
            task_id="test-task-1",
            workflow_type="containerized_workflow",
            workflow_params={"use_circuit_breaker": True}
        )
    assert "circuit breaker is open" in str(excinfo.value).lower()
    
    # Wait for the circuit breaker to reset
    await asyncio.sleep(1.5)
    
    # Mock the execute_task_workflow method to succeed
    task_workflow_integration.workflow_integration.execute_task_workflow = AsyncMock(return_value={"result": "success"})
    
    # Execute again and expect it to succeed (circuit breaker should be half-open)
    result = await task_workflow_integration.execute_task_workflow(
        task_id="test-task-1",
        workflow_type="containerized_workflow",
        workflow_params={"use_circuit_breaker": True}
    )
    assert result["result"] == "success"


@pytest.mark.asyncio
async def test_disable_circuit_breaker(dagger_adapter):
    """Test that the circuit breaker can be disabled."""
    # Mock the _execute_containerized_workflow method to fail
    dagger_adapter._execute_containerized_workflow = AsyncMock(side_effect=Exception("Test failure"))
    
    # Create an execution config with circuit breaker disabled
    execution_config = AgentExecutionConfig(
        task_id="test-task-1",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "test-image",
            "workflow_definition": "test-workflow",
            "use_circuit_breaker": False
        }
    )
    
    # Execute the workflow multiple times and expect it to fail each time
    # (circuit breaker should not open)
    for _ in range(5):
        result = await dagger_adapter.execute(execution_config)
        assert not result.success
        assert "Test failure" in result.error
        assert "circuit breaker is open" not in result.error.lower()


@pytest.mark.asyncio
async def test_circuit_breaker_with_retry(dagger_adapter):
    """Test that the circuit breaker works with retry."""
    # Mock the _execute_containerized_workflow method to fail
    dagger_adapter._execute_containerized_workflow = AsyncMock(side_effect=Exception("Test failure"))
    
    # Create an execution config with both circuit breaker and retry enabled
    execution_config = AgentExecutionConfig(
        task_id="test-task-1",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "test-image",
            "workflow_definition": "test-workflow",
            "use_circuit_breaker": True,
            "enable_retry": True
        }
    )
    
    # Execute the workflow and expect it to fail after retries
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "Test failure" in result.error
    
    # Execute again and expect it to fail after retries
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "Test failure" in result.error
    
    # Execute a third time and expect the circuit breaker to be open
    # (should not even attempt retries)
    result = await dagger_adapter.execute(execution_config)
    assert not result.success
    assert "circuit breaker is open" in result.error.lower()
