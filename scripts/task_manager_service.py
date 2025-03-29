#!/usr/bin/env python3
"""
Task Manager Service

This script provides a service for managing tasks in the AI Orchestration Platform.
It can find the next task to work on, generate prompts, and mark tasks as complete.
"""

import argparse
import asyncio
import json
import os
import sys
import textwrap
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the task manager and dagger integration
from src.task_manager.manager import get_task_manager, Task, Project, Phase
from src.task_manager.dagger_integration import get_task_workflow_integration


class TaskManagerService:
    """Task Manager Service class for managing tasks."""
    
    def __init__(self, data_path: str = "data/new"):
        """
        Initialize a TaskManagerService.
        
        Args:
            data_path: Path to task data
        """
        self.data_path = data_path
        self.task_manager = get_task_manager(data_path)
        self.workflow_integration = get_task_workflow_integration(
            dagger_config_path="config/dagger.yaml",
            templates_dir="templates"
        )
    
    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Get a project by name.
        
        Args:
            name: Project name
        
        Returns:
            Project or None if not found
        """
        for project in self.task_manager.projects.values():
            if project.name == name:
                return project
        return None
    
    def get_phase_by_name(self, project_id: str, name: str) -> Optional[Phase]:
        """
        Get a phase by name.
        
        Args:
            project_id: Project ID
            name: Phase name
        
        Returns:
            Phase or None if not found
        """
        project = self.task_manager.get_project(project_id)
        if not project:
            return None
        
        for phase in project.phases.values():
            if phase.name == name:
                return phase
        return None
    
    def get_task_by_name(self, name: str) -> Optional[Task]:
        """
        Get a task by name.
        
        Args:
            name: Task name
        
        Returns:
            Task or None if not found
        """
        for project in self.task_manager.projects.values():
            for task in project.tasks.values():
                if task.name == name:
                    return task
        return None
    
    def get_next_task(self, project_name: Optional[str] = None) -> Optional[Task]:
        """
        Get the next task to work on.
        
        Args:
            project_name: Project name to filter by
        
        Returns:
            Next task or None if no tasks are available
        """
        # Get all tasks
        all_tasks = []
        for project in self.task_manager.projects.values():
            # Filter by project name if provided
            if project_name and project.name != project_name:
                continue
            
            for task in project.tasks.values():
                # Only consider planned tasks
                if task.status == "planned":
                    all_tasks.append((project, task))
        
        if not all_tasks:
            return None
        
        # Sort tasks by phase order, then by priority
        def get_phase_order(project_task: Tuple[Project, Task]) -> int:
            project, task = project_task
            if task.phase_id and task.phase_id in project.phases:
                return project.phases[task.phase_id].order
            return 999  # High number for tasks without a phase
        
        def get_priority_value(project_task: Tuple[Project, Task]) -> int:
            _, task = project_task
            if task.priority == "high":
                return 0
            elif task.priority == "medium":
                return 1
            elif task.priority == "low":
                return 2
            return 3  # Default for tasks without a priority
        
        sorted_tasks = sorted(all_tasks, key=lambda pt: (get_phase_order(pt), get_priority_value(pt)))
        
        # Return the first task
        if sorted_tasks:
            return sorted_tasks[0][1]
        
        return None
    
    def mark_task_complete(self, task_id: str) -> Optional[Task]:
        """
        Mark a task as complete.
        
        Args:
            task_id: Task ID
        
        Returns:
            Updated task or None if not found
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return None
        
        # Update task status and progress
        updated_task = self.task_manager.update_task(
            task_id=task_id,
            status="completed",
            progress=100.0,
            metadata={
                **task.metadata,
                "completed_at": datetime.now().isoformat()
            }
        )
        
        # Save the data
        self.task_manager.save_data()
        
        return updated_task
    
    def generate_task_prompt(self, task: Task) -> str:
        """
        Generate a prompt for a task.
        
        Args:
            task: Task to generate prompt for
        
        Returns:
            Task prompt
        """
        # Get the project and phase
        project = None
        phase = None
        for p in self.task_manager.projects.values():
            if p.id == task.project_id:
                project = p
                if task.phase_id and task.phase_id in p.phases:
                    phase = p.phases[task.phase_id]
                break
        
        # Build the prompt
        prompt = f"# Task: {task.name}\n\n"
        
        if project:
            prompt += f"**Project**: {project.name}\n"
        
        if phase:
            prompt += f"**Phase**: {phase.name}\n"
        
        prompt += f"**Priority**: {task.priority or 'Not specified'}\n"
        prompt += f"**Status**: {task.status}\n"
        prompt += f"**Progress**: {task.progress or 0}%\n\n"
        
        prompt += f"## Description\n\n{task.description}\n\n"
        
        # Add subtasks if available
        if task.metadata and "subtasks" in task.metadata:
            prompt += "## Subtasks\n\n"
            for subtask in task.metadata["subtasks"]:
                prompt += f"- [ ] {subtask}\n"
            prompt += "\n"
        
        # Add estimated hours if available
        if task.metadata and "estimated_hours" in task.metadata:
            prompt += f"**Estimated Hours**: {task.metadata['estimated_hours']}\n\n"
        
        # Add acceptance criteria
        prompt += "## Acceptance Criteria\n\n"
        prompt += "- All subtasks completed\n"
        prompt += "- Code follows project standards\n"
        prompt += "- Tests pass\n"
        prompt += "- Documentation updated\n\n"
        
        # Add instructions for completion
        prompt += "## Instructions\n\n"
        prompt += "1. Complete all subtasks\n"
        prompt += "2. Run tests to ensure everything works\n"
        prompt += "3. Update documentation if necessary\n"
        prompt += "4. Mark the task as complete using the task manager service\n\n"
        
        prompt += "To mark this task as complete, run:\n\n"
        prompt += f"```bash\npython scripts/task_manager_service.py complete \"{task.name}\"\n```\n"
        
        return prompt
    
    async def execute_task_workflow(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a workflow for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            Workflow execution result
        """
        # Get the task
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Create workflow parameters based on task metadata
        workflow_params = {
            "task_name": task.name,
            "task_description": task.description,
            "task_command": f"echo 'Executing task: {task.name}'",
            "task_timeout": 3600,
            "task_image": "alpine:latest",
            "task_environment": {},
            "task_working_dir": "/app",
            "task_mounts": []
        }
        
        # Execute the workflow
        result = await self.workflow_integration.execute_task_workflow(
            task_id=task.id,
            workflow_type="basic_task",
            workflow_params=workflow_params,
            skip_cache=True
        )
        
        # Update the task with the workflow result
        self.task_manager.update_task(
            task_id=task.id,
            status="in_progress",
            progress=25.0,
            result=result
        )
        
        # Save the data
        self.task_manager.save_data()
        
        return result


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Task Manager Service")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Next task command
    next_parser = subparsers.add_parser("next", help="Get the next task")
    next_parser.add_argument("--project", help="Project name to filter by")
    next_parser.add_argument("--execute", action="store_true", help="Execute the task workflow")
    
    # Complete task command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as complete")
    complete_parser.add_argument("task_name", help="Task name to mark as complete")
    
    # Details command
    details_parser = subparsers.add_parser("details", help="Get details about a task")
    details_parser.add_argument("task_name", help="Task name to get details for")
    
    # List tasks command
    list_parser = subparsers.add_parser("list", help="List all tasks")
    list_parser.add_argument("--project", help="Project name to filter by")
    list_parser.add_argument("--status", help="Task status to filter by")
    
    args = parser.parse_args()
    
    # Initialize the task manager service
    service = TaskManagerService()
    
    if args.command == "next":
        # Get the next task
        next_task = service.get_next_task(args.project)
        if not next_task:
            print("No tasks available")
            return
        
        # Generate and print the task prompt
        prompt = service.generate_task_prompt(next_task)
        print(prompt)
        
        # Execute the task workflow if requested
        if args.execute:
            print(f"Executing workflow for task: {next_task.name}")
            result = await service.execute_task_workflow(next_task.id)
            print(f"Workflow execution result: {json.dumps(result, indent=2)}")
    
    elif args.command == "complete":
        # Find the task by name
        task = service.get_task_by_name(args.task_name)
        if not task:
            print(f"Task '{args.task_name}' not found")
            return
        
        # Mark the task as complete
        updated_task = service.mark_task_complete(task.id)
        if not updated_task:
            print(f"Failed to mark task '{args.task_name}' as complete")
            return
        
        print(f"Task '{args.task_name}' marked as complete")
        
        # Get the next task
        next_task = service.get_next_task()
        if not next_task:
            print("No more tasks available")
            return
        
        # Generate and print the task prompt
        print("\nNext task:")
        prompt = service.generate_task_prompt(next_task)
        print(prompt)
    
    elif args.command == "details":
        # Find the task by name
        task = service.get_task_by_name(args.task_name)
        if not task:
            print(f"Task '{args.task_name}' not found")
            return
        
        # Generate and print the task prompt
        prompt = service.generate_task_prompt(task)
        print(prompt)
    
    elif args.command == "list":
        # Get all tasks
        all_tasks = []
        for project in service.task_manager.projects.values():
            # Filter by project name if provided
            if args.project and project.name != args.project:
                continue
            
            for task in project.tasks.values():
                # Filter by task status if provided
                if args.status and task.status != args.status:
                    continue
                
                all_tasks.append((project, task))
        
        if not all_tasks:
            print("No tasks found")
            return
        
        # Print tasks
        print(f"Found {len(all_tasks)} tasks:")
        for project, task in all_tasks:
            phase_name = ""
            if task.phase_id and task.phase_id in project.phases:
                phase_name = project.phases[task.phase_id].name
            
            print(f"- {task.name} ({project.name}, {phase_name}, {task.status}, {task.priority})")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
