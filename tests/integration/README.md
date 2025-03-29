# Integration Tests

This directory contains integration tests for the AI Orchestration Platform. Integration tests focus on testing the interaction between multiple components or systems.

## Running Integration Tests

To run all integration tests:

```bash
pytest tests/integration
```

To run a specific integration test:

```bash
pytest tests/integration/test_file_name.py
```

## Test Organization

Integration tests are organized by feature or system interaction. For example, `test_dagger_workflow_integration.py` tests the integration between the Task Manager and Dagger workflow execution.

## Writing Integration Tests

When writing integration tests:

1. Focus on testing the interaction between components
2. Test end-to-end workflows
3. Verify that data flows correctly between components
4. Test error handling and recovery across component boundaries
5. Use realistic test data and scenarios
