#!/bin/bash

# Auto-task-workflow.sh
# Automatically generates the next task and creates the task file
# Usage: ./auto-task-workflow.sh [--template TEMPLATE]

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
TEMPLATE="default"

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --template)
      TEMPLATE="$2"
      shift
      ;;
    *)
      echo -e "${RED}Unknown parameter: $1${NC}"
      exit 1
      ;;
  esac
  shift
done

# Update the context cache
echo -e "${BLUE}Updating context cache...${NC}"
python3 "$SCRIPT_DIR/context-manager.py" --update

# Generate the next task prompt
echo -e "${YELLOW}Generating next task prompt...${NC}"
python3 "$SCRIPT_DIR/task-tracker.py" --next --template "$TEMPLATE"

# Get current timestamp for the filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TASK_DATA=$(python3 "$SCRIPT_DIR/task-tracker.py" --status 2>&1)
CURRENT_TASK=$(echo "$TASK_DATA" | grep "Current Task:" | sed 's/Current Task: //')
SANITIZED_TASK=$(echo "$CURRENT_TASK" | tr ' ' '_' | tr -d '[:punct:]')

# Create a new markdown file for the task
NEXT_TASK_PROMPT_FILE="$PROJECT_ROOT/docs/next-task-prompt.md"
NEW_TASK_FILE="$PROJECT_ROOT/tasks/task_${TIMESTAMP}_${SANITIZED_TASK}.md"

# Create tasks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/tasks"

# Copy the next task prompt to the new file
if [ -f "$NEXT_TASK_PROMPT_FILE" ]; then
  # Add a header with instructions
  echo "# New Cline Task - $(date)" > "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  echo "## Instructions" >> "$NEW_TASK_FILE"
  echo "1. Copy the entire content below this section" >> "$NEW_TASK_FILE"
  echo "2. Start a new Cline conversation" >> "$NEW_TASK_FILE"
  echo "3. Paste the content to begin the new task" >> "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  echo "---" >> "$NEW_TASK_FILE"
  echo "" >> "$NEW_TASK_FILE"
  cat "$NEXT_TASK_PROMPT_FILE" >> "$NEW_TASK_FILE"
  
  echo -e "${GREEN}=== New Task Ready ===${NC}"
  echo -e "New task file created at: ${BLUE}$NEW_TASK_FILE${NC}"
  
  # Open the file in VS Code if available
  if command -v code &> /dev/null; then
    code "$NEW_TASK_FILE"
    echo -e "${GREEN}File opened in VS Code${NC}"
  else
    echo -e "${YELLOW}VS Code command not found. Please open the file manually.${NC}"
  fi
  
  # Add a Git hook to monitor changes for this task
  HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
  POST_COMMIT_HOOK="$HOOKS_DIR/post-commit"
  
  # Create hooks directory if it doesn't exist
  mkdir -p "$HOOKS_DIR"
  
  # Create or append to post-commit hook
  if [ ! -f "$POST_COMMIT_HOOK" ]; then
    cat > "$POST_COMMIT_HOOK" << EOF
#!/bin/bash
# Auto-generated post-commit hook for task completion tracking
"$SCRIPT_DIR/auto-complete-task.sh"
EOF
    chmod +x "$POST_COMMIT_HOOK"
  else
    # Check if our hook is already included
    if ! grep -q "auto-complete-task.sh" "$POST_COMMIT_HOOK"; then
      echo -e "\n# Auto-generated post-commit hook for task completion tracking" >> "$POST_COMMIT_HOOK"
      echo "\"$SCRIPT_DIR/auto-complete-task.sh\"" >> "$POST_COMMIT_HOOK"
    fi
  fi
  
  echo -e "${GREEN}Git hook installed to automatically check task completion on commits${NC}"
else
  echo -e "${RED}Error: Next task prompt file not found.${NC}"
  exit 1
fi