#!/bin/bash

# Script to migrate tasks from the old system to the new task management system

echo "Starting task migration..."

# Make sure the script is executable
chmod +x src/task_manager/migrate_tasks.py

# Run the migration script
python3 -m src.task_manager.migrate_tasks

echo "Migration complete!"
echo "You can now use the new task management system to manage your tasks."
echo "To view the project progress, check the Dashboard in the UI."
