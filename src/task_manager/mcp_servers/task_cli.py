#!/usr/bin/env python3
"""
Task Management CLI Tool

This script provides a command-line interface for interacting with the Task Management system.
It allows users to create, update, and manage projects, phases, and tasks directly from the terminal.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

# Import the task manager
from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority, Task, Phase, Project


class TaskCLI:
    """Command-line interface for the Task Management system."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the Task CLI."""
        self.task_manager = get_task_manager(data_dir)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description="Task Management CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all projects
  task_cli.py list-projects

  # Create a new project
  task_cli.py create-project --name "My Project" --description "A sample project"

  # List tasks in a project
  task_cli.py list-tasks --project-id project_123

  # Create a new task
  task_cli.py create-task --name "Task 1" --description "A sample task" --project-id project_123

  # Update task status
  task_cli.py update-task-status --task-id task_123 --status in_progress

  # Calculate project progress
  task_cli.py calculate-project-progress --project-id project_123
""",
        )

        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        # Project commands
        list_projects_parser = subparsers.add_parser(
            "list-projects", help="List all projects"
        )

        create_project_parser = subparsers.add_parser(
            "create-project", help="Create a new project"
        )
        create_project_parser.add_argument("--name", required=True, help="Project name")
        create_project_parser.add_argument(
            "--description", help="Project description"
        )
        create_project_parser.add_argument(
            "--metadata", help="Project metadata (JSON string)"
        )

        get_project_parser = subparsers.add_parser(
            "get-project", help="Get project details"
        )
        get_project_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )

        update_project_parser = subparsers.add_parser(
            "update-project", help="Update a project"
        )
        update_project_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        update_project_parser.add_argument("--name", help="New project name")
        update_project_parser.add_argument(
            "--description", help="New project description"
        )
        update_project_parser.add_argument(
            "--metadata", help="New project metadata (JSON string)"
        )

        delete_project_parser = subparsers.add_parser(
            "delete-project", help="Delete a project"
        )
        delete_project_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )

        # Phase commands
        create_phase_parser = subparsers.add_parser(
            "create-phase", help="Create a new phase in a project"
        )
        create_phase_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        create_phase_parser.add_argument("--name", required=True, help="Phase name")
        create_phase_parser.add_argument("--description", help="Phase description")
        create_phase_parser.add_argument(
            "--order", type=int, default=0, help="Phase order"
        )
        create_phase_parser.add_argument(
            "--metadata", help="Phase metadata (JSON string)"
        )

        list_phases_parser = subparsers.add_parser(
            "list-phases", help="List phases in a project"
        )
        list_phases_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )

        # Task commands
        create_task_parser = subparsers.add_parser(
            "create-task", help="Create a new task"
        )
        create_task_parser.add_argument("--name", required=True, help="Task name")
        create_task_parser.add_argument(
            "--description", required=True, help="Task description"
        )
        create_task_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        create_task_parser.add_argument("--phase-id", help="Phase ID")
        create_task_parser.add_argument("--parent-id", help="Parent task ID")
        create_task_parser.add_argument(
            "--status",
            choices=[s.value for s in TaskStatus],
            default=TaskStatus.PLANNED.value,
            help="Task status",
        )
        create_task_parser.add_argument(
            "--priority",
            choices=[p.value for p in TaskPriority],
            default=TaskPriority.MEDIUM.value,
            help="Task priority",
        )
        create_task_parser.add_argument(
            "--progress", type=float, default=0.0, help="Task progress (0-100)"
        )
        create_task_parser.add_argument("--assignee-id", help="Assignee ID")
        create_task_parser.add_argument("--assignee-type", help="Assignee type")
        create_task_parser.add_argument(
            "--metadata", help="Task metadata (JSON string)"
        )

        get_task_parser = subparsers.add_parser("get-task", help="Get task details")
        get_task_parser.add_argument("--task-id", required=True, help="Task ID")

        list_tasks_parser = subparsers.add_parser(
            "list-tasks", help="List tasks in a project"
        )
        list_tasks_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        list_tasks_parser.add_argument(
            "--phase-id", help="Filter tasks by phase ID"
        )
        list_tasks_parser.add_argument(
            "--status", choices=[s.value for s in TaskStatus], help="Filter tasks by status"
        )

        update_task_parser = subparsers.add_parser("update-task", help="Update a task")
        update_task_parser.add_argument("--task-id", required=True, help="Task ID")
        update_task_parser.add_argument("--name", help="New task name")
        update_task_parser.add_argument(
            "--description", help="New task description"
        )
        update_task_parser.add_argument("--phase-id", help="New phase ID")
        update_task_parser.add_argument("--parent-id", help="New parent task ID")
        update_task_parser.add_argument(
            "--status",
            choices=[s.value for s in TaskStatus],
            help="New task status",
        )
        update_task_parser.add_argument(
            "--priority",
            choices=[p.value for p in TaskPriority],
            help="New task priority",
        )
        update_task_parser.add_argument(
            "--progress", type=float, help="New task progress (0-100)"
        )
        update_task_parser.add_argument("--assignee-id", help="New assignee ID")
        update_task_parser.add_argument("--assignee-type", help="New assignee type")
        update_task_parser.add_argument(
            "--metadata", help="New task metadata (JSON string)"
        )
        update_task_parser.add_argument("--result", help="Task result (JSON string)")
        update_task_parser.add_argument("--error", help="Task error message")

        update_task_status_parser = subparsers.add_parser(
            "update-task-status", help="Update task status"
        )
        update_task_status_parser.add_argument(
            "--task-id", required=True, help="Task ID"
        )
        update_task_status_parser.add_argument(
            "--status",
            required=True,
            choices=[s.value for s in TaskStatus],
            help="New task status",
        )

        update_task_progress_parser = subparsers.add_parser(
            "update-task-progress", help="Update task progress"
        )
        update_task_progress_parser.add_argument(
            "--task-id", required=True, help="Task ID"
        )
        update_task_progress_parser.add_argument(
            "--progress",
            required=True,
            type=float,
            help="New task progress (0-100)",
        )

        delete_task_parser = subparsers.add_parser("delete-task", help="Delete a task")
        delete_task_parser.add_argument("--task-id", required=True, help="Task ID")

        # Calculation commands
        calculate_project_progress_parser = subparsers.add_parser(
            "calculate-project-progress", help="Calculate project progress"
        )
        calculate_project_progress_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )

        calculate_phase_progress_parser = subparsers.add_parser(
            "calculate-phase-progress", help="Calculate phase progress"
        )
        calculate_phase_progress_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        calculate_phase_progress_parser.add_argument(
            "--phase-id", required=True, help="Phase ID"
        )

        # Query commands
        get_tasks_by_status_parser = subparsers.add_parser(
            "get-tasks-by-status", help="Get tasks by status"
        )
        get_tasks_by_status_parser.add_argument(
            "--project-id", required=True, help="Project ID"
        )
        get_tasks_by_status_parser.add_argument(
            "--status",
            required=True,
            choices=[s.value for s in TaskStatus],
            help="Task status",
        )

        get_tasks_by_assignee_parser = subparsers.add_parser(
            "get-tasks-by-assignee", help="Get tasks by assignee"
        )
        get_tasks_by_assignee_parser.add_argument(
            "--assignee-id", required=True, help="Assignee ID"
        )
        get_tasks_by_assignee_parser.add_argument(
            "--assignee-type", help="Assignee type"
        )

        return parser

    def run(self, args: Optional[List[str]] = None) -> None:
        """Run the CLI with the given arguments."""
        args = self.parser.parse_args(args)

        if not args.command:
            self.parser.print_help()
            return

        try:
            # Project commands
            if args.command == "list-projects":
                self._list_projects()
            elif args.command == "create-project":
                self._create_project(args)
            elif args.command == "get-project":
                self._get_project(args)
            elif args.command == "update-project":
                self._update_project(args)
            elif args.command == "delete-project":
                self._delete_project(args)
            # Phase commands
            elif args.command == "create-phase":
                self._create_phase(args)
            elif args.command == "list-phases":
                self._list_phases(args)
            # Task commands
            elif args.command == "create-task":
                self._create_task(args)
            elif args.command == "get-task":
                self._get_task(args)
            elif args.command == "list-tasks":
                self._list_tasks(args)
            elif args.command == "update-task":
                self._update_task(args)
            elif args.command == "update-task-status":
                self._update_task_status(args)
            elif args.command == "update-task-progress":
                self._update_task_progress(args)
            elif args.command == "delete-task":
                self._delete_task(args)
            # Calculation commands
            elif args.command == "calculate-project-progress":
                self._calculate_project_progress(args)
            elif args.command == "calculate-phase-progress":
                self._calculate_phase_progress(args)
            # Query commands
            elif args.command == "get-tasks-by-status":
                self._get_tasks_by_status(args)
            elif args.command == "get-tasks-by-assignee":
                self._get_tasks_by_assignee(args)
            else:
                print(f"Unknown command: {args.command}")
                self.parser.print_help()
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    def _list_projects(self) -> None:
        """List all projects."""
        projects = self.task_manager.projects
        if not projects:
            print("No projects found.")
            return

        print(f"Found {len(projects)} projects:")
        for project_id, project in projects.items():
            print(f"  {project_id}: {project.name}")
            print(f"    Description: {project.description}")
            print(f"    Phases: {len(project.phases)}")
            print(f"    Tasks: {len(project.tasks)}")
            print()

    def _create_project(self, args: argparse.Namespace) -> None:
        """Create a new project."""
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in metadata")
                sys.exit(1)

        project = self.task_manager.create_project(
            name=args.name,
            description=args.description,
            metadata=metadata,
        )

        print(f"Project created with ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Description: {project.description}")
        print(f"Created at: {project.created_at}")

    def _get_project(self, args: argparse.Namespace) -> None:
        """Get project details."""
        project = self.task_manager.get_project(args.project_id)
        if not project:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        print(f"Project ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Description: {project.description}")
        print(f"Created at: {project.created_at}")
        print(f"Updated at: {project.updated_at}")
        print(f"Phases: {len(project.phases)}")
        print(f"Tasks: {len(project.tasks)}")
        print(f"Metadata: {json.dumps(project.metadata, indent=2)}")

    def _update_project(self, args: argparse.Namespace) -> None:
        """Update a project."""
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in metadata")
                sys.exit(1)

        project = self.task_manager.update_project(
            project_id=args.project_id,
            name=args.name,
            description=args.description,
            metadata=metadata,
        )

        if not project:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        print(f"Project updated: {project.id}")
        print(f"Name: {project.name}")
        print(f"Description: {project.description}")
        print(f"Updated at: {project.updated_at}")

    def _delete_project(self, args: argparse.Namespace) -> None:
        """Delete a project."""
        result = self.task_manager.delete_project(args.project_id)
        if not result:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        print(f"Project deleted: {args.project_id}")

    def _create_phase(self, args: argparse.Namespace) -> None:
        """Create a new phase in a project."""
        project = self.task_manager.get_project(args.project_id)
        if not project:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in metadata")
                sys.exit(1)

        # Generate a phase ID
        import uuid
        phase_id = f"phase_{uuid.uuid4().hex[:8]}"

        phase = project.add_phase(
            phase_id=phase_id,
            name=args.name,
            description=args.description,
            order=args.order,
            metadata=metadata,
        )

        # Save the data
        self.task_manager.save_data()

        print(f"Phase created with ID: {phase.id}")
        print(f"Name: {phase.name}")
        print(f"Description: {phase.description}")
        print(f"Order: {phase.order}")
        print(f"Project ID: {phase.project_id}")

    def _list_phases(self, args: argparse.Namespace) -> None:
        """List phases in a project."""
        project = self.task_manager.get_project(args.project_id)
        if not project:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        phases = project.phases
        if not phases:
            print(f"No phases found in project: {args.project_id}")
            return

        print(f"Found {len(phases)} phases in project {args.project_id}:")
        # Sort phases by order
        sorted_phases = sorted(phases.values(), key=lambda p: p.order)
        for phase in sorted_phases:
            print(f"  {phase.id}: {phase.name}")
            print(f"    Description: {phase.description}")
            print(f"    Order: {phase.order}")
            print(f"    Tasks: {len(phase.tasks)}")
            print()

    def _create_task(self, args: argparse.Namespace) -> None:
        """Create a new task."""
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in metadata")
                sys.exit(1)

        task = self.task_manager.create_task(
            name=args.name,
            description=args.description,
            project_id=args.project_id,
            phase_id=args.phase_id,
            parent_id=args.parent_id,
            status=args.status,
            priority=args.priority,
            progress=args.progress,
            assignee_id=args.assignee_id,
            assignee_type=args.assignee_type,
            metadata=metadata,
        )

        if not task:
            print(f"Failed to create task. Check project ID: {args.project_id}")
            sys.exit(1)

        print(f"Task created with ID: {task.id}")
        print(f"Name: {task.name}")
        print(f"Description: {task.description}")
        print(f"Project ID: {task.project_id}")
        print(f"Phase ID: {task.phase_id}")
        print(f"Parent ID: {task.parent_id}")
        print(f"Status: {task.status.value}")
        print(f"Priority: {task.priority.value}")
        print(f"Progress: {task.progress}")
        print(f"Created at: {task.created_at}")

    def _get_task(self, args: argparse.Namespace) -> None:
        """Get task details."""
        task = self.task_manager.get_task(args.task_id)
        if not task:
            print(f"Task not found: {args.task_id}")
            sys.exit(1)

        print(f"Task ID: {task.id}")
        print(f"Name: {task.name}")
        print(f"Description: {task.description}")
        print(f"Project ID: {task.project_id}")
        print(f"Phase ID: {task.phase_id}")
        print(f"Parent ID: {task.parent_id}")
        print(f"Status: {task.status.value}")
        print(f"Priority: {task.priority.value}")
        print(f"Progress: {task.progress}")
        print(f"Assignee ID: {task.assignee_id}")
        print(f"Assignee Type: {task.assignee_type}")
        print(f"Created at: {task.created_at}")
        print(f"Updated at: {task.updated_at}")
        print(f"Started at: {task.started_at}")
        print(f"Completed at: {task.completed_at}")
        print(f"Children: {task.children}")
        print(f"Metadata: {json.dumps(task.metadata, indent=2)}")
        print(f"Result: {task.result}")
        print(f"Error: {task.error}")

    def _list_tasks(self, args: argparse.Namespace) -> None:
        """List tasks in a project."""
        project = self.task_manager.get_project(args.project_id)
        if not project:
            print(f"Project not found: {args.project_id}")
            sys.exit(1)

        tasks = project.tasks
        if not tasks:
            print(f"No tasks found in project: {args.project_id}")
            return

        # Filter tasks by phase ID if provided
        if args.phase_id:
            tasks = {
                task_id: task
                for task_id, task in tasks.items()
                if task.phase_id == args.phase_id
            }
            if not tasks:
                print(f"No tasks found in phase: {args.phase_id}")
                return

        # Filter tasks by status if provided
        if args.status:
            tasks = {
                task_id: task
                for task_id, task in tasks.items()
                if task.status.value == args.status
            }
            if not tasks:
                print(f"No tasks found with status: {args.status}")
                return

        print(f"Found {len(tasks)} tasks in project {args.project_id}:")
        for task_id, task in tasks.items():
            print(f"  {task_id}: {task.name}")
            print(f"    Description: {task.description}")
            print(f"    Status: {task.status.value}")
            print(f"    Priority: {task.priority.value}")
            print(f"    Progress: {task.progress}")
            print(f"    Phase ID: {task.phase_id}")
            print(f"    Parent ID: {task.parent_id}")
            print()

    def _update_task(self, args: argparse.Namespace) -> None:
        """Update a task."""
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in metadata")
                sys.exit(1)

        result = None
        if args.result:
            try:
                result = json.loads(args.result)
            except json.JSONDecodeError:
                print("Error: Invalid JSON in result")
                sys.exit(1)

        task = self.task_manager.update_task(
            task_id=args.task_id,
            name=args.name,
            description=args.description,
            phase_id=args.phase_id,
            parent_id=args.parent_id,
            status=args.status,
            priority=args.priority,
            progress=args.progress,
            assignee_id=args.assignee_id,
            assignee_type=args.assignee_type,
            metadata=metadata,
            result=result,
            error=args.error,
        )

        if not task:
            print(f"Task not found: {args.task_id}")
            sys.exit(1)

        print(f"Task updated: {task.id}")
        print(f"Name: {task.name}")
        print(f"Description: {task.description}")
        print(f"Status: {task.status.value}")
        print(f"Priority: {task.priority.value}")
        print(f"Progress: {task.progress}")
        print(f"Updated at: {task.updated_at}")

    def _update_task_status(self, args: argparse.Namespace) -> None:
        """Update task status."""
        task = self.task_manager.update_task_status(
            task_id=args.task_id, status=args.status
        )

        if not task:
            print(f"Task not found: {args.task_id}")
            sys.exit(1)

        print(f"Task status updated: {task.id}")
        print(f"New status: {task.status.value}")
        print(f"Updated at: {task.updated_at}")

    def _update_task_progress(self, args: argparse.Namespace) -> None:
        """Update task progress."""
        task = self.task_manager.update_task_progress(
            task_id=args.task_id, progress=args.progress
        )

        if not task:
            print(f"Task not found: {args.task_id}")
            sys.exit(1)

        print(f"Task progress updated: {task.id}")
        print(f"New progress: {task.progress}")
        print(f"Updated at: {task.updated_at}")

    def _delete_task(self, args: argparse.Namespace) -> None:
        """Delete a task."""
        result = self.task_manager.delete_task(args.task_id)
        if not result:
            print(f"Task not found: {args.task_id}")
            sys.exit(1)

        print(f"Task deleted: {args.task_id}")

    def _calculate_project_progress(self, args: argparse.Namespace) -> None:
        """Calculate project progress."""
        progress = self.task_manager.calculate_project_progress(args.project_id)
        print(f"Project progress: {progress:.2f}%")

    def _calculate_phase_progress(self, args: argparse.Namespace) -> None:
        """Calculate phase progress."""
        progress = self.task_manager.calculate_phase_progress(
            args.project_id, args.phase_id
        )
        print(f"Phase progress: {progress:.2f}%")

    def _get_tasks_by_status(self, args: argparse.Namespace) -> None:
        """Get tasks by status."""
        tasks = self.task_manager.get_tasks_by_status(
            args.project_id, args.status
        )

        if not tasks:
            print(f"No tasks found with status {args.status} in project {args.project_id}")
            return

        print(f"Found {len(tasks)} tasks with status {args.status}:")
        for task in tasks:
            print(f"  {task.id}: {task.name}")
            print(f"    Description: {task.description}")
            print(f"    Priority: {task.priority.value}")
            print(f"    Progress: {task.progress}")
            print(f"    Phase ID: {task.phase_id}")
            print()

    def _get_tasks_by_assignee(self, args: argparse.Namespace) -> None:
        """Get tasks by assignee."""
        tasks = self.task_manager.get_tasks_by_assignee(
            args.assignee_id, args.assignee_type
        )

        if not tasks:
            print(f"No tasks found assigned to {args.assignee_id}")
            return

        print(f"Found {len(tasks)} tasks assigned to {args.assignee_id}:")
        for task in tasks:
            print(f"  {task.id}: {task.name}")
            print(f"    Description: {task.description}")
            print(f"    Status: {task.status.value}")
            print(f"    Priority: {task.priority.value}")
            print(f"    Progress: {task.progress}")
            print(f"    Project ID: {task.project_id}")
            print(f"    Phase ID: {task.phase_id}")
            print()


def main():
    """Run the Task CLI."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Task Management CLI Tool")
    parser.add_argument("--data-dir", help="Directory for task manager data")
    
    # Parse only the known arguments
    args, remaining = parser.parse_known_args()
    
    # Create and run the CLI
    cli = TaskCLI(data_dir=args.data_dir)
    cli.run(remaining)


if __name__ == "__main__":
    main()
