# Dagger Gap Analysis Test Plan

This document outlines the testing strategy for the components being implemented to address the functionality gaps between the current AI-Orchestration-Platform and Dagger.

## 1. Testing Objectives

The primary objectives of this test plan are to:

1. Verify that all gap mitigation components function as expected
2. Ensure compatibility with the existing system
3. Validate that the system meets performance requirements
4. Confirm that the system is secure and reliable
5. Verify that the system can handle error conditions gracefully

## 2. Test Environments

### 2.1 Development Environment

- Local development machines
- Docker containers for isolated testing
- Mock Dagger server for unit testing

### 2.2 Integration Environment

- Shared development environment
- Integration with actual Dagger instances
- Simulated agent interactions

### 2.3 Staging Environment

- Production-like environment
- Full integration with all components
- Performance testing environment

## 3. Test Types

### 3.1 Unit Testing

Unit tests will be written for all new components to verify their individual functionality.

| Component | Test Focus | Test Tools |
|-----------|------------|------------|
| Circuit Breaker | State transitions, failure counting, timeout behavior | pytest, unittest.mock |
| Error Classification | Error mapping, custom error types | pytest, unittest.mock |
| Retry Handler | Retry logic, backoff calculation, max retries | pytest, unittest.mock |
| MCP Integration | Resource handling, tool execution | pytest, unittest.mock |
| Task Manager Integration | Task-to-workflow mapping, execution flow | pytest, unittest.mock |
| Agent Communication | Message passing, registration | pytest, unittest.mock |
| Agent Discovery | Registration, discovery mechanisms | pytest, unittest.mock |
| Capabilities Registry | Registration, capability lookup | pytest, unittest.mock |
| Dashboard Components | Rendering, data fetching | Jest, React Testing Library |
| Progress Tracking | Progress calculation, status updates | pytest, unittest.mock |
| Access Control | Permission checking, role assignment | pytest, unittest.mock |
| Token Management | Token generation, validation | pytest, unittest.mock |

### 3.2 Integration Testing

Integration tests will verify that the components work together correctly.

| Integration Point | Test Focus | Test Tools |
|-------------------|------------|------------|
| Circuit Breaker + Retry Handler | Combined error handling | pytest, integration fixtures |
| MCP + Task Manager | End-to-end workflow execution | pytest, integration fixtures |
| Agent Communication + Discovery | Agent registration and communication | pytest, integration fixtures |
| Dashboard + Monitoring | Metrics collection and visualization | Cypress, integration fixtures |
| Access Control + API | Authentication and authorization | pytest, integration fixtures |

### 3.3 System Testing

System tests will verify that the entire system functions correctly.

| System Aspect | Test Focus | Test Tools |
|---------------|------------|------------|
| Workflow Execution | End-to-end workflow execution | pytest, system fixtures |
| Error Handling | System-wide error handling | pytest, system fixtures |
| Agent Interaction | Multi-agent interactions | pytest, system fixtures |
| User Interface | Dashboard functionality | Cypress, Selenium |
| API | External API functionality | pytest, requests |

### 3.4 Performance Testing

Performance tests will verify that the system meets performance requirements.

| Performance Aspect | Test Focus | Test Tools |
|-------------------|------------|------------|
| Workflow Execution | Execution time, resource usage | locust, custom benchmarks |
| Concurrency | Multiple simultaneous workflows | locust, custom benchmarks |
| Scalability | Performance under load | locust, custom benchmarks |
| Caching | Cache hit rate, performance improvement | custom benchmarks |

### 3.5 Security Testing

Security tests will verify that the system is secure.

| Security Aspect | Test Focus | Test Tools |
|-----------------|------------|------------|
| Authentication | Token validation, session management | OWASP ZAP, custom tests |
| Authorization | Permission checking | custom tests |
| Data Protection | Sensitive data handling | custom tests |
| API Security | Input validation, output sanitization | OWASP ZAP, custom tests |

## 4. Test Cases

### 4.1 Circuit Breaker Tests

