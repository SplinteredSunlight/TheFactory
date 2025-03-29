#!/bin/bash
# Script to invoke Claude with the system prompt as context

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

# Create a temporary file for the prompt
TEMP_FILE=$(mktemp)

# Write the system prompt to the temporary file
echo "$SYSTEM_PROMPT" > "$TEMP_FILE"

# Append the user's message if provided
if [ "$#" -gt 0 ]; then
    echo -e "\n\n---\n\n" >> "$TEMP_FILE"
    echo "$@" >> "$TEMP_FILE"
fi

# Open the file in the default editor
if [ -n "$EDITOR" ]; then
    $EDITOR "$TEMP_FILE"
elif command -v code &> /dev/null; then
    code "$TEMP_FILE"
elif command -v vim &> /dev/null; then
    vim "$TEMP_FILE"
elif command -v nano &> /dev/null; then
    nano "$TEMP_FILE"
else
    echo "No suitable editor found. Please set the EDITOR environment variable."
    exit 1
fi

# Instructions for the user
echo "The system prompt has been included in the file: $TEMP_FILE"
echo "You can now copy the contents of this file and paste it into Claude."
echo "Press Enter to open the file again, or Ctrl+C to exit."
read

# Open the file again for the user to copy
if [ -n "$EDITOR" ]; then
    $EDITOR "$TEMP_FILE"
elif command -v code &> /dev/null; then
    code "$TEMP_FILE"
elif command -v vim &> /dev/null; then
    vim "$TEMP_FILE"
elif command -v nano &> /dev/null; then
    nano "$TEMP_FILE"
fi

# Clean up
echo "Cleaning up temporary file..."
rm "$TEMP_FILE"
echo "Done."
