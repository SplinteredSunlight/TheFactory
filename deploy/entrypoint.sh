#!/bin/bash
set -e

# Create the required directories if they don't exist
mkdir -p /app/workflows
mkdir -p /app/logs

# Wait for dependencies
echo "Waiting for dependencies..."
python /app/deploy/wait_for_dependencies.py

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Initialize the Dagger configuration
echo "Initializing Dagger configuration..."
python /app/deploy/init_dagger_config.py

# Start the application
echo "Starting the application..."
exec "$@"