1. **Test Initial State**
   - Verify that the circuit breaker starts in the closed state
   - Verify that requests are allowed in the closed state

2. **Test Failure Threshold**
   - Verify that the circuit breaker transitions to the open state after reaching the failure threshold
   - Verify that requests are rejected in the open state

3. **Test Reset Timeout**
   - Verify that the circuit breaker transitions to the half-open state after the reset timeout
   - Verify that a single request is allowed in the half-open state

4. **Test Success in Half-Open State**
   - Verify that a successful request in the half-open state transitions the circuit breaker to the closed state
   - Verify that the failure count is reset after transitioning to the closed state

5. **Test Failure in Half-Open State**
   - Verify that a failed request in the half-open state transitions the circuit breaker back to the open state
   - Verify that the reset timeout is restarted after transitioning back to the open state

### 4.2 Error Classification Tests

1. **Test Error Mapping**
   - Verify that Dagger errors are correctly mapped to custom error types
   - Verify that unknown errors are passed through unchanged

2. **Test Error Hierarchy**
   - Verify that custom error types maintain the correct inheritance hierarchy
   - Verify that error types can be correctly identified using isinstance()

3. **Test Error Attributes**
   - Verify that custom error types preserve the original error message
   - Verify that custom error types add additional context information

### 4.3 Retry Handler Tests

1. **Test Retry Logic**
   - Verify that the retry handler attempts the operation the specified number of times
   - Verify that the retry handler stops retrying after a successful operation

2. **Test Backoff Calculation**
   - Verify that the backoff time increases exponentially with each retry
   - Verify that the backoff time includes the specified jitter

3. **Test Max Retries**
   - Verify that the retry handler stops after reaching the maximum number of retries
   - Verify that the original error is raised after exhausting all retries

4. **Test Retry Filtering**
   - Verify that the retry handler only retries operations with retryable errors
   - Verify that non-retryable errors are raised immediately

### 4.4 MCP Integration Tests

1. **Test Resource Listing**
   - Verify that the MCP server correctly lists available resources
   - Verify that resource templates are correctly listed

2. **Test Resource Reading**
   - Verify that resources can be read correctly
   - Verify that resource templates are correctly expanded

3. **Test Tool Listing**
   - Verify that the MCP server correctly lists available tools
   - Verify that tool schemas are correctly defined

4. **Test Tool Execution**
   - Verify that tools can be executed correctly
   - Verify that tool results are correctly returned

### 4.5 Task Manager Integration Tests

1. **Test Workflow Creation**
   - Verify that workflows can be created from tasks
   - Verify that task parameters are correctly mapped to workflow parameters

2. **Test Workflow Execution**
   - Verify that workflows can be executed correctly
   - Verify that workflow results are correctly mapped to task results

3. **Test Status Updates**
   - Verify that task status is updated during workflow execution
   - Verify that task errors are correctly recorded

4. **Test Error Handling**
   - Verify that workflow errors are correctly handled
   - Verify that the circuit breaker and retry handler are correctly integrated

### 4.6 Agent Communication Tests

1. **Test Agent Registration**
   - Verify that agents can register with the communication manager
   - Verify that registered agents can be unregistered

2. **Test Message Sending**
   - Verify that messages can be sent between agents
   - Verify that messages are correctly queued for offline agents

3. **Test Message Receiving**
   - Verify that agents can receive messages
   - Verify that messages are correctly ordered

4. **Test Error Handling**
   - Verify that communication errors are correctly handled
   - Verify that the system is resilient to agent failures

### 4.7 Dashboard Tests

1. **Test Rendering**
   - Verify that the dashboard components render correctly
   - Verify that the dashboard is responsive

2. **Test Data Fetching**
   - Verify that the dashboard correctly fetches data from the API
   - Verify that the dashboard handles loading and error states

3. **Test Interactivity**
   - Verify that the dashboard responds to user interactions
   - Verify that the dashboard updates in real-time

4. **Test Filtering and Sorting**
   - Verify that the dashboard supports filtering and sorting
   - Verify that filters and sorts are correctly applied

