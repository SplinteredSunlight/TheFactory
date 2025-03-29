#!/usr/bin/env python3
"""
Legacy System Decommissioning Script

This script handles the decommissioning of the legacy task management system
after migration to the new Dagger-based Task Management System. It verifies
that all data has been migrated, creates a verification report, and reclaims
resources used by the legacy system.
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
        logging.FileHandler("decommission_legacy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("decommission_legacy")


class LegacyDecommissioner:
    """
    Handles decommissioning of the legacy task management system.
    """
    
    def __init__(
        self,
        legacy_data_path: str,
        new_data_path: str,
        id_mapping_path: str,
        archive_path: Optional[str] = None,
        verification_report_path: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Initialize the legacy decommissioner.
        
        Args:
            legacy_data_path: Path to legacy task data
            new_data_path: Path to new task data
            id_mapping_path: Path to ID mapping file
            archive_path: Path to archive legacy data
            verification_report_path: Path to save verification report
            dry_run: Whether to perform a dry run without making changes
        """
        self.legacy_data_path = legacy_data_path
        self.new_data_path = new_data_path
        self.id_mapping_path = id_mapping_path
        self.archive_path = archive_path or f"{legacy_data_path}_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.verification_report_path = verification_report_path or "verification_report.json"
        self.dry_run = dry_run
        
        # Initialize task managers
        self.legacy_task_manager = get_task_manager(legacy_data_path)
        self.new_task_manager = get_task_manager(new_data_path)
        
        # Load ID mapping
        self.id_mapping = self._load_id_mapping()
        
        # Verification results
        self.verification_results = {
            "projects": {"verified": 0, "missing": 0, "details": []},
            "phases": {"verified": 0, "missing": 0, "details": []},
            "tasks": {"verified": 0, "missing": 0, "details": []}
        }
        
        # Statistics
        self.stats = {
            "start_time": datetime.now(),
            "end_time": None,
            "duration_seconds": 0,
            "projects_verified": 0,
            "projects_missing": 0,
            "phases_verified": 0,
            "phases_missing": 0,
            "tasks_verified": 0,
            "tasks_missing": 0,
            "archived": False,
            "decommissioned": False
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
    
    async def decommission(self) -> bool:
        """
        Decommission the legacy system.
        
        Returns:
            True if decommissioning succeeded, False otherwise
        """
        logger.info("Starting legacy system decommissioning")
        logger.info(f"Legacy data path: {self.legacy_data_path}")
        logger.info(f"New data path: {self.new_data_path}")
        logger.info(f"ID mapping path: {self.id_mapping_path}")
        logger.info(f"Archive path: {self.archive_path}")
        logger.info(f"Verification report path: {self.verification_report_path}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # Verify data migration
        logger.info("Verifying data migration")
        if not await self._verify_data_migration():
            logger.error("Data migration verification failed")
            return False
        
        # Create verification report
        logger.info("Creating verification report")
        if not self._create_verification_report():
            logger.error("Verification report creation failed")
            return False
        
        # Archive legacy data
        logger.info("Archiving legacy data")
        if not await self._archive_legacy_data():
            logger.error("Legacy data archiving failed")
            return False
        
        # Decommission legacy system
        logger.info("Decommissioning legacy system")
        if not await self._decommission_legacy_system():
            logger.error("Legacy system decommissioning failed")
            return False
        
        # Update statistics
        self.stats["end_time"] = datetime.now()
        self.stats["duration_seconds"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.stats["projects_verified"] = self.verification_results["projects"]["verified"]
        self.stats["projects_missing"] = self.verification_results["projects"]["missing"]
        self.stats["phases_verified"] = self.verification_results["phases"]["verified"]
        self.stats["phases_missing"] = self.verification_results["phases"]["missing"]
        self.stats["tasks_verified"] = self.verification_results["tasks"]["verified"]
        self.stats["tasks_missing"] = self.verification_results["tasks"]["missing"]
        
        # Print decommissioning summary
        self._print_decommissioning_summary()
        
        # Export statistics
        self._export_stats("decommission_stats.json")
        
        logger.info("Legacy system decommissioning completed successfully")
        return True
    
    async def _verify_data_migration(self) -> bool:
        """
        Verify that all data has been migrated from legacy to new system.
        
        Returns:
            True if verification succeeded, False otherwise
        """
        try:
            # Verify projects
            logger.info("Verifying projects")
            for legacy_project_id, legacy_project in self.legacy_task_manager.projects.items():
                # Get the new project ID from the mapping
                new_project_id = self.id_mapping["projects"].get(legacy_project_id)
                if not new_project_id:
                    logger.warning(f"No mapping found for project {legacy_project_id}")
                    self.verification_results["projects"]["missing"] += 1
                    self.verification_results["projects"]["details"].append({
                        "legacy_id": legacy_project_id,
                        "status": "missing",
                        "reason": "No mapping found"
                    })
                    continue
                
                # Get the new project
                new_project = self.new_task_manager.get_project(new_project_id)
                if not new_project:
                    logger.warning(f"Project not found in new system: {new_project_id}")
                    self.verification_results["projects"]["missing"] += 1
                    self.verification_results["projects"]["details"].append({
                        "legacy_id": legacy_project_id,
                        "new_id": new_project_id,
                        "status": "missing",
                        "reason": "Project not found in new system"
                    })
                    continue
                
                # Verify project data
                if (
                    legacy_project.name != new_project.name or
                    legacy_project.description != new_project.description
                ):
                    logger.warning(f"Project data mismatch: {legacy_project_id} -> {new_project_id}")
                    self.verification_results["projects"]["missing"] += 1
                    self.verification_results["projects"]["details"].append({
                        "legacy_id": legacy_project_id,
                        "new_id": new_project_id,
                        "status": "missing",
                        "reason": "Project data mismatch"
                    })
                    continue
                
                # Project verified
                self.verification_results["projects"]["verified"] += 1
                self.verification_results["projects"]["details"].append({
                    "legacy_id": legacy_project_id,
                    "new_id": new_project_id,
                    "status": "verified"
                })
            
            # Verify phases
            logger.info("Verifying phases")
            for legacy_project_id, legacy_project in self.legacy_task_manager.projects.items():
                for legacy_phase_id, legacy_phase in legacy_project.phases.items():
                    # Get the new phase ID from the mapping
                    new_phase_id = self.id_mapping["phases"].get(legacy_phase_id)
                    if not new_phase_id:
                        logger.warning(f"No mapping found for phase {legacy_phase_id}")
                        self.verification_results["phases"]["missing"] += 1
                        self.verification_results["phases"]["details"].append({
                            "legacy_id": legacy_phase_id,
                            "status": "missing",
                            "reason": "No mapping found"
                        })
                        continue
                    
                    # Find the new phase in the new system
                    new_phase = None
                    new_project = None
                    for project in self.new_task_manager.projects.values():
                        if new_phase_id in project.phases:
                            new_phase = project.phases[new_phase_id]
                            new_project = project
                            break
                    
                    if not new_phase:
                        logger.warning(f"Phase not found in new system: {new_phase_id}")
                        self.verification_results["phases"]["missing"] += 1
                        self.verification_results["phases"]["details"].append({
                            "legacy_id": legacy_phase_id,
                            "new_id": new_phase_id,
                            "status": "missing",
                            "reason": "Phase not found in new system"
                        })
                        continue
                    
                    # Verify phase data
                    if (
                        legacy_phase.name != new_phase.name or
                        legacy_phase.description != new_phase.description or
                        legacy_phase.order != new_phase.order
                    ):
                        logger.warning(f"Phase data mismatch: {legacy_phase_id} -> {new_phase_id}")
                        self.verification_results["phases"]["missing"] += 1
                        self.verification_results["phases"]["details"].append({
                            "legacy_id": legacy_phase_id,
                            "new_id": new_phase_id,
                            "status": "missing",
                            "reason": "Phase data mismatch"
                        })
                        continue
                    
                    # Phase verified
                    self.verification_results["phases"]["verified"] += 1
                    self.verification_results["phases"]["details"].append({
                        "legacy_id": legacy_phase_id,
                        "new_id": new_phase_id,
                        "status": "verified"
                    })
            
            # Verify tasks
            logger.info("Verifying tasks")
            for legacy_project_id, legacy_project in self.legacy_task_manager.projects.items():
                for legacy_task_id, legacy_task in legacy_project.tasks.items():
                    # Get the new task ID from the mapping
                    new_task_id = self.id_mapping["tasks"].get(legacy_task_id)
                    if not new_task_id:
                        logger.warning(f"No mapping found for task {legacy_task_id}")
                        self.verification_results["tasks"]["missing"] += 1
                        self.verification_results["tasks"]["details"].append({
                            "legacy_id": legacy_task_id,
                            "status": "missing",
                            "reason": "No mapping found"
                        })
                        continue
                    
                    # Find the new task in the new system
                    new_task = None
                    new_project = None
                    for project in self.new_task_manager.projects.values():
                        if new_task_id in project.tasks:
                            new_task = project.tasks[new_task_id]
                            new_project = project
                            break
                    
                    if not new_task:
                        logger.warning(f"Task not found in new system: {new_task_id}")
                        self.verification_results["tasks"]["missing"] += 1
                        self.verification_results["tasks"]["details"].append({
                            "legacy_id": legacy_task_id,
                            "new_id": new_task_id,
                            "status": "missing",
                            "reason": "Task not found in new system"
                        })
                        continue
                    
                    # Verify task data
                    if (
                        legacy_task.name != new_task.name or
                        legacy_task.description != new_task.description or
                        legacy_task.status != new_task.status
                    ):
                        logger.warning(f"Task data mismatch: {legacy_task_id} -> {new_task_id}")
                        self.verification_results["tasks"]["missing"] += 1
                        self.verification_results["tasks"]["details"].append({
                            "legacy_id": legacy_task_id,
                            "new_id": new_task_id,
                            "status": "missing",
                            "reason": "Task data mismatch"
                        })
                        continue
                    
                    # Task verified
                    self.verification_results["tasks"]["verified"] += 1
                    self.verification_results["tasks"]["details"].append({
                        "legacy_id": legacy_task_id,
                        "new_id": new_task_id,
                        "status": "verified"
                    })
            
            # Check if verification was successful
            verification_successful = (
                self.verification_results["projects"]["missing"] == 0 and
                self.verification_results["phases"]["missing"] == 0 and
                self.verification_results["tasks"]["missing"] == 0
            )
            
            if verification_successful:
                logger.info("Data migration verification succeeded")
            else:
                logger.warning("Data migration verification found missing items")
            
            return verification_successful
        except Exception as e:
            logger.error(f"Error during data migration verification: {e}")
            return False
    
    def _create_verification_report(self) -> bool:
        """
        Create a verification report.
        
        Returns:
            True if report creation succeeded, False otherwise
        """
        try:
            # Create report
            report = {
                "timestamp": datetime.now().isoformat(),
                "legacy_data_path": self.legacy_data_path,
                "new_data_path": self.new_data_path,
                "id_mapping_path": self.id_mapping_path,
                "verification_results": self.verification_results,
                "summary": {
                    "projects_verified": self.verification_results["projects"]["verified"],
                    "projects_missing": self.verification_results["projects"]["missing"],
                    "phases_verified": self.verification_results["phases"]["verified"],
                    "phases_missing": self.verification_results["phases"]["missing"],
                    "tasks_verified": self.verification_results["tasks"]["verified"],
                    "tasks_missing": self.verification_results["tasks"]["missing"],
                    "verification_successful": (
                        self.verification_results["projects"]["missing"] == 0 and
                        self.verification_results["phases"]["missing"] == 0 and
                        self.verification_results["tasks"]["missing"] == 0
                    )
                }
            }
            
            # Save report
            if not self.dry_run:
                with open(self.verification_report_path, 'w') as f:
                    json.dump(report, f, indent=2)
                logger.info(f"Verification report saved to {self.verification_report_path}")
            else:
                logger.info(f"Would save verification report to {self.verification_report_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating verification report: {e}")
            return False
    
    async def _archive_legacy_data(self) -> bool:
        """
        Archive legacy data.
        
        Returns:
            True if archiving succeeded, False otherwise
        """
        try:
            if not self.dry_run:
                # Create archive directory
                os.makedirs(os.path.dirname(self.archive_path), exist_ok=True)
                
                # Check if archive directory already exists
                if os.path.exists(self.archive_path):
                    # Rename existing archive directory
                    import time
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    new_archive_path = f"{self.archive_path}_{timestamp}"
                    os.rename(self.archive_path, new_archive_path)
                    logger.info(f"Renamed existing archive to {new_archive_path}")
                
                # Copy legacy data to archive
                import shutil
                shutil.copytree(self.legacy_data_path, self.archive_path)
                
                logger.info(f"Legacy data archived to {self.archive_path}")
                self.stats["archived"] = True
            else:
                logger.info(f"Would archive legacy data to {self.archive_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error archiving legacy data: {e}")
            return False
    
    async def _decommission_legacy_system(self) -> bool:
        """
        Decommission the legacy system.
        
        Returns:
            True if decommissioning succeeded, False otherwise
        """
        try:
            if not self.dry_run:
                # In a real implementation, this would involve:
                # 1. Stopping legacy services
                # 2. Removing legacy system from load balancers
                # 3. Updating DNS records
                # 4. Reclaiming resources
                
                # For this example, we'll just log the actions
                logger.info("Stopping legacy services")
                logger.info("Removing legacy system from load balancers")
                logger.info("Updating DNS records")
                logger.info("Reclaiming resources")
                
                self.stats["decommissioned"] = True
            else:
                logger.info("Would decommission legacy system")
            
            return True
        except Exception as e:
            logger.error(f"Error decommissioning legacy system: {e}")
            return False
    
    def _print_decommissioning_summary(self):
        """Print decommissioning summary."""
        print("\n=== Legacy System Decommissioning Summary ===")
        print(f"Start time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        
        print("\nVerification Results:")
        print(f"Projects: {self.stats['projects_verified']} verified, {self.stats['projects_missing']} missing")
        print(f"Phases: {self.stats['phases_verified']} verified, {self.stats['phases_missing']} missing")
        print(f"Tasks: {self.stats['tasks_verified']} verified, {self.stats['tasks_missing']} missing")
        
        print("\nActions:")
        print(f"Legacy data archived: {self.stats['archived']}")
        print(f"Legacy system decommissioned: {self.stats['decommissioned']}")
        
        if self.dry_run:
            print("\nThis was a dry run. No changes were made to the systems.")
    
    def _export_stats(self, output_path: str):
        """
        Export decommissioning statistics to a file.
        
        Args:
            output_path: Path to save the statistics
        """
        # Convert datetime objects to strings
        stats_copy = self.stats.copy()
        stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        stats_copy["end_time"] = stats_copy["end_time"].isoformat() if stats_copy["end_time"] else None
        
        if not self.dry_run:
            with open(output_path, 'w') as f:
                json.dump(stats_copy, f, indent=2)
            
            logger.info(f"Decommissioning statistics exported to {output_path}")
        else:
            logger.info(f"Would export decommissioning statistics to {output_path}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Decommission legacy task management system")
    parser.add_argument("--legacy-data", required=True, help="Path to legacy task data")
    parser.add_argument("--new-data", required=True, help="Path to new task data")
    parser.add_argument("--id-mapping", required=True, help="Path to ID mapping file")
    parser.add_argument("--archive", help="Path to archive legacy data")
    parser.add_argument("--verification-report", help="Path to save verification report")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    args = parser.parse_args()
    
    # Create decommissioner
    decommissioner = LegacyDecommissioner(
        legacy_data_path=args.legacy_data,
        new_data_path=args.new_data,
        id_mapping_path=args.id_mapping,
        archive_path=args.archive,
        verification_report_path=args.verification_report,
        dry_run=args.dry_run
    )
    
    # Decommission legacy system
    success = await decommissioner.decommission()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
