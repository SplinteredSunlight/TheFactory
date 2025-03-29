#!/bin/bash
# Script to copy all legacy task manager files to the archive

# Paths
SOURCE_DIR="/Users/dc/Projects/AI-Orchestration-Platform/.task-manager"
TARGET_DIR="/Users/dc/Projects/AI-Orchestration-Platform/archive/legacy_task_manager"
BACKUP_SOURCE_DIR="/Users/dc/Projects/AI-Orchestration-Platform/.task-manager-backup"
BACKUP_TARGET_DIR="/Users/dc/Projects/AI-Orchestration-Platform/archive/legacy_task_manager/backup"

# Copy all files from the main task manager
find "$SOURCE_DIR" -type f -not -path "*/\.*" -exec cp {} "$TARGET_DIR/" \;

# Copy all files from the backup task manager
find "$BACKUP_SOURCE_DIR" -type f -not -path "*/\.*" -exec cp {} "$BACKUP_TARGET_DIR/" \;

# Copy the documentation directory structure
cp -r "$SOURCE_DIR/docs" "$TARGET_DIR/"

# Copy the task manager README
cp "/Users/dc/Projects/AI-Orchestration-Platform/README-task-manager.md" "$TARGET_DIR/"

echo "Legacy task manager files copied to archive"
