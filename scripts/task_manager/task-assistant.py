#!/usr/bin/env python3
"""
Task Assistant - A command-line interface for the Task Management MCP Server

This script provides a simple command-line interface for interacting with the
Task Management MCP Server. It can automatically start the server and dashboard UI
when you type in commands like "project status", "next task", or "what's next".
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Define command patterns
PROJECT_STATUS_PATTERNS = [
    r"project\s+status",
    r"status\s+of\s+project",
    r"how\s+is\s+the\s+project",
    r"project\s+progress",
]

NEXT_TASK_PATTERNS = [
    r"next\s+task",
    r"what'?s\s+next",
    r"upcoming\s+task",
    r"todo",
    r"to\s+do",
]

ALL_PATTERNS = PROJECT_STATUS_PATTERNS + NEXT_TASK_PATTERNS

# Global variables for processes
server_process = None
dashboard_process = None
http_port = 8080
dashboard_port = 8081
server_started = False
dashboard_started = False

def find_available_port(start_port=8080, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port  # Fallback to the start port if none available

def start_server(data_dir=None, dagger_config=None, enable_dagger=False):
    """Start the Mock API Server."""
    global server_process, server_started, http_port
    
    if server_started:
        print("Server is already running.")
        return
    
    # Find an available port
    http_port = find_available_port()
    
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    server_script = script_dir / "mock-api-server.js"
    
    # Start the server process
    try:
        env = os.environ.copy()
        env["PORT"] = str(http_port)
        
        server_process = subprocess.Popen(
            ["node", str(server_script)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        # Wait for the server to start
        time.sleep(2)
        
        if server_process.poll() is None:
            print("Mock API Server started successfully.")
            server_started = True
        else:
            stdout, stderr = server_process.communicate()
            print(f"Failed to start server: {stderr}")
            server_process = None
    
    except Exception as e:
        print(f"Error starting server: {e}")
        server_process = None

def start_dashboard(data_dir=None, dagger_config=None, enable_dagger=False, no_browser=False):
    """Start the Project Master Dashboard."""
    global dashboard_process, dashboard_started, dashboard_port
    
    if dashboard_started:
        print("Dashboard is already running.")
        return
    
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    dashboard_dir = script_dir / "dashboard"
    
    # Ensure data directory exists
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
    else:
        data_dir = script_dir / ".task-manager"
        os.makedirs(data_dir, exist_ok=True)
    
    # Use a different port for the dashboard
    dashboard_port = find_available_port(http_port + 1)
    
    # Create a configuration file for the dashboard
    config_path = dashboard_dir / "config.json"
    
    if not config_path.exists():
        print(f"Creating configuration file at {config_path}...")
        with open(config_path, "w") as f:
            f.write(f"""{{
  "api": {{
    "baseUrl": "http://localhost:{http_port}",
    "authToken": "",
    "refreshInterval": 5000
  }},
  "ui": {{
    "theme": "light",
    "defaultView": "projects",
    "refreshInterval": 5000,
    "showCompletedTasks": true
  }}
}}
""")
    
    # Start the dashboard process
    try:
        # Set up environment variables
        env = os.environ.copy()
        env["PORT"] = str(dashboard_port)
        
        # Start the dashboard process
        dashboard_process = subprocess.Popen(
            ["node", str(dashboard_dir / "server.js")],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        
        # Wait for the dashboard to start
        time.sleep(2)
        
        if dashboard_process.poll() is None:
            print(f"Project Master Dashboard started successfully at http://localhost:{dashboard_port}")
            dashboard_started = True
            
            # Open browser
            if not no_browser:
                webbrowser.open(f"http://localhost:{dashboard_port}")
        else:
            stdout, stderr = dashboard_process.communicate()
            print(f"Failed to start dashboard: {stderr}")
            dashboard_process = None
    
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        dashboard_process = None

def stop_server():
    """Stop the Task Management MCP Server."""
    global server_process, server_started
    
    if server_process:
        server_process.terminate()
        server_process.wait()
        server_process = None
        server_started = False
        print("Task Management MCP Server stopped.")

def stop_dashboard():
    """Stop the Project Master Dashboard."""
    global dashboard_process, dashboard_started
    
    if dashboard_process:
        dashboard_process.terminate()
        dashboard_process.wait()
        dashboard_process = None
        dashboard_started = False
        print("Project Master Dashboard stopped.")

def stop_all():
    """Stop all processes."""
    stop_dashboard()
    stop_server()

def get_project_status():
    """Get the status of all projects."""
    import requests
    import json
    
    try:
        response = requests.get(f"http://localhost:{http_port}/mcp/resource?uri=task-manager://dashboard/projects/summary")
        if response.status_code == 200:
            projects = json.loads(response.text)
            
            if not projects:
                print("No projects found.")
                return
            
            print("\nProject Status:")
            print("==============")
            
            for project in projects:
                print(f"\nProject: {project['name']}")
                print(f"Progress: {project['progress']:.1f}%")
                print(f"Tasks: {project['completedTasks']}/{project['taskCount']} completed")
                
                if project['phases']:
                    print("\nPhases:")
                    for phase in project['phases']:
                        print(f"  - {phase['name']}: {phase['progress']:.1f}% ({phase['completedTasks']}/{phase['taskCount']} tasks)")
        else:
            print(f"Failed to get project status: {response.status_code} {response.text}")
    
    except Exception as e:
        print(f"Error getting project status: {e}")

def get_next_tasks():
    """Get the next tasks to work on."""
    import requests
    import json
    
    try:
        # Get all projects
        response = requests.get(f"http://localhost:{http_port}/mcp/resource?uri=task-manager://projects")
        if response.status_code != 200:
            print(f"Failed to get projects: {response.status_code} {response.text}")
            return
        
        projects = json.loads(response.text)
        
        if not projects:
            print("No projects found.")
            return
        
        print("\nNext Tasks:")
        print("==========")
        
        for project_id, project in projects.items():
            # Get tasks for this project
            response = requests.get(f"http://localhost:{http_port}/mcp/resource?uri=task-manager://projects/{project_id}/tasks")
            if response.status_code != 200:
                print(f"Failed to get tasks for project {project['name']}: {response.status_code} {response.text}")
                continue
            
            tasks = json.loads(response.text)
            
            # Filter for planned or in-progress tasks
            next_tasks = [task for task in tasks.values() if task['status'] in ['planned', 'in_progress']]
            
            if next_tasks:
                print(f"\nProject: {project['name']}")
                
                for task in next_tasks:
                    status_icon = "🔄" if task['status'] == 'in_progress' else "⏳"
                    progress = f" ({task['progress']}%)" if task['status'] == 'in_progress' else ""
                    print(f"  {status_icon} {task['name']}{progress}")
    
    except Exception as e:
        print(f"Error getting next tasks: {e}")

def process_command(command):
    """Process a command from the user."""
    # Check if the command matches any of the patterns
    for pattern in PROJECT_STATUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Start server and dashboard if not already running
            if not server_started:
                start_server()
            if not dashboard_started:
                start_dashboard(no_browser=True)
            
            # Get project status
            get_project_status()
            return
    
    for pattern in NEXT_TASK_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Start server and dashboard if not already running
            if not server_started:
                start_server()
            if not dashboard_started:
                start_dashboard(no_browser=True)
            
            # Get next tasks
            get_next_tasks()
            return
    
    # Handle other commands
    if command.lower() in ["exit", "quit", "q"]:
        stop_all()
        sys.exit(0)
    elif command.lower() in ["help", "h", "?"]:
        print_help()
    elif command.lower() in ["start", "run"]:
        start_server()
        start_dashboard()
    elif command.lower() in ["stop", "shutdown"]:
        stop_all()
    elif command.lower() in ["dashboard", "open dashboard", "show dashboard"]:
        # Open the HTML dashboard
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        dashboard_path = script_dir / "dashboard.html"
        if dashboard_path.exists():
            print(f"Opening dashboard: {dashboard_path}")
            webbrowser.open(f"file://{dashboard_path.absolute()}")
        else:
            print(f"Dashboard file not found: {dashboard_path}")
    elif command.lower() == "server":
        if not server_started:
            start_server()
        else:
            print("Server is already running.")
    else:
        print(f"Unknown command: {command}")
        print_help()

def print_help():
    """Print help information."""
    print("\nTask Assistant Commands:")
    print("======================")
    print("project status    - Show the status of all projects")
    print("what's next       - Show the next tasks to work on")
    print("start             - Start the server and dashboard")
    print("stop              - Stop the server and dashboard")
    print("dashboard         - Open the dashboard in a browser")
    print("server            - Start the server only")
    print("help              - Show this help information")
    print("exit              - Exit the Task Assistant")

def signal_handler(sig, frame):
    """Handle termination signals."""
    print("\nShutting down...")
    stop_all()
    sys.exit(0)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Task Assistant - A command-line interface for the Task Management MCP Server")
    parser.add_argument("--data-dir", help="Directory to store task data")
    parser.add_argument("--dagger-config", help="Path to Dagger configuration file")
    parser.add_argument("--enable-dagger", action="store_true", help="Enable Dagger integration")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--auto-start", action="store_true", help="Automatically start the server and dashboard")
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Auto-start if requested
    if args.auto_start:
        start_server(args.data_dir, args.dagger_config, args.enable_dagger)
        start_dashboard(args.data_dir, args.dagger_config, args.enable_dagger, args.no_browser)
    
    # Print welcome message
    print("\nWelcome to Task Assistant!")
    print("Type 'help' for a list of commands.")
    
    # Main loop
    while True:
        try:
            command = input("\n> ")
            process_command(command)
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    
    # Clean up
    stop_all()

if __name__ == "__main__":
    main()
