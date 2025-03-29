"""
Integration tests for the Dagger integration.
"""
import os
import yaml
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import dagger
from src.examples.dagger_workflow_example import run_example, load_dagger_config


@pytest.mark.asyncio
async def test_run_example(mock_dagger_connection, dagger_config_file, monkeypatch):
    """Test the Dagger workflow example."""
    # Set environment variables for the test
    monkeypatch.setenv("DAGGER_REGISTRY", "gcr.io")
    monkeypatch.setenv("DAGGER_USERNAME", "test-user")
    monkeypatch.setenv("DAGGER_PASSWORD", "test-password")
    
    # Patch the dagger Connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Patch the config loading function to use our test config
        with patch('src.examples.dagger_workflow_example.load_dagger_config', return_value=yaml.safe_load(open(dagger_config_file))):
            # Run the example
            result = await run_example()
    
    # Verify the result
    assert result is not None
    assert result.get("status") == "success"
    assert result.get("engine") == "dagger"
    assert len(result.get("tasks", {})) > 0


def test_load_dagger_config(dagger_config_file, monkeypatch):
    """Test loading the Dagger configuration."""
    # Set environment variables for the test
    monkeypatch.setenv("DAGGER_REGISTRY", "gcr.io")
    monkeypatch.setenv("DAGGER_USERNAME", "env-user")
    monkeypatch.setenv("DAGGER_PASSWORD", "env-password")
    
    # Load the config
    with patch('src.examples.dagger_workflow_example.load_dagger_config') as mock_load:
        mock_load.return_value = yaml.safe_load(open(dagger_config_file))
        config = load_dagger_config()
    
    # Verify the config
    assert "workflow" in config
    assert "container" in config
    assert "pipeline" in config
    assert "agents" in config


@pytest.mark.asyncio
async def test_workflow_execution_with_dagger(engine_with_workflow, mock_dagger_connection, dagger_config):
    """Test executing a workflow with Dagger."""
    engine, workflow = engine_with_workflow
    
    # Patch the dagger Connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Execute the workflow
        result = engine.execute_workflow(
            workflow_id=workflow.id,
            engine_type="dagger",
            container_registry=dagger_config["container"]["registry"],
            container_credentials=dagger_config["container"]["credentials"],
            workflow_directory=dagger_config["workflow"]["directory"],
            workflow_defaults={
                "inputs": {
                    "default_timeout": dagger_config["workflow"]["default_timeout"]
                }
            }
        )
    
    # Verify the result
    assert result.get("status") == "success"
    assert result.get("engine") == "dagger"
    assert len(result.get("tasks", {})) == 3  # Three tasks in the workflow


@pytest.mark.asyncio
async def test_workflow_execution_error_handling(engine_with_workflow, mock_dagger_connection):
    """Test error handling in workflow execution with Dagger."""
    engine, workflow = engine_with_workflow
    
    # Make the mock connection raise an exception
    mock_dagger_connection.container.side_effect = Exception("Connection error")
    
    # Patch the dagger Connection
    with patch('dagger.Connection', return_value=mock_dagger_connection):
        # Execute the workflow
        result = engine.execute_workflow(
            workflow_id=workflow.id,
            engine_type="dagger"
        )
    
    # Verify the result
    assert result.get("status") == "error"
    assert result.get("engine") == "dagger"
    assert "error" in result
    assert "Connection error" in result.get("error")