# AI-Orchestration-Platform Documentation

This directory contains the documentation for the AI-Orchestration-Platform project. The documentation is organized into a structured hierarchy to make it easy to find the information you need.

## Documentation Structure

```
docs/
├── planning/                  # Project planning documents
│   ├── consolidated-project-plan.md  # Single source of truth for project plan
│   ├── task-templates/        # Task templates for common tasks
│
├── system/                    # System documentation
│   ├── components/            # Component documentation
│   ├── api/                   # API documentation
│   └── integration/           # Integration documentation
│
├── guides/                    # User and developer guides
│
├── wiki/                      # Project wiki
│   ├── adr/                   # Architectural Decision Records
│   ├── components/            # Component documentation
│   ├── journal/               # Development journal
│   └── workflows/             # Workflow documentation
│
└── system-prompt/             # Claude system prompt
```

## Key Documentation Files

### Project Planning
- [Consolidated Project Plan](planning/consolidated-project-plan.md): The single source of truth for project status, phases, and roadmap

### System Documentation
- [Architecture Overview](system/components/architecture.md): High-level architecture of the system
- [API Documentation](system/api/api-contracts.md): API contracts and interfaces
- [Integration Documentation](system/integration/integration-plan.md): Integration points and strategies

### User and Developer Guides
- [Task Management Guide](guides/TASK_MANAGER_MCP_README.md): Guide for using the Task Management MCP server
- [Dagger Integration Guide](guides/DAGGER_WORKFLOW_INTEGRATION_README.md): Guide for Dagger workflow integration
- [Error Handling Protocol](guides/error-handling-protocol.md): Protocol for handling errors

### Project Wiki
- [Wiki Structure](wiki/structure.md): Structure of the project wiki
- [Architectural Decision Records](wiki/adr/): Records of architectural decisions
- [Development Journal](wiki/journal/): Journal of development activities

## How to Use This Documentation

### Finding Information
1. Start with the [Consolidated Project Plan](planning/consolidated-project-plan.md) to get an overview of the project
2. Look in the appropriate section for more detailed information:
   - `planning/` for project planning documents
   - `system/` for system documentation
   - `guides/` for user and developer guides
   - `wiki/` for project wiki

### Updating Documentation
1. Use the `scripts/update-docs-from-task-manager.py` script to update the documentation based on the current state of the task management system
2. When making changes to the documentation, ensure that you update the appropriate files
3. If you're adding new documentation, follow the existing structure

### Working with Claude
1. Use the `scripts/invoke-claude-with-context.sh` script to invoke Claude with the system prompt as context
2. This will ensure that Claude has the necessary context to assist with the project

## Documentation Integration

The documentation is integrated with the Task Management system to ensure that it's always up-to-date. The following scripts are available:

- `scripts/update-docs-from-task-manager.py`: Updates the documentation based on the current state of the task management system
- `scripts/invoke-claude-with-context.sh`: Invokes Claude with the system prompt as context

## Contributing to Documentation

When contributing to the documentation, please follow these guidelines:

1. **Use Markdown**: All documentation should be written in Markdown format
2. **Follow the Structure**: Place new documentation in the appropriate directory
3. **Link to Related Documents**: Include links to related documents
4. **Keep it Up-to-Date**: Update documentation when making changes to the code
5. **Include Examples**: Provide examples to illustrate concepts

## Documentation Roadmap

The documentation system will continue to evolve as the project grows. Future enhancements include:

1. **Documentation Dashboard**: A web-based dashboard for browsing and searching documentation
2. **Automated Documentation Generation**: Tools for generating documentation from code
3. **Documentation Testing**: Tests to ensure documentation is accurate and up-to-date
4. **Documentation Versioning**: Version control for documentation to track changes over time
