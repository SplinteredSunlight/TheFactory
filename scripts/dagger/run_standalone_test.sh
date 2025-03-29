#!/bin/bash
# Script to run the standalone workflow templates test

# Make the script executable
chmod +x test_workflow_templates_standalone.py

# Run the test
./test_workflow_templates_standalone.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Standalone workflow templates test passed!"
else
    echo "Standalone workflow templates test failed!"
fi