## 5. Test Data

### 5.1 Mock Data

- Mock Dagger client for unit testing
- Mock agent implementations for communication testing
- Mock workflow definitions for task manager testing
- Mock metrics data for dashboard testing

### 5.2 Test Fixtures

- Predefined circuit breaker states for testing state transitions
- Predefined error scenarios for testing error handling
- Predefined task definitions for testing task manager integration
- Predefined agent configurations for testing agent discovery

### 5.3 Test Users

- Admin user for testing administrative functions
- Regular user for testing standard functions
- Guest user for testing limited access

## 6. Test Execution

### 6.1 Test Schedule

| Phase | Test Types | Duration | Environment |
|-------|------------|----------|-------------|
| Phase 1 | Unit Tests | Continuous | Development |
| Phase 1 | Integration Tests | Weekly | Integration |
| Phase 2 | System Tests | Bi-weekly | Staging |
| Phase 2 | Performance Tests | Monthly | Staging |
| Phase 3 | Security Tests | Monthly | Staging |

### 6.2 Test Dependencies

- Unit tests must pass before integration tests
- Integration tests must pass before system tests
- System tests must pass before performance and security tests

### 6.3 Test Reporting

- Test results will be reported in CI/CD pipeline
- Test coverage reports will be generated
- Test failures will trigger notifications

## 7. Test Automation

### 7.1 CI/CD Integration

- Unit tests will run on every commit
- Integration tests will run on pull requests
- System, performance, and security tests will run on merges to main branch

### 7.2 Test Scripts

- Automated test scripts will be created for all test cases
- Test scripts will be maintained in the tests directory
- Test scripts will be versioned alongside the code

### 7.3 Test Data Generation

- Test data will be generated automatically where possible
- Test fixtures will be created for complex test scenarios
- Test data will be reset between test runs

## 8. Test Deliverables

### 8.1 Test Plan

- This document

### 8.2 Test Cases

- Detailed test cases for each component
- Test case documentation in code

### 8.3 Test Scripts

- Automated test scripts for all test cases
- Test fixtures and mock implementations

### 8.4 Test Reports

- Test execution reports
- Test coverage reports
- Performance test reports
- Security test reports

## 9. Test Exit Criteria

### 9.1 Unit Test Criteria

- 90% code coverage for all new components
- All unit tests passing

### 9.2 Integration Test Criteria

- All integration tests passing
- No critical or high-severity issues

### 9.3 System Test Criteria

- All system tests passing
- No critical or high-severity issues
- Performance requirements met

### 9.4 Performance Test Criteria

- Response time within acceptable limits
- Resource usage within acceptable limits
- Scalability requirements met

### 9.5 Security Test Criteria

- No critical or high-severity security issues
- All security requirements met

## 10. Test Implementation Examples

### 10.1 Circuit Breaker Tests

```python
import pytest
import time
from unittest.mock import patch
from src.error_handling.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

def test_initial_state():
    cb = CircuitBreaker()
    assert cb.state == "closed"
    assert cb.allow_request() is True

def test_failure_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == "closed"
    
    cb.record_failure()
    assert cb.state == "closed"
    
    cb.record_failure()
    assert cb.state == "closed"
    
    cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False

def test_reset_timeout():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
    cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False
    
    time.sleep(0.2)
    assert cb.allow_request() is True
    assert cb.state == "half-open"

def test_success_in_half_open():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
    cb.record_failure()
    assert cb.state == "open"
    
    time.sleep(0.2)
    assert cb.allow_request() is True
    assert cb.state == "half-open"
    
    cb.record_success()
    assert cb.state == "closed"
    assert cb.failure_count == 0

def test_failure_in_half_open():
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
    cb.record_failure()
    assert cb.state == "open"
    
    time.sleep(0.2)
    assert cb.allow_request() is True
    assert cb.state == "half-open"
    
    cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False

async def test_execute_with_circuit_breaker():
    from src.error_handling.circuit_breaker import execute_with_circuit_breaker
    
    cb = CircuitBreaker()
    
    # Test successful execution
    result = await execute_with_circuit_breaker(cb, lambda: "success")
    assert result == "success"
    
    # Test failed execution
    with pytest.raises(ValueError):
        await execute_with_circuit_breaker(cb, lambda: (_ for _ in ()).throw(ValueError("test error")))
    
    # Test circuit open
    cb.state = "open"
    with pytest.raises(CircuitBreakerOpenError):
        await execute_with_circuit_breaker(cb, lambda: "success")
```

