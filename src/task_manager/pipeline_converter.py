"""
Pipeline Converter for Task Management

This module provides utilities for converting tasks to Dagger pipelines.
It supports template-based pipeline generation and custom pipeline definitions.
"""

import os
import sys
import logging
import yaml
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.manager import Task

logger = logging.getLogger(__name__)


class PipelineTemplate:
    """
    Template for generating Dagger pipelines.
    
    A pipeline template defines a parameterized pipeline that can be
    instantiated with specific values for different tasks.
    """
    
    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        template_content: Dict[str, Any],
        parameters: Dict[str, Any],
        category: str = "general",
        version: str = "1.0.0"
    ):
        """
        Initialize a pipeline template.
        
        Args:
            template_id: Unique identifier for the template
            name: Human-readable name for the template
            description: Description of the template
            template_content: The template content as a dictionary
            parameters: Parameter definitions for the template
            category: Category for the template
            version: Version of the template
        """
        self.template_id = template_id
        self.name = name
        self.description = description
        self.template_content = template_content
        self.parameters = parameters
        self.category = category
        self.version = version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "version": self.version,
            # Don't include template_content in the dictionary representation
            # as it might be large
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineTemplate':
        """Create a template from a dictionary."""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            template_content=data["template_content"],
            parameters=data["parameters"],
            category=data.get("category", "general"),
            version=data.get("version", "1.0.0")
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'PipelineTemplate':
        """Load a template from a file."""
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                data = yaml.safe_load(f)
            elif file_path.endswith('.json'):
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        
        return cls.from_dict(data)


