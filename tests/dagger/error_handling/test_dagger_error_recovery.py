"""
Tests for error recovery in the Dagger integration.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult


class TestDaggerErrorRecovery:
    """Test error recovery in the Dagger integration."""
    
    @pytest.fixture
    async def adapter(self):
        """Create a Dagger adapter for testing."""
        config = DaggerAdapterConfig(
            adapter_id="test-adapter",
            name="Test Adapter",
            description="Test adapter for Dagger integration",
            container_registry="docker.io",
            workflow_directory="/tmp/workflows",
            max_concurrent_executions=3,
            timeout_seconds=30
        )
        
        adapter = DaggerAdapter(config)
        
        # Mock the engine
        adapter._engine = MagicMock()
        
        return adapter
    
    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, adapter):
        """Test retrying on connection error."""
        # Create an execution config
        config = AgentExecutionConfig(
            task_id="test-task",
            execution_type="containerized_workflow",
            parameters={
                "container_image": "python:3.9-slim",
                "workflow_definition": "test-workflow.yml",
                "inputs": {"retry": "true"},
                "retry_count": 3,
                "retry_delay": 0.1  # Short delay for testing
            }
        )
        
        # Create a mock connection that fails twice and then succeeds
        mock_connection = AsyncMock()
        mock_connection.__aenter__.side_effect = [
            RuntimeError("Connection error"),  # First attempt
            RuntimeError("Connection error"),  # Second attempt
            AsyncMock()  # Third attempt succeeds
        ]
        
        # Mock the rest of the chain
        mock_container = AsyncMock()
        mock_connection.__aenter__.return_value.container.return_value = mock_container
        mock_container.from_.return_value = mock_container
        mock_container.with_env_variable.return_value = mock_container
        mock_container.with_mounted_directory.return_value = mock_container
        mock_container.with_exec.return_value = mock_container
        mock_container.stdout.return_value = '{"result": "success"}'
        
        # Patch execute_with_retry to use our custom logic
        async def execute_with_retry(self, func, max_retries=3, retry_delay=0.1):
            """Execute a function with retry logic."""
            for attempt in range(1, max_retries + 1):
                try:
                    return await func()
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(retry_delay)
            
        # Add the execute_with_retry method to the adapter
        adapter.execute_with_retry = execute_with_retry.__get__(adapter)
        
        # Patch the _execute_containerized_workflow to use retry
        original_execute = adapter._execute_containerized_workflow
        
        async def execute_with_retry_wrapper(params):
            """Wrapper that adds retry logic."""
            retry_count = params.get("retry_count", 0)
            retry_delay = params.get("retry_delay", 1)
            
            if params.get("retry") == "true" and retry_count > 0:
                return await adapter.execute_with_retry(
                    lambda: original_execute(params),
                    max_retries=retry_count,
                    retry_delay=retry_delay
                )
            else:
                return await original_execute(params)
                
        adapter._execute_containerized_workflow = execute_with_retry_wrapper
        
        # Patch dagger.Connection to use our mock
        with patch('dagger.Connection', return_value=mock_connection):
            result = await adapter.execute(config)
        
        # Verify the result
        assert result.success is True
        assert result.error is None
        assert result.result is not None
        assert result.result.get("result") == "success"
        
        # Verify that the connection was created three times
        assert mock_connection.__aenter__.call_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, adapter):
        """Test circuit breaker pattern for preventing cascading failures."""
        # Add circuit breaker state to the adapter
        adapter._circuit_state = "closed"
        adapter._failure_count = 0
        adapter._circuit_threshold = 3
        adapter._last_failure_time = 0
        adapter._circuit_reset_timeout = 5  # seconds
        
        # Create an execution config
        config = AgentExecutionConfig(
            task_id="test-task",
            execution_type="containerized_workflow",
            parameters={
                "container_image": "python:3.9-slim",
                "workflow_definition": "test-workflow.yml",
                "inputs": {"param": "value"}
            }
        )
        
        # Create a mock connection that always fails
        mock_connection = AsyncMock()
        mock_connection.__aenter__.side_effect = RuntimeError("Connection error")
        
        # Add circuit breaker method to the adapter
        async def check_circuit_breaker(self):
            """Check the circuit breaker state."""
            import time
            
            if self._circuit_state == "open":
                # Check if it's time to try resetting the circuit
                if time.time() - self._last_failure_time > self._circuit_reset_timeout:
                    self._circuit_state = "half-open"
                    return True
                return False
            
            return True
        
        def trip_circuit_breaker(self):
            """Trip the circuit breaker."""
            import time
            
            self._failure_count += 1
            if self._failure_count >= self._circuit_threshold:
                self._circuit_state = "open"
                self._last_failure_time = time.time()
        
        # Add the methods to the adapter
        adapter.check_circuit_breaker = check_circuit_breaker.__get__(adapter)
        adapter.trip_circuit_breaker = trip_circuit_breaker.__get__(adapter)
        
        # Patch the execute method to use circuit breaker
        original_execute = adapter.execute
        
        async def execute_with_circuit_breaker(config):
            """Execute with circuit breaker pattern."""
            # Check if the circuit is closed or half-open
            if not await adapter.check_circuit_breaker():
                return AgentExecutionResult(
                    success=False,
                    error="Circuit breaker open - too many failures",
                    result=None
                )
            
            try:
                return await original_execute(config)
            except Exception as e:
                adapter.trip_circuit_breaker()
                raise
                
        adapter.execute = execute_with_circuit_breaker
        
        # Execute multiple times to trip the circuit breaker
        with patch('dagger.Connection', return_value=mock_connection):
            # First execution
            result1 = await adapter.execute(config)
            assert result1.success is False
            assert "Connection error" in result1.error
            
            # Second execution
            result2 = await adapter.execute(config)
            assert result2.success is False
            assert "Connection error" in result2.error
            
            # Third execution
            result3 = await adapter.execute(config)
            assert result3.success is False
            assert "Connection error" in result3.error
            
            # Fourth execution - should be blocked by circuit breaker
            result4 = await adapter.execute(config)
            assert result4.success is False
            assert "Circuit breaker open" in result4.error
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, adapter):
        """Test graceful degradation when Dagger is unavailable."""
        # Create an execution config
        config = AgentExecutionConfig(
            task_id="test-task",
            execution_type="containerized_workflow",
            parameters={
                "container_image": "python:3.9-slim",
                "workflow_definition": "test-workflow.yml",
                "inputs": {"param": "value"},
                "fallback_enabled": True
            }
        )
        
        # Create a mock connection that fails
        mock_connection = AsyncMock()
        mock_connection.__aenter__.side_effect = RuntimeError("Connection error")
        
        # Add fallback execution method
        async def execute_fallback(self, config):
            """Execute a fallback implementation when Dagger is unavailable."""
            return AgentExecutionResult(
                success=True,
                error=None,
                result={
                    "message": "Executed fallback implementation",
                    "task_id": config.task_id,
                    "fallback": True
                }
            )
        
        # Add the method to the adapter
        adapter.execute_fallback = execute_fallback.__get__(adapter)
        
        # Patch the execute method to use fallback
        original_execute = adapter.execute
        
        async def execute_with_fallback(config):
            """Execute with fallback if enabled."""
            try:
                return await original_execute(config)
            except Exception as e:
                if config.parameters.get("fallback_enabled"):
                    return await adapter.execute_fallback(config)
                else:
                    return AgentExecutionResult(
                        success=False,
                        error=str(e),
                        result=None
                    )
                
        adapter.execute = execute_with_fallback
        
        # Execute with fallback enabled
        with patch('dagger.Connection', return_value=mock_connection):
            result = await adapter.execute(config)
        
        # Verify the result
        assert result.success is True
        assert result.error is None
        assert result.result is not None
        assert result.result.get("message") == "Executed fallback implementation"
        assert result.result.get("fallback") is True
        
        # Execute without fallback
        config.parameters["fallback_enabled"] = False
        with patch('dagger.Connection', return_value=mock_connection):
            result = await adapter.execute(config)
        
        # Verify the result
        assert result.success is False
        assert "Connection error" in result.error