### 10.2 Retry Handler Tests

```python
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.error_handling.retry_handler import RetryHandler
from src.error_handling.errors import DaggerConnectionError, DaggerTimeoutError

def test_should_retry():
    handler = RetryHandler(max_retries=3)
    
    # Test retryable errors
    assert handler.should_retry(DaggerConnectionError("test"), 0) is True
    assert handler.should_retry(DaggerTimeoutError("test"), 0) is True
    
    # Test non-retryable errors
    assert handler.should_retry(ValueError("test"), 0) is False
    
    # Test max retries
    assert handler.should_retry(DaggerConnectionError("test"), 3) is False

def test_get_backoff_time():
    handler = RetryHandler(initial_backoff=1.0, max_backoff=60.0, jitter=0.1)
    
    # Test initial backoff
    backoff = handler.get_backoff_time(0)
    assert 0.9 <= backoff <= 1.1
    
    # Test exponential backoff
    backoff = handler.get_backoff_time(1)
    assert 1.8 <= backoff <= 2.2
    
    # Test max backoff
    backoff = handler.get_backoff_time(10)
    assert 54.0 <= backoff <= 66.0

async def test_execute_success():
    handler = RetryHandler()
    
    # Test successful execution
    result = await handler.execute(lambda: "success")
    assert result == "success"

async def test_execute_retry_success():
    handler = RetryHandler(max_retries=3)
    
    # Mock function that fails twice then succeeds
    mock_func = MagicMock()
    mock_func.side_effect = [
        DaggerConnectionError("test"),
        DaggerConnectionError("test"),
        "success"
    ]
    
    with patch("asyncio.sleep") as mock_sleep:
        result = await handler.execute(lambda: mock_func())
    
    assert result == "success"
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2

async def test_execute_retry_failure():
    handler = RetryHandler(max_retries=3)
    
    # Mock function that always fails
    mock_func = MagicMock()
    mock_func.side_effect = DaggerConnectionError("test")
    
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(DaggerConnectionError):
            await handler.execute(lambda: mock_func())
    
    assert mock_func.call_count == 4  # Initial + 3 retries
    assert mock_sleep.call_count == 3
```

### 10.3 MCP Integration Tests

