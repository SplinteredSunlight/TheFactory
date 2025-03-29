"""
Tests for the caching functionality in the Dagger integration.
"""
import os
import json
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult


@pytest.fixture
def cache_directory(tmp_path):
    """Create a temporary directory for cache files."""
    cache_dir = tmp_path / "dagger_cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def adapter_config(cache_directory):
    """Create a DaggerAdapterConfig with caching enabled."""
    return DaggerAdapterConfig(
        adapter_id="test-dagger-adapter",
        name="Test Dagger Adapter",
        description="Test adapter for Dagger integration",
        container_registry="docker.io",
        workflow_directory="/tmp/workflows",
        max_concurrent_executions=3,
        timeout_seconds=30,
        max_retries=3,
        retry_backoff_factor=0.1,
        retry_jitter=False,
        caching_enabled=True,
        cache_directory=cache_directory,
        cache_ttl_seconds=60  # Short TTL for testing
    )


@pytest.fixture
def adapter(adapter_config):
    """Create a DaggerAdapter with caching enabled."""
    adapter = DaggerAdapter(adapter_config)
    adapter._engine = MagicMock()
    return adapter


@pytest.mark.asyncio
async def test_cache_initialization(adapter, cache_directory):
    """Test that the cache is initialized correctly."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Check that the cache directory exists
    assert os.path.exists(cache_directory)
    
    # Check that the cache is empty
    assert adapter._cache == {}


@pytest.mark.asyncio
async def test_cache_save_and_load(adapter, cache_directory):
    """Test that cache entries can be saved and loaded."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Add an entry to the cache
    cache_key = "test_key"
    test_result = {"stdout": "test output"}
    await adapter._add_to_cache(cache_key, test_result)
    
    # Check that the cache file exists
    cache_file = os.path.join(cache_directory, "cache.json")
    assert os.path.exists(cache_file)
    
    # Check that the cache file contains the entry
    with open(cache_file, "r") as f:
        cache_data = json.load(f)
        assert cache_key in cache_data
        assert cache_data[cache_key]["result"] == test_result
    
    # Create a new adapter and load the cache
    new_adapter = DaggerAdapter(adapter.config)
    new_adapter._engine = MagicMock()
    await new_adapter.initialize()
    
    # Check that the cache was loaded
    assert cache_key in new_adapter._cache
    cached_result = await new_adapter._get_from_cache(cache_key)
    assert cached_result == test_result


@pytest.mark.asyncio
async def test_cache_expiry(adapter, cache_directory):
    """Test that expired cache entries are not used."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Add an entry to the cache with a short TTL
    cache_key = "test_key"
    test_result = {"stdout": "test output"}
    
    # Manually set a cache entry with a short expiry
    expiry = time.time() + 1  # 1 second from now
    adapter._cache[cache_key] = {
        "result": test_result,
        "expiry": expiry,
        "timestamp": time.time()
    }
    
    # Save the cache
    await adapter._save_cache()
    
    # Wait for the cache entry to expire
    await asyncio.sleep(1.5)
    
    # Try to get the expired entry
    cached_result = await adapter._get_from_cache(cache_key)
    assert cached_result is None
    
    # Check that the expired entry was removed from the cache
    assert cache_key not in adapter._cache


@pytest.mark.asyncio
async def test_workflow_caching(adapter):
    """Test that workflow results are cached and reused."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Create a mock for the _execute_containerized_workflow method
    mock_execute = AsyncMock()
    mock_execute.return_value = {"stdout": "test output"}
    
    # Replace the _execute_containerized_workflow method with our mock
    with patch.object(adapter, '_execute_containerized_workflow', mock_execute):
        # Create execution parameters
        params = {
            "container_image": "python:3.9",
            "workflow_definition": "test_workflow.yml",
            "inputs": {"param1": "value1"}
        }
        
        # Execute the workflow twice with the same parameters
        config1 = AgentExecutionConfig(
            task_id="test-task-1",
            execution_type="containerized_workflow",
            parameters=params
        )
        
        config2 = AgentExecutionConfig(
            task_id="test-task-2",
            execution_type="containerized_workflow",
            parameters=params
        )
        
        # First execution should call the mock
        result1 = await adapter.execute(config1)
        
        # Second execution should use the cached result
        result2 = await adapter.execute(config2)
        
        # Verify that the mock was called only once
        assert mock_execute.call_count == 1
        
        # Verify that both results are the same
        assert result1.result == result2.result


