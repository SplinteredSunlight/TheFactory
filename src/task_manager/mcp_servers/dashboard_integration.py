#!/usr/bin/env python3
"""
Dashboard UI Integration for Task Management MCP Server

This module extends the Task Manager MCP Server with dashboard-specific tools and resources
to enable integration with the Project Master Dashboard.
"""

import asyncio
import json
import os
import sys
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from mcp.types import (
    CallToolRequest,
    ErrorCode,
    ListResourcesRequestSchema,
    ListResourceTemplatesRequestSchema,
    ListToolsRequestSchema,
    McpError,
    ReadResourceRequestSchema,
)

# Import the Task Manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority, Task, Phase, Project


class DashboardIntegration:
    """Dashboard UI Integration for the Task Manager MCP Server."""

    def __init__(self, server, task_manager):
        """Initialize the Dashboard Integration component.
        
        Args:
            server: The MCP server instance
            task_manager: The Task Manager instance
        """
        self.server = server
        self.task_manager = task_manager
        
        # Set up dashboard-specific resources and tools
        self.setup_dashboard_resources()
        self.setup_dashboard_tools()

    def setup_dashboard_resources(self):
        """Set up dashboard-specific resources for the MCP server."""
        # Add dashboard resources to the list_resources handler
        original_list_resources = self.server._request_handlers.get(ListResourcesRequestSchema.__name__)
        
        async def enhanced_list_resources(request):
            """Enhanced handler for listing resources that includes dashboard resources."""
            # Get original resources
            original_response = await original_list_resources(request)
            resources = original_response.get("resources", [])
            
            # Add dashboard-specific resources
            dashboard_resources = [
                {
                    "uri": "task-manager://dashboard/stats",
                    "name": "Dashboard Statistics",
                    "mimeType": "application/json",
                    "description": "Statistics for the Project Master Dashboard",
                },
                {
                    "uri": "task-manager://dashboard/config",
                    "name": "Dashboard Configuration",
                    "mimeType": "application/json",
                    "description": "Configuration for the Project Master Dashboard",
                },
                {
                    "uri": "task-manager://dashboard/projects/summary",
                    "name": "Projects Summary",
                    "mimeType": "application/json",
                    "description": "Summary of all projects for the dashboard",
                },
                {
                    "uri": "task-manager://dashboard/tasks/recent",
                    "name": "Recent Tasks",
                    "mimeType": "application/json",
                    "description": "Recently updated tasks for the dashboard",
                },
            ]
            
            resources.extend(dashboard_resources)
            return {"resources": resources}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListResourcesRequestSchema, enhanced_list_resources)
        
        # Add dashboard resource templates
        original_list_templates = self.server._request_handlers.get(ListResourceTemplatesRequestSchema.__name__)
        
        async def enhanced_list_templates(request):
            """Enhanced handler for listing resource templates that includes dashboard templates."""
            # Get original templates
            original_response = await original_list_templates(request)
            templates = original_response.get("resourceTemplates", [])
            
            # Add dashboard-specific templates
            dashboard_templates = [
                {
                    "uriTemplate": "task-manager://dashboard/projects/{project_id}/summary",
                    "name": "Project Dashboard Summary",
                    "mimeType": "application/json",
                    "description": "Dashboard summary for a specific project",
                },
                {
                    "uriTemplate": "task-manager://dashboard/projects/{project_id}/phases/{phase_id}/tasks",
                    "name": "Phase Tasks for Dashboard",
                    "mimeType": "application/json",
                    "description": "Tasks in a specific phase for the dashboard",
                },
            ]
            
            templates.extend(dashboard_templates)
            return {"resourceTemplates": templates}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListResourceTemplatesRequestSchema, enhanced_list_templates)
        
        # Enhance the read_resource handler to handle dashboard resources
        original_read_resource = self.server._request_handlers.get(ReadResourceRequestSchema.__name__)
        
        async def enhanced_read_resource(request):
            """Enhanced handler for reading resources that handles dashboard resources."""
            uri = request.params.uri
            
            # Handle dashboard-specific resources
            if uri.startswith("task-manager://dashboard/"):
                return await self._handle_dashboard_resource(uri)
            
            # For other resources, use the original handler
            return await original_read_resource(request)
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ReadResourceRequestSchema, enhanced_read_resource)

    async def _handle_dashboard_resource(self, uri):
        """Handle dashboard-specific resources.
        
        Args:
            uri: The resource URI
            
        Returns:
            The resource content
            
        Raises:
            McpError: If the resource is not found
        """
        # Dashboard statistics
        if uri == "task-manager://dashboard/stats":
            stats = self._get_dashboard_stats()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(stats, indent=2),
                    }
                ],
            }
        
        # Dashboard configuration
        elif uri == "task-manager://dashboard/config":
            config = self._get_dashboard_config()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(config, indent=2),
                    }
                ],
            }
        
        # Projects summary
        elif uri == "task-manager://dashboard/projects/summary":
            summaries = self._get_projects_summary()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(summaries, indent=2),
                    }
                ],
            }
        
        # Recent tasks
        elif uri == "task-manager://dashboard/tasks/recent":
            tasks = self._get_recent_tasks(limit=10)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(tasks, indent=2),
                    }
                ],
            }
        
        # Project dashboard summary
        elif uri.startswith("task-manager://dashboard/projects/") and uri.endswith("/summary"):
            # Extract project_id from URI
            parts = uri.split("/")
            if len(parts) >= 5:
                project_id = parts[4]
                summary = self._get_project_summary(project_id)
                if summary:
                    return {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(summary, indent=2),
                            }
                        ],
                    }
        
        # Phase tasks for dashboard
        elif uri.startswith("task-manager://dashboard/projects/") and "/phases/" in uri and uri.endswith("/tasks"):
            # Extract project_id and phase_id from URI
            parts = uri.split("/")
            if len(parts) >= 7:
                project_id = parts[4]
                phase_id = parts[6]
                tasks = self._get_phase_tasks(project_id, phase_id)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(tasks, indent=2),
                        }
                    ],
                }
        
        # If we get here, the resource wasn't found
        raise McpError(ErrorCode.NotFound, f"Resource not found: {uri}")

    def _get_dashboard_stats(self):
        """Get dashboard statistics.
        
        Returns:
            Dict containing dashboard statistics
        """
        projects = list(self.task_manager.projects.values())
        
        # Count projects by status
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if any(
            t.status == TaskStatus.IN_PROGRESS for t in p.tasks.values()
        ))
        completed_projects = sum(1 for p in projects if all(
            t.status == TaskStatus.COMPLETED for t in p.tasks.values()
        ) and len(p.tasks) > 0)
        
        # Count tasks by status
        all_tasks = [task for p in projects for task in p.tasks.values()]
        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.IN_PROGRESS)
        planned_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.PLANNED)
        blocked_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.BLOCKED)
        
        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "planned_tasks": planned_tasks,
            "blocked_tasks": blocked_tasks,
            "timestamp": datetime.now().isoformat()
        }

    def _get_dashboard_config(self):
        """Get dashboard configuration.
        
        Returns:
            Dict containing dashboard configuration
        """
        # Default configuration
        config = {
            "api": {
                "baseUrl": "http://localhost:8000",
                "authToken": "",
                "refreshInterval": 30000
            },
            "scan": {
                "enabled": True,
                "directories": [
                    "./src/task_manager/data/projects",
                    "./tasks"
                ],
                "depth": 2,
                "includePatterns": ["*.json", "*.yaml", "*.md"],
                "excludePatterns": ["node_modules", ".git", "dist", "build"]
            },
            "ui": {
                "theme": "light",
                "defaultView": "projects",
                "refreshInterval": 30000,
                "showCompletedTasks": True
            },
            "dashboard": {
                "title": "Project Master Dashboard",
                "logo": "",
                "showProjectSelector": True,
                "defaultProjectId": "",
                "enableTaskManagement": True,
                "enableRealTimeUpdates": True
            },
            "integration": {
                "aiOrchestrationPlatform": {
                    "enabled": True,
                    "apiEndpoint": "http://localhost:8000",
                    "authToken": "",
                    "projectId": ""
                },
                "mcp": {
                    "enabled": True,
                    "serverName": "task-manager",
                    "refreshInterval": 30000
                }
            }
        }
        
        # Try to load configuration from file
        config_path = os.path.join("dashboard", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    # Merge saved config with default config
                    for key, value in saved_config.items():
                        if key in config and isinstance(config[key], dict):
                            config[key].update(value)
                        else:
                            config[key] = value
            except Exception as e:
                # Use default config if there's an error
                pass
        
        return config

    def _get_projects_summary(self):
        """Get a summary of all projects.
        
        Returns:
            List of project summaries
        """
        projects = list(self.task_manager.projects.values())
        
        summaries = []
        for project in projects:
            # Calculate project progress
            total_tasks = len(project.tasks)
            completed_tasks = sum(1 for t in project.tasks.values() if t.status == TaskStatus.COMPLETED)
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get phase information
            phases = []
            for phase_id, phase in project.phases.items():
                phase_tasks = [project.tasks[task_id] for task_id in phase.tasks if task_id in project.tasks]
                phase_total = len(phase_tasks)
                phase_completed = sum(1 for t in phase_tasks if t.status == TaskStatus.COMPLETED)
                phase_progress = (phase_completed / phase_total * 100) if phase_total > 0 else 0
                
                phases.append({
                    "id": phase_id,
                    "name": phase.name,
                    "order": phase.order,
                    "taskCount": phase_total,
                    "completedTasks": phase_completed,
                    "progress": phase_progress
                })
            
            # Sort phases by order
            phases.sort(key=lambda p: p["order"])
            
            # Create project summary
            summary = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "taskCount": total_tasks,
                "completedTasks": completed_tasks,
                "progress": progress,
                "phases": phases,
                "createdAt": project.created_at.isoformat() if hasattr(project, 'created_at') else None,
                "updatedAt": project.updated_at.isoformat() if hasattr(project, 'updated_at') else None
            }
            
            summaries.append(summary)
        
        return summaries

    def _get_project_summary(self, project_id):
        """Get a summary of a specific project.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dict containing project summary or None if project not found
        """
        project = self.task_manager.get_project(project_id)
        if not project:
            return None
        
        # Calculate project progress
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks.values() if t.status == TaskStatus.COMPLETED)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get phase information
        phases = []
        for phase_id, phase in project.phases.items():
            phase_tasks = [project.tasks[task_id] for task_id in phase.tasks if task_id in project.tasks]
            phase_total = len(phase_tasks)
            phase_completed = sum(1 for t in phase_tasks if t.status == TaskStatus.COMPLETED)
            phase_progress = (phase_completed / phase_total * 100) if phase_total > 0 else 0
            
            phases.append({
                "id": phase_id,
                "name": phase.name,
                "order": phase.order,
                "taskCount": phase_total,
                "completedTasks": phase_completed,
                "progress": phase_progress
            })
        
        # Sort phases by order
        phases.sort(key=lambda p: p["order"])
        
        # Create project summary
        summary = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "taskCount": total_tasks,
            "completedTasks": completed_tasks,
            "progress": progress,
            "phases": phases,
            "createdAt": project.created_at.isoformat() if hasattr(project, 'created_at') else None,
            "updatedAt": project.updated_at.isoformat() if hasattr(project, 'updated_at') else None
        }
        
        return summary

    def _get_recent_tasks(self, limit=10):
        """Get recently updated tasks.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of recent tasks
        """
        # Collect all tasks from all projects
        all_tasks = []
        for project in self.task_manager.projects.values():
            for task_id, task in project.tasks.items():
                # Add project information to task
                task_dict = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status.value,
                    "progress": task.progress,
                    "projectId": project.id,
                    "projectName": project.name,
                    "phaseId": task.phase_id,
                    "phaseName": project.phases[task.phase_id].name if task.phase_id in project.phases else None,
                    "updatedAt": task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
                }
                all_tasks.append(task_dict)
        
        # Sort by updated_at (most recent first)
        all_tasks.sort(key=lambda t: t["updatedAt"] if t["updatedAt"] else "", reverse=True)
        
        # Return limited number of tasks
        return all_tasks[:limit]

    def _get_phase_tasks(self, project_id, phase_id):
        """Get tasks in a specific phase.
        
        Args:
            project_id: The ID of the project
            phase_id: The ID of the phase
            
        Returns:
            List of tasks in the phase
        """
        project = self.task_manager.get_project(project_id)
        if not project:
            return []
        
        phase = project.phases.get(phase_id)
        if not phase:
            return []
        
        tasks = []
        for task_id in phase.tasks:
            if task_id in project.tasks:
                task = project.tasks[task_id]
                task_dict = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value if hasattr(task, 'priority') else None,
                    "progress": task.progress,
                    "assigneeId": task.assignee_id if hasattr(task, 'assignee_id') else None,
                    "assigneeType": task.assignee_type if hasattr(task, 'assignee_type') else None,
                    "createdAt": task.created_at.isoformat() if hasattr(task, 'created_at') else None,
                    "updatedAt": task.updated_at.isoformat() if hasattr(task, 'updated_at') else None
                }
                tasks.append(task_dict)
        
        return tasks

    def setup_dashboard_tools(self):
        """Set up dashboard-specific tools for the MCP server."""
        # Add dashboard tools to the list_tools handler
        original_list_tools = self.server._request_handlers.get(ListToolsRequestSchema.__name__)
        
        async def enhanced_list_tools(request):
            """Enhanced handler for listing tools that includes dashboard tools."""
            # Get original tools
            original_response = await original_list_tools(request)
            tools = original_response.get("tools", [])
            
            # Add dashboard-specific tools
            dashboard_tools = [
                {
                    "name": "update_dashboard_config",
                    "description": "Update the dashboard configuration",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "config": {
                                "type": "object",
                                "description": "Dashboard configuration",
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["config"],
                    },
                },
                {
                    "name": "scan_directory",
                    "description": "Scan a directory for project files",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory to scan",
                            },
                            "depth": {
                                "type": "integer",
                                "description": "Scan depth",
                                "default": 2,
                            },
                            "include_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to include",
                                "default": ["*.json", "*.yaml", "*.md"],
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to exclude",
                                "default": ["node_modules", ".git", "dist", "build"],
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                        "required": ["directory"],
                    },
                },
                {
                    "name": "get_dashboard_stats",
                    "description": "Get dashboard statistics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                    },
                },
                {
                    "name": "get_projects_summary",
                    "description": "Get a summary of all projects for the dashboard",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                    },
                },
                {
                    "name": "get_recent_tasks",
                    "description": "Get recently updated tasks for the dashboard",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of tasks to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100,
                            },
                            "auth_token": {
                                "type": "string",
                                "description": "Authentication token (if required)",
                            },
                        },
                    },
                },
            ]
            
            tools.extend(dashboard_tools)
            return {"tools": tools}
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(ListToolsRequestSchema, enhanced_list_tools)
        
        # Enhance the call_tool handler to handle dashboard tools
        original_call_tool = self.server._request_handlers.get(CallToolRequest.__name__)
        
        async def enhanced_call_tool(request):
            """Enhanced handler for calling tools that handles dashboard tools."""
            tool_name = request.params.name
            args = request.params.arguments
            
            # Handle dashboard-specific tools
            if tool_name in ["update_dashboard_config", "scan_directory", "get_dashboard_stats", 
                            "get_projects_summary", "get_recent_tasks"]:
                return await self._handle_dashboard_tool(tool_name, args)
            
            # For other tools, use the original handler
            return await original_call_tool(request)
        
        # Replace the original handler with the enhanced one
        self.server.set_request_handler(CallToolRequest, enhanced_call_tool)

    async def _handle_dashboard_tool(self, tool_name, args):
        """Handle dashboard-specific tools.
        
        Args:
            tool_name: The name of the tool
            args: The tool arguments
            
        Returns:
            The tool result
            
        Raises:
            McpError: If there's an error executing the tool
        """
        try:
            # Update dashboard configuration
            if tool_name == "update_dashboard_config":
                # Validate required arguments
                if "config" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: config",
                    )
                
                # Update the configuration
                config = args["config"]
                config_path = os.path.join("dashboard", "config.json")
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
                # Write config to file
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"success": True, "config": config}, indent=2),
                        }
                    ],
                }
            
            # Scan directory for project files
            elif tool_name == "scan_directory":
                # Validate required arguments
                if "directory" not in args:
                    raise McpError(
                        ErrorCode.InvalidParams,
                        "Missing required parameter: directory",
                    )
                
                # Get scan parameters
                directory = args["directory"]
                depth = args.get("depth", 2)
                include_patterns = args.get("include_patterns", ["*.json", "*.yaml", "*.md"])
                exclude_patterns = args.get("exclude_patterns", ["node_modules", ".git", "dist", "build"])
                
                # Validate directory
                if not os.path.isdir(directory):
                    raise McpError(
                        ErrorCode.InvalidParams,
                        f"Directory not found: {directory}",
                    )
                
                # Scan directory for project files
                projects = await self._scan_directory(
                    directory, depth, include_patterns, exclude_patterns
                )
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"projects": projects}, indent=2),
                        }
                    ],
                }
            
            # Get dashboard statistics
            elif tool_name == "get_dashboard_stats":
                stats = self._get_dashboard_stats()
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(stats, indent=2),
                        }
                    ],
                }
            
            # Get projects summary
            elif tool_name == "get_projects_summary":
                summaries = self._get_projects_summary()
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(summaries, indent=2),
                        }
                    ],
                }
            
            # Get recent tasks
            elif tool_name == "get_recent_tasks":
                limit = args.get("limit", 10)
                tasks = self._get_recent_tasks(limit=limit)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tasks, indent=2),
                        }
                    ],
                }
            
            # If we get here, the tool wasn't found
            raise McpError(ErrorCode.MethodNotFound, f"Unknown tool: {tool_name}")
        
        except McpError:
            # Re-raise MCP errors
            raise
        except Exception as e:
            # Convert other exceptions to MCP errors
            raise McpError(ErrorCode.InternalError, f"Internal error: {str(e)}")

    async def _scan_directory(self, directory, depth, include_patterns, exclude_patterns):
        """Scan a directory for project files.
        
        Args:
            directory: Directory to scan
            depth: Scan depth
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            List of projects found in the directory
        """
        import glob
        import fnmatch
        
        projects = []
        
        # Helper function to check if a path matches any pattern
        def matches_any_pattern(path, patterns):
            return any(fnmatch.fnmatch(os.path.basename(path), pattern) for pattern in patterns)
        
        # Helper function to scan directory recursively
        def scan_dir(dir_path, current_depth):
            if current_depth <= 0:
                return
            
            try:
                entries = os.listdir(dir_path)
                
                for entry in entries:
                    entry_path = os.path.join(dir_path, entry)
                    
                    # Skip excluded patterns
                    if matches_any_pattern(entry_path, exclude_patterns):
                        continue
                    
                    if os.path.isdir(entry_path):
                        # Recursively scan subdirectory
                        scan_dir(entry_path, current_depth - 1)
                    elif os.path.isfile(entry_path):
                        # Check if file matches include patterns
                        if matches_any_pattern(entry_path, include_patterns):
                            try:
                                # Try to parse as JSON
                                if entry_path.endswith('.json'):
                                    with open(entry_path, 'r') as f:
                                        data = json.load(f)
                                    
                                    # Check if it's a project file
                                    if isinstance(data, dict) and "tasks" in data and "name" in data:
                                        projects.append(data)
                                
                                # Parse YAML files
                                elif entry_path.endswith(('.yaml', '.yml')):
                                    try:
                                        import yaml
                                        with open(entry_path, 'r') as f:
                                            data = yaml.safe_load(f)
                                        
                                        # Check if it's a project file
                                        if isinstance(data, dict) and "tasks" in data and "name" in data:
                                            projects.append(data)
                                    except ImportError:
                                        # YAML module not available
                                        pass
                                
                                # Parse Markdown files
                                elif entry_path.endswith('.md'):
                                    with open(entry_path, 'r') as f:
                                        content = f.read()
                                    
                                    # Extract project info from markdown
                                    project_info = self._extract_project_info_from_markdown(content)
                                    if project_info:
                                        projects.append(project_info)
                            
                            except Exception as e:
                                # Skip files that can't be parsed
                                continue
            
            except Exception as e:
                # Skip directories that can't be accessed
                pass
        
        # Start scanning from the root directory
        scan_dir(directory, depth)
        
        return projects
    
    def _extract_project_info_from_markdown(self, content):
        """Extract project information from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Dict containing project information or None if no project info found
        """
        # Simple extraction of project info from markdown
        # This is a basic implementation that can be extended
        
        if not content:
            return None
            
        lines = content.split('\n')
        
        # Extract title from first heading
        title = None
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        if not title:
            # Try to find any heading if no level 1 heading
            for line in lines:
                if line.startswith('## '):
                    title = line[3:].strip()
                    break
        
        if not title:
            # Use filename as fallback
            return None
        
        # Extract description from content below title
        description = ""
        description_started = False
        for line in lines:
            if line.startswith('# ') or line.startswith('## '):
                if description_started:
                    break
                description_started = True
                continue
            
            if description_started and line.strip() and not line.startswith('#'):
                description += line.strip() + " "
        
        # Extract tasks from markdown
        tasks = {}
        current_task = None
        task_id = 1
        
        for i, line in enumerate(lines):
            # Look for task markers like "- [ ]" or "- [x]"
            if re.match(r'^\s*-\s*\[\s*[xX ]?\s*\]', line):
                task_text = re.sub(r'^\s*-\s*\[\s*[xX ]?\s*\]\s*', '', line).strip()
                is_completed = '[x]' in line.lower()
                
                current_task = {
                    "id": f"task_{task_id}",
                    "name": task_text,
                    "description": "",
                    "status": TaskStatus.COMPLETED.value if is_completed else TaskStatus.PLANNED.value,
                    "progress": 100 if is_completed else 0,
                    "phase_id": "default_phase"
                }
                tasks[f"task_{task_id}"] = current_task
                task_id += 1
            
            # Add indented lines as description to the current task
            elif current_task and i + 1 < len(lines) and lines[i + 1].startswith('    '):
                current_task["description"] += lines[i + 1].strip() + " "
        
        # Create phases
        phases = {
            "default_phase": {
                "id": "default_phase",
                "name": "Default Phase",
                "order": 1,
                "tasks": list(tasks.keys())
            }
        }
        
        # Create project info
        project_info = {
            "id": re.sub(r'[^a-zA-Z0-9_-]', '_', title.lower()),
            "name": title,
            "description": description.strip(),
            "tasks": tasks,
            "phases": phases
        }
        
        return project_info
