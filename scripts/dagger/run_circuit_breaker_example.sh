#!/bin/bash
# Run the Circuit Breaker example with Dagger

set -e

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Ensure the virtual environment is activated if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if the example file exists
if [ ! -f "examples/dagger/circuit_breaker_example.py" ]; then
    echo "Error: Circuit Breaker example file not found"
    exit 1
fi

echo "Running Circuit Breaker example..."
echo "=================================="

# Run the example
python3 -m examples.dagger.circuit_breaker_example

echo "=================================="
echo "Circuit Breaker example completed"
