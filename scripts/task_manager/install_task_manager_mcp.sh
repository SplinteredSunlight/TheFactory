#!/bin/bash
# Install Task Manager MCP Server Configuration
# This script copies the Task Manager MCP server configuration to the appropriate locations
# for both Cline (VSCode extension) and Claude Desktop.

set -e

echo "Installing Task Manager MCP Server Configuration..."

# Create directories if they don't exist
mkdir -p ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/
mkdir -p ~/Library/Application\ Support/Claude/

# Copy configuration files
echo "Copying Cline MCP settings..."
cp cline_mcp_settings.json ~/Library/Application\ Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/

echo "Copying Claude Desktop configuration..."
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/

echo "Installation complete!"
echo "You can now use the Task Manager MCP server with both Cline and Claude Desktop."
echo "Restart Cline and Claude Desktop to apply the changes."