class PipelineConverter:
    """
    Converter for transforming tasks to Dagger pipelines.
    
    This class provides methods for converting tasks to Dagger pipelines
    based on templates or custom definitions.
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the pipeline converter.
        
        Args:
            templates_dir: Directory containing pipeline templates
        """
        self.templates_dir = templates_dir or os.path.join(os.getcwd(), "templates", "pipelines")
        self.templates = {}
        self.cache = {}
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # Load templates
        self._load_templates()
    
    def _load_templates(self):
        """Load pipeline templates from the templates directory."""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(('.yaml', '.yml', '.json')):
                try:
                    file_path = os.path.join(self.templates_dir, filename)
                    template = PipelineTemplate.from_file(file_path)
                    self.templates[template.template_id] = template
                    logger.debug(f"Loaded pipeline template: {template.template_id}")
                except Exception as e:
                    logger.error(f"Failed to load template {filename}: {e}")
        
        logger.info(f"Loaded {len(self.templates)} pipeline templates")
    
    def get_template(self, template_id: str) -> Optional[PipelineTemplate]:
        """
        Get a pipeline template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            The template or None if not found
        """
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available pipeline templates.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of template dictionaries
        """
        templates = []
        for template_id, template in self.templates.items():
            if category and template.category != category:
                continue
            templates.append(template.to_dict())
        return templates
    
    def get_categories(self) -> List[str]:
        """
        Get a list of template categories.
        
        Returns:
            List of category names
        """
        categories = set()
        for template in self.templates.values():
            categories.add(template.category)
        return sorted(list(categories))
    
    def _get_cache_key(self, task: Task, template_id: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a cache key for a task and template combination.
        
        Args:
            task: The task
            template_id: ID of the template
            parameters: Template parameters
            
        Returns:
            Cache key as a string
        """
        # Create a deterministic string representation of the task and parameters
        task_dict = {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status,
            "metadata": task.metadata
        }
        
        # Combine task, template ID, and parameters
        combined = {
            "task": task_dict,
            "template_id": template_id,
            "parameters": parameters
        }
        
        # Convert to JSON and hash
        combined_json = json.dumps(combined, sort_keys=True)
        return hashlib.sha256(combined_json.encode()).hexdigest()
    
    def convert_task_to_pipeline(
        self,
        task: Task,
        template_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        skip_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Convert a task to a Dagger pipeline using a template.
        
        Args:
            task: The task to convert
            template_id: ID of the template to use
            parameters: Parameters for the template
            skip_cache: Whether to skip the cache
            
        Returns:
            The generated pipeline as a dictionary
            
        Raises:
            ValueError: If the template is not found
        """
        # Get the template
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Check cache if not skipping
        if not skip_cache:
            cache_key = self._get_cache_key(task, template_id, parameters or {})
            if cache_key in self.cache:
                logger.debug(f"Using cached pipeline for task {task.id}")
                return self.cache[cache_key]
        
        # Prepare parameters
        params = {}
        
        # Add default parameters from template
        for param_name, param_def in template.parameters.items():
            if "default" in param_def:
                params[param_name] = param_def["default"]
        
        # Add task-specific parameters
        if task.metadata and "pipeline_parameters" in task.metadata:
            task_params = task.metadata["pipeline_parameters"]
            for param_name, param_value in task_params.items():
                if param_name in template.parameters:
                    params[param_name] = param_value
        
        # Add provided parameters (overrides defaults and task parameters)
        if parameters:
            for param_name, param_value in parameters.items():
                if param_name in template.parameters:
                    params[param_name] = param_value
        
        # Validate parameters
        self._validate_parameters(template, params)
        
        # Generate pipeline from template
        pipeline = self._generate_pipeline(template, params, task)
        
        # Add to cache
        if not skip_cache:
            cache_key = self._get_cache_key(task, template_id, parameters or {})
            self.cache[cache_key] = pipeline
        
        return pipeline
    
    def _validate_parameters(self, template: PipelineTemplate, parameters: Dict[str, Any]):
        """
        Validate parameters against template requirements.
        
        Args:
            template: The template
            parameters: Parameters to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Check for required parameters
        for param_name, param_def in template.parameters.items():
            if param_def.get("required", False) and param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")
        
        # Check parameter types
        for param_name, param_value in parameters.items():
            if param_name not in template.parameters:
                continue
            
            param_def = template.parameters[param_name]
            param_type = param_def.get("type")
            
            if param_type == "string" and not isinstance(param_value, str):
                raise ValueError(f"Parameter {param_name} must be a string")
            elif param_type == "number" and not isinstance(param_value, (int, float)):
                raise ValueError(f"Parameter {param_name} must be a number")
            elif param_type == "boolean" and not isinstance(param_value, bool):
                raise ValueError(f"Parameter {param_name} must be a boolean")
            elif param_type == "array" and not isinstance(param_value, list):
                raise ValueError(f"Parameter {param_name} must be an array")
            elif param_type == "object" and not isinstance(param_value, dict):
                raise ValueError(f"Parameter {param_name} must be an object")
    
    def _generate_pipeline(
        self,
        template: PipelineTemplate,
        parameters: Dict[str, Any],
        task: Task
    ) -> Dict[str, Any]:
        """
        Generate a pipeline from a template and parameters.
        
        Args:
            template: The template
            parameters: Parameters for the template
            task: The task
            
        Returns:
            The generated pipeline as a dictionary
        """
        # Start with a copy of the template content
        pipeline = template.template_content.copy()
        
        # Add task information
        pipeline["task_id"] = task.id
        pipeline["task_name"] = task.name
        pipeline["task_description"] = task.description
        
        # Replace parameter placeholders in the pipeline
        pipeline = self._replace_parameters(pipeline, parameters, task)
        
        # Add metadata
        pipeline["metadata"] = {
            "template_id": template.template_id,
            "template_version": template.version,
            "generated_at": datetime.now().isoformat(),
            "parameters": parameters
        }
        
        return pipeline
    
    def _replace_parameters(
        self,
        obj: Any,
        parameters: Dict[str, Any],
        task: Task
    ) -> Any:
        """
        Replace parameter placeholders in an object recursively.
        
        Args:
            obj: The object to process
            parameters: Parameters for replacement
            task: The task
            
        Returns:
            The processed object
        """
        if isinstance(obj, dict):
            return {k: self._replace_parameters(v, parameters, task) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_parameters(item, parameters, task) for item in obj]
        elif isinstance(obj, str):
            # Replace parameter placeholders
            result = obj
            
            # Replace task-related placeholders
            result = result.replace("${task.id}", task.id)
            result = result.replace("${task.name}", task.name)
            result = result.replace("${task.description}", task.description)
            
            # Replace parameter placeholders
            for param_name, param_value in parameters.items():
                placeholder = f"${{{param_name}}}"
                if placeholder in result:
                    if isinstance(param_value, (str, int, float, bool)):
                        result = result.replace(placeholder, str(param_value))
            
            return result
        else:
            return obj
    
    def create_custom_pipeline(
        self,
        task: Task,
        pipeline_definition: Dict[str, Any],
        skip_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Create a custom pipeline for a task.
        
        Args:
            task: The task
            pipeline_definition: Custom pipeline definition
            skip_cache: Whether to skip the cache
            
        Returns:
            The processed pipeline as a dictionary
        """
        # Check cache if not skipping
        if not skip_cache:
            # Generate a cache key based on task and pipeline definition
            pipeline_json = json.dumps(pipeline_definition, sort_keys=True)
            cache_key = hashlib.sha256(f"{task.id}:{pipeline_json}".encode()).hexdigest()
            
            if cache_key in self.cache:
                logger.debug(f"Using cached custom pipeline for task {task.id}")
                return self.cache[cache_key]
        
        # Start with a copy of the pipeline definition
        pipeline = pipeline_definition.copy()
        
        # Add task information
        pipeline["task_id"] = task.id
        pipeline["task_name"] = task.name
        pipeline["task_description"] = task.description
        
        # Add metadata
        pipeline["metadata"] = {
            "custom_pipeline": True,
            "generated_at": datetime.now().isoformat()
        }
        
        # Add to cache
        if not skip_cache:
            pipeline_json = json.dumps(pipeline_definition, sort_keys=True)
            cache_key = hashlib.sha256(f"{task.id}:{pipeline_json}".encode()).hexdigest()
            self.cache[cache_key] = pipeline
        
        return pipeline
    
    def optimize_pipeline(self, pipeline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize a pipeline for better performance.
        
        Args:
            pipeline: The pipeline to optimize
            
        Returns:
            The optimized pipeline
        """
        # This is a placeholder for pipeline optimization logic
        # In a real implementation, this would analyze the pipeline and make optimizations
        
        # For now, just return the original pipeline
        return pipeline
    
    def validate_pipeline(self, pipeline: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a pipeline for correctness.
        
        Args:
            pipeline: The pipeline to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for required fields
        required_fields = ["task_id", "task_name"]
        for field in required_fields:
            if field not in pipeline:
                errors.append(f"Missing required field: {field}")
        
        # Check for valid steps
        if "steps" in pipeline:
            steps = pipeline["steps"]
            if not isinstance(steps, list):
                errors.append("Steps must be an array")
            else:
                for i, step in enumerate(steps):
                    if not isinstance(step, dict):
                        errors.append(f"Step {i} must be an object")
                    elif "name" not in step:
                        errors.append(f"Step {i} is missing a name")
        
        return len(errors) == 0, errors
    
    def clear_cache(self):
        """Clear the pipeline cache."""
        self.cache = {}
        logger.debug("Pipeline cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the pipeline cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys())
        }


def get_pipeline_converter(templates_dir: Optional[str] = None) -> PipelineConverter:
    """
    Get a PipelineConverter instance.
    
    Args:
        templates_dir: Directory containing pipeline templates
        
    Returns:
        PipelineConverter instance
    """
    return PipelineConverter(templates_dir)
