#!/bin/bash
# Script to run the Dagger workflow integration example

# Set up the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/mock_modules

# Create templates directory if it doesn't exist
mkdir -p config/templates

# Make the example script executable
chmod +x src/task_manager/mcp_servers/dagger_workflow_example.py

# Run the example
echo "Running Dagger workflow integration example..."
src/task_manager/mcp_servers/dagger_workflow_example.py --task example_task_$(date +%Y%m%d%H%M%S) --param input_file=example.csv --param threshold=0.75

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Dagger workflow integration example completed successfully!"
else
    echo "Dagger workflow integration example failed!"
fi
