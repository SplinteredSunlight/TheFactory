# Integration Testing Framework for AI-Orchestration-Platform

This directory contains the Integration Testing Framework for the AI-Orchestration-Platform, focusing on the integration between AI-Orchestrator and Fast-Agent components.

## Overview

The Integration Testing Framework provides a structured approach to testing the integration between AI-Orchestrator and Fast-Agent. It includes:

- API endpoint and data format documentation
- Test scenarios and workflows
- Mock data and fixtures
- Validation criteria and assertions
- Utility functions for test setup and teardown

## Directory Structure

```
tests/
├── README.md                      # This file
├── conftest.py                    # Pytest configuration and fixtures
├── integration_test_config.py     # Test configuration
├── integration_test_utils.py      # Utility functions for tests
├── test_integration_framework.py  # Integration tests
└── ...                            # Other test files
```

## Key Components

### Documentation

- `docs/integration-testing-framework.md`: Comprehensive documentation of API endpoints, data formats, and test scenarios

### Test Configuration

- `integration_test_config.py`: Configuration options for the integration tests, including test environment, authentication, agent and task data, and error test configuration

### Test Utilities

- `integration_test_utils.py`: Utility functions for integration testing, including the `IntegrationTestEnvironment` class for managing the test environment, and helper functions for retries and waiting for conditions

### Pytest Configuration

- `conftest.py`: Pytest fixtures and configuration for integration tests, including fixtures for the test environment, agents, tasks, and utility functions

### Integration Tests

- `test_integration_framework.py`: Integration tests for the AI-Orchestration-Platform, focusing on authentication, agent management, task management, and error handling

## Running the Tests

### Prerequisites

- Python 3.8 or higher
- Pytest and pytest-asyncio
- AI-Orchestration-Platform dependencies

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Install the package in development mode:

```bash
pip install -e .
```

### Running All Integration Tests

```bash
pytest tests/test_integration_framework.py -v
```

### Running Specific Test Categories

You can use pytest markers to run specific categories of tests:

```bash
# Run authentication tests
pytest tests/test_integration_framework.py -v -m auth

# Run agent management tests
pytest tests/test_integration_framework.py -v -m agent

# Run task management tests
pytest tests/test_integration_framework.py -v -m task

# Run error handling tests
pytest tests/test_integration_framework.py -v -m error

# Run MCP server tests
pytest tests/test_integration_framework.py -v -m mcp
```

## Extending the Framework

### Adding New Test Scenarios

1. Define the test scenario in `docs/integration-testing-framework.md`
2. Add any necessary configuration in `integration_test_config.py`
3. Implement the test in `test_integration_framework.py` or create a new test file
4. Add any necessary fixtures in `conftest.py`

### Adding New API Endpoints

1. Document the new API endpoint in `docs/integration-testing-framework.md`
2. Update the test configuration in `integration_test_config.py` if necessary
3. Implement tests for the new endpoint

### Adding New Test Utilities

1. Add the new utility function to `integration_test_utils.py`
2. Add a fixture for the utility function in `conftest.py` if needed

## Best Practices

1. **Isolation**: Each test should be isolated and not depend on the state of other tests
2. **Cleanup**: Always clean up resources created during tests
3. **Retries**: Use the retry utility for operations that may fail transiently
4. **Waiting**: Use the wait_for_condition utility for operations that may take time to complete
5. **Logging**: Use the logger to log test actions and results
6. **Assertions**: Use pytest assertions to verify test results
7. **Fixtures**: Use fixtures to set up and tear down test environments
8. **Markers**: Use markers to categorize tests

## Troubleshooting

### Common Issues

1. **MCP Server Not Starting**: Check that the MCP server path in `integration_test_config.py` is correct
2. **Authentication Failures**: Check that the API key in `integration_test_config.py` is correct
3. **Test Timeouts**: Increase the test timeout in `integration_test_config.py`
4. **Resource Cleanup Failures**: Check the test logs for errors during resource cleanup

### Debugging

1. Enable debug logging:

```bash
pytest tests/test_integration_framework.py -v --log-cli-level=DEBUG
```

2. Use the `--pdb` option to drop into the debugger on test failures:

```bash
pytest tests/test_integration_framework.py -v --pdb
```

3. Use the `--trace` option to drop into the debugger at the start of each test:

```bash
pytest tests/test_integration_framework.py -v --trace
```

## Contributing

1. Follow the project's coding style and conventions
2. Write tests for new features
3. Update documentation for new features
4. Run the tests before submitting a pull request
5. Include a description of the changes in the pull request
