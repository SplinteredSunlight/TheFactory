# Mock Modules

This directory contains mock implementations of various modules and dependencies used in the AI Orchestration Platform. These mocks are used in tests to simulate the behavior of external systems and dependencies without requiring the actual systems to be available.

## Purpose

The mock modules serve several purposes:

1. **Isolation**: They allow tests to run in isolation without external dependencies
2. **Speed**: They make tests faster by avoiding network calls and external processing
3. **Determinism**: They provide consistent, predictable behavior for testing
4. **Control**: They allow tests to simulate specific scenarios, including error conditions

## Available Mocks

The following mock modules are available:

- **dagger/**: Mock implementation of the Dagger API
- **mcp/**: Mock implementation of the Model Context Protocol
- **mcp_agent/**: Mock implementation of MCP agents
- **pydagger/**: Mock implementation of the PyDagger library
- **src/**: Mock implementations of internal modules

## Using Mocks in Tests

To use these mocks in your tests, you can use Python's module import system with monkeypatching or dependency injection. For example:

```python
# Using pytest's monkeypatch fixture
def test_with_mock_dagger(monkeypatch):
    import mock_modules.dagger as mock_dagger
    monkeypatch.setattr('your_module.dagger', mock_dagger)
    
    # Your test code here
```

Or with dependency injection:

```python
from mock_modules.dagger import MockDaggerClient

def test_with_mock_dagger():
    client = MockDaggerClient()
    your_function_under_test(dagger_client=client)
