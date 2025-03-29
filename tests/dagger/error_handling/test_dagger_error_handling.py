"""
Tests for error handling in the Dagger integration.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult


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
        timeout_seconds=30
    )


@pytest.fixture
def adapter(adapter_config):
    """Create a DaggerAdapter for testing."""
    adapter = DaggerAdapter(adapter_config)
    adapter._engine = MagicMock()
    return adapter


@pytest.mark.asyncio
async def test_initialize_error_handling(adapter_config):
    """Test error handling during adapter initialization."""
    adapter = DaggerAdapter(adapter_config)
    
    # Mock os.path.exists to return False
    with patch('os.path.exists', return_value=False):
        # Mock os.makedirs to raise an exception
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            result = await adapter.initialize()
    
    # Verify that initialization failed
    assert result is False


@pytest.mark.asyncio
async def test_registry_auth_error_handling(adapter_config):
    """Test error handling during registry authentication."""
    adapter = DaggerAdapter(adapter_config)
    
    # Set up registry credentials
    adapter.config.container_registry = "docker.io"
    adapter.config.container_credentials = {"username": "user", "password": "pass"}
    
    # Mock _setup_registry_auth to raise an exception
    with patch.object(adapter, '_setup_registry_auth', side_effect=Exception("Auth error")):
        result = await adapter.initialize()
    
    # Verify that initialization failed
    assert result is False


@pytest.mark.asyncio
async def test_execute_unsupported_workflow_type(adapter):
    """Test error handling for unsupported workflow types."""
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="unsupported_type",
        parameters={}
    )
    
    result = await adapter.execute(config)
    
    assert result.success is False
    assert "Unsupported workflow type" in result.error


@pytest.mark.asyncio
async def test_execute_missing_required_params(adapter):
    """Test error handling for missing required parameters."""
    # Missing container_image in containerized_workflow
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={}  # Missing container_image
    )
    
    result = await adapter.execute(config)
    
    assert result.success is False
    assert "Container image is required" in result.error
    
    # Missing pipeline_definition in dagger_pipeline
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="dagger_pipeline",
        parameters={}  # Missing pipeline_definition
    )
    
    result = await adapter.execute(config)
    
    assert result.success is False
    assert "Pipeline definition is required" in result.error


@pytest.mark.asyncio
async def test_execute_connection_error(adapter):
    """Test error handling for connection errors."""
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={"container_image": "python:3.9"}
    )
    
    # Mock dagger.Connection to raise an exception
    with patch('dagger.Connection', side_effect=Exception("Connection error")):
        result = await adapter.execute(config)
    
    assert result.success is False
    assert "Connection error" in result.error


@pytest.mark.asyncio
async def test_execute_container_error(adapter):
    """Test error handling for container errors."""
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={"container_image": "python:3.9"}
    )
    
    # Create a mock connection that raises an exception when used
    mock_connection = AsyncMock()
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.container.side_effect = Exception("Container error")
    
    with patch('dagger.Connection', return_value=mock_connection):
        result = await adapter.execute(config)
    
    assert result.success is False
    assert "Container error" in result.error


@pytest.mark.asyncio
async def test_execute_with_malformed_workflow_file(adapter, tmp_path):
    """Test error handling for malformed workflow files."""
    # Create a malformed workflow file
    workflow_file = tmp_path / "malformed.yml"
    workflow_file.write_text("this is not valid yaml: [")
    
    config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "python:3.9",
            "workflow_definition": str(workflow_file)
        }
    )
    
    # Mock the connection
    mock_connection = AsyncMock()
    mock_connection.__aenter__.return_value = mock_connection
    mock_container = AsyncMock()
    mock_connection.container.return_value = mock_container
    mock_container.from_.return_value = mock_container
    
    # Mock open to raise an exception
    with patch('builtins.open', side_effect=Exception("File error")):
        with patch('dagger.Connection', return_value=mock_connection):
            result = await adapter.execute(config)
    
    assert result.success is False
    assert "File error" in result.error


@pytest.mark.asyncio
async def test_shutdown_with_active_workflows(adapter):
    """Test shutdown with active workflows."""
    # Add active workflows
    adapter._active_workflows = {
        "workflow1": {"status": "running"},
        "workflow2": {"status": "running"}
    }
    
    result = await adapter.shutdown()
    
    assert result is True
    assert adapter._engine is None


@pytest.mark.asyncio
async def test_shutdown_error_handling(adapter):
    """Test error handling during shutdown."""
    # Make the engine raise an exception when accessed
    adapter._engine = MagicMock(side_effect=Exception("Shutdown error"))
    
    result = await adapter.shutdown()
    
    assert result is False