#!/bin/bash

# Auto-complete-task.sh
# Automatically marks tasks as complete based on code changes
# Usage: ./auto-complete-task.sh [--dry-run]
#
# This script:
# 1. Monitors git changes since task was created
# 2. Evaluates completion criteria based on task metadata
# 3. Automatically marks the task as complete when criteria are met

# Set up colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse arguments
DRY_RUN=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      exit 1
      ;;
  esac
done

# Get current task info
TASK_INFO=$(python3 "$SCRIPT_DIR/task-tracker.py" --status --json)
TASK_NAME=$(echo "$TASK_INFO" | grep -o '"current_task": "[^"]*"' | cut -d'"' -f4)
TASK_ID=$(echo "$TASK_INFO" | grep -o '"task_id": "[^"]*"' | cut -d'"' -f4)
TASK_CREATED_AT=$(echo "$TASK_INFO" | grep -o '"created_at": "[^"]*"' | cut -d'"' -f4)

if [ -z "$TASK_NAME" ]; then
  echo -e "${RED}Error: No current task found.${NC}"
  exit 1
fi

echo -e "${BLUE}Checking completion status for task: ${YELLOW}$TASK_NAME${NC}"

# Read the task tracking file
TRACKING_FILE="$PROJECT_ROOT/docs/task-tracking.json"
TASK_METADATA=$(cat "$TRACKING_FILE")

# Extract completion criteria from the task metadata
COMPLETION_CRITERIA=$(echo "$TASK_METADATA" | grep -o "\"$TASK_ID\"[^}]*\"completion_criteria\"[^]]*" | grep -o '"completion_criteria": \[[^]]*\]' | grep -o '\[[^]]*\]')

if [ -z "$COMPLETION_CRITERIA" ]; then
  echo -e "${YELLOW}No specific completion criteria found for this task.${NC}"
  echo -e "${YELLOW}Using default criteria: Changes to implementation files.${NC}"
  
  # Default criteria: Any changes to implementation files in src directory
  if git diff --name-only --diff-filter=AMRC $(git log --since="$TASK_CREATED_AT" --format="%H" | tail -n 1)..HEAD | grep -q "^src/.*\.\(py\|js\|tsx\|ts\)$"; then
    if [ "$DRY_RUN" = true ]; then
      echo -e "${GREEN}Task would be marked as complete based on implementation changes.${NC}"
    else
      echo -e "${GREEN}Implementation changes detected. Marking task as complete.${NC}"
      "$SCRIPT_DIR/complete-current-task.sh"
      
      # Generate the next task
      echo -e "${BLUE}Generating next task...${NC}"
      "$SCRIPT_DIR/auto-task-workflow.sh"
    fi
  else
    echo -e "${YELLOW}No implementation changes detected yet.${NC}"
  fi
  exit 0
fi

# Process specific completion criteria
COMPLETION_READY=true
echo -e "${BLUE}Evaluating specific completion criteria:${NC}"

# Parse the JSON completion criteria
echo "$COMPLETION_CRITERIA" | sed 's/\[//g' | sed 's/\]//g' | sed 's/,/\n/g' | sed 's/"//g' | while read -r criterion; do
  criterion=$(echo "$criterion" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  if [ -n "$criterion" ]; then
    echo -e "${YELLOW}Checking: ${criterion}${NC}"
    
    # Evaluate different types of criteria
    if [[ "$criterion" == file:* ]]; then
      # File existence criterion
      FILE_PATH=$(echo "$criterion" | sed 's/file://')
      if [ -f "$PROJECT_ROOT/$FILE_PATH" ]; then
        echo -e "  ${GREEN}✓ File exists${NC}"
      else
        echo -e "  ${RED}✗ File doesn't exist${NC}"
        COMPLETION_READY=false
      fi
      
    elif [[ "$criterion" == dir:* ]]; then
      # Directory existence criterion
      DIR_PATH=$(echo "$criterion" | sed 's/dir://')
      if [ -d "$PROJECT_ROOT/$DIR_PATH" ]; then
        echo -e "  ${GREEN}✓ Directory exists${NC}"
      else
        echo -e "  ${RED}✗ Directory doesn't exist${NC}"
        COMPLETION_READY=false
      fi
      
    elif [[ "$criterion" == change:* ]]; then
      # File changes criterion
      PATTERN=$(echo "$criterion" | sed 's/change://')
      if git diff --name-only --diff-filter=AMRC $(git log --since="$TASK_CREATED_AT" --format="%H" | tail -n 1)..HEAD | grep -q "$PATTERN"; then
        echo -e "  ${GREEN}✓ Changes detected${NC}"
      else
        echo -e "  ${RED}✗ No changes detected${NC}"
        COMPLETION_READY=false
      fi
      
    elif [[ "$criterion" == test:* ]]; then
      # Test file existence/changes criterion
      TEST_PATTERN=$(echo "$criterion" | sed 's/test://')
      if git diff --name-only --diff-filter=AMRC $(git log --since="$TASK_CREATED_AT" --format="%H" | tail -n 1)..HEAD | grep -q "tests/.*$TEST_PATTERN"; then
        echo -e "  ${GREEN}✓ Test changes detected${NC}"
      else
        echo -e "  ${RED}✗ No test changes detected${NC}"
        COMPLETION_READY=false
      fi
      
    elif [[ "$criterion" == doc:* ]]; then
      # Documentation changes criterion
      DOC_PATTERN=$(echo "$criterion" | sed 's/doc://')
      if git diff --name-only --diff-filter=AMRC $(git log --since="$TASK_CREATED_AT" --format="%H" | tail -n 1)..HEAD | grep -q "docs/.*$DOC_PATTERN"; then
        echo -e "  ${GREEN}✓ Documentation changes detected${NC}"
      else
        echo -e "  ${RED}✗ No documentation changes detected${NC}"
        COMPLETION_READY=false
      fi
    fi
  fi
done

# Check if all criteria are met
if [ "$COMPLETION_READY" = true ]; then
  if [ "$DRY_RUN" = true ]; then
    echo -e "${GREEN}Task would be marked as complete based on all criteria being met.${NC}"
  else
    echo -e "${GREEN}All completion criteria met. Marking task as complete.${NC}"
    "$SCRIPT_DIR/complete-current-task.sh"
    
    # Generate the next task
    echo -e "${BLUE}Generating next task...${NC}"
    "$SCRIPT_DIR/auto-task-workflow.sh"
  fi
else
  echo -e "${YELLOW}Not all completion criteria have been met yet.${NC}"
fi