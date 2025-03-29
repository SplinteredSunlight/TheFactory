#!/bin/bash

# Script to run the agent communication circuit breaker integration tests

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

# Run the tests
echo "Running agent communication circuit breaker integration tests..."
pytest tests/test_agent_communication_circuit_breaker.py -v

# Check the test result
if [ $? -eq 0 ]; then
    echo "All tests passed successfully!"
else
    echo "Some tests failed. Please check the output above for details."
    exit 1
fi

# Deactivate the virtual environment
deactivate

echo "Test run completed."
