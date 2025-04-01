#!/bin/bash

SOURCE="/mnt/data/TheFactory"
TARGET="$HOME/Projects/TheFactory"

echo "🔄 Syncing cleaned project structure to $TARGET..."

# Remove known legacy artifacts from local project
rm -rf \
  "$TARGET/ai_orchestration_platform.egg-info" \
  "$TARGET/task_manager_cleanup.log" \
  "$TARGET/task_migration.log" \
  "$TARGET/archive" \
  "$TARGET/dashboard" \
  "$TARGET/project_master_dashboard" \
  "$TARGET/node_modules" \
  "$TARGET/package.json" \
  "$TARGET/package-lock.json" \
  "$TARGET/.DS_Store"

# Copy over cleaned directory content (excluding .venv or untracked content)
rsync -av --exclude='.venv' "$SOURCE/" "$TARGET/"

echo "✅ Sync complete. Your local project is now clean and Poetry-ready."
