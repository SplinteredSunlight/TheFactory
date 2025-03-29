#!/bin/bash
# Run the circuit breaker Dagger example

# Set up the environment
set -e
cd "$(dirname "$0")/../.."
PROJECT_ROOT=$(pwd)

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if the example file exists
EXAMPLE_FILE="examples/dagger/circuit_breaker_dagger_example.py"
if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "Error: Example file not found: $EXAMPLE_FILE"
    exit 1
fi

# Make the example file executable
chmod +x "$EXAMPLE_FILE"

# Run the example
echo "Running Dagger circuit breaker example..."
echo "----------------------------------------"
python3 "$EXAMPLE_FILE"

# Check if the example ran successfully
if [ $? -eq 0 ]; then
    echo "----------------------------------------"
    echo "Circuit breaker example completed successfully!"
    echo ""
    echo "This example demonstrates how the circuit breaker pattern can be used with Dagger"
    echo "to prevent cascading failures in a distributed system."
    echo ""
    echo "Key benefits of the circuit breaker pattern:"
    echo "1. Prevents system overload during failures"
    echo "2. Allows for graceful degradation of service"
    echo "3. Provides automatic recovery when the system stabilizes"
    echo "4. Improves overall system resilience"
    echo ""
    echo "The example shows the difference between using and not using the circuit breaker pattern"
    echo "when a service is experiencing failures. With the circuit breaker, requests are blocked"
    echo "after a certain number of failures, preventing further load on the failing service."
    echo "Without the circuit breaker, requests continue to be sent to the failing service,"
    echo "potentially causing cascading failures throughout the system."
else
    echo "----------------------------------------"
    echo "Error: Circuit breaker example failed."
    exit 1
fi
