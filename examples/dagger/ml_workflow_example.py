"""
Example demonstrating a machine learning workflow with Dagger.

This example shows how to create a multi-step machine learning workflow
that includes data preprocessing, model training, evaluation, and deployment
using Dagger's containerized workflow capabilities.
"""

import asyncio
import logging
import os
import json
import time
from src.orchestrator.engine import OrchestrationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_ml_workflow():
    """Create a machine learning workflow with multiple steps."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="ml_pipeline",
        description="Machine Learning Pipeline with Data Preprocessing, Training, and Evaluation"
    )
    
    # Step 1: Data Preprocessing
    data_prep_task = workflow.add_task(
        name="data_preprocessing",
        agent="data_processor",
        inputs={
            "dataset_path": "/data/raw/dataset.csv",
            "operations": [
                {"type": "fill_missing", "strategy": "mean"},
                {"type": "normalize", "method": "min_max"},
                {"type": "split", "test_size": 0.2, "random_state": 42}
            ],
            "output_path": "/data/processed/"
        }
    )
    
    # Step 2: Feature Engineering
    feature_eng_task = workflow.add_task(
        name="feature_engineering",
        agent="feature_engineer",
        inputs={
            "data_path": "/data/processed/",
            "features_to_create": [
                {"name": "interaction_term", "columns": ["feature_a", "feature_b"], "operation": "multiply"},
                {"name": "time_feature", "column": "timestamp", "extract": ["hour", "day_of_week", "month"]}
            ],
            "output_path": "/data/features/"
        },
        depends_on=[data_prep_task]
    )
    
    # Step 3: Model Training
    model_train_task = workflow.add_task(
        name="model_training",
        agent="model_trainer",
        inputs={
            "data_path": "/data/features/",
            "model_type": "gradient_boosting",
            "hyperparameters": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5
            },
            "target_column": "target",
            "output_path": "/models/gradient_boosting_model.pkl"
        },
        depends_on=[feature_eng_task]
    )
    
    # Step 4: Model Evaluation
    model_eval_task = workflow.add_task(
        name="model_evaluation",
        agent="model_evaluator",
        inputs={
            "model_path": "/models/gradient_boosting_model.pkl",
            "test_data_path": "/data/features/test.csv",
            "metrics": ["accuracy", "precision", "recall", "f1", "roc_auc"],
            "output_path": "/evaluation/metrics.json"
        },
        depends_on=[model_train_task]
    )
    
    # Step 5: Model Deployment (if evaluation meets criteria)
    model_deploy_task = workflow.add_task(
        name="model_deployment",
        agent="model_deployer",
        inputs={
            "model_path": "/models/gradient_boosting_model.pkl",
            "metrics_path": "/evaluation/metrics.json",
            "deployment_config": {
                "min_accuracy": 0.85,
                "environment": "staging",
                "api_endpoint": "/api/v1/predict",
                "version": "1.0.0"
            },
            "output_path": "/deployment/deployment_info.json"
        },
        depends_on=[model_eval_task]
    )
    
    # Step 6: Notification
    notification_task = workflow.add_task(
        name="notification",
        agent="notifier",
        inputs={
            "deployment_info_path": "/deployment/deployment_info.json",
            "notification_type": "email",
            "recipients": ["data-science-team@example.com", "ml-ops@example.com"],
            "subject": "ML Model Deployment Status"
        },
        depends_on=[model_deploy_task]
    )
    
    return workflow


async def execute_ml_workflow():
    """Execute the machine learning workflow with Dagger."""
    # Create the workflow
    workflow = await create_ml_workflow()
    
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Add the workflow to the engine
    engine.workflows[workflow.id] = workflow
    
    # Configure Dagger execution parameters
    dagger_config = {
        "engine_type": "dagger",
        "container_registry": "docker.io",
        "workflow_directory": "workflows",
        "caching_enabled": True,
        "cache_directory": "./.dagger_cache",
        "cache_ttl_seconds": 3600,
        "max_retries": 3,
        "retry_backoff_factor": 0.5,
        "retry_jitter": True
    }
    
    # Execute the workflow
    logger.info("Executing ML workflow with Dagger...")
    start_time = time.time()
    
    try:
        result = await engine.execute_workflow(
            workflow_id=workflow.id,
            **dagger_config
        )
        
        execution_time = time.time() - start_time
        logger.info(f"Workflow execution completed in {execution_time:.2f} seconds")
        logger.info(f"Result: {result}")
        
        # Check if the model was deployed
        if result.get("status") == "success":
            logger.info("ML model successfully trained and deployed!")
            
            # In a real implementation, we would parse the deployment info
            # and provide more detailed information about the deployed model
            deployment_info = {
                "model_version": "1.0.0",
                "deployment_environment": "staging",
                "api_endpoint": "https://api.example.com/models/gradient_boosting/predict",
                "metrics": {
                    "accuracy": 0.92,
                    "precision": 0.89,
                    "recall": 0.87,
                    "f1": 0.88,
                    "roc_auc": 0.95
                }
            }
            
            logger.info(f"Deployment Info: {json.dumps(deployment_info, indent=2)}")
        else:
            logger.warning("Workflow execution failed or model did not meet deployment criteria")
            
        return result
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise


async def main():
    """Run the example."""
    logger.info("=== Dagger ML Workflow Example ===")
    
    try:
        await execute_ml_workflow()
    except Exception as e:
        logger.error(f"Error in ML workflow example: {e}")
    
    logger.info("=== Example complete ===")


if __name__ == "__main__":
    asyncio.run(main())
