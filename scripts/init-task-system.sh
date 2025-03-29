#!/bin/bash

# Initialize Task Management System for AI-Orchestration-Platform
# This script sets up the task management system for tracking integration work

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}AI-Orchestration-Platform - Task System Initialization${NC}"

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_DIR="$PROJECT_ROOT/.task-manager"

# Ensure task manager scripts are executable
echo -e "${YELLOW}Making task manager scripts executable...${NC}"
chmod +x "$TASK_DIR/"*.sh
chmod +x "$TASK_DIR/"*.py

# Create task command in project root
echo -e "${YELLOW}Creating 'task' command in project root...${NC}"
cat > "$PROJECT_ROOT/task" << 'EOF'
#!/bin/bash

# Main entry point for AI Task Manager
# Usage: ./task [command] [options]

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine script location
TASK_MANAGER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.task-manager" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Commands
case "$1" in
  status)
    echo -e "${BLUE}Current Task Status:${NC}"
    python3 "$TASK_MANAGER_DIR/task-tracker.py" --status
    ;;
    
  complete)
    echo -e "${GREEN}Completing current task...${NC}"
    "$TASK_MANAGER_DIR/complete-current-task.sh" "${@:2}"
    ;;
    
  next)
    echo -e "${YELLOW}Generating next task prompt...${NC}"
    "$TASK_MANAGER_DIR/generate-next-task-prompt.sh" "${@:2}"
    ;;
    
  start)
    echo -e "${GREEN}Preparing task for Claude...${NC}"
    # Get the prompt
    PROMPT=$("$TASK_MANAGER_DIR/next-task-for-claude.sh")
    
    # Copy to clipboard
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      echo "$PROMPT" | pbcopy
      echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      # Linux with xclip
      if command -v xclip &> /dev/null; then
        echo "$PROMPT" | xclip -selection clipboard
        echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
      elif command -v xsel &> /dev/null; then
        echo "$PROMPT" | xsel --clipboard
        echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
      else
        echo -e "${YELLOW}Could not copy to clipboard. Please install xclip or xsel.${NC}"
      fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
      # Windows
      echo "$PROMPT" | clip
      echo -e "${GREEN}Task prompt copied to clipboard!${NC}"
    else
      echo -e "${YELLOW}Clipboard not supported on this OS. Task prompt not copied.${NC}"
    fi
    
    # Open Claude if requested
    if [[ "$2" == "--browser" || "$2" == "-b" ]]; then
      echo -e "${BLUE}Opening Claude in browser...${NC}"
      if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "https://claude.ai"
      elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "https://claude.ai"
      elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        start "https://claude.ai"
      else
        echo -e "${YELLOW}Could not open browser on this OS.${NC}"
      fi
    fi
    ;;
    
  cline)
    echo -e "${BLUE}Running Cline workflow...${NC}"
    "$TASK_MANAGER_DIR/cline-workflow.sh" "${@:2}"
    ;;
    
  context)
    echo -e "${BLUE}Managing context cache...${NC}"
    python3 "$TASK_MANAGER_DIR/context-manager.py" "${@:2}"
    ;;
    
  help|--help|-h)
    echo -e "${BLUE}AI Task Manager - Help${NC}"
    echo "Usage: ./task [command] [options]"
    echo ""
    echo "Commands:"
    echo "  status              Show current task status"
    echo "  complete [options]  Complete the current task"
    echo "  next [options]      Generate the next task prompt"
    echo "  start [options]     Prepare task for Claude and copy to clipboard"
    echo "  cline [options]     Run the Cline workflow (optimized for VS Code)"
    echo "  context [options]   Manage the context cache"
    echo "  help                Show this help message"
    echo ""
    echo "Options for 'complete', 'next', and 'cline':"
    echo "  --template NAME     Use specified template (default, concise, detailed,"
    echo "                      integration-task, orchestrator-enhancement, agent-integration,"
    echo "                      frontend-integration)"
    echo "  --sub-task NAME     Specify a sub-task"
    echo ""
    echo "Options for 'start':"
    echo "  --browser, -b       Open Claude in the default browser"
    echo ""
    echo "Options for 'context':"
    echo "  --update            Update the context cache"
    echo "  --force             Force update the context cache"
    ;;
    
  *)
    if [ -z "$1" ]; then
      echo -e "${BLUE}AI Task Manager${NC}"
      echo "Run './task help' for usage information"
    else
      echo -e "${RED}Unknown command: $1${NC}"
      echo "Run './task help' for usage information"
      exit 1
    fi
    ;;
esac
EOF

chmod +x "$PROJECT_ROOT/task"

