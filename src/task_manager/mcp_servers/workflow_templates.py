#!/usr/bin/env python3
"""
Workflow Templates Module for Task Manager MCP Server.

This module provides functionality for managing workflow templates in the Task Manager MCP Server.
"""

import os
import json
import yaml
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from mcp.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListResourcesRequestSchema,
    ListResourceTemplatesRequestSchema,
    ListToolsRequestSchema,
    McpError,
    ReadResourceRequestSchema,
)


class WorkflowTemplate:
    """
    Represents a workflow template with predefined structure and parameters.
    
    A workflow template defines a reusable workflow pattern that can be customized
    and instantiated for specific tasks.
    """
    
    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        category: str,
        version: str,
        parameters: Dict[str, Any],
        stages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow template.
        
        Args:
            template_id: Unique identifier for the template
            name: Human-readable name for the template
            description: Description of the template's purpose
            category: Category for grouping templates
            version: Version of the template
            parameters: Default parameters for the template
            stages: List of workflow stages
            metadata: Additional metadata for the template
        """
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self.parameters = parameters
        self.stages = stages
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "parameters": self.parameters,
            "stages": self.stages,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Create a template from a dictionary."""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            version=data["version"],
            parameters=data["parameters"],
            stages=data["stages"],
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'WorkflowTemplate':
        """Create a template from a YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml_file(cls, file_path: str) -> 'WorkflowTemplate':
        """Create a template from a YAML file."""
        with open(file_path, 'r') as f:
            return cls.from_yaml(f.read())
    
    def to_yaml(self) -> str:
        """Convert the template to a YAML string."""
        return yaml.dump(self.to_dict(), sort_keys=False)
    
    def to_yaml_file(self, file_path: str) -> None:
        """Save the template to a YAML file."""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    def customize(self, parameters: Dict[str, Any]) -> 'WorkflowTemplate':
        """
        Create a customized copy of the template with updated parameters.
        
        Args:
            parameters: Custom parameters to override defaults
            
        Returns:
            A new WorkflowTemplate instance with customized parameters
        """
        # Create a deep copy of the template
        template_dict = self.to_dict()
        
        # Update parameters
        merged_parameters = {**template_dict["parameters"], **parameters}
        template_dict["parameters"] = merged_parameters
        
        # Process parameter substitutions in stages
        for stage in template_dict["stages"]:
            stage = self._substitute_parameters(stage, merged_parameters)
        
        # Create a new template with a unique ID
        template_dict["template_id"] = f"{self.template_id}_custom_{uuid.uuid4().hex[:8]}"
        template_dict["metadata"]["customized_from"] = self.template_id
        template_dict["metadata"]["customized_at"] = datetime.now().isoformat()
        
        return WorkflowTemplate.from_dict(template_dict)
    
    def _substitute_parameters(self, obj: Any, parameters: Dict[str, Any]) -> Any:
        """
        Recursively substitute parameters in an object.
        
        Args:
            obj: Object to process
            parameters: Parameters to substitute
            
        Returns:
            Object with substituted parameters
        """
        if isinstance(obj, str):
            # Handle parameter substitution in strings
            if obj.startswith("${") and obj.endswith("}"):
                param_name = obj[2:-1]
                if param_name.startswith("parameters."):
                    param_key = param_name[11:]  # Remove "parameters."
                    if param_key in parameters:
                        return parameters[param_key]
            return obj
        elif isinstance(obj, dict):
            # Process dictionary values
            return {k: self._substitute_parameters(v, parameters) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Process list items
            return [self._substitute_parameters(item, parameters) for item in obj]
        else:
            # Return other types unchanged
            return obj
    
    def create_workflow_definition(self, task_id: str, custom_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a workflow definition from the template for a specific task.
        
        Args:
            task_id: ID of the task to create a workflow for
            custom_parameters: Custom parameters to override defaults
            
        Returns:
            Workflow definition dictionary
        """
        # Start with a customized template if parameters are provided
        template = self
        if custom_parameters:
            template = self.customize(custom_parameters)
        
        # Create a workflow definition
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        # Create workflow stages from template stages
        stages = []
        for stage_template in template.stages:
            stage = {
                "id": stage_template["id"],
                "name": stage_template["name"],
                "description": stage_template.get("description", ""),
                "agent": stage_template.get("agent", "default"),
                "inputs": stage_template.get("inputs", {}),
            }
            
            # Add dependencies if specified
            if "depends_on" in stage_template:
                stage["depends_on"] = stage_template["depends_on"]
            
            stages.append(stage)
        
        # Create the workflow definition
        workflow_definition = {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "name": f"{template.name} for Task {task_id}",
            "description": template.description,
            "template_id": template.template_id,
            "parameters": template.parameters,
            "stages": stages,
            "metadata": {
                "created_from_template": template.template_id,
                "created_at": datetime.now().isoformat(),
                "template_version": template.version
            }
        }
        
        return workflow_definition


