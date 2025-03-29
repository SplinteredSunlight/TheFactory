#!/bin/bash
# Migration Execution Script
# This script runs the entire migration process from the legacy task management system
# to the new Dagger-based Task Management System.

set -e  # Exit on error

# Default paths
LEGACY_DATA_PATH="./data/legacy"
NEW_DATA_PATH="./data/new"
BACKUP_PATH="./data/backup"
ID_MAPPING_PATH="./data/id_mapping.json"
DAGGER_CONFIG_PATH="./config/dagger.yaml"
TEMPLATES_DIR="./templates"
VERIFICATION_REPORT_PATH="./data/verification_report.json"
ARCHIVE_PATH="./data/legacy_archive"

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
    --dagger-config)
      DAGGER_CONFIG_PATH="$2"
      shift 2
      ;;
    --templates-dir)
      TEMPLATES_DIR="$2"
      shift 2
      ;;
    --verification-report)
      VERIFICATION_REPORT_PATH="$2"
      shift 2
      ;;
    --archive)
      ARCHIVE_PATH="$2"
      shift 2
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
mkdir -p $(dirname "$VERIFICATION_REPORT_PATH")
mkdir -p $(dirname "$ARCHIVE_PATH")

# Print configuration
echo "=== Migration Configuration ==="
echo "Legacy data path: $LEGACY_DATA_PATH"
echo "New data path: $NEW_DATA_PATH"
echo "Backup path: $BACKUP_PATH"
echo "ID mapping path: $ID_MAPPING_PATH"
echo "Dagger config path: $DAGGER_CONFIG_PATH"
echo "Templates directory: $TEMPLATES_DIR"
echo "Verification report path: $VERIFICATION_REPORT_PATH"
echo "Archive path: $ARCHIVE_PATH"
if [ -n "$DRY_RUN" ]; then
  echo "Dry run: Yes"
else
  echo "Dry run: No"
fi
echo

# Confirm execution
if [ -z "$DRY_RUN" ]; then
  read -p "This will execute the migration process. Are you sure you want to continue? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration aborted."
    exit 1
  fi
fi

# Step 1: Execute migration
echo "=== Step 1: Executing Migration ==="
python3 scripts/task_manager/execute_migration.py \
  --legacy-data "$LEGACY_DATA_PATH" \
  --new-data "$NEW_DATA_PATH" \
  --backup "$BACKUP_PATH" \
  --dagger-config "$DAGGER_CONFIG_PATH" \
  --templates-dir "$TEMPLATES_DIR" \
  --id-mapping "$ID_MAPPING_PATH" \
  $DRY_RUN

# Check if migration was successful
if [ $? -ne 0 ]; then
  echo "Migration failed. Aborting."
  exit 1
fi

# Step 2: Optimize performance
echo "=== Step 2: Optimizing Performance ==="
python3 scripts/task_manager/optimize_performance.py \
  --data-path "$NEW_DATA_PATH" \
  --dagger-config "$DAGGER_CONFIG_PATH" \
  --templates-dir "$TEMPLATES_DIR" \
  --optimize \
  $DRY_RUN

# Check if optimization was successful
if [ $? -ne 0 ]; then
  echo "Performance optimization failed. Aborting."
  exit 1
fi

# Step 3: Decommission legacy system
echo "=== Step 3: Decommissioning Legacy System ==="
python3 scripts/task_manager/decommission_legacy.py \
  --legacy-data "$LEGACY_DATA_PATH" \
  --new-data "$NEW_DATA_PATH" \
  --id-mapping "$ID_MAPPING_PATH" \
  --archive "$ARCHIVE_PATH" \
  --verification-report "$VERIFICATION_REPORT_PATH" \
  $DRY_RUN

# Check if decommissioning was successful
if [ $? -ne 0 ]; then
  echo "Legacy system decommissioning failed."
  exit 1
fi

echo "=== Migration Process Completed Successfully ==="
echo "The migration from the legacy task management system to the new Dagger-based"
echo "Task Management System has been completed successfully."
echo
echo "Summary:"
echo "- Legacy data has been migrated to the new system"
echo "- Performance has been optimized"
echo "- Legacy system has been decommissioned"
echo
echo "Verification report: $VERIFICATION_REPORT_PATH"
echo "Legacy data archive: $ARCHIVE_PATH"
echo

if [ -n "$DRY_RUN" ]; then
  echo "This was a dry run. No changes were made to the systems."
  echo "To execute the actual migration, run this script without the --dry-run flag."
fi
