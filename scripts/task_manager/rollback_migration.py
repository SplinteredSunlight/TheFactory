#!/usr/bin/env python3
"""
Migration Rollback Script

This script rolls back a migration from the legacy task management system to the new
Dagger-based Task Management System in case of issues. It restores the legacy system
to its previous state and handles any necessary cleanup.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the task manager
from src.task_manager.manager import get_task_manager, Task, Project, Phase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_rollback.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migration_rollback")


class MigrationRollback:
    """
    Handles rollback of migration from new Dagger-based system to legacy system.
    """
    
    def __init__(
        self,
        legacy_data_path: str,
        new_data_path: str,
        backup_path: str,
        id_mapping_path: Optional[str] = None,
        restore_only: bool = False,
        dry_run: bool = False
    ):
        """
        Initialize the migration rollback.
        
        Args:
            legacy_data_path: Path to legacy task data
            new_data_path: Path to new task data
            backup_path: Path to backup data
            id_mapping_path: Path to ID mapping file
            restore_only: Whether to only restore legacy data without syncing changes
            dry_run: Whether to perform a dry run without making changes
        """
        self.legacy_data_path = legacy_data_path
        self.new_data_path = new_data_path
        self.backup_path = backup_path
        self.id_mapping_path = id_mapping_path
        self.restore_only = restore_only
        self.dry_run = dry_run
        
        # Initialize task managers
        self.legacy_task_manager = get_task_manager(legacy_data_path)
        self.new_task_manager = get_task_manager(new_data_path)
        
        # Load ID mapping if provided
        self.id_mapping = self._load_id_mapping() if id_mapping_path else None
        
        # Statistics
        self.stats = {
            "backup_restored": False,
            "changes_synced": False,
            "projects_updated": 0,
            "tasks_updated": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "duration_seconds": 0
        }
    
    def _load_id_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Load ID mapping from file.
        
        Returns:
            Dictionary mapping legacy IDs to new IDs
        """
        try:
            with open(self.id_mapping_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load ID mapping: {e}")
            return {"projects": {}, "phases": {}, "tasks": {}}
    
    def _create_reverse_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Create a reverse mapping from new IDs to legacy IDs.
        
        Returns:
            Dictionary mapping new IDs to legacy IDs
        """
        if not self.id_mapping:
            return {"projects": {}, "phases": {}, "tasks": {}}
        
        reverse_mapping = {"projects": {}, "phases": {}, "tasks": {}}
        
        for entity_type in ["projects", "phases", "tasks"]:
            for legacy_id, new_id in self.id_mapping[entity_type].items():
                reverse_mapping[entity_type][new_id] = legacy_id
        
        return reverse_mapping
    
    async def rollback(self) -> bool:
        """
        Perform the rollback from new system to legacy system.
        
        Returns:
            True if rollback succeeded, False otherwise
        """
        logger.info("Starting migration rollback")
        logger.info(f"Legacy data path: {self.legacy_data_path}")
        logger.info(f"New data path: {self.new_data_path}")
        logger.info(f"Backup path: {self.backup_path}")
        logger.info(f"Restore only: {self.restore_only}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # Verify backup exists
        if not os.path.exists(self.backup_path):
            logger.error(f"Backup path does not exist: {self.backup_path}")
            return False
        
        # Restore backup
        logger.info("Restoring backup to legacy system")
        if not await self._restore_backup():
            logger.error("Failed to restore backup")
            return False
        
        # If restore-only mode, stop here
        if self.restore_only:
            logger.info("Restore-only mode, skipping change synchronization")
        else:
            # Sync changes from new system to legacy system
            logger.info("Synchronizing changes from new system to legacy system")
            if not await self._sync_changes():
                logger.warning("Failed to synchronize some changes")
                # Continue anyway, as partial sync is better than none
        
        # Update statistics
        self.stats["end_time"] = datetime.now()
        self.stats["duration_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Print rollback summary
        self._print_rollback_summary()
        
        logger.info("Migration rollback completed successfully")
        return True
    
    async def _restore_backup(self) -> bool:
        """
        Restore backup to legacy system.
        
        Returns:
            True if restore succeeded, False otherwise
        """
        try:
            if not self.dry_run:
                # Create a backup of the current legacy data
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_backup_path = f"{self.legacy_data_path}_pre_rollback_{current_time}"
                
                # Copy legacy data directory to backup
                import shutil
                if os.path.exists(self.legacy_data_path):
                    shutil.copytree(self.legacy_data_path, current_backup_path)
                    logger.info(f"Created backup of current legacy data at {current_backup_path}")
                
                # Clear legacy data directory
                if os.path.exists(self.legacy_data_path):
                    shutil.rmtree(self.legacy_data_path)
                
                # Copy backup to legacy data directory
                shutil.copytree(self.backup_path, self.legacy_data_path)
                
                # Reload legacy task manager
                self.legacy_task_manager = get_task_manager(self.legacy_data_path)
                
                logger.info(f"Restored backup from {self.backup_path} to {self.legacy_data_path}")
            else:
                logger.info(f"Would restore backup from {self.backup_path} to {self.legacy_data_path}")
            
            self.stats["backup_restored"] = True
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    async def _sync_changes(self) -> bool:
        """
        Synchronize changes from new system to legacy system.
        
        Returns:
            True if sync succeeded, False otherwise
        """
        # Create reverse mapping
        reverse_mapping = self._create_reverse_mapping()
        
        # If no ID mapping is available, we can't sync changes
        if not self.id_mapping:
            logger.warning("No ID mapping available, skipping change synchronization")
            return False
        
        # Get the timestamp of the backup
        backup_time = self._get_backup_timestamp()
        if not backup_time:
            logger.warning("Could not determine backup timestamp, using current time")
            backup_time = datetime.now()
        
        # Sync projects
        for new_project_id, new_project in self.new_task_manager.projects.items():
            # Skip projects created before backup
            if hasattr(new_project, 'created_at') and new_project.created_at:
                created_at = datetime.fromisoformat(new_project.created_at) if isinstance(new_project.created_at, str) else new_project.created_at
                if created_at < backup_time:
                    continue
            
            # Check if this is a new project or an update to an existing one
            legacy_project_id = reverse_mapping["projects"].get(new_project_id)
            
            if legacy_project_id:
                # Update existing project
                logger.info(f"Updating legacy project: {legacy_project_id}")
                
                if not self.dry_run:
                    self.legacy_task_manager.update_project(
                        project_id=legacy_project_id,
                        name=new_project.name,
                        description=new_project.description,
                        metadata=new_project.metadata
                    )
                else:
                    logger.info(f"Would update legacy project: {legacy_project_id}")
                
                self.stats["projects_updated"] += 1
            else:
                # New project, create in legacy system
                logger.info(f"Creating new project in legacy system: {new_project.name}")
                
                if not self.dry_run:
                    legacy_project = self.legacy_task_manager.create_project(
                        name=new_project.name,
                        description=new_project.description,
                        metadata=new_project.metadata
                    )
                    
                    # Add to reverse mapping
                    reverse_mapping["projects"][new_project_id] = legacy_project.id
                else:
                    logger.info(f"Would create new project in legacy system: {new_project.name}")
                
                self.stats["projects_updated"] += 1
        
        # Sync tasks
        for new_project_id, new_project in self.new_task_manager.projects.items():
            legacy_project_id = reverse_mapping["projects"].get(new_project_id)
            
            if not legacy_project_id:
                logger.warning(f"No mapping found for project {new_project_id}, skipping tasks")
                continue
            
            for new_task_id, new_task in new_project.tasks.items():
                # Skip tasks created before backup
                if hasattr(new_task, 'created_at') and new_task.created_at:
                    created_at = datetime.fromisoformat(new_task.created_at) if isinstance(new_task.created_at, str) else new_task.created_at
                    if created_at < backup_time:
                        continue
                
                # Check if this is a new task or an update to an existing one
                legacy_task_id = reverse_mapping["tasks"].get(new_task_id)
                
                if legacy_task_id:
                    # Update existing task
                    logger.info(f"Updating legacy task: {legacy_task_id}")
                    
                    if not self.dry_run:
                        # Map phase ID if task has one
                        legacy_phase_id = None
                        if hasattr(new_task, 'phase_id') and new_task.phase_id:
                            legacy_phase_id = reverse_mapping["phases"].get(new_task.phase_id)
                        
                        # Map parent ID if task has one
                        legacy_parent_id = None
                        if hasattr(new_task, 'parent_id') and new_task.parent_id:
                            legacy_parent_id = reverse_mapping["tasks"].get(new_task.parent_id)
                        
                        self.legacy_task_manager.update_task(
                            task_id=legacy_task_id,
                            name=new_task.name,
                            description=new_task.description,
                            phase_id=legacy_phase_id,
                            parent_id=legacy_parent_id,
                            status=new_task.status,
                            priority=new_task.priority if hasattr(new_task, 'priority') else None,
                            progress=new_task.progress if hasattr(new_task, 'progress') else None,
                            assignee_id=new_task.assignee_id if hasattr(new_task, 'assignee_id') else None,
                            assignee_type=new_task.assignee_type if hasattr(new_task, 'assignee_type') else None,
                            metadata=new_task.metadata,
                            result=new_task.result if hasattr(new_task, 'result') else None,
                            error=new_task.error if hasattr(new_task, 'error') else None
                        )
                    else:
                        logger.info(f"Would update legacy task: {legacy_task_id}")
                    
                    self.stats["tasks_updated"] += 1
                else:
                    # New task, create in legacy system
                    logger.info(f"Creating new task in legacy system: {new_task.name}")
                    
                    if not self.dry_run:
                        # Map phase ID if task has one
                        legacy_phase_id = None
                        if hasattr(new_task, 'phase_id') and new_task.phase_id:
                            legacy_phase_id = reverse_mapping["phases"].get(new_task.phase_id)
                        
                        # Map parent ID if task has one
                        legacy_parent_id = None
                        if hasattr(new_task, 'parent_id') and new_task.parent_id:
                            legacy_parent_id = reverse_mapping["tasks"].get(new_task.parent_id)
                        
                        legacy_task = self.legacy_task_manager.create_task(
                            name=new_task.name,
                            description=new_task.description,
                            project_id=legacy_project_id,
                            phase_id=legacy_phase_id,
                            parent_id=legacy_parent_id,
                            status=new_task.status,
                            priority=new_task.priority if hasattr(new_task, 'priority') else "medium",
                            progress=new_task.progress if hasattr(new_task, 'progress') else 0.0,
                            assignee_id=new_task.assignee_id if hasattr(new_task, 'assignee_id') else None,
                            assignee_type=new_task.assignee_type if hasattr(new_task, 'assignee_type') else None,
                            metadata=new_task.metadata,
                            result=new_task.result if hasattr(new_task, 'result') else None,
                            error=new_task.error if hasattr(new_task, 'error') else None
                        )
                        
                        # Add to reverse mapping
                        reverse_mapping["tasks"][new_task_id] = legacy_task.id
                    else:
                        logger.info(f"Would create new task in legacy system: {new_task.name}")
                    
                    self.stats["tasks_updated"] += 1
        
        # Save changes to legacy system
        if not self.dry_run:
            self.legacy_task_manager.save_data()
            logger.info("Saved changes to legacy system")
        else:
            logger.info("Would save changes to legacy system")
        
        self.stats["changes_synced"] = True
        return True
    
    def _get_backup_timestamp(self) -> Optional[datetime]:
        """
        Get the timestamp of the backup.
        
        Returns:
            Timestamp of the backup or None if not available
        """
        # Try to get the timestamp from the backup directory
        try:
            # Get the modification time of the backup directory
            backup_time = os.path.getmtime(self.backup_path)
            return datetime.fromtimestamp(backup_time)
        except Exception as e:
            logger.warning(f"Failed to get backup timestamp: {e}")
            return None
    
    def _print_rollback_summary(self):
        """Print rollback summary."""
        print("\n=== Rollback Summary ===")
        print(f"Start time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        print(f"Backup restored: {self.stats['backup_restored']}")
        
        if not self.restore_only:
            print(f"Changes synced: {self.stats['changes_synced']}")
            print(f"Projects updated: {self.stats['projects_updated']}")
            print(f"Tasks updated: {self.stats['tasks_updated']}")
        
        if self.dry_run:
            print("\nThis was a dry run. No changes were made to the legacy system.")
    
    def export_stats(self, output_path: str):
        """
        Export rollback statistics to a file.
        
        Args:
            output_path: Path to save the statistics
        """
        # Convert datetime objects to strings
        stats_copy = self.stats.copy()
        stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        stats_copy["end_time"] = stats_copy["end_time"].isoformat() if stats_copy["end_time"] else None
        
        with open(output_path, 'w') as f:
            json.dump(stats_copy, f, indent=2)
        
        logger.info(f"Rollback statistics exported to {output_path}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Roll back migration from new to legacy system")
    parser.add_argument("--legacy-data", required=True, help="Path to legacy task data")
    parser.add_argument("--new-data", required=True, help="Path to new task data")
    parser.add_argument("--backup", required=True, help="Path to backup data")
    parser.add_argument("--id-mapping", help="Path to ID mapping file")
    parser.add_argument("--restore-only", action="store_true", help="Only restore backup without syncing changes")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    parser.add_argument("--export-stats", help="Path to export rollback statistics")
    args = parser.parse_args()
    
    # Create rollback handler
    rollback = MigrationRollback(
        legacy_data_path=args.legacy_data,
        new_data_path=args.new_data,
        backup_path=args.backup,
        id_mapping_path=args.id_mapping,
        restore_only=args.restore_only,
        dry_run=args.dry_run
    )
    
    # Perform rollback
    success = await rollback.rollback()
    
    # Export statistics if requested
    if args.export_stats and success:
        rollback.export_stats(args.export_stats)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
