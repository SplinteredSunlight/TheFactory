#!/bin/bash
# Script to install the custom instructions for Cline

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Get the project root directory (parent of script directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Path to the custom instructions
CUSTOM_INSTRUCTIONS_PATH="$PROJECT_ROOT/docs/system-prompt/custom-instructions.md"

# Check if the custom instructions file exists
if [ ! -f "$CUSTOM_INSTRUCTIONS_PATH" ]; then
    echo "Error: Custom instructions file not found at $CUSTOM_INSTRUCTIONS_PATH"
    exit 1
fi

# Read the custom instructions
CUSTOM_INSTRUCTIONS=$(cat "$CUSTOM_INSTRUCTIONS_PATH")

# Display the custom instructions
echo "Custom Instructions for Cline:"
echo "=============================="
echo "$CUSTOM_INSTRUCTIONS"
echo "=============================="
echo ""

# Instructions for the user
echo "To install these custom instructions for Cline:"
echo ""
echo "1. Open the Cline settings by clicking on the gear icon in the top right corner"
echo "2. Click on 'Custom Instructions'"
echo "3. Copy and paste the content above into the appropriate sections:"
echo "   - The 'What would you like Cline to know about you' section goes in the first box"
echo "   - The 'How would you like Cline to respond' section goes in the second box"
echo "4. Click 'Save'"
echo ""
echo "Would you like to copy the custom instructions to your clipboard? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    # Check which clipboard command is available
    if command -v pbcopy &> /dev/null; then
        # macOS
        echo "$CUSTOM_INSTRUCTIONS" | pbcopy
        echo "Custom instructions copied to clipboard (macOS)"
    elif command -v xclip &> /dev/null; then
        # Linux with xclip
        echo "$CUSTOM_INSTRUCTIONS" | xclip -selection clipboard
        echo "Custom instructions copied to clipboard (Linux with xclip)"
    elif command -v xsel &> /dev/null; then
        # Linux with xsel
        echo "$CUSTOM_INSTRUCTIONS" | xsel --clipboard --input
        echo "Custom instructions copied to clipboard (Linux with xsel)"
    elif command -v clip &> /dev/null; then
        # Windows
        echo "$CUSTOM_INSTRUCTIONS" | clip
        echo "Custom instructions copied to clipboard (Windows)"
    else
        echo "No clipboard command found. Please copy the custom instructions manually."
    fi
fi

echo "Done."
