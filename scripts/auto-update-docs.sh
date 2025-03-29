#!/bin/bash
# Script to automatically update documentation from the task manager
# This script can be set up as a cron job or git hook

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory (parent of script directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Path to the update script
UPDATE_SCRIPT="$PROJECT_ROOT/scripts/update-docs-from-task-manager.py"

# Check if the update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "Error: Update script not found at $UPDATE_SCRIPT"
    exit 1
fi

# Run the update script
echo "Updating documentation from task manager..."
python3 "$UPDATE_SCRIPT"

# Check if the update was successful
if [ $? -eq 0 ]; then
    echo "Documentation updated successfully"
    
    # If this is run as a git hook, add the changes to git
    if [ -d "$PROJECT_ROOT/.git" ]; then
        echo "Adding documentation changes to git..."
        git -C "$PROJECT_ROOT" add docs/planning/consolidated-project-plan.md
        
        # Check if there are changes to commit
        if git -C "$PROJECT_ROOT" diff --cached --quiet; then
            echo "No changes to commit"
        else
            echo "Committing changes..."
            git -C "$PROJECT_ROOT" commit -m "Auto-update documentation from task manager"
            echo "Changes committed"
        fi
    fi
else
    echo "Error: Failed to update documentation"
    exit 1
fi

# Instructions for setting up as a cron job
if [ "$1" == "--install-cron" ]; then
    # Create a temporary file for the cron job
    TEMP_CRON=$(mktemp)
    
    # Export the current crontab
    crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# New crontab" > "$TEMP_CRON"
    
    # Check if the cron job already exists
    if grep -q "$SCRIPT_DIR/auto-update-docs.sh" "$TEMP_CRON"; then
        echo "Cron job already exists"
    else
        # Add the cron job to run every hour
        echo "# Update documentation from task manager every hour" >> "$TEMP_CRON"
        echo "0 * * * * $SCRIPT_DIR/auto-update-docs.sh" >> "$TEMP_CRON"
        
        # Install the new crontab
        crontab "$TEMP_CRON"
        echo "Cron job installed to run every hour"
    fi
    
    # Clean up
    rm "$TEMP_CRON"
fi

# Instructions for setting up as a git hook
if [ "$1" == "--install-git-hook" ]; then
    # Path to the pre-commit hook
    HOOK_PATH="$PROJECT_ROOT/.git/hooks/pre-commit"
    
    # Create the hooks directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/.git/hooks"
    
    # Check if the hook already exists
    if [ -f "$HOOK_PATH" ]; then
        # Check if our script is already in the hook
        if grep -q "$SCRIPT_DIR/auto-update-docs.sh" "$HOOK_PATH"; then
            echo "Git hook already exists"
        else
            # Append our script to the existing hook
            echo "" >> "$HOOK_PATH"
            echo "# Update documentation from task manager" >> "$HOOK_PATH"
            echo "$SCRIPT_DIR/auto-update-docs.sh" >> "$HOOK_PATH"
            echo "Git hook updated"
        fi
    else
        # Create a new hook
        echo "#!/bin/bash" > "$HOOK_PATH"
        echo "" >> "$HOOK_PATH"
        echo "# Update documentation from task manager" >> "$HOOK_PATH"
        echo "$SCRIPT_DIR/auto-update-docs.sh" >> "$HOOK_PATH"
        
        # Make the hook executable
        chmod +x "$HOOK_PATH"
        echo "Git hook created"
    fi
fi

echo "Done."
