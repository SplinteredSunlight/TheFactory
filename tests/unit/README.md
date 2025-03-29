# Unit Tests

This directory contains unit tests for the AI Orchestration Platform. Unit tests focus on testing individual components in isolation, without dependencies on external systems or services.

## Running Unit Tests

To run all unit tests:

```bash
pytest tests/unit
```

To run a specific unit test:

```bash
pytest tests/unit/test_file_name.py
```

## Test Organization

Unit tests are organized by component, with each test file corresponding to a specific component or module in the system. For example, `test_agent_discovery.py` tests the functionality in `src/orchestrator/agent_discovery.py`.

## Writing Unit Tests

When writing unit tests:

1. Focus on testing a single component in isolation
2. Use mocks or stubs for dependencies
3. Test both success and failure cases
4. Keep tests fast and independent