@pytest.mark.asyncio
async def test_skip_cache(adapter):
    """Test that caching can be skipped when requested."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Create a mock for the _execute_containerized_workflow method
    mock_execute = AsyncMock()
    mock_execute.return_value = {"stdout": "test output"}
    
    # Replace the _execute_containerized_workflow method with our mock
    with patch.object(adapter, '_execute_containerized_workflow', mock_execute):
        # Create execution parameters with skip_cache=True
        params = {
            "container_image": "python:3.9",
            "workflow_definition": "test_workflow.yml",
            "inputs": {"param1": "value1"},
            "skip_cache": True
        }
        
        # Execute the workflow twice with the same parameters
        config1 = AgentExecutionConfig(
            task_id="test-task-1",
            execution_type="containerized_workflow",
            parameters=params
        )
        
        config2 = AgentExecutionConfig(
            task_id="test-task-2",
            execution_type="containerized_workflow",
            parameters=params
        )
        
        # Both executions should call the mock
        await adapter.execute(config1)
        await adapter.execute(config2)
        
        # Verify that the mock was called twice
        assert mock_execute.call_count == 2


@pytest.mark.asyncio
async def test_pipeline_caching(adapter):
    """Test that pipeline results are cached and reused."""
    # Initialize the adapter
    await adapter.initialize()
    
    # Create a mock for the _execute_dagger_pipeline method
    mock_execute = AsyncMock()
    mock_execute.return_value = {"result": {"message": "test output"}, "inputs": {}}
    
    # Replace the _execute_dagger_pipeline method with our mock
    with patch.object(adapter, '_execute_dagger_pipeline', mock_execute):
        # Create execution parameters
        params = {
            "pipeline_definition": "test_pipeline.yml",
            "inputs": {"param1": "value1"},
            "source_directory": "/tmp/source"
        }
        
        # Execute the pipeline twice with the same parameters
        config1 = AgentExecutionConfig(
            task_id="test-task-1",
            execution_type="dagger_pipeline",
            parameters=params
        )
        
        config2 = AgentExecutionConfig(
            task_id="test-task-2",
            execution_type="dagger_pipeline",
            parameters=params
        )
        
        # First execution should call the mock
        result1 = await adapter.execute(config1)
        
        # Second execution should use the cached result
        result2 = await adapter.execute(config2)
        
        # Verify that the mock was called only once
        assert mock_execute.call_count == 1
        
        # Verify that both results are the same
        assert result1.result == result2.result


@pytest.mark.asyncio
async def test_cache_key_generation(adapter):
    """Test that cache keys are generated correctly."""
    # Different parameters should generate different cache keys
    params1 = {
        "container_image": "python:3.9",
        "workflow_definition": "test_workflow.yml",
        "inputs": {"param1": "value1"}
    }
    
    params2 = {
        "container_image": "python:3.9",
        "workflow_definition": "test_workflow.yml",
        "inputs": {"param1": "value2"}  # Different input value
    }
    
    key1 = adapter._get_cache_key(params1)
    key2 = adapter._get_cache_key(params2)
    
    assert key1 != key2
    
    # Same parameters in different order should generate the same cache key
    params3 = {
        "inputs": {"param1": "value1"},
        "container_image": "python:3.9",
        "workflow_definition": "test_workflow.yml"
    }
    
    key3 = adapter._get_cache_key(params3)
    
    assert key1 == key3


@pytest.mark.asyncio
async def test_disable_caching(cache_directory):
    """Test that caching can be disabled."""
    # Create a config with caching disabled
    config = DaggerAdapterConfig(
        adapter_id="test-dagger-adapter",
        name="Test Dagger Adapter",
        description="Test adapter for Dagger integration",
        caching_enabled=False,
        cache_directory=cache_directory
    )
    
    adapter = DaggerAdapter(config)
    adapter._engine = MagicMock()
    
    # Initialize the adapter
    await adapter.initialize()
    
    # Add an entry to the cache (should be a no-op)
    cache_key = "test_key"
    test_result = {"stdout": "test output"}
    await adapter._add_to_cache(cache_key, test_result)
    
    # Check that the cache is empty
    assert adapter._cache == {}
    
    # Check that the cache file doesn't exist
    cache_file = os.path.join(cache_directory, "cache.json")
    assert not os.path.exists(cache_file)
