# Task Manager Migration Scripts

This directory contains scripts for migrating from the legacy task management system to the new Dagger-based Task Management System.

## Overview

The migration process involves the following steps:

1. **Preparation**: Validate legacy data and create backups
2. **Migration**: Migrate projects, phases, tasks, and workflows to the new system
3. **Verification**: Verify data integrity, functionality, and performance
4. **Optimization**: Optimize performance of the new system
5. **Decommissioning**: Archive legacy data and decommission the legacy system

## Scripts

### Main Scripts

- `run_migration.sh`: Main script to run the entire migration process
- `execute_migration.py`: Script to execute the migration
- `test_migration.py`: Script to test the migration
- `optimize_performance.py`: Script to optimize performance
- `decommission_legacy.py`: Script to decommission the legacy system
- `rollback_migration.py`: Script to rollback the migration if needed

### Usage

#### Running the Migration

To run the migration, use the following command:

```bash
./scripts/task_manager/run_migration.sh
```

This will execute the entire migration process, including preparation, migration, verification, optimization, and decommissioning.

#### Running a Dry Run

To run a dry run without making any changes, use the following command:

```bash
./scripts/task_manager/run_migration.sh --dry-run
```

This will simulate the migration process without making any changes to the systems.

#### Running Specific Phases

To run specific phases of the migration, use the following command:

```bash
./scripts/task_manager/run_migration.sh --phase prepare,migrate,verify
```

This will only execute the specified phases of the migration process.

#### Specifying Custom Paths

To specify custom paths for the migration, use the following command:

```bash
./scripts/task_manager/run_migration.sh \
  --legacy-data /path/to/legacy/data \
  --new-data /path/to/new/data \
  --backup /path/to/backup \
  --id-mapping /path/to/id_mapping.json \
  --dagger-config /path/to/dagger.yaml \
  --templates-dir /path/to/templates \
  --verification-report /path/to/verification_report.json \
  --archive /path/to/archive
```

#### Rolling Back the Migration

If the migration fails or needs to be rolled back, use the following command:

```bash
./scripts/task_manager/rollback_migration.sh
```

This will restore the legacy system from the backup and clean up any data created in the new system.

## Configuration

The migration scripts use the following configuration files:

- `config/dagger.yaml`: Dagger configuration
- `data/legacy/tasks.json`: Legacy task data
- `data/new/tasks.json`: New task data
- `data/id_mapping.json`: Mapping of legacy IDs to new IDs
- `data/verification_report.json`: Verification report

## Logging

The migration scripts generate the following log files:

- `migration_execution.log`: Log file for the migration execution
- `task_migration.log`: Log file for the task migration
- `migration_test.log`: Log file for the migration testing

## Troubleshooting

### Common Issues

1. **Legacy data validation fails**
   - Check the legacy data for inconsistencies
   - Fix any issues in the legacy data and try again

2. **Migration fails**
   - Check the log files for errors
   - Fix any issues and try again

3. **Verification fails**
   - Check the verification report for details
   - Fix any issues and try again

4. **Performance issues**
   - Run the optimization script
   - Check the database configuration
   - Check the Dagger configuration

### Getting Help

If you encounter issues that are not covered in this guide, please contact the migration team:

- Email: migration@example.com
- Slack: #dagger-migration
- GitHub Issues: https://github.com/example/ai-orchestration-platform/issues
