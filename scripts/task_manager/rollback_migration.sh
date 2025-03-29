#!/bin/bash
# Migration Rollback Script
# This script rolls back the migration from the legacy task management system
# to the new Dagger-based Task Management System in case of issues.

set -e  # Exit on error

# Default paths
LEGACY_DATA_PATH="./data/legacy"
NEW_DATA_PATH="./data/new"
BACKUP_PATH="./data/backup"
ID_MAPPING_PATH="./data/id_mapping.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --legacy-data)
      LEGACY_DATA_PATH="$2"
      shift 2
      ;;
    --new-data)
      NEW_DATA_PATH="$2"
      shift 2
      ;;
    --backup)
      BACKUP_PATH="$2"
      shift 2
      ;;
    --id-mapping)
      ID_MAPPING_PATH="$2"
      shift 2
      ;;
    --restore-only)
      RESTORE_ONLY="--restore-only"
      shift
      ;;
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create directories if they don't exist
mkdir -p $(dirname "$LEGACY_DATA_PATH")
mkdir -p $(dirname "$NEW_DATA_PATH")
mkdir -p $(dirname "$BACKUP_PATH")
mkdir -p $(dirname "$ID_MAPPING_PATH")

# Print configuration
echo "=== Rollback Configuration ==="
echo "Legacy data path: $LEGACY_DATA_PATH"
echo "New data path: $NEW_DATA_PATH"
echo "Backup path: $BACKUP_PATH"
echo "ID mapping path: $ID_MAPPING_PATH"
if [ -n "$RESTORE_ONLY" ]; then
  echo "Restore only: Yes"
else
  echo "Restore only: No"
fi
if [ -n "$DRY_RUN" ]; then
  echo "Dry run: Yes"
else
  echo "Dry run: No"
fi
echo

# Confirm execution
if [ -z "$DRY_RUN" ]; then
  read -p "This will roll back the migration process. Are you sure you want to continue? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback aborted."
    exit 1
  fi
fi

# Execute rollback
echo "=== Executing Rollback ==="
python3 scripts/task_manager/rollback_migration.py \
  --legacy-data "$LEGACY_DATA_PATH" \
  --new-data "$NEW_DATA_PATH" \
  --backup "$BACKUP_PATH" \
  --id-mapping "$ID_MAPPING_PATH" \
  $RESTORE_ONLY \
  $DRY_RUN

# Check if rollback was successful
if [ $? -ne 0 ]; then
  echo "Rollback failed. Please check the logs for details."
  exit 1
fi

echo "=== Rollback Process Completed Successfully ==="
echo "The migration has been rolled back successfully."
echo
echo "Summary:"
echo "- Legacy system has been restored from backup"
if [ -z "$RESTORE_ONLY" ]; then
  echo "- Changes made in the new system have been synchronized to the legacy system"
fi
echo

if [ -n "$DRY_RUN" ]; then
  echo "This was a dry run. No changes were made to the systems."
  echo "To execute the actual rollback, run this script without the --dry-run flag."
fi
