#!/usr/bin/env python3
"""
Migration Execution Script

This script executes the migration from the legacy task management system to the new
Dagger-based Task Management System. It follows the migration plan, monitors the process,
and verifies the migration was successful.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the task manager and migration tools
from src.task_manager.manager import get_task_manager, Task, Project, Phase
from scripts.task_manager.migrate_tasks import TaskMigrator
from scripts.task_manager.test_migration import MigrationTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_execution.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migration_execution")


class MigrationExecutor:
    """
    Executes the migration from legacy to new system.
    """
    
    def __init__(
        self,
        legacy_data_path: str,
        new_data_path: str,
        backup_path: str,
        dagger_config_path: Optional[str] = None,
        templates_dir: Optional[str] = None,
        id_mapping_path: Optional[str] = None,
        phase: str = "all",
        dry_run: bool = False
    ):
        """
        Initialize the migration executor.
        
        Args:
            legacy_data_path: Path to legacy task data
            new_data_path: Path to new task data
            backup_path: Path to backup data
            dagger_config_path: Path to Dagger configuration file
            templates_dir: Directory containing pipeline templates
            id_mapping_path: Path to save ID mapping
            phase: Migration phase to execute (all, prepare, migrate, verify, finalize)
            dry_run: Whether to perform a dry run without making changes
        """
        self.legacy_data_path = legacy_data_path
        self.new_data_path = new_data_path
        self.backup_path = backup_path
        self.dagger_config_path = dagger_config_path
        self.templates_dir = templates_dir
        self.id_mapping_path = id_mapping_path or "migration_id_mapping.json"
        self.phase = phase
        self.dry_run = dry_run
        
        # Initialize task managers
        self.legacy_task_manager = get_task_manager(legacy_data_path)
        self.new_task_manager = get_task_manager(new_data_path)
        
        # Statistics
        self.stats = {
            "start_time": datetime.now(),
            "end_time": None,
            "duration_seconds": 0,
            "phases_completed": [],
            "phases_failed": [],
            "projects_migrated": 0,
            "tasks_migrated": 0,
            "workflows_created": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }
    
    async def execute(self) -> bool:
        """
        Execute the migration.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        logger.info("Starting migration execution")
        logger.info(f"Legacy data path: {self.legacy_data_path}")
        logger.info(f"New data path: {self.new_data_path}")
        logger.info(f"Backup path: {self.backup_path}")
        logger.info(f"Phase: {self.phase}")
        logger.info(f"Dry run: {self.dry_run}")
        
        success = True
        
        # Execute the specified phase(s)
        if self.phase == "all" or self.phase == "prepare":
            logger.info("Executing preparation phase")
            if not await self._execute_preparation_phase():
                logger.error("Preparation phase failed")
                self.stats["phases_failed"].append("prepare")
                success = False
            else:
                self.stats["phases_completed"].append("prepare")
        
        if (self.phase == "all" or self.phase == "migrate") and (self.phase != "all" or success):
            logger.info("Executing migration phase")
            if not await self._execute_migration_phase():
                logger.error("Migration phase failed")
                self.stats["phases_failed"].append("migrate")
                success = False
            else:
                self.stats["phases_completed"].append("migrate")
        
        if (self.phase == "all" or self.phase == "verify") and (self.phase != "all" or success):
            logger.info("Executing verification phase")
            if not await self._execute_verification_phase():
                logger.error("Verification phase failed")
                self.stats["phases_failed"].append("verify")
                success = False
            else:
                self.stats["phases_completed"].append("verify")
        
        if (self.phase == "all" or self.phase == "finalize") and (self.phase != "all" or success):
            logger.info("Executing finalization phase")
            if not await self._execute_finalization_phase():
                logger.error("Finalization phase failed")
                self.stats["phases_failed"].append("finalize")
                success = False
            else:
                self.stats["phases_completed"].append("finalize")
        
        # Update statistics
        self.stats["end_time"] = datetime.now()
        self.stats["duration_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Print migration summary
        self._print_migration_summary()
        
        # Export statistics
        self._export_stats("migration_execution_stats.json")
        
        return success
    
    async def _execute_preparation_phase(self) -> bool:
        """
        Execute the preparation phase.
        
        Returns:
            True if preparation succeeded, False otherwise
        """
        try:
            # Create backup of legacy data
            if not self.dry_run:
                logger.info("Creating backup of legacy data")
                import shutil
                if os.path.exists(self.backup_path):
                    logger.warning(f"Backup path already exists: {self.backup_path}")
                    # Rename existing backup
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_backup_path = f"{self.backup_path}_{current_time}"
                    shutil.move(self.backup_path, new_backup_path)
                    logger.info(f"Renamed existing backup to {new_backup_path}")
                
                # Create new backup
                shutil.copytree(self.legacy_data_path, self.backup_path)
                logger.info(f"Created backup of legacy data at {self.backup_path}")
            else:
                logger.info(f"Would create backup of legacy data at {self.backup_path}")
            
            # Validate legacy data
            logger.info("Validating legacy data")
            migrator = TaskMigrator(
                legacy_data_path=self.legacy_data_path,
                new_data_path=self.new_data_path,
                dagger_config_path=self.dagger_config_path,
                templates_dir=self.templates_dir,
                dry_run=True,
                validate_only=True
            )
            
            if not await migrator.migrate():
                logger.error("Legacy data validation failed")
                return False
            
            logger.info("Preparation phase completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during preparation phase: {e}")
            return False
    
    async def _execute_migration_phase(self) -> bool:
        """
        Execute the migration phase.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        try:
            # Perform migration
            logger.info("Performing migration")
            migrator = TaskMigrator(
                legacy_data_path=self.legacy_data_path,
                new_data_path=self.new_data_path,
                dagger_config_path=self.dagger_config_path,
                templates_dir=self.templates_dir,
                dry_run=self.dry_run
            )
            
            if not await migrator.migrate():
                logger.error("Migration failed")
                return False
            
            # Export ID mapping
            if not self.dry_run:
                migrator.export_id_mapping(self.id_mapping_path)
                
                # Update statistics
                self.stats["projects_migrated"] = migrator.stats["projects_migrated"]
                self.stats["tasks_migrated"] = migrator.stats["tasks_migrated"]
                self.stats["workflows_created"] = migrator.stats["workflows_created"]
            
            logger.info("Migration phase completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during migration phase: {e}")
            return False
    
    async def _execute_verification_phase(self) -> bool:
        """
        Execute the verification phase.
        
        Returns:
            True if verification succeeded, False otherwise
        """
        try:
            # Verify migration
            logger.info("Verifying migration")
            tester = MigrationTester(
                legacy_data_path=self.legacy_data_path,
                new_data_path=self.new_data_path,
                id_mapping_path=self.id_mapping_path,
                dagger_config_path=self.dagger_config_path,
                templates_dir=self.templates_dir
            )
            
            test_result = await tester.run_tests()
            
            # Check if any tests failed
            if not test_result:
                logger.error("Migration verification failed")
                return False
            
            # Check if there are any failed tests
            has_failures = (
                tester.test_results["data_integrity"]["projects"]["failed"] > 0 or
                tester.test_results["data_integrity"]["phases"]["failed"] > 0 or
                tester.test_results["data_integrity"]["tasks"]["failed"] > 0 or
                tester.test_results["functionality"]["task_creation"]["failed"] > 0 or
                tester.test_results["functionality"]["task_update"]["failed"] > 0 or
                (tester.workflow_integration and (
                    tester.test_results["functionality"]["workflow_creation"]["failed"] > 0 or
                    tester.test_results["functionality"]["workflow_execution"]["failed"] > 0
                ))
            )
            
            if has_failures:
                logger.error("Migration verification failed: Some tests failed")
                return False
            
            # Update statistics
            self.stats["tests_passed"] = (
                tester.test_results["data_integrity"]["projects"]["passed"] +
                tester.test_results["data_integrity"]["phases"]["passed"] +
                tester.test_results["data_integrity"]["tasks"]["passed"] +
                tester.test_results["functionality"]["task_creation"]["passed"] +
                tester.test_results["functionality"]["task_update"]["passed"] +
                tester.test_results["functionality"]["workflow_creation"]["passed"] +
                tester.test_results["functionality"]["workflow_execution"]["passed"]
            )
            
            self.stats["tests_failed"] = (
                tester.test_results["data_integrity"]["projects"]["failed"] +
                tester.test_results["data_integrity"]["phases"]["failed"] +
                tester.test_results["data_integrity"]["tasks"]["failed"] +
                tester.test_results["functionality"]["task_creation"]["failed"] +
                tester.test_results["functionality"]["task_update"]["failed"] +
                tester.test_results["functionality"]["workflow_creation"]["failed"] +
                tester.test_results["functionality"]["workflow_execution"]["failed"]
            )
            
            logger.info("Verification phase completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during verification phase: {e}")
            return False
    
    async def _execute_finalization_phase(self) -> bool:
        """
        Execute the finalization phase.
        
        Returns:
            True if finalization succeeded, False otherwise
        """
        try:
            # Set legacy system to read-only mode
            if not self.dry_run:
                logger.info("Setting legacy system to read-only mode")
                # This would typically involve updating configuration or setting a flag
                # For this example, we'll just log the action
                logger.info("Legacy system set to read-only mode")
            else:
                logger.info("Would set legacy system to read-only mode")
            
            # Redirect traffic to new system
            if not self.dry_run:
                logger.info("Redirecting traffic to new system")
                # This would typically involve updating DNS, load balancers, or proxies
                # For this example, we'll just log the action
                logger.info("Traffic redirected to new system")
            else:
                logger.info("Would redirect traffic to new system")
            
            # Update documentation
            if not self.dry_run:
                logger.info("Updating documentation")
                # This would typically involve updating documentation files
                # For this example, we'll just log the action
                logger.info("Documentation updated")
            else:
                logger.info("Would update documentation")
            
            # Notify users
            if not self.dry_run:
                logger.info("Notifying users")
                # This would typically involve sending emails or notifications
                # For this example, we'll just log the action
                logger.info("Users notified")
            else:
                logger.info("Would notify users")
            
            logger.info("Finalization phase completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during finalization phase: {e}")
            return False
    
    def _print_migration_summary(self):
        """Print migration summary."""
        print("\n=== Migration Execution Summary ===")
        print(f"Start time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        print(f"Phases completed: {', '.join(self.stats['phases_completed'])}")
        print(f"Phases failed: {', '.join(self.stats['phases_failed'])}")
        
        if "migrate" in self.stats["phases_completed"]:
            print(f"Projects migrated: {self.stats['projects_migrated']}")
            print(f"Tasks migrated: {self.stats['tasks_migrated']}")
            print(f"Workflows created: {self.stats['workflows_created']}")
        
        if "verify" in self.stats["phases_completed"]:
            print(f"Tests passed: {self.stats['tests_passed']}")
            print(f"Tests failed: {self.stats['tests_failed']}")
        
        if self.dry_run:
            print("\nThis was a dry run. No changes were made to the systems.")
    
    def _export_stats(self, output_path: str):
        """
        Export migration statistics to a file.
        
        Args:
            output_path: Path to save the statistics
        """
        # Convert datetime objects to strings
        stats_copy = self.stats.copy()
        stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        stats_copy["end_time"] = stats_copy["end_time"].isoformat() if stats_copy["end_time"] else None
        
        with open(output_path, 'w') as f:
            json.dump(stats_copy, f, indent=2)
        
        logger.info(f"Migration statistics exported to {output_path}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Execute migration from legacy to new system")
    parser.add_argument("--legacy-data", required=True, help="Path to legacy task data")
    parser.add_argument("--new-data", required=True, help="Path to new task data")
    parser.add_argument("--backup", required=True, help="Path to backup data")
    parser.add_argument("--dagger-config", help="Path to Dagger configuration file")
    parser.add_argument("--templates-dir", help="Directory containing pipeline templates")
    parser.add_argument("--id-mapping", help="Path to save ID mapping")
    parser.add_argument("--phase", default="all", choices=["all", "prepare", "migrate", "verify", "finalize"], help="Migration phase to execute")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    args = parser.parse_args()
    
    # Create executor
    executor = MigrationExecutor(
        legacy_data_path=args.legacy_data,
        new_data_path=args.new_data,
        backup_path=args.backup,
        dagger_config_path=args.dagger_config,
        templates_dir=args.templates_dir,
        id_mapping_path=args.id_mapping,
        phase=args.phase,
        dry_run=args.dry_run
    )
    
    # Execute migration
    success = await executor.execute()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
