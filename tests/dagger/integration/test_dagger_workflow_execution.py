"""
Integration tests for Dagger workflow execution.
"""
import os
import pytest
import yaml
import uuid
from unittest.mock import patch, AsyncMock

from src.orchestrator.engine import OrchestrationEngine, Workflow
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig

# Constants
TEST_WORKFLOW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "workflows")
TEST_WORKFLOW_FILE = os.path.join(TEST_WORKFLOW_DIR, "example_workflow.yml")


@pytest.fixture
def mock_dagger_connection():
    """Create a mock Dagger connection."""
    mock_conn = AsyncMock()
    mock_container = AsyncMock()
    mock_host = AsyncMock()
    mock_dir = AsyncMock()
    
    # Set up the chain of calls
    mock_conn.__aenter__.return_value = mock_conn
    mock_conn.container.return_value = mock_container
    mock_conn.host.return_value = mock_host
    mock_host.directory.return_value = mock_dir
    
    mock_container.from_.return_value = mock_container
    mock_container.with_env_variable.return_value = mock_container
    mock_container.with_mounted_directory.return_value = mock_container
    mock_container.with_new_file.return_value = mock_container
    mock_container.with_exec.return_value = mock_container
    mock_container.stdout.return_value = '{"result": "success", "data": [1, 2, 3]}'
    
    return mock_conn


@pytest.fixture
def engine():
    """Create an orchestration engine."""
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="test-workflow",
        description="Test workflow"
    )
    
    # Add tasks
    task1_id = workflow.add_task(
        name="fetch-data",
        agent="python:3.9-slim",
        inputs={
            "url": "https://example.com/data",
            "format": "json"
        }
    )
    
    task2_id = workflow.add_task(
        name="process-data",
        agent="python:3.9-slim",
        inputs={
            "operation": "transform",
            "schema": {
                "fields": ["name", "value", "timestamp"]
            }
        },
        depends_on=[task1_id]
    )
    
    task3_id = workflow.add_task(
        name="analyze-data",
        agent="python:3.9-slim",
        inputs={
            "metrics": ["mean", "median", "std_dev"],
            "groupby": "timestamp"
        },
        depends_on=[task2_id]
    )
    
    return engine


@pytest.mark.asyncio
async def test_workflow_execution_with_dagger(engine, mock_dagger_connection):
    """Test executing a workflow with Dagger."""
    workflow_id = list(engine.workflows.keys())[0]
    
    # Mock the Dagger connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Execute the workflow
        result = engine.execute_workflow(
            workflow_id=workflow_id,
            engine_type="dagger",
            container_registry="docker.io",
            container_credentials={"username": "test", "password": "test"},
            workflow_directory=TEST_WORKFLOW_DIR,
            workflow_defaults={"inputs": {"default_timeout": 30}}
        )
    
    # Verify the result
    assert result["workflow_id"] == workflow_id
    assert result["status"] == "success"
    assert result["engine"] == "dagger"
    assert len(result["tasks"]) == 3
    assert "message" in result["results"]


@pytest.mark.asyncio
async def test_workflow_execution_with_file(engine, mock_dagger_connection):
    """Test executing a workflow with a workflow file."""
    workflow_id = list(engine.workflows.keys())[0]
    
    # Create a test workflow file if it doesn't exist
    if not os.path.exists(TEST_WORKFLOW_FILE):
        os.makedirs(os.path.dirname(TEST_WORKFLOW_FILE), exist_ok=True)
        workflow_data = {
            "name": "Example Workflow",
            "description": "A simple example workflow for testing",
            "steps": [
                {
                    "id": "fetch-data",
                    "name": "Fetch Data",
                    "image": "python:3.9-slim",
                    "command": ["python", "-c", "print('Fetching data...')"],
                    "environment": {"API_KEY": "test"}
                },
                {
                    "id": "process-data",
                    "name": "Process Data",
                    "image": "python:3.9-slim",
                    "command": ["python", "-c", "print('Processing data...')"],
                    "depends_on": ["fetch-data"]
                }
            ]
        }
        
        with open(TEST_WORKFLOW_FILE, "w") as f:
            yaml.dump(workflow_data, f)
    
    # Mock the Dagger connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Execute the workflow with a workflow file
        result = engine.execute_workflow(
            workflow_id=workflow_id,
            engine_type="dagger",
            workflow_definition=TEST_WORKFLOW_FILE,
            container_registry="docker.io",
            workflow_directory=TEST_WORKFLOW_DIR
        )
    
    # Verify the result
    assert result["workflow_id"] == workflow_id
    assert result["status"] == "success"
    assert result["engine"] == "dagger"


