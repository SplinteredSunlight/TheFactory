#!/bin/bash

# Script to run the agent communication circuit breaker example

# Set the working directory to the project root
cd "$(dirname "$0")/.." || exit

# Set up the Python environment
echo "Setting up Python environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    pip install -e .
fi

# Run the example
echo "Running agent communication circuit breaker example..."
python examples/agent_communication_circuit_breaker_example.py

# Check the result
if [ $? -eq 0 ]; then
    echo "Example ran successfully!"
else
    echo "Example failed. Please check the output above for details."
    exit 1
fi

# Deactivate the virtual environment
deactivate

echo "Example run completed."
