"""
Integration tests for Dagger configuration handling.
"""
import os
import yaml
import pytest
from unittest.mock import patch, MagicMock

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.examples.dagger_workflow_example import load_dagger_config


def test_load_config_from_file(dagger_config_file):
    """Test loading the Dagger configuration from a file."""
    # Mock the open function to return our config file
    with patch('builtins.open', return_value=open(dagger_config_file)):
        # Load the config
        with patch('os.path.join', return_value=dagger_config_file):
            config = load_dagger_config()
    
    # Verify the config
    assert "workflow" in config
    assert config["workflow"]["max_concurrent_executions"] == 3
    assert "container" in config
    assert config["container"]["registry"] == "docker.io"
    assert "pipeline" in config
    assert config["pipeline"]["caching_enabled"] is True
    assert "agents" in config
    assert "containerized_workflow" in config["agents"]


def test_environment_variable_substitution(dagger_config_file, monkeypatch):
    """Test that environment variables are substituted in the configuration."""
    # Set environment variables for the test
    monkeypatch.setenv("DAGGER_REGISTRY", "gcr.io")
    monkeypatch.setenv("DAGGER_USERNAME", "env-user")
    monkeypatch.setenv("DAGGER_PASSWORD", "env-password")
    
    # Load the config with environment variables
    with patch('builtins.open', return_value=open(dagger_config_file)):
        with patch('os.path.join', return_value=dagger_config_file):
            with patch('os.environ', {"DAGGER_REGISTRY": "gcr.io", "DAGGER_USERNAME": "env-user", "DAGGER_PASSWORD": "env-password"}):
                config = load_dagger_config()
    
    # Verify the environment variables were applied
    assert config.get("registry", None) == "gcr.io"
    assert config.get("username", {}).get("env_value") == "env-user"
    assert config.get("password", {}).get("env_value") == "env-password"


def test_adapter_from_config(dagger_config):
    """Test creating a DaggerAdapter from a configuration dictionary."""
    # Extract relevant config for the adapter
    adapter_config = {
        "adapter_id": "test-adapter",
        "name": dagger_config["agents"]["containerized_workflow"]["name"],
        "description": dagger_config["agents"]["containerized_workflow"]["description"],
        "container_registry": dagger_config["container"]["registry"],
        "container_credentials": dagger_config["container"]["credentials"],
        "workflow_directory": dagger_config["workflow"]["directory"],
        "max_concurrent_executions": dagger_config["workflow"]["max_concurrent_executions"],
        "timeout_seconds": dagger_config["workflow"]["default_timeout"]
    }
    
    # Create the adapter
    adapter = DaggerAdapter.from_config(adapter_config)
    
    # Verify the adapter
    assert adapter.id == "test-adapter"
    assert adapter.name == dagger_config["agents"]["containerized_workflow"]["name"]
    assert adapter.description == dagger_config["agents"]["containerized_workflow"]["description"]
    assert adapter.config.container_registry == dagger_config["container"]["registry"]
    assert adapter.config.container_credentials == dagger_config["container"]["credentials"]
    assert adapter.config.workflow_directory == dagger_config["workflow"]["directory"]
    assert adapter.config.max_concurrent_executions == dagger_config["workflow"]["max_concurrent_executions"]
    assert adapter.config.timeout_seconds == dagger_config["workflow"]["default_timeout"]


def test_adapter_config_validation():
    """Test validation of adapter configurations."""
    # Valid configuration
    valid_config = DaggerAdapterConfig(
        adapter_id="test-adapter",
        name="Test Adapter",
        description="Test description",
        container_registry="docker.io",
        container_credentials={"username": "user", "password": "pass"},
        workflow_directory="/workflows",
        max_concurrent_executions=5,
        timeout_seconds=600
    )
    
    assert valid_config.adapter_id == "test-adapter"
    assert valid_config.name == "Test Adapter"
    
    # Test with invalid values (these should be accepted but might cause issues later)
    edge_case_config = DaggerAdapterConfig(
        adapter_id="",  # Empty ID
        name=None,  # None name
        description="",  # Empty description
        container_registry=None,  # None registry
        container_credentials=None,  # None credentials
        workflow_directory="",  # Empty directory
        max_concurrent_executions=0,  # Zero concurrent executions
        timeout_seconds=0  # Zero timeout
    )
    
    assert edge_case_config.adapter_id == ""
    assert edge_case_config.name is None
    assert edge_case_config.workflow_directory == ""
    assert edge_case_config.max_concurrent_executions == 0
    assert edge_case_config.timeout_seconds == 0


def test_workflow_config_integration(dagger_config, sample_workflow):
    """Test integrating workflow configuration with Dagger."""
    # Extract workflow configuration from Dagger config
    workflow_config = {
        "max_concurrent_executions": dagger_config["workflow"]["max_concurrent_executions"],
        "default_timeout": dagger_config["workflow"]["default_timeout"],
        "steps": []
    }
    
    # Add steps from the sample workflow
    for task_id, task in sample_workflow.tasks.items():
        step = {
            "id": task.id,
            "name": task.name,
            "agent": task.agent,
            "inputs": task.inputs,
            "depends_on": task.depends_on
        }
        workflow_config["steps"].append(step)
    
    # Verify the workflow configuration
    assert len(workflow_config["steps"]) == 3  # Three tasks in the workflow
    assert workflow_config["max_concurrent_executions"] == 3
    assert workflow_config["default_timeout"] == 30