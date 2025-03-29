"""
Test fixtures for Dagger unit tests.
"""
import os
import asyncio
import tempfile
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.agent_manager.dagger_adapter import DaggerAdapterConfig, DaggerAdapter
from src.agent_manager.schemas import AgentExecutionConfig


@pytest.fixture
def temp_workflow_dir():
    """Create a temporary directory for workflow files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_dagger_engine():
    """Create a mock Dagger engine."""
    mock_engine = MagicMock()
    return mock_engine


@pytest.fixture
def dagger_adapter_config(temp_workflow_dir):
    """Create a DaggerAdapterConfig for testing."""
    return DaggerAdapterConfig(
        adapter_id="test-dagger-adapter",
        name="Test Dagger Adapter",
        description="Test adapter for Dagger integration",
        container_registry="docker.io",
        workflow_directory=temp_workflow_dir,
        max_concurrent_executions=3,
        timeout_seconds=30
    )


@pytest.fixture
def dagger_adapter(dagger_adapter_config, mock_dagger_engine):
    """Create a DaggerAdapter for testing."""
    adapter = DaggerAdapter(dagger_adapter_config)
    adapter._engine = mock_dagger_engine
    return adapter


@pytest.fixture
def execution_config():
    """Create an execution configuration for testing."""
    return AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "python:3.9-alpine",
            "workflow_definition": "test-workflow.yml",
            "inputs": {"key": "value"},
            "volumes": [{"source": "/tmp", "target": "/data"}],
            "environment": {"ENV_VAR": "value"}
        },
        timeout_seconds=30
    )


@pytest.fixture
def pipeline_execution_config():
    """Create a pipeline execution configuration for testing."""
    return AgentExecutionConfig(
        task_id="test-pipeline-task",
        execution_type="dagger_pipeline",
        parameters={
            "pipeline_definition": "test-pipeline.yml",
            "inputs": {"key": "value"},
            "source_directory": "/tmp/source"
        },
        timeout_seconds=60
    )


@pytest.fixture
def mock_dagger_connection():
    """Create a mock Dagger connection."""
    mock_connection = AsyncMock()
    mock_container = AsyncMock()
    mock_host = AsyncMock()
    mock_directory = AsyncMock()
    
    # Set up the chain of calls
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.container.return_value = mock_container
    mock_connection.host.return_value = mock_host
    mock_host.directory.return_value = mock_directory
    
    mock_container.from_.return_value = mock_container
    mock_container.with_env_variable.return_value = mock_container
    mock_container.with_mounted_directory.return_value = mock_container
    mock_container.with_new_file.return_value = mock_container
    mock_container.with_exec.return_value = mock_container
    mock_container.stdout.return_value = "Test output"
    
    return mock_connection