@pytest.mark.asyncio
async def test_workflow_error_handling(engine, mock_dagger_connection):
    """Test error handling in workflow execution."""
    workflow_id = list(engine.workflows.keys())[0]
    
    # Make the mock connection raise an exception
    mock_dagger_connection.container.side_effect = RuntimeError("Test error")
    
    # Mock the Dagger connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Execute the workflow
        result = engine.execute_workflow(
            workflow_id=workflow_id,
            engine_type="dagger"
        )
    
    # Verify the result
    assert result["workflow_id"] == workflow_id
    assert result["status"] == "error"
    assert result["engine"] == "dagger"
    assert "error" in result
    assert "Test error" in result["error"]


@pytest.mark.asyncio
async def test_dagger_adapter_execution(mock_dagger_connection):
    """Test executing a task with the Dagger adapter."""
    # Create a Dagger adapter config
    config = DaggerAdapterConfig(
        adapter_id=str(uuid.uuid4()),
        name="Test Adapter",
        description="Test description",
        container_registry="docker.io",
        workflow_directory=TEST_WORKFLOW_DIR,
        max_concurrent_executions=5,
        timeout_seconds=30
    )
    
    # Create a Dagger adapter
    adapter = DaggerAdapter(config)
    
    # Initialize the adapter
    with patch('pydagger.Engine', AsyncMock()):
        await adapter.initialize()
    
    # Create an execution config
    execution_config = AgentExecutionConfig(
        task_id="test-task",
        execution_type="containerized_workflow",
        parameters={
            "container_image": "python:3.9-slim",
            "workflow_definition": TEST_WORKFLOW_FILE,
            "inputs": {"param": "value"},
            "volumes": [{"source": "/tmp", "target": "/data"}],
            "environment": {"ENV_VAR": "value"}
        },
        timeout_seconds=30
    )
    
    # Execute the task
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        result = await adapter.execute(execution_config)
    
    # Verify the result
    assert result.success is True
    assert result.error is None
    assert "stdout" in result.result


@pytest.mark.asyncio
async def test_dagger_adapter_pipeline_execution(mock_dagger_connection):
    """Test executing a pipeline with the Dagger adapter."""
    # Create a Dagger adapter config
    config = DaggerAdapterConfig(
        adapter_id=str(uuid.uuid4()),
        name="Test Adapter",
        description="Test description",
        container_registry="docker.io",
        workflow_directory=TEST_WORKFLOW_DIR,
        max_concurrent_executions=5,
        timeout_seconds=30
    )
    
    # Create a Dagger adapter
    adapter = DaggerAdapter(config)
    
    # Initialize the adapter
    with patch('pydagger.Engine', AsyncMock()):
        await adapter.initialize()
    
    # Create an execution config
    execution_config = AgentExecutionConfig(
        task_id="test-pipeline-task",
        execution_type="dagger_pipeline",
        parameters={
            "pipeline_definition": os.path.join(TEST_WORKFLOW_DIR, "example_pipeline.yml"),
            "inputs": {"param": "value"},
            "source_directory": "/tmp/source"
        },
        timeout_seconds=60
    )
    
    # Execute the task
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        result = await adapter.execute(execution_config)
    
    # Verify the result
    assert result.success is True
    assert result.error is None
    assert "result" in result.result
    assert "inputs" in result.result