#!/bin/bash
# Script to run the workflow templates test

# Set up the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/mock_modules

# Run the test
python3 tests/test_workflow_templates.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Workflow templates test passed!"
else
    echo "Workflow templates test failed!"
fi
