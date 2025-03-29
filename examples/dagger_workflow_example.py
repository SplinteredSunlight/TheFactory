"""
Dagger Workflow Example

This example demonstrates how to create and execute a workflow using Dagger integration.
"""

import os
import asyncio
import logging
from typing import Dict, Any

from src.orchestrator.engine import OrchestrationEngine, Workflow
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load Dagger configuration
def load_dagger_config() -> Dict[str, Any]:
    """Load the Dagger configuration from the config file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              "config", "dagger.yaml")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables
    for key, value in os.environ.items():
        if key.startswith("DAGGER_"):
            config_key = key[7:].lower()
            if isinstance(config.get(config_key), dict):
                config[config_key].update({"env_value": value})
            else:
                config[config_key] = value
    
    return config

async def run_example() -> None:
    """Run the Dagger workflow example."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="dagger_example_workflow",
        description="Example workflow executed with Dagger"
    )
    
    # Add tasks to the workflow
    task1_id = workflow.add_task(
        name="fetch_data",
        agent="data_fetcher",
        inputs={
            "url": "https://example.com/data",
            "format": "json"
        }
    )
    
    task2_id = workflow.add_task(
        name="process_data",
        agent="data_processor",
        inputs={
            "operation": "transform",
            "schema": {
                "fields": ["name", "value", "timestamp"]
            }
        },
        depends_on=[task1_id]
    )
    
    task3_id = workflow.add_task(
        name="analyze_data",
        agent="data_analyzer",
        inputs={
            "metrics": ["mean", "median", "std_dev"],
            "groupby": "timestamp"
        },
        depends_on=[task2_id]
    )
    
    task4_id = workflow.add_task(
        name="generate_report",
        agent="report_generator",
        inputs={
            "template": "analysis_report",
            "format": "pdf"
        },
        depends_on=[task3_id]
    )
    
    # Load Dagger configuration
    dagger_config = load_dagger_config()
    
    # Prepare container configuration
    container_config = {
        "container_registry": dagger_config.get("container", {}).get("registry"),
        "container_credentials": dagger_config.get("container", {}).get("credentials", {}),
        "workflow_directory": dagger_config.get("workflow", {}).get("directory", "workflows"),
        "workflow_defaults": {
            "inputs": {
                "default_timeout": dagger_config.get("workflow", {}).get("default_timeout", 600)
            }
        }
    }
    
    try:
        # Execute the workflow with Dagger
        logger.info(f"Executing workflow {workflow.id} with Dagger")
        result = engine.execute_workflow(
            workflow_id=workflow.id,
            engine_type="dagger",
            **container_config
        )
        
        # Print the results
        logger.info(f"Workflow execution results: {result}")
        
        # Process the workflow results
        if result.get("status") == "success":
            logger.info("Workflow executed successfully")
            
            # In a real application, you would process the results here
            # For example, store them in a database, send notifications, etc.
            
            return result
        else:
            logger.error(f"Workflow execution failed: {result.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(run_example())