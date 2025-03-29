"""
Test fixtures for Dagger integration tests.
"""
import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.orchestrator.engine import OrchestrationEngine, Workflow


@pytest.fixture
def temp_workflow_dir():
    """Create a temporary directory for workflow files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def dagger_config():
    """Create a Dagger configuration for testing."""
    return {
        "workflow": {
            "directory": "/tmp/workflows",
            "max_concurrent_executions": 3,
            "default_timeout": 30
        },
        "container": {
            "registry": "docker.io",
            "credentials": {
                "username": "test-user",
                "password": "test-password"
            },
            "default_images": {
                "python": "python:3.9-slim",
                "node": "node:16-alpine",
                "base": "ubuntu:20.04"
            }
        },
        "pipeline": {
            "caching_enabled": True,
            "default_timeout": 60,
            "source_directory": "/tmp/source"
        },
        "agents": {
            "containerized_workflow": {
                "name": "dagger_workflow_agent",
                "description": "Agent for containerized workflows",
                "capabilities": ["containerized_workflow"],
                "priority": 2
            },
            "pipeline": {
                "name": "dagger_pipeline_agent",
                "description": "Agent for Dagger pipelines",
                "capabilities": ["dagger_pipeline"],
                "priority": 2
            }
        }
    }


@pytest.fixture
def dagger_config_file(dagger_config, temp_workflow_dir):
    """Create a temporary Dagger configuration file."""
    config_file = os.path.join(temp_workflow_dir, "dagger.yaml")
    with open(config_file, "w") as f:
        yaml.dump(dagger_config, f)
    return config_file


@pytest.fixture
def sample_workflow():
    """Create a sample workflow for testing."""
    workflow = Workflow(name="test-workflow", description="Test workflow")
    
    # Add tasks
    task1_id = workflow.add_task(
        name="fetch_data",
        agent="data_fetcher",
        inputs={
            "url": "https://example.com/data",
            "format": "json"
        }
    )
    
    task2_id = workflow.add_task(
        name="process_data",
        agent="data_processor",
        inputs={
            "operation": "transform",
            "schema": {
                "fields": ["name", "value", "timestamp"]
            }
        },
        depends_on=[task1_id]
    )
    
    task3_id = workflow.add_task(
        name="analyze_data",
        agent="data_analyzer",
        inputs={
            "metrics": ["mean", "median", "std_dev"],
            "groupby": "timestamp"
        },
        depends_on=[task2_id]
    )
    
    return workflow


@pytest.fixture
def engine_with_workflow(sample_workflow):
    """Create an OrchestrationEngine with a sample workflow."""
    engine = OrchestrationEngine()
    engine.workflows[sample_workflow.id] = sample_workflow
    return engine, sample_workflow


@pytest.fixture
def mock_dagger_connection():
    """Create a mock Dagger connection for integration tests."""
    mock_connection = AsyncMock()
    mock_container = AsyncMock()
    mock_host = AsyncMock()
    mock_directory = AsyncMock()
    
    # Set up the chain of calls
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None
    mock_connection.container.return_value = mock_container
    mock_connection.host.return_value = mock_host
    mock_host.directory.return_value = mock_directory
    
    mock_container.from_.return_value = mock_container
    mock_container.with_env_variable.return_value = mock_container
    mock_container.with_mounted_directory.return_value = mock_container
    mock_container.with_new_file.return_value = mock_container
    mock_container.with_exec.return_value = mock_container
    mock_container.stdout.return_value = '{"status": "success", "result": "Test result"}'
    
    return mock_connection