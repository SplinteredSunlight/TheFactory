#!/bin/bash
# Update Claude Desktop Configuration for Task Manager MCP Server with Mock Dagger
# This script updates the Claude Desktop configuration to use the mock modules for the Task Manager MCP Server.

# Set the path to the Claude Desktop configuration file
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Check if the configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Claude Desktop configuration file not found at: $CONFIG_FILE"
    exit 1
fi

# Create a backup of the configuration file
BACKUP_FILE="$CONFIG_FILE.bak"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "Created backup of Claude Desktop configuration at: $BACKUP_FILE"

# Update the configuration file
cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "task-manager": {
      "command": "python3",
      "args": ["/Users/dc/Projects/AI-Orchestration-Platform/src/task_manager/mcp_servers/run_task_manager_server.py", "--enable-dagger", "--dagger-config", "/Users/dc/Projects/AI-Orchestration-Platform/config/dagger.yaml"],
      "env": {
        "PYTHONPATH": "/Users/dc/Projects/AI-Orchestration-Platform:/Users/dc/Projects/AI-Orchestration-Platform/mock_modules",
        "TASK_MANAGER_DAGGER_ENABLED": "1",
        "TASK_MANAGER_DAGGER_CONFIG": "/Users/dc/Projects/AI-Orchestration-Platform/config/dagger.yaml"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
EOF

echo "Updated Claude Desktop configuration to use mock modules for Task Manager MCP Server"
echo "You may need to restart Claude Desktop for the changes to take effect"
