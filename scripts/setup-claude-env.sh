#!/bin/bash
# Script to set up environment variables for Claude

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory (parent of script directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Path to the system prompt
SYSTEM_PROMPT_PATH="$PROJECT_ROOT/docs/system-prompt/system-prompt.md"

# Check if the system prompt file exists
if [ ! -f "$SYSTEM_PROMPT_PATH" ]; then
    echo "Error: System prompt file not found at $SYSTEM_PROMPT_PATH"
    exit 1
fi

# Read the system prompt
SYSTEM_PROMPT=$(cat "$SYSTEM_PROMPT_PATH")

# Export the environment variable
export CLAUDE_SYSTEM_PROMPT="$SYSTEM_PROMPT"

# Add to .bashrc or .zshrc if requested
if [ "$1" == "--permanent" ]; then
    # Determine which shell is being used
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        echo "Unknown shell. Please add the following line to your shell's rc file manually:"
        echo "export CLAUDE_SYSTEM_PROMPT=\"\$(cat $SYSTEM_PROMPT_PATH)\""
        exit 1
    fi
    
    # Check if the line already exists in the rc file
    if grep -q "CLAUDE_SYSTEM_PROMPT" "$SHELL_RC"; then
        echo "Environment variable already exists in $SHELL_RC"
    else
        echo "# Claude system prompt" >> "$SHELL_RC"
        echo "export CLAUDE_SYSTEM_PROMPT=\"\$(cat $SYSTEM_PROMPT_PATH)\"" >> "$SHELL_RC"
        echo "Added environment variable to $SHELL_RC"
    fi
    
    echo "Please restart your shell or run 'source $SHELL_RC' to apply the changes"
else
    echo "Environment variable CLAUDE_SYSTEM_PROMPT has been set for this session"
    echo "To make this permanent, run this script with the --permanent flag"
fi

# Instructions
echo ""
echo "You can now use the CLAUDE_SYSTEM_PROMPT environment variable in your scripts"
echo "For example, in a Python script:"
echo "  import os"
echo "  system_prompt = os.environ.get('CLAUDE_SYSTEM_PROMPT', '')"
echo ""
echo "Or in a shell script:"
echo "  SYSTEM_PROMPT=\$CLAUDE_SYSTEM_PROMPT"
