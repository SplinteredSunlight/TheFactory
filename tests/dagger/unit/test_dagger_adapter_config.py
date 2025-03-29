"""
Unit tests for the DaggerAdapterConfig.
"""
import os
import pytest
from src.agent_manager.dagger_adapter import DaggerAdapterConfig


def test_init_with_defaults():
    """Test initialization with default values."""
    config = DaggerAdapterConfig()
    
    assert config.adapter_id is not None  # Should generate a UUID
    assert config.name is None
    assert config.description is None
    assert config.container_registry is None
    assert config.container_credentials == {}
    assert os.path.basename(config.workflow_directory) == "workflows"
    assert config.workflow_defaults == {}
    assert config.max_concurrent_executions == 5
    assert config.timeout_seconds == 600


def test_init_with_custom_values():
    """Test initialization with custom values."""
    config = DaggerAdapterConfig(
        adapter_id="custom-id",
        name="Custom Name",
        description="Custom description",
        container_registry="gcr.io",
        container_credentials={"username": "user", "password": "pass"},
        workflow_directory="/custom/path",
        workflow_defaults={"runtime": "python"},
        max_concurrent_executions=10,
        timeout_seconds=1200
    )
    
    assert config.adapter_id == "custom-id"
    assert config.name == "Custom Name"
    assert config.description == "Custom description"
    assert config.container_registry == "gcr.io"
    assert config.container_credentials == {"username": "user", "password": "pass"}
    assert config.workflow_directory == "/custom/path"
    assert config.workflow_defaults == {"runtime": "python"}
    assert config.max_concurrent_executions == 10
    assert config.timeout_seconds == 1200


def test_to_dict_excludes_credentials():
    """Test that to_dict excludes sensitive credentials."""
    config = DaggerAdapterConfig(
        adapter_id="test-id",
        name="Test Name",
        description="Test description",
        container_registry="docker.io",
        container_credentials={"username": "user", "password": "secret"},
        workflow_directory="/test/path",
        workflow_defaults={"runtime": "python"},
        max_concurrent_executions=5,
        timeout_seconds=600
    )
    
    config_dict = config.to_dict()
    
    assert config_dict["adapter_id"] == "test-id"
    assert config_dict["name"] == "Test Name"
    assert config_dict["description"] == "Test description"
    assert config_dict["container_registry"] == "docker.io"
    assert "container_credentials" not in config_dict
    assert config_dict["workflow_directory"] == "/test/path"
    assert config_dict["workflow_defaults"] == {"runtime": "python"}
    assert config_dict["max_concurrent_executions"] == 5
    assert config_dict["timeout_seconds"] == 600


def test_additional_kwargs():
    """Test that additional kwargs are accepted but not used."""
    config = DaggerAdapterConfig(
        extra_param1="value1",
        extra_param2="value2"
    )
    
    # These are not stored in the object attributes
    assert not hasattr(config, "extra_param1")
    assert not hasattr(config, "extra_param2")


def test_negative_max_concurrent_executions():
    """Test with negative max_concurrent_executions (should still be allowed)."""
    config = DaggerAdapterConfig(
        max_concurrent_executions=-1
    )
    
    assert config.max_concurrent_executions == -1


def test_negative_timeout_seconds():
    """Test with negative timeout_seconds (should still be allowed)."""
    config = DaggerAdapterConfig(
        timeout_seconds=-1
    )
    
    assert config.timeout_seconds == -1