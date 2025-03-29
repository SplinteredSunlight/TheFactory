#!/usr/bin/env python3
"""
Setup Project Structure Script

This script sets up the project structure in the task manager for the
AI Orchestration Platform Enhancement project.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the task manager
from src.task_manager.manager import get_task_manager


async def setup_project_structure():
    """Set up the project structure in the task manager."""
    # Initialize task manager
    task_manager = get_task_manager("data/new")
    
    # Create main project
    project = task_manager.create_project(
        name="AI Orchestration Platform Enhancement",
        description="Project to enhance the AI Orchestration Platform with improved organization, dashboard, testing, and documentation",
        metadata={
            "priority": "high",
            "category": "enhancement",
            "start_date": datetime.now().isoformat(),
            "estimated_completion": (datetime.now().replace(month=datetime.now().month + 2)).isoformat()
        }
    )
    
    # Create phases
    phase1 = task_manager.create_phase(
        project_id=project.id,
        name="Cleanup and Organization",
        description="Focus on removing legacy components and organizing the codebase",
        order=1
    )
    
    phase2 = task_manager.create_phase(
        project_id=project.id,
        name="Core Improvements",
        description="Focus on enhancing the Dagger integration and workflow templates",
        order=2
    )
    
    phase3 = task_manager.create_phase(
        project_id=project.id,
        name="Testing Implementation",
        description="Focus on comprehensive testing across all components",
        order=3
    )
    
    phase4 = task_manager.create_phase(
        project_id=project.id,
        name="Dashboard Development",
        description="Focus on implementing the monitoring dashboard",
        order=4
    )
    
    phase5 = task_manager.create_phase(
        project_id=project.id,
        name="Documentation",
        description="Focus on creating comprehensive documentation",
        order=5
    )
    
    # Create tasks for Phase 1: Cleanup and Organization
    task1_1 = task_manager.create_task(
        name="Remove Legacy Migration Files",
        description="Remove migration scripts and legacy data that are no longer needed",
        project_id=project.id,
        phase_id=phase1.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 4,
            "subtasks": [
                "Remove data/legacy directory",
                "Remove migration scripts in scripts/task_manager",
                "Remove .task-manager directory"
            ]
        }
    )
    
    task1_2 = task_manager.create_task(
        name="Standardize Directory Structure",
        description="Implement the desired project structure as outlined in claude-prompt.md",
        project_id=project.id,
        phase_id=phase1.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Reorganize source code directories",
                "Consolidate configuration files",
                "Standardize documentation structure",
                "Organize test files"
            ]
        }
    )
    
    task1_3 = task_manager.create_task(
        name="Consolidate Similar Functionality",
        description="Identify and consolidate duplicate code and similar functionality",
        project_id=project.id,
        phase_id=phase1.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Identify duplicate utility functions",
                "Create common modules for shared functionality",
                "Refactor code to use common modules",
                "Update imports and references"
            ]
        }
    )
    
    task1_4 = task_manager.create_task(
        name="Standardize Naming Conventions",
        description="Implement consistent naming across the project",
        project_id=project.id,
        phase_id=phase1.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Define naming conventions for files, classes, and functions",
                "Update file names to follow conventions",
                "Update class and function names to follow conventions",
                "Update variable names to follow conventions"
            ]
        }
    )
    
    # Create tasks for Phase 2: Core Improvements
    task2_1 = task_manager.create_task(
        name="Enhance Workflow Templates",
        description="Create additional workflow templates for common use cases",
        project_id=project.id,
        phase_id=phase2.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Create CI/CD workflow template",
                "Create data analysis workflow template",
                "Create AI agent workflow template"
            ]
        }
    )
    
    task2_2 = task_manager.create_task(
        name="Improve Parameter Substitution",
        description="Enhance parameter handling in workflow templates",
        project_id=project.id,
        phase_id=phase2.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Add support for complex parameter types",
                "Implement parameter validation",
                "Add default value handling",
                "Support environment variable substitution"
            ]
        }
    )
    
    task2_3 = task_manager.create_task(
        name="Add Workflow Validation",
        description="Implement validation for workflow definitions",
        project_id=project.id,
        phase_id=phase2.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Create schema for workflow validation",
                "Implement validation logic",
                "Add error reporting for invalid workflows",
                "Add validation to workflow creation process"
            ]
        }
    )
    
    task2_4 = task_manager.create_task(
        name="Extend Dagger Integration",
        description="Add support for more workflow types",
        project_id=project.id,
        phase_id=phase2.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 24,
            "subtasks": [
                "Add support for parallel execution",
                "Implement conditional steps",
                "Add support for workflow composition",
                "Implement workflow versioning"
            ]
        }
    )
    
    task2_5 = task_manager.create_task(
        name="Improve Error Handling",
        description="Enhance error handling and recovery mechanisms",
        project_id=project.id,
        phase_id=phase2.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Implement detailed error reporting",
                "Add retry mechanisms for failed steps",
                "Create error recovery strategies",
                "Implement workflow resumption after failure"
            ]
        }
    )
    
    # Create tasks for Phase 3: Testing Implementation
    task3_1 = task_manager.create_task(
        name="Create Unit Tests",
        description="Write unit tests for all components",
        project_id=project.id,
        phase_id=phase3.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 24,
            "subtasks": [
                "Task manager unit tests",
                "Dagger integration unit tests",
                "Workflow template unit tests"
            ]
        }
    )
    
    task3_2 = task_manager.create_task(
        name="Implement Integration Tests",
        description="Create tests for cross-component functionality",
        project_id=project.id,
        phase_id=phase3.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Task-to-workflow integration tests",
                "API-to-task-manager integration tests",
                "Dashboard-to-backend integration tests",
                "End-to-end workflow execution tests"
            ]
        }
    )
    
    task3_3 = task_manager.create_task(
        name="Develop End-to-End Tests",
        description="Implement tests for complete user workflows",
        project_id=project.id,
        phase_id=phase3.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Task creation and execution workflow",
                "Dashboard monitoring workflow",
                "Error handling and recovery workflow",
                "User authentication and authorization workflow"
            ]
        }
    )
    
    task3_4 = task_manager.create_task(
        name="Add Performance Tests",
        description="Create tests for critical performance paths",
        project_id=project.id,
        phase_id=phase3.id,
        status="planned",
        priority="low",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Task creation performance tests",
                "Workflow execution performance tests",
                "Dashboard rendering performance tests",
                "API response time tests"
            ]
        }
    )
    
    # Create tasks for Phase 4: Dashboard Development
    task4_1 = task_manager.create_task(
        name="Design Dashboard UI",
        description="Create the UI design for the comprehensive dashboard",
        project_id=project.id,
        phase_id=phase4.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Create wireframes for dashboard layout",
                "Design component styles and themes",
                "Create responsive design for different screen sizes",
                "Design navigation and user flow"
            ]
        }
    )
    
    task4_2 = task_manager.create_task(
        name="Implement Task Status Visualization",
        description="Create real-time visualization of task status",
        project_id=project.id,
        phase_id=phase4.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Create task list view",
                "Implement task status indicators",
                "Add task filtering and sorting",
                "Implement real-time updates"
            ]
        }
    )
    
    task4_3 = task_manager.create_task(
        name="Add Agent Performance Monitoring",
        description="Implement monitoring for AI agent performance",
        project_id=project.id,
        phase_id=phase4.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Create agent performance metrics",
                "Implement agent status visualization",
                "Add agent resource usage monitoring",
                "Create agent error reporting"
            ]
        }
    )
    
    task4_4 = task_manager.create_task(
        name="Create Metrics and Analytics",
        description="Add visualization components for metrics and analytics",
        project_id=project.id,
        phase_id=phase4.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Implement charts and graphs for key metrics",
                "Create analytics dashboard",
                "Add data export functionality",
                "Implement custom report generation"
            ]
        }
    )
    
    task4_5 = task_manager.create_task(
        name="Integrate with Task Management",
        description="Connect dashboard with the task management system",
        project_id=project.id,
        phase_id=phase4.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Implement API integration",
                "Create real-time data synchronization",
                "Add task creation and update functionality",
                "Implement workflow execution from dashboard"
            ]
        }
    )
    
    # Create tasks for Phase 5: Documentation
    task5_1 = task_manager.create_task(
        name="Create Developer Documentation",
        description="Comprehensive documentation for developers",
        project_id=project.id,
        phase_id=phase5.id,
        status="planned",
        priority="high",
        progress=0.0,
        metadata={
            "estimated_hours": 24,
            "subtasks": [
                "Document code architecture",
                "Create API documentation",
                "Write development setup guide",
                "Document contribution guidelines"
            ]
        }
    )
    
    task5_2 = task_manager.create_task(
        name="Develop User Guides",
        description="User guides for the platform",
        project_id=project.id,
        phase_id=phase5.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Create getting started guide",
                "Write task management guide",
                "Document dashboard usage",
                "Create workflow creation guide"
            ]
        }
    )
    
    task5_3 = task_manager.create_task(
        name="Document API Endpoints",
        description="Documentation for all API endpoints",
        project_id=project.id,
        phase_id=phase5.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 16,
            "subtasks": [
                "Document task management API",
                "Document workflow API",
                "Document dashboard API",
                "Create API usage examples"
            ]
        }
    )
    
    task5_4 = task_manager.create_task(
        name="Update README Files",
        description="Clear README files in each directory",
        project_id=project.id,
        phase_id=phase5.id,
        status="planned",
        priority="medium",
        progress=0.0,
        metadata={
            "estimated_hours": 8,
            "subtasks": [
                "Update main README",
                "Create README files for each component",
                "Add usage examples to READMEs",
                "Include setup instructions in READMEs"
            ]
        }
    )
    
    # Save the data
    task_manager.save_data()
    
    print(f"Project structure created successfully with ID: {project.id}")
    print(f"Created 5 phases and {4 + 5 + 4 + 5 + 4} tasks")
    
    return project.id


if __name__ == "__main__":
    project_id = asyncio.run(setup_project_structure())
