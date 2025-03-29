#!/usr/bin/env python3
"""
Initialize the Dagger configuration.
"""
import os
import yaml
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = Path("/app/config")
WORKFLOWS_DIR = Path("/app/workflows")
DEFAULT_CONFIG_PATH = CONFIG_DIR / "dagger.yaml"

def load_config():
    """Load the Dagger configuration from the config file."""
    try:
        if not DEFAULT_CONFIG_PATH.exists():
            logger.error(f"Config file not found: {DEFAULT_CONFIG_PATH}")
            return None
            
        with open(DEFAULT_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
            
        logger.info(f"Loaded configuration from {DEFAULT_CONFIG_PATH}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def update_config_with_env(config):
    """Update the configuration with environment variables."""
    if not config:
        return None
        
    # Update with environment variables
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("DAGGER_")}
    logger.info(f"Found {len(env_vars)} Dagger environment variables")
    
    for key, value in env_vars.items():
        # Convert DAGGER_WORKFLOW_MAX_EXECUTIONS to config["workflow"]["max_concurrent_executions"]
        parts = key[7:].lower().split("_")
        current = config
        
        # Navigate to the nested dictionary
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Set the value
        current[parts[-1]] = value
        logger.info(f"Set {key} to {value}")
        
    return config

def create_default_resources():
    """Create default resources for Dagger."""
    # Create workflow directories
    WORKFLOWS_DIR.mkdir(exist_ok=True)
    (WORKFLOWS_DIR / "templates").mkdir(exist_ok=True)
    
    # Create example workflow
    example_workflow = {
        "name": "Example Workflow",
        "description": "A simple example workflow",
        "steps": [
            {
                "id": "step1",
                "name": "Fetch Data",
                "image": "python:3.9-slim",
                "command": ["python", "-c", "print('Fetching data...')"],
                "environment": {
                    "API_KEY": "${API_KEY}"
                }
            },
            {
                "id": "step2",
                "name": "Process Data",
                "image": "python:3.9-slim",
                "command": ["python", "-c", "print('Processing data...')"],
                "depends_on": ["step1"]
            }
        ]
    }
    
    with open(WORKFLOWS_DIR / "templates" / "example.yaml", "w") as f:
        yaml.dump(example_workflow, f)
        
    logger.info("Created example workflow template")

def main():
    """Main function."""
    logger.info("Initializing Dagger configuration...")
    
    # Create config directory
    CONFIG_DIR.mkdir(exist_ok=True)
    
    # Load and update configuration
    config = load_config()
    updated_config = update_config_with_env(config)
    
    if updated_config:
        # Write updated configuration
        with open(CONFIG_DIR / "dagger.runtime.yaml", "w") as f:
            yaml.dump(updated_config, f)
        logger.info("Configuration updated successfully")
    else:
        logger.warning("No configuration found or could not be updated")
    
    # Create default resources
    create_default_resources()
    
    logger.info("Dagger initialization completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())