```python
import pytest
from unittest.mock import MagicMock, patch
from src.task_manager.mcp_servers.dagger_workflow_integration import DaggerWorkflowIntegration
from mcp.types import ListResourcesRequestSchema, ListToolsRequestSchema, CallToolRequestSchema

@pytest.fixture
def mock_server():
    server = MagicMock()
    server.setRequestHandler = MagicMock()
    return server

@pytest.fixture
def mock_task_manager():
    task_manager = MagicMock()
    return task_manager

@pytest.fixture
def integration(mock_server, mock_task_manager):
    return DaggerWorkflowIntegration(
        server=mock_server,
        task_manager=mock_task_manager,
        dagger_config_path="config/dagger.yaml",
        templates_dir="templates"
    )

def test_setup_resources(integration, mock_server):
    # Verify that resource handlers are set up
    assert mock_server.setRequestHandler.call_count >= 3
    
    # Verify that ListResourcesRequestSchema handler is set up
    mock_server.setRequestHandler.assert_any_call(
        ListResourcesRequestSchema,
        integration.handle_list_resources
    )

def test_setup_tools(integration, mock_server):
    # Verify that tool handlers are set up
    assert mock_server.setRequestHandler.call_count >= 2
    
    # Verify that ListToolsRequestSchema handler is set up
    mock_server.setRequestHandler.assert_any_call(
        ListToolsRequestSchema,
        integration.handle_list_tools
    )
    
    # Verify that CallToolRequestSchema handler is set up
    mock_server.setRequestHandler.assert_any_call(
        CallToolRequestSchema,
        integration.handle_call_tool
    )

async def test_handle_list_resources(integration):
    # Mock the request
    request = MagicMock()
    
    # Call the handler
    response = await integration.handle_list_resources(request)
    
    # Verify the response
    assert "resources" in response
    assert isinstance(response["resources"], list)

async def test_handle_list_tools(integration):
    # Mock the request
    request = MagicMock()
    
    # Call the handler
    response = await integration.handle_list_tools(request)
    
    # Verify the response
    assert "tools" in response
    assert isinstance(response["tools"], list)

async def test_handle_call_tool(integration, mock_task_manager):
    # Mock the request
    request = MagicMock()
    request.params = {
        "name": "execute_workflow",
        "arguments": {
            "workflow_id": "test-workflow",
            "inputs": {"param1": "value1"}
        }
    }
    
    # Mock the task manager
    mock_task_manager.get_workflow.return_value = {"id": "test-workflow"}
    mock_task_manager.execute_workflow.return_value = {"result": "success"}
    
    # Call the handler
    response = await integration.handle_call_tool(request)
    
    # Verify the response
    assert "content" in response
    assert isinstance(response["content"], list)
    assert len(response["content"]) > 0
    assert response["content"][0]["type"] == "text"
```

### 10.4 Dashboard Tests

```typescript
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { DaggerDashboard } from '../components/dashboard/DaggerDashboard';
import { fetchDaggerMetrics } from '../../services/api';

// Mock the API service
jest.mock('../../services/api');

describe('DaggerDashboard', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    // Mock the API response
    (fetchDaggerMetrics as jest.Mock).mockResolvedValue({});

    // Render the component
    render(<DaggerDashboard />);

    // Check that loading state is shown
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  test('renders dashboard with data', async () => {
    // Mock the API response
    const mockData = {
      workflows: [
        { id: 'workflow1', status: 'completed' },
        { id: 'workflow2', status: 'running' }
      ],
      agents: [
        { id: 'agent1', status: 'online' },
        { id: 'agent2', status: 'offline' }
      ],
      execution: [
        { timestamp: '2025-03-01', count: 10 },
        { timestamp: '2025-03-02', count: 15 }
      ]
    };
    (fetchDaggerMetrics as jest.Mock).mockResolvedValue(mockData);

    // Render the component
    render(<DaggerDashboard />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Dagger Workflow Dashboard')).toBeInTheDocument();
    });

    // Check that dashboard sections are shown
    expect(screen.getByText('Workflow Status')).toBeInTheDocument();
    expect(screen.getByText('Agent Performance')).toBeInTheDocument();
    expect(screen.getByText('Execution Metrics')).toBeInTheDocument();
  });

  test('renders error state', async () => {
    // Mock the API error
    (fetchDaggerMetrics as jest.Mock).mockRejectedValue(new Error('API error'));

    // Render the component
    render(<DaggerDashboard />);

    // Wait for error to be shown
    await waitFor(() => {
      expect(screen.getByText('Error: Failed to fetch metrics')).toBeInTheDocument();
    });
  });

  test('refreshes data on interval', async () => {
    // Mock the API response
    (fetchDaggerMetrics as jest.Mock).mockResolvedValue({});

    // Mock timer
    jest.useFakeTimers();

    // Render the component with short refresh interval
    render(<DaggerDashboard refreshInterval={1000} />);

    // Wait for initial data load
    await waitFor(() => {
      expect(fetchDaggerMetrics).toHaveBeenCalledTimes(1);
    });

    // Advance timer
    jest.advanceTimersByTime(1000);

    // Check that API was called again
    await waitFor(() => {
      expect(fetchDaggerMetrics).toHaveBeenCalledTimes(2);
    });

    // Clean up
    jest.useRealTimers();
  });
});
