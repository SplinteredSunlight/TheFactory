# AI-Orchestration-Platform Scripts

This directory contains utility scripts for working with the AI-Orchestration-Platform project. These scripts are designed to make common tasks easier and more efficient.

## Available Scripts

### Claude Integration Scripts

- **setup-claude-env.sh**: Sets up environment variables for Claude with the system prompt
  ```bash
  # Set up for current session
  ./setup-claude-env.sh
  
  # Set up permanently (adds to .bashrc or .zshrc)
  ./setup-claude-env.sh --permanent
  ```

- **invoke-claude-with-context.sh**: Invokes Claude with the system prompt as context
  ```bash
  ./invoke-claude-with-context.sh
  ```

- **claude_api_helper.py**: Helper script for interacting with Claude's API
  ```bash
  # Send a message to Claude with the system prompt included
  ./claude_api_helper.py "Your message here"
  
  # Send a message without the system prompt
  ./claude_api_helper.py --no-system-prompt "Your message here"
  
  # Use a different model
  ./claude_api_helper.py --model claude-3-sonnet-20240229 "Your message here"
  
  # Interactive mode (enter message, press Ctrl+D when done)
  ./claude_api_helper.py
  ```

- **install-custom-instructions.sh**: Installs the custom instructions for Cline
  ```bash
  # Display the custom instructions and offer to copy to clipboard
  ./install-custom-instructions.sh
  ```

### Documentation Scripts

- **update-docs-from-task-manager.py**: Updates documentation based on the current state of the task management system
  ```bash
  ./update-docs-from-task-manager.py
  ```

- **auto-update-docs.sh**: Automatically updates documentation from the task manager
  ```bash
  # Update documentation
  ./auto-update-docs.sh
  
  # Install as a cron job to run every hour
  ./auto-update-docs.sh --install-cron
  
  # Install as a git pre-commit hook
  ./auto-update-docs.sh --install-git-hook
  ```

## Environment Variables

The scripts in this directory use the following environment variables:

- **CLAUDE_SYSTEM_PROMPT**: The system prompt to include when invoking Claude
- **ANTHROPIC_API_KEY**: API key for Claude's API

You can set these environment variables using the `setup-claude-env.sh` script.

## Automatic Documentation Updates

The documentation is automatically updated from the task management system using the `auto-update-docs.sh` script. This script can be set up to run:

1. **Manually**: Run `./auto-update-docs.sh` whenever you want to update the documentation
2. **As a cron job**: Run `./auto-update-docs.sh --install-cron` to set up a cron job that runs every hour
3. **As a git hook**: Run `./auto-update-docs.sh --install-git-hook` to set up a git pre-commit hook that updates the documentation before each commit

## Custom Instructions for Cline

The custom instructions for Cline are stored in `docs/system-prompt/custom-instructions.md`. You can install these instructions using the `install-custom-instructions.sh` script, which will:

1. Display the custom instructions
2. Provide instructions for installing them in Cline
3. Offer to copy them to your clipboard for easy pasting

## Using the Claude API Helper in Your Code

You can import the Claude API helper functions in your Python code:

```python
from scripts.claude_api_helper import get_claude_response

# Get a response from Claude with the system prompt included
response = get_claude_response("Your message here")
print(response)

# Get a response without the system prompt
response = get_claude_response("Your message here", include_system_prompt=False)
print(response)

# Use a different model
response = get_claude_response("Your message here", model="claude-3-sonnet-20240229")
print(response)
```

## Adding New Scripts

When adding new scripts to this directory, please follow these guidelines:

1. Make the script executable with `chmod +x script_name`
2. Add documentation to this README file
3. Include a usage message in the script (e.g., with `--help`)
4. Follow the existing naming conventions

## Script Categories

The scripts in this directory are organized into the following categories:

- **Claude Integration**: Scripts for working with Claude
- **Documentation**: Scripts for working with documentation
- **Task Management**: Scripts for working with the task management system
- **Development**: Scripts for development tasks

## Troubleshooting

If you encounter issues with the scripts, check the following:

1. Make sure the script is executable (`chmod +x script_name`)
2. Check that any required environment variables are set
3. Verify that any required dependencies are installed
