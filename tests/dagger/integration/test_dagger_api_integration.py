"""
Integration tests for Dagger API endpoints.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from src.api.main import app
from src.orchestrator.engine import OrchestrationEngine, Workflow


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_engine():
    """Mock the orchestration engine."""
    mock_engine = MagicMock(spec=OrchestrationEngine)
    
    # Mock a workflow
    mock_workflow = MagicMock(spec=Workflow)
    mock_workflow.id = str(uuid.uuid4())
    mock_workflow.name = "test-workflow"
    mock_workflow.description = "Test workflow"
    mock_workflow.status = "pending"
    mock_workflow.tasks = {}
    mock_workflow.engine_type = "dagger"
    
    # Mock the execute method
    mock_workflow.execute.return_value = {
        "workflow_id": mock_workflow.id,
        "status": "success",
        "engine": "dagger",
        "tasks": {},
        "results": {"message": "Workflow executed with Dagger"}
    }
    
    # Set up the engine
    mock_engine.workflows = {mock_workflow.id: mock_workflow}
    mock_engine.get_workflow.return_value = mock_workflow
    mock_engine.create_workflow.return_value = mock_workflow
    mock_engine.execute_workflow.return_value = {
        "workflow_id": mock_workflow.id,
        "status": "success",
        "engine": "dagger",
        "tasks": {},
        "results": {"message": "Workflow executed with Dagger"}
    }
    mock_engine.list_workflows.return_value = [
        {
            "id": mock_workflow.id,
            "name": mock_workflow.name,
            "description": mock_workflow.description,
            "status": mock_workflow.status,
            "engine_type": "dagger",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": None
        }
    ]
    
    return mock_engine


def test_list_workflows(client, mock_engine):
    """Test listing workflows."""
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.get("/dagger/workflows")
    
    assert response.status_code == 200
    assert "workflows" in response.json()
    assert "total" in response.json()
    assert len(response.json()["workflows"]) == 1


def test_get_workflow(client, mock_engine):
    """Test getting a specific workflow."""
    workflow_id = list(mock_engine.workflows.keys())[0]
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.get(f"/dagger/workflows/{workflow_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == workflow_id
    assert response.json()["name"] == "test-workflow"


def test_get_workflow_not_found(client, mock_engine):
    """Test getting a non-existent workflow."""
    # Make get_workflow raise a KeyError
    mock_engine.get_workflow.side_effect = KeyError("Workflow not found")
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.get(f"/dagger/workflows/{uuid.uuid4()}")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_create_workflow(client, mock_engine):
    """Test creating a workflow."""
    workflow_data = {
        "name": "new-workflow",
        "description": "New workflow",
        "steps": [
            {
                "id": "step1",
                "name": "Step 1",
                "container": {
                    "image": "python:3.9-slim"
                }
            }
        ]
    }
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.post("/dagger/workflows", json=workflow_data)
    
    assert response.status_code == 201
    assert response.json()["name"] == "test-workflow"  # From mock


def test_update_workflow(client, mock_engine):
    """Test updating a workflow."""
    workflow_id = list(mock_engine.workflows.keys())[0]
    update_data = {
        "name": "updated-workflow",
        "description": "Updated workflow"
    }
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.patch(f"/dagger/workflows/{workflow_id}", json=update_data)
    
    assert response.status_code == 200
    assert response.json()["id"] == workflow_id


def test_delete_workflow(client, mock_engine):
    """Test deleting a workflow."""
    workflow_id = list(mock_engine.workflows.keys())[0]
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        response = client.delete(f"/dagger/workflows/{workflow_id}")
    
    assert response.status_code == 204


def test_execute_workflow(client, mock_engine):
    """Test executing a workflow."""
    workflow_id = list(mock_engine.workflows.keys())[0]
    execution_data = {
        "inputs": {"param": "value"},
        "container_registry": "docker.io",
        "container_credentials": {"username": "test", "password": "test"}
    }
    
    with patch("src.api.routes.dagger_routes.get_orchestration_engine", return_value=mock_engine):
        with patch("src.api.routes.dagger_routes.uuid4", return_value=uuid.UUID("00000000-0000-0000-0000-000000000000")):
            response = client.post(f"/dagger/workflows/{workflow_id}/execute", json=execution_data)
    
    assert response.status_code == 202
    assert response.json()["execution_id"] == "00000000-0000-0000-0000-000000000000"
    assert response.json()["status"] == "pending"
    assert response.json()["workflow_id"] == workflow_id