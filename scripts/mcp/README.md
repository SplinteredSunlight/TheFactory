# MCP Scripts

This directory contains scripts and utilities for working with the Model Context Protocol (MCP) in the AI-Orchestration-Platform.

## Scripts

### MCP Server Scripts

- **simple_dagger_mcp_server.py**: A simple MCP server implementation that provides Dagger functionality.
- **run_simple_dagger_mcp_server.sh**: Script to run the simple Dagger MCP server.

### Configuration Scripts

- **update_mcp_settings.py**: Python script to update MCP settings in the configuration files.
- **update_claude_desktop_config.sh**: Script to update the Claude desktop configuration for MCP.

### Configuration Files

- **cline_mcp_settings.json**: Configuration file for Cline MCP settings.
- **claude_desktop_config.json**: Configuration file for Claude desktop MCP settings.

## Usage

### Running the Simple Dagger MCP Server

```bash
./scripts/mcp/run_simple_dagger_mcp_server.sh
```

### Updating MCP Settings

```bash
./scripts/mcp/update_mcp_settings.py
```

### Updating Claude Desktop Configuration

```bash
./scripts/mcp/update_claude_desktop_config.sh
```

## What is MCP?

The Model Context Protocol (MCP) is a protocol for communication between AI models and external tools or services. It allows AI models to access external functionality, such as retrieving information from databases, executing code, or interacting with APIs.

In the AI-Orchestration-Platform, MCP is used to provide AI models with access to the platform's functionality, such as task management, workflow execution, and agent communication.

For more information about MCP, see the [MCP Documentation](https://github.com/modelcontextprotocol/mcp).
