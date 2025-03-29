#!/usr/bin/env python3

"""
Update Project Progress Script

This script reads the task tracking data and updates the project progress in the FastAPI backend.
It calculates the progress based on completed tasks and updates the project progress endpoint.
"""

import os
import json
from datetime import datetime, timedelta
import argparse

# Get the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Path to the task tracking data
TASK_TRACKING_PATH = os.path.join(PROJECT_ROOT, "docs/task-tracking.json")

# Path to the project plan
PROJECT_PLAN_PATH = os.path.join(PROJECT_ROOT, "docs/project-plan.md")

def load_task_tracking():
    """Load the task tracking data from the JSON file."""
    if os.path.exists(TASK_TRACKING_PATH):
        with open(TASK_TRACKING_PATH, 'r') as f:
            return json.load(f)
    else:
        print(f"Task tracking file not found at {TASK_TRACKING_PATH}")
        return None

def count_total_tasks():
    """Count the total number of tasks in the project plan."""
    if not os.path.exists(PROJECT_PLAN_PATH):
        print(f"Project plan not found at {PROJECT_PLAN_PATH}")
        return 0
    
    try:
        with open(PROJECT_PLAN_PATH, 'r') as f:
            plan_text = f.read()
        
        # Count tasks (lines with "**Task Name**:")
        task_count = plan_text.count("**")
        return task_count // 2  # Each task has two ** markers
    except Exception as e:
        print(f"Error reading project plan: {e}")
        return 0

def calculate_progress(tracking_data):
    """Calculate the progress based on completed tasks."""
    if not tracking_data:
        return 0, 0, 0
    
    completed_tasks = tracking_data.get("completed_tasks", [])
    completed_count = len(completed_tasks)
    
    # Count total tasks from the project plan or use a fallback
    total_tasks = count_total_tasks()
    if total_tasks == 0:
        # Fallback: estimate total tasks based on phases in tracking data
        planned_tasks = []
        for phase in tracking_data.get("planned_tasks", []):
            planned_tasks.extend(phase.get("tasks", []))
        total_tasks = len(planned_tasks)
    
    # Calculate progress percentage
    if total_tasks > 0:
        progress = (completed_count / total_tasks) * 100
    else:
        progress = 0
    
    return progress, completed_count, total_tasks

def determine_status(progress):
    """Determine the project status based on progress."""
    if progress >= 100:
        return "completed"
    elif progress >= 75:
        return "on_track"
    elif progress >= 50:
        return "on_track"
    elif progress >= 25:
        return "at_risk"
    else:
        return "on_track"  # Default to on_track for early stages

def estimate_completion_date(tracking_data, total_tasks):
    """Estimate the completion date based on current progress."""
    completed_tasks = tracking_data.get("completed_tasks", [])
    
    if not completed_tasks or total_tasks == 0:
        # Default to 3 months from now if no data
        return (datetime.now() + timedelta(days=90)).isoformat()
    
    # Calculate average time between task completions
    completion_times = [datetime.fromisoformat(task["completed_at"]) 
                        for task in completed_tasks]
    
    if len(completion_times) < 2:
        # Default to 3 months from now if not enough data
        return (datetime.now() + timedelta(days=90)).isoformat()
    
    # Sort completion times
    completion_times.sort()
    
    # Calculate average time between completions
    time_diffs = [(completion_times[i+1] - completion_times[i]).total_seconds() 
                 for i in range(len(completion_times)-1)]
    avg_time_between_tasks = sum(time_diffs) / len(time_diffs)
    
    # Calculate remaining tasks
    remaining_tasks = total_tasks - len(completed_tasks)
    
    # Estimate completion date
    seconds_to_completion = avg_time_between_tasks * remaining_tasks
    estimated_completion = datetime.now() + timedelta(seconds=seconds_to_completion)
    
    return estimated_completion.isoformat()

def save_progress_to_file(progress, completed_tasks, total_tasks, status, estimated_completion):
    """Save the progress data to a local file."""
    progress_data = {
        "progress": progress,
        "completedTasks": completed_tasks,
        "totalTasks": total_tasks,
        "status": status,
        "estimatedCompletion": estimated_completion,
        "lastUpdated": datetime.now().isoformat()
    }
    
    # Save to a local file
    progress_file = os.path.join(PROJECT_ROOT, "docs/project_progress.json")
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        print(f"Project progress saved to {progress_file}")
        return True
    except Exception as e:
        print(f"Error saving progress data: {e}")
        return False

def display_progress(progress, completed_tasks, total_tasks, status, estimated_completion):
    """Display the progress in the terminal."""
    status_emoji = {
        "on_track": "🟢",
        "at_risk": "🟡",
        "delayed": "🔴",
        "completed": "✅"
    }
    
    emoji = status_emoji.get(status, "⚪")
    
    print("\n" + "=" * 50)
    print(f"AI-Orchestration-Platform Project Progress")
    print("=" * 50)
    print(f"Progress: {progress:.1f}% complete {emoji}")
    print(f"Tasks: {completed_tasks} of {total_tasks} completed")
    print(f"Status: {status.replace('_', ' ').title()}")
    
    if estimated_completion:
        try:
            est_date = datetime.fromisoformat(estimated_completion.split('T')[0])
            print(f"Estimated completion: {est_date.strftime('%B %d, %Y')}")
        except Exception:
            print(f"Estimated completion: {estimated_completion}")
    
    print("=" * 50 + "\n")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update Project Progress")
    parser.add_argument('--update-api', action='store_true', 
                        help="Update the progress in the FastAPI backend")
    parser.add_argument('--show', action='store_true', 
                        help="Show the progress in the terminal")
    args = parser.parse_args()
    
    # Default to showing progress if no arguments provided
    if not args.update_api and not args.show:
        args.show = True
    
    # Load the task tracking data
    tracking_data = load_task_tracking()
    if not tracking_data:
        return
    
    # Calculate progress
    progress, completed_tasks, total_tasks = calculate_progress(tracking_data)
    
    # Determine status
    status = determine_status(progress)
    
    # Estimate completion date
    estimated_completion = estimate_completion_date(tracking_data, total_tasks)
    
    # Update the project progress
    if args.update_api:
        save_progress_to_file(progress, completed_tasks, total_tasks, status, estimated_completion)
    
    # Display the progress in the terminal
    if args.show:
        display_progress(progress, completed_tasks, total_tasks, status, estimated_completion)

if __name__ == "__main__":
    main()
