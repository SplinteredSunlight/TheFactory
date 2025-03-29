#!/usr/bin/env python3
"""
Task Migration Script

This script migrates tasks from the legacy task management system to the new
Dagger-based Task Management System. It handles data export, transformation,
import, and validation to ensure a smooth migration.
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

# Import the task manager and Dagger integration
from src.task_manager.manager import get_task_manager, Task, Project, Phase
from src.task_manager.dagger_integration import get_task_workflow_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("task_migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task_migration")


class TaskMigrator:
    """
    Handles migration of tasks from legacy system to new Dagger-based system.
    """
    
    def __init__(
        self,
        legacy_data_path: str,
        new_data_path: str,
        dagger_config_path: Optional[str] = None,
        templates_dir: Optional[str] = None,
        dry_run: bool = False,
        validate_only: bool = False
    ):
        """
        Initialize the task migrator.
        
        Args:
            legacy_data_path: Path to legacy task data
            new_data_path: Path to new task data
            dagger_config_path: Path to Dagger configuration file
            templates_dir: Directory containing pipeline templates
            dry_run: Whether to perform a dry run without making changes
            validate_only: Whether to only validate data without migrating
        """
        self.legacy_data_path = legacy_data_path
        self.new_data_path = new_data_path
        self.dagger_config_path = dagger_config_path
        self.templates_dir = templates_dir
        self.dry_run = dry_run
        self.validate_only = validate_only
        
        # Initialize task managers
        self.legacy_task_manager = get_task_manager(legacy_data_path)
        self.new_task_manager = get_task_manager(new_data_path)
        
        # Initialize Dagger integration if not in validate-only mode
        self.workflow_integration = None
        if not validate_only and dagger_config_path:
            self.workflow_integration = get_task_workflow_integration(
                dagger_config_path=dagger_config_path,
                templates_dir=templates_dir
            )
        
        # Statistics
        self.stats = {
            "projects_total": 0,
            "projects_migrated": 0,
            "projects_failed": 0,
            "phases_total": 0,
            "phases_migrated": 0,
            "phases_failed": 0,
            "tasks_total": 0,
            "tasks_migrated": 0,
            "tasks_failed": 0,
            "workflows_created": 0,
            "workflows_failed": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "duration_seconds": 0
        }
        
        # Mapping of legacy IDs to new IDs
        self.id_mapping = {
            "projects": {},
            "phases": {},
            "tasks": {}
        }
        
        # Validation results
        self.validation_results = {
            "projects": {
                "valid": [],
                "invalid": []
            },
            "phases": {
                "valid": [],
                "invalid": []
            },
            "tasks": {
                "valid": [],
                "invalid": []
            }
        }
    
    async def migrate(self):
        """
        Perform the migration from legacy to new system.
        """
        logger.info("Starting task migration")
        logger.info(f"Legacy data path: {self.legacy_data_path}")
        logger.info(f"New data path: {self.new_data_path}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Validate only: {self.validate_only}")
        
        # Validate legacy data
        logger.info("Validating legacy data")
        if not self._validate_legacy_data():
            logger.error("Legacy data validation failed")
            return False
        
        # If validate-only mode, stop here
        if self.validate_only:
            logger.info("Validation completed successfully")
            self._print_validation_results()
            return True
        
        # Migrate projects
        logger.info("Migrating projects")
        if not await self._migrate_projects():
            logger.error("Project migration failed")
            return False
        
        # Migrate phases
        logger.info("Migrating phases")
        if not await self._migrate_phases():
            logger.error("Phase migration failed")
            return False
        
        # Migrate tasks
        logger.info("Migrating tasks")
        if not await self._migrate_tasks():
            logger.error("Task migration failed")
            return False
        
        # Create workflows for tasks if Dagger integration is enabled
        if self.workflow_integration and not self.dry_run:
            logger.info("Creating workflows for tasks")
            if not await self._create_workflows():
                logger.error("Workflow creation failed")
                # Continue anyway, as this is not critical
        
        # Save data in new system if not in dry run mode
        if not self.dry_run:
            logger.info("Saving data in new system")
            self.new_task_manager.save_data()
        
        # Update statistics
        self.stats["end_time"] = datetime.now()
        self.stats["duration_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Print migration summary
        self._print_migration_summary()
        
        logger.info("Task migration completed successfully")
        return True
    
    def _validate_legacy_data(self) -> bool:
        """
        Validate legacy data before migration.
        
        Returns:
            True if validation passed, False otherwise
        """
        # Check if legacy data exists
        if not os.path.exists(self.legacy_data_path):
            logger.error(f"Legacy data path does not exist: {self.legacy_data_path}")
            return False
        
        # Validate projects
        for project_id, project in self.legacy_task_manager.projects.items():
            self.stats["projects_total"] += 1
            
            # Validate project data
            if not self._validate_project(project):
                self.validation_results["projects"]["invalid"].append(project_id)
                logger.warning(f"Project validation failed: {project_id}")
            else:
                self.validation_results["projects"]["valid"].append(project_id)
            
            # Validate phases
            for phase_id, phase in project.phases.items():
                self.stats["phases_total"] += 1
                
                # Validate phase data
                if not self._validate_phase(phase):
                    self.validation_results["phases"]["invalid"].append(phase_id)
                    logger.warning(f"Phase validation failed: {phase_id}")
                else:
                    self.validation_results["phases"]["valid"].append(phase_id)
            
            # Validate tasks
            for task_id, task in project.tasks.items():
                self.stats["tasks_total"] += 1
                
                # Validate task data
                if not self._validate_task(task):
                    self.validation_results["tasks"]["invalid"].append(task_id)
                    logger.warning(f"Task validation failed: {task_id}")
                else:
                    self.validation_results["tasks"]["valid"].append(task_id)
        
        # Check if there are any invalid items
        has_invalid = (
            len(self.validation_results["projects"]["invalid"]) > 0 or
            len(self.validation_results["phases"]["invalid"]) > 0 or
            len(self.validation_results["tasks"]["invalid"]) > 0
        )
        
        if has_invalid:
            logger.warning("Validation found invalid items")
            return False
        
        logger.info("Legacy data validation passed")
        return True
    
    def _validate_project(self, project: Project) -> bool:
        """
        Validate a project.
        
        Args:
            project: The project to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        # Check required fields
        if not project.id or not project.name:
            return False
        
        # Check data types
        if not isinstance(project.id, str) or not isinstance(project.name, str):
            return False
        
        # Check if phases and tasks are dictionaries
        if not isinstance(project.phases, dict) or not isinstance(project.tasks, dict):
            return False
        
        return True
    
    def _validate_phase(self, phase: Phase) -> bool:
        """
        Validate a phase.
        
        Args:
            phase: The phase to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        # Check required fields
        if not phase.id or not phase.name:
            return False
        
        # Check data types
        if not isinstance(phase.id, str) or not isinstance(phase.name, str):
            return False
        
        # Check if order is a number
        if not isinstance(phase.order, (int, float)):
            return False
        
        return True
    
    def _validate_task(self, task: Task) -> bool:
        """
        Validate a task.
        
        Args:
            task: The task to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        # Check required fields
        if not task.id or not task.name or not task.description:
            return False
        
        # Check data types
        if not isinstance(task.id, str) or not isinstance(task.name, str) or not isinstance(task.description, str):
            return False
        
        # Check if status is valid
        if not hasattr(task, 'status') or not task.status:
            return False
        
        # Check if metadata is a dictionary
        if not isinstance(task.metadata, dict):
            return False
        
        return True
    
    async def _migrate_projects(self) -> bool:
        """
        Migrate projects from legacy to new system.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        for project_id, project in self.legacy_task_manager.projects.items():
            logger.info(f"Migrating project: {project_id}")
            
            try:
                # Create new project
                if not self.dry_run:
                    new_project = self.new_task_manager.create_project(
                        name=project.name,
                        description=project.description,
                        metadata=project.metadata
                    )
                    
                    # Store ID mapping
                    self.id_mapping["projects"][project_id] = new_project.id
                    
                    logger.info(f"Created new project: {new_project.id}")
                else:
                    # In dry run mode, just log the action
                    logger.info(f"Would create new project: {project.name}")
                    # Create a fake mapping for dry run
                    self.id_mapping["projects"][project_id] = f"new_{project_id}"
                
                self.stats["projects_migrated"] += 1
            except Exception as e:
                logger.error(f"Failed to migrate project {project_id}: {e}")
                self.stats["projects_failed"] += 1
                return False
        
        return True
    
    async def _migrate_phases(self) -> bool:
        """
        Migrate phases from legacy to new system.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        for project_id, project in self.legacy_task_manager.projects.items():
            new_project_id = self.id_mapping["projects"].get(project_id)
            if not new_project_id:
                logger.warning(f"No mapping found for project {project_id}, skipping phases")
                continue
            
            for phase_id, phase in project.phases.items():
                logger.info(f"Migrating phase: {phase_id}")
                
                try:
                    # Create new phase
                    if not self.dry_run:
                        # Get the new project
                        new_project = self.new_task_manager.get_project(new_project_id)
                        if not new_project:
                            logger.error(f"New project not found: {new_project_id}")
                            self.stats["phases_failed"] += 1
                            continue
                        
                        # Create new phase
                        new_phase = self.new_task_manager.create_phase(
                            project_id=new_project_id,
                            name=phase.name,
                            description=phase.description,
                            order=phase.order
                        )
                        
                        # Store ID mapping
                        self.id_mapping["phases"][phase_id] = new_phase.id
                        
                        logger.info(f"Created new phase: {new_phase.id}")
                    else:
                        # In dry run mode, just log the action
                        logger.info(f"Would create new phase: {phase.name}")
                        # Create a fake mapping for dry run
                        self.id_mapping["phases"][phase_id] = f"new_{phase_id}"
                    
                    self.stats["phases_migrated"] += 1
                except Exception as e:
                    logger.error(f"Failed to migrate phase {phase_id}: {e}")
                    self.stats["phases_failed"] += 1
                    return False
        
        return True
    
    async def _migrate_tasks(self) -> bool:
        """
        Migrate tasks from legacy to new system.
        
        Returns:
            True if migration succeeded, False otherwise
        """
        for project_id, project in self.legacy_task_manager.projects.items():
            new_project_id = self.id_mapping["projects"].get(project_id)
            if not new_project_id:
                logger.warning(f"No mapping found for project {project_id}, skipping tasks")
                continue
            
            for task_id, task in project.tasks.items():
                logger.info(f"Migrating task: {task_id}")
                
                try:
                    # Map phase ID if task has one
                    new_phase_id = None
                    if hasattr(task, 'phase_id') and task.phase_id:
                        new_phase_id = self.id_mapping["phases"].get(task.phase_id)
                    
                    # Map parent ID if task has one
                    new_parent_id = None
                    if hasattr(task, 'parent_id') and task.parent_id:
                        new_parent_id = self.id_mapping["tasks"].get(task.parent_id)
                    
                    # Create new task
                    if not self.dry_run:
                        new_task = self.new_task_manager.create_task(
                            name=task.name,
                            description=task.description,
                            project_id=new_project_id,
                            phase_id=new_phase_id,
                            parent_id=new_parent_id,
                            status=task.status,
                            priority=task.priority if hasattr(task, 'priority') else "medium",
                            progress=task.progress if hasattr(task, 'progress') else 0.0,
                            assignee_id=task.assignee_id if hasattr(task, 'assignee_id') else None,
                            assignee_type=task.assignee_type if hasattr(task, 'assignee_type') else None,
                            metadata=task.metadata,
                            result=task.result if hasattr(task, 'result') else None,
                            error=task.error if hasattr(task, 'error') else None
                        )
                        
                        # Store ID mapping
                        self.id_mapping["tasks"][task_id] = new_task.id
                        
                        logger.info(f"Created new task: {new_task.id}")
                    else:
                        # In dry run mode, just log the action
                        logger.info(f"Would create new task: {task.name}")
                        # Create a fake mapping for dry run
                        self.id_mapping["tasks"][task_id] = f"new_{task_id}"
                    
                    self.stats["tasks_migrated"] += 1
                except Exception as e:
                    logger.error(f"Failed to migrate task {task_id}: {e}")
                    self.stats["tasks_failed"] += 1
                    return False
        
        return True
    
    async def _create_workflows(self) -> bool:
        """
        Create workflows for migrated tasks.
        
        Returns:
            True if workflow creation succeeded, False otherwise
        """
        if not self.workflow_integration:
            logger.warning("Workflow integration not initialized, skipping workflow creation")
            return True
        
        for legacy_task_id, new_task_id in self.id_mapping["tasks"].items():
            logger.info(f"Creating workflow for task: {new_task_id}")
            
            try:
                # Get the legacy task to check if it had a workflow
                legacy_project_id = None
                legacy_task = None
                
                for project_id, project in self.legacy_task_manager.projects.items():
                    if legacy_task_id in project.tasks:
                        legacy_project_id = project_id
                        legacy_task = project.tasks[legacy_task_id]
                        break
                
                if not legacy_task:
                    logger.warning(f"Legacy task not found: {legacy_task_id}")
                    continue
                
                # Check if the legacy task had a workflow
                if not legacy_task.metadata.get("workflow_id"):
                    logger.info(f"Legacy task {legacy_task_id} did not have a workflow, skipping")
                    continue
                
                # Create a workflow for the new task
                workflow_info = await self.workflow_integration.create_workflow_from_task(
                    task_id=new_task_id,
                    workflow_name=f"Migrated: {legacy_task.name}",
                    custom_inputs=legacy_task.metadata.get("workflow_inputs", {})
                )
                
                logger.info(f"Created workflow for task {new_task_id}: {workflow_info['workflow_id']}")
                self.stats["workflows_created"] += 1
            except Exception as e:
                logger.error(f"Failed to create workflow for task {new_task_id}: {e}")
                self.stats["workflows_failed"] += 1
                # Continue anyway, as this is not critical
        
        return True
    
    def _print_validation_results(self):
        """Print validation results."""
        print("\n=== Validation Results ===")
        print(f"Projects: {len(self.validation_results['projects']['valid'])} valid, {len(self.validation_results['projects']['invalid'])} invalid")
        print(f"Phases: {len(self.validation_results['phases']['valid'])} valid, {len(self.validation_results['phases']['invalid'])} invalid")
        print(f"Tasks: {len(self.validation_results['tasks']['valid'])} valid, {len(self.validation_results['tasks']['invalid'])} invalid")
        
        if len(self.validation_results["projects"]["invalid"]) > 0:
            print("\nInvalid Projects:")
            for project_id in self.validation_results["projects"]["invalid"]:
                print(f"  - {project_id}")
        
        if len(self.validation_results["phases"]["invalid"]) > 0:
            print("\nInvalid Phases:")
            for phase_id in self.validation_results["phases"]["invalid"]:
                print(f"  - {phase_id}")
        
        if len(self.validation_results["tasks"]["invalid"]) > 0:
            print("\nInvalid Tasks:")
            for task_id in self.validation_results["tasks"]["invalid"]:
                print(f"  - {task_id}")
    
    def _print_migration_summary(self):
        """Print migration summary."""
        print("\n=== Migration Summary ===")
        print(f"Start time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        print(f"Projects: {self.stats['projects_migrated']}/{self.stats['projects_total']} migrated, {self.stats['projects_failed']} failed")
        print(f"Phases: {self.stats['phases_migrated']}/{self.stats['phases_total']} migrated, {self.stats['phases_failed']} failed")
        print(f"Tasks: {self.stats['tasks_migrated']}/{self.stats['tasks_total']} migrated, {self.stats['tasks_failed']} failed")
        
        if self.workflow_integration:
            print(f"Workflows: {self.stats['workflows_created']} created, {self.stats['workflows_failed']} failed")
        
        if self.dry_run:
            print("\nThis was a dry run. No changes were made to the new system.")
    
    def export_id_mapping(self, output_path: str):
        """
        Export ID mapping to a file.
        
        Args:
            output_path: Path to save the ID mapping
        """
        with open(output_path, 'w') as f:
            json.dump(self.id_mapping, f, indent=2)
        
        logger.info(f"ID mapping exported to {output_path}")
    
    def export_stats(self, output_path: str):
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
    parser = argparse.ArgumentParser(description="Migrate tasks from legacy to new system")
    parser.add_argument("--legacy-data", required=True, help="Path to legacy task data")
    parser.add_argument("--new-data", required=True, help="Path to new task data")
    parser.add_argument("--dagger-config", help="Path to Dagger configuration file")
    parser.add_argument("--templates-dir", help="Directory containing pipeline templates")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    parser.add_argument("--validate-only", action="store_true", help="Only validate data without migrating")
    parser.add_argument("--export-mapping", help="Path to export ID mapping")
    parser.add_argument("--export-stats", help="Path to export migration statistics")
    args = parser.parse_args()
    
    # Create migrator
    migrator = TaskMigrator(
        legacy_data_path=args.legacy_data,
        new_data_path=args.new_data,
        dagger_config_path=args.dagger_config,
        templates_dir=args.templates_dir,
        dry_run=args.dry_run,
        validate_only=args.validate_only
    )
    
    # Perform migration
    success = await migrator.migrate()
    
    # Export ID mapping if requested
    if args.export_mapping and success and not args.validate_only:
        migrator.export_id_mapping(args.export_mapping)
    
    # Export statistics if requested
    if args.export_stats and success:
        migrator.export_stats(args.export_stats)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