class WorkflowTemplateRegistry:
    """
    Registry for managing workflow templates.
    
    The registry provides methods for registering, retrieving, and listing templates.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the template registry.
        
        Args:
            templates_dir: Directory to load templates from
        """
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.templates_dir = templates_dir
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Load templates from directory if provided
        if templates_dir and os.path.exists(templates_dir):
            self._load_templates_from_directory(templates_dir)
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        # Register CI/CD pipeline template
        self.register_template(self._create_cicd_pipeline_template())
        
        # Register data processing template
        self.register_template(self._create_data_processing_template())
        
        # Register ML training template
        self.register_template(self._create_ml_training_template())
        
        # Register scheduled maintenance template
        self.register_template(self._create_scheduled_maintenance_template())
    
    def _load_templates_from_directory(self, directory: str) -> None:
        """
        Load templates from a directory.
        
        Args:
            directory: Directory containing template YAML files
        """
        for filename in os.listdir(directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(directory, filename)
                try:
                    template = WorkflowTemplate.from_yaml_file(file_path)
                    self.register_template(template)
                    print(f"Loaded template {template.template_id} from {file_path}")
                except Exception as e:
                    print(f"Failed to load template from {file_path}: {e}")
    
    def register_template(self, template: WorkflowTemplate) -> None:
        """
        Register a template in the registry.
        
        Args:
            template: Template to register
        """
        self.templates[template.template_id] = template
        print(f"Registered template: {template.template_id}")
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all templates, optionally filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = self.templates.values()
        
        # Filter by category if provided
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Convert to dictionaries with basic info
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "version": t.version
            }
            for t in templates
        ]
    
    def get_categories(self) -> List[str]:
        """
        Get all template categories.
        
        Returns:
            List of category names
        """
        return sorted(set(t.category for t in self.templates.values()))
    
    def save_template(self, template: WorkflowTemplate) -> None:
        """
        Save a template to the templates directory.
        
        Args:
            template: Template to save
        """
        if not self.templates_dir:
            raise ValueError("Templates directory not set")
        
        # Create the directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Save the template
        file_path = os.path.join(self.templates_dir, f"{template.template_id}.yaml")
        template.to_yaml_file(file_path)
        print(f"Saved template {template.template_id} to {file_path}")
    
    def _create_cicd_pipeline_template(self) -> WorkflowTemplate:
        """Create a CI/CD pipeline template."""
        return WorkflowTemplate(
            template_id="cicd_pipeline",
            name="CI/CD Pipeline",
            description="Standard CI/CD pipeline for software projects",
            category="deployment",
            version="1.0.0",
            parameters={
                "build_image": "python:3.9-slim",
                "test_framework": "pytest",
                "artifact_type": "docker",
                "deployment_target": "kubernetes",
                "notification_channel": "slack"
            },
            stages=[
                {
                    "id": "build",
                    "name": "Build",
                    "description": "Compile and lint the code",
                    "agent": "builder",
                    "inputs": {
                        "image": "${parameters.build_image}",
                        "commands": [
                            "pip install -r requirements.txt",
                            "flake8 .",
                            "mypy ."
                        ]
                    }
                },
                {
                    "id": "test",
                    "name": "Test",
                    "description": "Run tests",
                    "agent": "tester",
                    "depends_on": ["build"],
                    "inputs": {
                        "framework": "${parameters.test_framework}",
                        "commands": [
                            "pytest -xvs tests/"
                        ]
                    }
                },
                {
                    "id": "package",
                    "name": "Package",
                    "description": "Create deployment artifacts",
                    "agent": "packager",
                    "depends_on": ["test"],
                    "inputs": {
                        "artifact_type": "${parameters.artifact_type}",
                        "commands": [
                            "docker build -t myapp:latest ."
                        ]
                    }
                },
                {
                    "id": "deploy",
                    "name": "Deploy",
                    "description": "Deploy to target environment",
                    "agent": "deployer",
                    "depends_on": ["package"],
                    "inputs": {
                        "target": "${parameters.deployment_target}",
                        "commands": [
                            "kubectl apply -f k8s/deployment.yaml"
                        ]
                    }
                },
                {
                    "id": "notify",
                    "name": "Notify",
                    "description": "Send deployment notification",
                    "agent": "notifier",
                    "depends_on": ["deploy"],
                    "inputs": {
                        "channel": "${parameters.notification_channel}",
                        "message": "Deployment completed successfully"
                    }
                }
            ],
            metadata={
                "tags": ["cicd", "deployment", "automation"],
                "complexity": "medium",
                "estimated_duration": "30m"
            }
        )
    
    def _create_data_processing_template(self) -> WorkflowTemplate:
        """Create a data processing template."""
        return WorkflowTemplate(
            template_id="data_processing",
            name="Data Processing Pipeline",
            description="ETL workflow for data processing and transformation",
            category="data",
            version="1.0.0",
            parameters={
                "source_type": "csv",
                "source_path": "/data/raw/",
                "destination_type": "database",
                "destination_path": "postgresql://user:pass@localhost:5432/db",
                "validation_rules": "basic"
            },
            stages=[
                {
                    "id": "extract",
                    "name": "Extract",
                    "description": "Extract data from source",
                    "agent": "data_extractor",
                    "inputs": {
                        "source_type": "${parameters.source_type}",
                        "source_path": "${parameters.source_path}",
                        "output_path": "/data/extracted/"
                    }
                },
                {
                    "id": "validate",
                    "name": "Validate",
                    "description": "Validate data quality",
                    "agent": "data_validator",
                    "depends_on": ["extract"],
                    "inputs": {
                        "data_path": "/data/extracted/",
                        "rules": "${parameters.validation_rules}",
                        "output_path": "/data/validated/"
                    }
                },
                {
                    "id": "transform",
                    "name": "Transform",
                    "description": "Transform data",
                    "agent": "data_transformer",
                    "depends_on": ["validate"],
                    "inputs": {
                        "data_path": "/data/validated/",
                        "transformations": [
                            "normalize",
                            "deduplicate",
                            "enrich"
                        ],
                        "output_path": "/data/transformed/"
                    }
                },
                {
                    "id": "load",
                    "name": "Load",
                    "description": "Load data to destination",
                    "agent": "data_loader",
                    "depends_on": ["transform"],
                    "inputs": {
                        "data_path": "/data/transformed/",
                        "destination_type": "${parameters.destination_type}",
                        "destination_path": "${parameters.destination_path}"
                    }
                },
                {
                    "id": "report",
                    "name": "Report",
                    "description": "Generate processing report",
                    "agent": "reporter",
                    "depends_on": ["load"],
                    "inputs": {
                        "data_path": "/data/transformed/",
                        "report_type": "summary",
                        "output_path": "/reports/etl_report.html"
                    }
                }
            ],
            metadata={
                "tags": ["etl", "data", "processing"],
                "complexity": "medium",
                "estimated_duration": "1h"
            }
        )
    
    def _create_ml_training_template(self) -> WorkflowTemplate:
        """Create a machine learning training template."""
        return WorkflowTemplate(
            template_id="ml_training",
            name="ML Training Pipeline",
            description="End-to-end machine learning model training workflow",
            category="machine_learning",
            version="1.0.0",
            parameters={
                "dataset_path": "/data/raw/dataset.csv",
                "model_type": "gradient_boosting",
                "hyperparameters": {
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "max_depth": 5
                },
                "target_column": "target",
                "test_size": 0.2,
                "random_state": 42
            },
            stages=[
                {
                    "id": "data_prep",
                    "name": "Data Preprocessing",
                    "description": "Prepare and clean the dataset",
                    "agent": "data_processor",
                    "inputs": {
                        "dataset_path": "${parameters.dataset_path}",
                        "operations": [
                            {"type": "fill_missing", "strategy": "mean"},
                            {"type": "normalize", "method": "min_max"},
                            {"type": "split", "test_size": "${parameters.test_size}", "random_state": "${parameters.random_state}"}
                        ],
                        "output_path": "/data/processed/"
                    }
                },
                {
                    "id": "feature_eng",
                    "name": "Feature Engineering",
                    "description": "Create and select features",
                    "agent": "feature_engineer",
                    "depends_on": ["data_prep"],
                    "inputs": {
                        "data_path": "/data/processed/",
                        "features_to_create": [
                            {"name": "interaction_term", "columns": ["feature_a", "feature_b"], "operation": "multiply"},
                            {"name": "time_feature", "column": "timestamp", "extract": ["hour", "day_of_week", "month"]}
                        ],
                        "output_path": "/data/features/"
                    }
                },
                {
                    "id": "model_train",
                    "name": "Model Training",
                    "description": "Train the machine learning model",
                    "agent": "model_trainer",
                    "depends_on": ["feature_eng"],
                    "inputs": {
                        "data_path": "/data/features/",
                        "model_type": "${parameters.model_type}",
                        "hyperparameters": "${parameters.hyperparameters}",
                        "target_column": "${parameters.target_column}",
                        "output_path": "/models/model.pkl"
                    }
                },
                {
                    "id": "model_eval",
                    "name": "Model Evaluation",
                    "description": "Evaluate model performance",
                    "agent": "model_evaluator",
                    "depends_on": ["model_train"],
                    "inputs": {
                        "model_path": "/models/model.pkl",
                        "test_data_path": "/data/features/test.csv",
                        "metrics": ["accuracy", "precision", "recall", "f1", "roc_auc"],
                        "output_path": "/evaluation/metrics.json"
                    }
                },
                {
                    "id": "model_deploy",
                    "name": "Model Deployment",
                    "description": "Deploy the model if it meets criteria",
                    "agent": "model_deployer",
                    "depends_on": ["model_eval"],
                    "inputs": {
                        "model_path": "/models/model.pkl",
                        "metrics_path": "/evaluation/metrics.json",
                        "deployment_config": {
                            "min_accuracy": 0.85,
                            "environment": "staging",
                            "api_endpoint": "/api/v1/predict",
                            "version": "1.0.0"
                        },
                        "output_path": "/deployment/deployment_info.json"
                    }
                }
            ],
            metadata={
                "tags": ["machine_learning", "ml", "training"],
                "complexity": "high",
                "estimated_duration": "2h"
            }
        )
    
    def _create_scheduled_maintenance_template(self) -> WorkflowTemplate:
        """Create a scheduled maintenance template."""
        return WorkflowTemplate(
            template_id="scheduled_maintenance",
            name="Scheduled Maintenance",
            description="Automated system maintenance and health check workflow",
            category="operations",
            version="1.0.0",
            parameters={
                "target_systems": ["database", "api", "frontend"],
                "backup_destination": "/backups/",
                "retention_days": 30,
                "notification_email": "admin@example.com"
            },
            stages=[
                {
                    "id": "health_check",
                    "name": "Health Check",
                    "description": "Check system health",
                    "agent": "health_checker",
                    "inputs": {
                        "target_systems": "${parameters.target_systems}",
                        "checks": ["connectivity", "performance", "disk_space"],
                        "output_path": "/reports/health_check.json"
                    }
                },
                {
                    "id": "backup",
                    "name": "Backup",
                    "description": "Create system backups",
                    "agent": "backup_agent",
                    "depends_on": ["health_check"],
                    "inputs": {
                        "target_systems": "${parameters.target_systems}",
                        "destination": "${parameters.backup_destination}",
                        "compression": "gzip",
                        "output_path": "/reports/backup_report.json"
                    }
                },
                {
                    "id": "cleanup",
                    "name": "Cleanup",
                    "description": "Clean up old files and logs",
                    "agent": "cleanup_agent",
                    "depends_on": ["backup"],
                    "inputs": {
                        "target_systems": "${parameters.target_systems}",
                        "retention_days": "${parameters.retention_days}",
                        "file_types": ["logs", "temp", "cache"],
                        "output_path": "/reports/cleanup_report.json"
                    }
                },
                {
                    "id": "verify",
                    "name": "Verification",
                    "description": "Verify system integrity after maintenance",
                    "agent": "verifier",
                    "depends_on": ["cleanup"],
                    "inputs": {
                        "target_systems": "${parameters.target_systems}",
                        "checks": ["connectivity", "data_integrity", "performance"],
                        "output_path": "/reports/verification_report.json"
                    }
                },
                {
                    "id": "report",
                    "name": "Reporting",
                    "description": "Generate maintenance report",
                    "agent": "reporter",
                    "depends_on": ["verify"],
                    "inputs": {
                        "report_inputs": [
                            "/reports/health_check.json",
                            "/reports/backup_report.json",
                            "/reports/cleanup_report.json",
                            "/reports/verification_report.json"
                        ],
                        "email": "${parameters.notification_email}",
                        "output_path": "/reports/maintenance_report.html"
                    }
                }
            ],
            metadata={
                "tags": ["maintenance", "operations", "automation"],
                "complexity": "medium",
                "estimated_duration": "1h",
                "recommended_schedule": "weekly"
            }
        )


# Create a global template registry
_template_registry = None

def get_template_registry(templates_dir: Optional[str] = None) -> WorkflowTemplateRegistry:
    """
    Get the global template registry.
    
    Args:
        templates_dir: Directory to load templates from
        
    Returns:
        Global template registry
    """
    global _template_registry
    if _template_registry is None:
        _template_registry = WorkflowTemplateRegistry(templates_dir)
    return _template_registry
