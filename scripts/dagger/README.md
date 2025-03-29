# Dagger Scripts

This directory contains scripts and utilities for working with Dagger integration in the AI-Orchestration-Platform.

## Scripts

### Testing Scripts

- **run_dagger_tests.sh**: Runs all Dagger-related tests in the project.
- **run_standalone_test.sh**: Runs standalone Dagger tests without requiring the full platform.
- **run_workflow_templates_test.sh**: Runs tests for the workflow templates functionality.
- **test_dagger_workflow_integration_fix.py**: Test script for fixing Dagger workflow integration issues.
- **test_workflow_templates_standalone.py**: Standalone test for workflow templates.

### Verification Scripts

- **run_dagger_verification.sh**: Verifies the Dagger integration is working correctly.
- **run_dagger_verification_with_mock.sh**: Verifies the Dagger integration using mock implementations.
- **verify_dagger_workflow_integration.py**: Python script to verify Dagger workflow integration.
- **verify_dagger_workflow_with_mock.py**: Python script to verify Dagger workflow integration using mocks.

### Example Scripts

- **run_dagger_workflow_example.sh**: Runs an example Dagger workflow.
- **standalone_dagger_test.py**: Standalone test script for Dagger functionality.

### Task Completion Scripts

- **complete_dagger_workflow_integration_task.sh**: Script to complete the Dagger workflow integration task.

## Usage

Most scripts can be run directly from the command line. For example:

```bash
./scripts/dagger/run_dagger_tests.sh
```

For more detailed information about Dagger integration, see the [Dagger Integration Documentation](../../docs/DAGGER_INTEGRATION.md).