# Ensure necessary directories exist
echo -e "${YELLOW}Ensuring necessary directories exist...${NC}"
mkdir -p "$PROJECT_ROOT/config/templates"

# Create .vscode directory and tasks.json if it doesn't exist
mkdir -p "$PROJECT_ROOT/.vscode"
if [ ! -f "$PROJECT_ROOT/.vscode/tasks.json" ]; then
  echo -e "${YELLOW}Creating VS Code tasks configuration...${NC}"
  echo '{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Task: Show Status",
      "type": "shell",
      "command": "./task status",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Complete Current",
      "type": "shell",
      "command": "./task complete",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Generate Next",
      "type": "shell",
      "command": "./task next",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Start with Claude",
      "type": "shell",
      "command": "./task start --browser",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Task: Cline Workflow",
      "type": "shell",
      "command": "./task cline",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    }
  ]
}' > "$PROJECT_ROOT/.vscode/tasks.json"
fi

# Create project-plan.md if it doesn't exist
if [ ! -f "$PROJECT_ROOT/docs/project-plan.md" ]; then
  echo -e "${YELLOW}Creating initial project plan...${NC}"
  echo '# AI-Orchestration-Platform Integration Project Plan

## Overview
This project plan outlines the integration work between AI-Orchestrator and Fast-Agent systems.

## Phases and Tasks

### 1. Integration Setup

- **API Contract Definition**: Define the API contract between AI-Orchestrator and Fast-Agent **Status: 🔄 In Progress**
- **Authentication Mechanism**: Implement secure authentication between systems **Status: 📅 Planned**
- **Data Schema Alignment**: Ensure consistent data schemas across both systems **Status: 📅 Planned**
- **Error Handling Protocol**: Define standardized error handling between systems **Status: 📅 Planned**
- **Integration Testing Framework**: Set up automated testing for cross-system integration **Status: 📅 Planned**

**Next Steps:**
1. Document API endpoints and data formats
2. Create OpenAPI specification
3. Implement validation mechanisms

### 2. Orchestrator Enhancements

- **Agent Communication Module**: Develop module for communicating with Fast-Agent **Status: 📅 Planned**
- **Task Distribution Logic**: Implement logic for distributing tasks to Fast-Agent **Status: 📅 Planned**

**Next Steps:**
1. Design communication protocol
2. Implement request/response handling
3. Add error recovery mechanisms

### 3. Agent Integration

- **Orchestrator API Client**: Implement client for Fast-Agent to communicate with Orchestrator **Status: 📅 Planned**
- **Result Reporting System**: Develop system for reporting task results back to Orchestrator **Status: 📅 Planned**

**Next Steps:**
1. Create API client library
2. Implement authentication
3. Add result formatting and validation

### 4. Frontend Integration

- **Unified Dashboard**: Create unified dashboard for monitoring both systems **Status: 📅 Planned**
- **Cross-System Configuration UI**: Develop UI for configuring integration parameters **Status: 📅 Planned**

**Next Steps:**
1. Design dashboard layout
2. Create configuration forms
3. Implement real-time status updates
' > "$PROJECT_ROOT/docs/project-plan.md"
fi

# Create context cache if it doesn't exist
if [ ! -f "$PROJECT_ROOT/docs/context-cache.json" ]; then
  echo -e "${YELLOW}Creating initial context cache...${NC}"
  echo '{
  "version": 1,
  "last_updated": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
  "file_hashes": {},
  "project_structure": {},
  "architecture_summary": "The AI-Orchestration-Platform consists of several key components: the Orchestrator (manages workflows and task distribution), Agent Manager (handles communication with AI agents), and Frontend (provides user interface). The system is being integrated with Fast-Agent, which is a specialized system for executing AI tasks efficiently.",
  "completed_tasks_summary": [],
  "task_references": {}
}' > "$PROJECT_ROOT/docs/context-cache.json"
fi

echo -e "${GREEN}Task system initialization complete!${NC}"
echo -e "You can now use the following commands:"
echo -e "  ${YELLOW}./task status${NC} - Show current task status"
echo -e "  ${YELLOW}./task next${NC} - Generate the next task prompt"
echo -e "  ${YELLOW}./task complete${NC} - Complete the current task"
echo -e "  ${YELLOW}./task start${NC} - Prepare task for Claude and copy to clipboard"
echo -e "  ${YELLOW}./task cline${NC} - Run the Cline workflow (optimized for VS Code)"
echo -e "  ${YELLOW}./task help${NC} - Show help message"
echo -e ""
echo -e "Current task: ${GREEN}API Contract Definition${NC} in ${BLUE}Integration Setup${NC}"
