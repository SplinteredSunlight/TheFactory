#!/bin/bash
# Script to run tests for the Dagger Workflow Integration

set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Set up Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the Dagger Workflow Integration tests
echo "Running Dagger Workflow Integration tests..."
python3 tests/test_dagger_workflow_integration.py

# Run the Workflow Templates tests
echo "Running Workflow Templates tests..."
python3 tests/test_workflow_templates.py

# Run the verification script with mock Dagger
echo "Running verification with mock Dagger..."
python3 scripts/dagger/verify_dagger_workflow_with_mock.py

echo "All tests completed successfully!"
