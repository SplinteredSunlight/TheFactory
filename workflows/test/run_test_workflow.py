#!/usr/bin/env python3
"""
Test Workflow Runner

This script runs the simple data processing workflow for testing the Dagger integration.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-workflow-runner")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run test workflow')
    parser.add_argument('--input-dir', required=False, 
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'),
                        help='Directory containing input data')
    parser.add_argument('--scripts-dir', required=False, 
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'),
                        help='Directory containing processing scripts')
    parser.add_argument('--workflow-file', required=False, 
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simple-data-processing-workflow.yml'),
                        help='Workflow YAML file')
    parser.add_argument('--simulate-failures', action='store_true',
                        help='Simulate transient failures to test retry mechanism')
    parser.add_argument('--validation-level', default='strict',
                        choices=['strict', 'moderate', 'relaxed'],
                        help='Validation level')
    parser.add_argument('--transformation-type', default='standard',
                        choices=['standard', 'aggregated', 'normalized'],
                        help='Transformation type')
    parser.add_argument('--analysis-depth', default='full',
                        choices=['full', 'summary', 'minimal'],
                        help='Analysis depth')
    return parser.parse_args()

def run_step(step_name, command, env=None):
    """Run a single workflow step."""
    logger.info(f"Running {step_name} step...")
    
    # Create a copy of the environment variables
    step_env = os.environ.copy()
    
    # Update with step-specific environment variables
    if env:
        step_env.update(env)
    
    try:
        # Run the command
        result = subprocess.run(
            command,
            env=step_env,
            check=True,
            text=True,
            capture_output=True
        )
        logger.info(f"{step_name} step completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{step_name} step failed: {e}")
        logger.error(f"Standard output: {e.stdout}")
        logger.error(f"Standard error: {e.stderr}")
        return False

def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure the input directory exists
    input_dir = os.path.abspath(args.input_dir)
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    # Ensure the scripts directory exists
    scripts_dir = os.path.abspath(args.scripts_dir)
    if not os.path.isdir(scripts_dir):
        logger.error(f"Scripts directory does not exist: {scripts_dir}")
        sys.exit(1)
    
    # Ensure the workflow file exists
    workflow_file = os.path.abspath(args.workflow_file)
    if not os.path.isfile(workflow_file):
        logger.error(f"Workflow file does not exist: {workflow_file}")
        sys.exit(1)
    
    # Set up environment for failures if requested
    env = {}
    if args.simulate_failures:
        env["SIMULATE_FAILURE"] = "true"
        logger.warning("Simulating transient failures to test retry mechanism")
        
        # Remove any existing attempt markers
        for marker in ['.validation_attempt', '.transformation_attempt', '.analysis_attempt']:
            if os.path.exists(marker):
                os.remove(marker)
    
    # Set up file paths
    validation_script = os.path.join(scripts_dir, "validation", "validate.py")
    validation_schema = os.path.join(scripts_dir, "validation", "schema.json")
    transformation_script = os.path.join(scripts_dir, "transformation", "transform.py")
    analysis_script = os.path.join(scripts_dir, "analysis", "analyze.py")
    
    input_csv = os.path.join(input_dir, "input.csv")
    validated_json = os.path.join(input_dir, "validated.json")
    transformed_json = os.path.join(input_dir, "transformed.json")
    results_json = os.path.join(input_dir, "results.json")
    
    # Run the validation step
    validation_env = env.copy()
    validation_env["VALIDATION_LEVEL"] = args.validation_level
    
    validation_success = run_step(
        "Validation",
        [
            sys.executable, validation_script,
            "--input", input_csv,
            "--schema", validation_schema,
            "--output", validated_json,
            "--level", args.validation_level
        ],
        env=validation_env
    )
    
    if not validation_success:
        logger.error("Validation step failed, aborting workflow")
        sys.exit(1)
    
    # Run the transformation step
    transformation_env = env.copy()
    transformation_env["TRANSFORMATION_TYPE"] = args.transformation_type
    
    transformation_success = run_step(
        "Transformation",
        [
            sys.executable, transformation_script,
            "--input", validated_json,
            "--output", transformed_json,
            "--type", args.transformation_type
        ],
        env=transformation_env
    )
    
    if not transformation_success:
        logger.error("Transformation step failed, aborting workflow")
        sys.exit(1)
    
    # Run the analysis step
    analysis_env = env.copy()
    analysis_env["ANALYSIS_DEPTH"] = args.analysis_depth
    
    analysis_success = run_step(
        "Analysis",
        [
            sys.executable, analysis_script,
            "--input", transformed_json,
            "--output", results_json,
            "--depth", args.analysis_depth
        ],
        env=analysis_env
    )
    
    if not analysis_success:
        logger.error("Analysis step failed, aborting workflow")
        sys.exit(1)
    
    # Print workflow summary
    logger.info("Workflow completed successfully!")
    
    try:
        with open(results_json, 'r') as f:
            results = json.load(f)
        
        logger.info("Analysis Results Summary:")
        
        # Print insights
        insights = results.get("insights", [])
        logger.info(f"Generated {len(insights)} insights:")
        
        for i, insight in enumerate(insights, 1):
            importance = insight.get("importance", "unknown")
            message = insight.get("message", "No message")
            logger.info(f"  {i}. [{importance.upper()}] {message}")
        
        # Print summary metrics
        summary = results.get("summary", {})
        metrics = summary.get("metrics", {})
        
        logger.info(f"Processed {summary.get('total_records', 0)} records")
        
        if metrics:
            logger.info("Key Metrics:")
            for key, value in metrics.items():
                if isinstance(value, dict):
                    continue
                logger.info(f"  {key}: {value}")
    except Exception as e:
        logger.error(f"Error reading results: {e}")


if __name__ == "__main__":
    main()
