"""
Mock Dagger module for testing.

This module provides mock implementations of Dagger classes and functions
for testing purposes.
"""

class Connection:
    """Mock Dagger Connection class."""
    
    def __init__(self):
        """Initialize a new Connection."""
        pass
    
    async def __aenter__(self):
        """Enter the async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        pass
    
    def container(self):
        """Get a container."""
        return Container()
    
    def host(self):
        """Get a host."""
        return Host()


class Container:
    """Mock Dagger Container class."""
    
    def __init__(self):
        """Initialize a new Container."""
        pass
    
    def from_(self, image):
        """Set the container image."""
        return self
    
    def with_env_variable(self, key, value):
        """Add an environment variable."""
        return self
    
    def with_mounted_directory(self, target, source):
        """Mount a directory."""
        return self
    
    def with_new_file(self, path, content):
        """Add a new file."""
        return self
    
    def with_exec(self, command, inputs=None):
        """Execute a command."""
        return self
    
    async def stdout(self):
        """Get the command output."""
        return "Mock command output"


class Host:
    """Mock Dagger Host class."""
    
    def __init__(self):
        """Initialize a new Host."""
        pass
    
    def directory(self, path):
        """Get a directory."""
        return Directory()


class Directory:
    """Mock Dagger Directory class."""
    
    def __init__(self):
        """Initialize a new Directory."""
        pass
