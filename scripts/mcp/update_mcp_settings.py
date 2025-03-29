#!/usr/bin/env python3
"""
Update MCP Settings

This script updates the MCP settings to include the Simple Dagger MCP Server.
"""

import json
import os
import sys

# Define the paths to the MCP settings files
CLINE_MCP_SETTINGS_PATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_mcp_settings.json")
CLAUDE_DESKTOP_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Claude", "claude_desktop_config.json")

# Define the new MCP server configuration
NEW_SERVER_CONFIG = {
    "command": "bash",
    "args": [os.path.join(os.getcwd(), "run_simple_dagger_mcp_server.sh")],
    "env": {
        "TASK_MANAGER_DAGGER_ENABLED": "1",
        "TASK_MANAGER_DAGGER_CONFIG": os.path.join(os.getcwd(), "config", "dagger.yaml"),
        "TASK_MANAGER_DATA_DIR": os.path.join(os.getcwd(), ".task-manager")
    },
    "disabled": False,
    "autoApprove": []
}

def update_mcp_settings(settings_path, server_name="dagger-workflow"):
    """Update the MCP settings file with the new server configuration."""
    try:
        # Read the existing settings
        with open(settings_path, "r") as f:
            settings = json.load(f)
        
        # Add or update the new server configuration
        if "mcpServers" not in settings:
            settings["mcpServers"] = {}
        
        settings["mcpServers"][server_name] = NEW_SERVER_CONFIG
        
        # Write the updated settings
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        
        print(f"Updated MCP settings in {settings_path}")
        return True
    except Exception as e:
        print(f"Error updating MCP settings in {settings_path}: {e}")
        return False

def main():
    """Update the MCP settings in both Cline and Claude Desktop."""
    # Update Cline MCP settings
    if os.path.exists(CLINE_MCP_SETTINGS_PATH):
        update_mcp_settings(CLINE_MCP_SETTINGS_PATH)
    else:
        print(f"Cline MCP settings file not found at {CLINE_MCP_SETTINGS_PATH}")
    
    # Update Claude Desktop MCP settings
    if os.path.exists(CLAUDE_DESKTOP_CONFIG_PATH):
        update_mcp_settings(CLAUDE_DESKTOP_CONFIG_PATH)
    else:
        print(f"Claude Desktop config file not found at {CLAUDE_DESKTOP_CONFIG_PATH}")

if __name__ == "__main__":
    main()
