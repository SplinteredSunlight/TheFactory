#!/bin/bash
# Setup test environment for Dagger integration tests

echo "Setting up test environment for Dagger integration tests..."

# Create necessary directories
mkdir -p tests/dagger/unit
mkdir -p tests/dagger/integration
mkdir -p tests/dagger/error_handling
mkdir -p workflows

# Create mock MCP agent module for testing
mkdir -p mock_modules/mcp_agent
touch mock_modules/mcp_agent/__init__.py
mkdir -p mock_modules/mcp_agent/app
touch mock_modules/mcp_agent/app/__init__.py

cat > mock_modules/mcp_agent/app/__init__.py << 'EOF'
"""Mock MCP agent module for testing."""

class MCPApp:
    """Mock MCPApp class."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock MCPApp."""
        pass
    
    def run(self, *args, **kwargs):
        """Run the mock MCPApp."""
        pass
EOF

# Create mock dagger module for testing
mkdir -p mock_modules/dagger
touch mock_modules/dagger/__init__.py

cat > mock_modules/dagger/__init__.py << 'EOF'
"""Mock dagger module for testing."""
import asyncio
from typing import Any, Dict, List, Optional

class Connection:
    """Mock Dagger Connection class."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock Connection."""
        pass
    
    async def __aenter__(self):
        """Enter the async context."""
        return self
    
    async def __aexit__(self, *args):
        """Exit the async context."""
        pass
    
    def container(self):
        """Get a container client."""
        return Container()
    
    def host(self):
        """Get a host client."""
        return Host()

class Container:
    """Mock Container class."""
    
    def from_(self, image: str):
        """From a container image."""
        return self
    
    def with_env_variable(self, name: str, value: str):
        """Set an environment variable."""
        return self
    
    def with_mounted_directory(self, target: str, source: Any):
        """Mount a directory."""
        return self
    
    def with_new_file(self, path: str, contents: str):
        """Create a new file."""
        return self
    
    def with_exec(self, args: List[str], **kwargs):
        """Execute a command."""
        return self
    
    async def stdout(self):
        """Get the standard output."""
        return '{"result": "mock result"}'

class Host:
    """Mock Host class."""
    
    def directory(self, path: str):
        """Get a directory."""
        return Directory()

class Directory:
    """Mock Directory class."""
    pass
EOF

# Create mock pydagger module for testing
mkdir -p mock_modules/pydagger
touch mock_modules/pydagger/__init__.py

cat > mock_modules/pydagger/__init__.py << 'EOF'
"""Mock pydagger module for testing."""

class Engine:
    """Mock Dagger Engine class."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock Engine."""
        pass
EOF

# Add the mock modules to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/mock_modules

echo "Test environment setup complete!"