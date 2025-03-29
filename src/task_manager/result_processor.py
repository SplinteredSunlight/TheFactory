"""
Result Processor for Task Management

This module provides utilities for processing and handling workflow execution results.
It supports result validation, normalization, transformation, and storage.
"""

import os
import sys
import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple, Callable

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.circuit_breaker import get_circuit_breaker, execute_with_circuit_breaker
from src.orchestrator.error_handling import IntegrationError

logger = logging.getLogger(__name__)


class ResultSchema:
    """
    Schema for workflow execution results.
    
    This class defines the expected structure and validation rules
    for workflow execution results.
    """
    
    def __init__(
        self,
        schema_id: str,
        properties: Dict[str, Dict[str, Any]],
        required: Optional[List[str]] = None,
        description: Optional[str] = None
    ):
        """
        Initialize a result schema.
        
        Args:
            schema_id: Unique identifier for the schema
            properties: Dictionary of property definitions
            required: List of required property names
            description: Description of the schema
        """
        self.schema_id = schema_id
        self.properties = properties
        self.required = required or []
        self.description = description
    
    def validate(self, result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a result against this schema.
        
        Args:
            result: The result to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required properties
        for prop in self.required:
            if prop not in result:
                errors.append(f"Missing required property: {prop}")
        
        # Check property types
        for prop_name, prop_value in result.items():
            if prop_name not in self.properties:
                continue
            
            prop_def = self.properties[prop_name]
            prop_type = prop_def.get("type")
            
            if prop_type == "string" and not isinstance(prop_value, str):
                errors.append(f"Property {prop_name} must be a string")
            elif prop_type == "number" and not isinstance(prop_value, (int, float)):
                errors.append(f"Property {prop_name} must be a number")
            elif prop_type == "boolean" and not isinstance(prop_value, bool):
                errors.append(f"Property {prop_name} must be a boolean")
            elif prop_type == "array" and not isinstance(prop_value, list):
                errors.append(f"Property {prop_name} must be an array")
            elif prop_type == "object" and not isinstance(prop_value, dict):
                errors.append(f"Property {prop_name} must be an object")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary."""
        return {
            "schema_id": self.schema_id,
            "properties": self.properties,
            "required": self.required,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultSchema':
        """Create a schema from a dictionary."""
        return cls(
            schema_id=data["schema_id"],
            properties=data["properties"],
            required=data.get("required", []),
            description=data.get("description")
        )


class ResultTransformer:
    """
    Transformer for workflow execution results.
    
    This class provides methods for transforming results from one format to another.
    """
    
    def __init__(
        self,
        transformer_id: str,
        source_schema_id: str,
        target_schema_id: str,
        transform_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        description: Optional[str] = None
    ):
        """
        Initialize a result transformer.
        
        Args:
            transformer_id: Unique identifier for the transformer
            source_schema_id: ID of the source schema
            target_schema_id: ID of the target schema
            transform_func: Function to transform results
            description: Description of the transformer
        """
        self.transformer_id = transformer_id
        self.source_schema_id = source_schema_id
        self.target_schema_id = target_schema_id
        self.transform_func = transform_func
        self.description = description
    
    def transform(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a result.
        
        Args:
            result: The result to transform
            
        Returns:
            The transformed result
        """
        return self.transform_func(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the transformer to a dictionary."""
        return {
            "transformer_id": self.transformer_id,
            "source_schema_id": self.source_schema_id,
            "target_schema_id": self.target_schema_id,
            "description": self.description
        }


class ResultProcessor:
    """
    Processor for workflow execution results.
    
    This class provides methods for processing, validating, transforming,
    and storing workflow execution results.
    """
    
    def __init__(
        self,
        result_dir: Optional[str] = None,
        max_cache_size: int = 100
    ):
        """
        Initialize a result processor.
        
        Args:
            result_dir: Directory for storing results
            max_cache_size: Maximum number of results to cache in memory
        """
        self.result_dir = result_dir or os.path.join(os.getcwd(), ".workflow_results")
        self.max_cache_size = max_cache_size
        self.schemas = {}
        self.transformers = {}
        self.result_cache = {}
        self.circuit_breaker = get_circuit_breaker("result_processor")
        
        # Create result directory if it doesn't exist
        if not os.path.exists(self.result_dir):
            os.makedirs(self.result_dir)
        
        # Load default schemas
        self._load_default_schemas()
    
    def _load_default_schemas(self) -> None:
        """Load default result schemas."""
        # Generic result schema
        generic_schema = ResultSchema(
            schema_id="generic",
            properties={
                "success": {"type": "boolean", "description": "Whether the workflow succeeded"},
                "result": {"type": "object", "description": "The result data"},
                "error": {"type": "string", "description": "Error message if the workflow failed"},
                "timestamp": {"type": "string", "description": "When the result was generated"}
            },
            required=["success"],
            description="Generic workflow result schema"
        )
        self.schemas["generic"] = generic_schema
        
        # Containerized workflow result schema
        container_schema = ResultSchema(
            schema_id="containerized_workflow",
            properties={
                "success": {"type": "boolean", "description": "Whether the workflow succeeded"},
                "result": {"type": "object", "description": "The result data"},
                "error": {"type": "string", "description": "Error message if the workflow failed"},
                "timestamp": {"type": "string", "description": "When the result was generated"},
                "container_id": {"type": "string", "description": "ID of the container"},
                "container_status": {"type": "string", "description": "Status of the container"},
                "logs": {"type": "string", "description": "Container logs"}
            },
            required=["success", "container_id"],
            description="Containerized workflow result schema"
        )
        self.schemas["containerized_workflow"] = container_schema
        
        # Dagger pipeline result schema
        pipeline_schema = ResultSchema(
            schema_id="dagger_pipeline",
            properties={
                "success": {"type": "boolean", "description": "Whether the pipeline succeeded"},
                "result": {"type": "object", "description": "The result data"},
                "error": {"type": "string", "description": "Error message if the pipeline failed"},
                "timestamp": {"type": "string", "description": "When the result was generated"},
                "pipeline_id": {"type": "string", "description": "ID of the pipeline"},
                "pipeline_status": {"type": "string", "description": "Status of the pipeline"},
                "steps": {"type": "array", "description": "Pipeline steps and their results"}
            },
            required=["success", "pipeline_id"],
            description="Dagger pipeline result schema"
        )
        self.schemas["dagger_pipeline"] = pipeline_schema
    
    def register_schema(self, schema: ResultSchema) -> None:
        """
        Register a result schema.
        
        Args:
            schema: The schema to register
        """
        self.schemas[schema.schema_id] = schema
        logger.debug(f"Registered result schema: {schema.schema_id}")
    
    def get_schema(self, schema_id: str) -> Optional[ResultSchema]:
        """
        Get a result schema by ID.
        
        Args:
            schema_id: ID of the schema to retrieve
            
        Returns:
            The schema or None if not found
        """
        return self.schemas.get(schema_id)
    
    def register_transformer(self, transformer: ResultTransformer) -> None:
        """
        Register a result transformer.
        
        Args:
            transformer: The transformer to register
        """
        self.transformers[transformer.transformer_id] = transformer
        logger.debug(f"Registered result transformer: {transformer.transformer_id}")
    
    def get_transformer(self, transformer_id: str) -> Optional[ResultTransformer]:
        """
        Get a result transformer by ID.
        
        Args:
            transformer_id: ID of the transformer to retrieve
            
        Returns:
            The transformer or None if not found
        """
        return self.transformers.get(transformer_id)
    
    def validate_result(
        self,
        result: Dict[str, Any],
        schema_id: str = "generic"
    ) -> Tuple[bool, List[str]]:
        """
        Validate a result against a schema.
        
        Args:
            result: The result to validate
            schema_id: ID of the schema to validate against
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.get_schema(schema_id)
        if not schema:
            return False, [f"Schema not found: {schema_id}"]
        
        return schema.validate(result)
    
    def normalize_result(
        self,
        result: Dict[str, Any],
        schema_id: str = "generic"
    ) -> Dict[str, Any]:
        """
        Normalize a result to match a schema.
        
        Args:
            result: The result to normalize
            schema_id: ID of the schema to normalize against
            
        Returns:
            The normalized result
        """
        schema = self.get_schema(schema_id)
        if not schema:
            return result
        
        # Start with a copy of the result
        normalized = result.copy()
        
        # Add default values for missing properties
        for prop_name, prop_def in schema.properties.items():
            if prop_name not in normalized and "default" in prop_def:
                normalized[prop_name] = prop_def["default"]
        
        # Add timestamp if not present
        if "timestamp" in schema.properties and "timestamp" not in normalized:
            normalized["timestamp"] = datetime.now().isoformat()
        
        return normalized
    
    def transform_result(
        self,
        result: Dict[str, Any],
        transformer_id: str
    ) -> Dict[str, Any]:
        """
        Transform a result using a transformer.
        
        Args:
            result: The result to transform
            transformer_id: ID of the transformer to use
            
        Returns:
            The transformed result
            
        Raises:
            ValueError: If the transformer is not found
        """
        transformer = self.get_transformer(transformer_id)
        if not transformer:
            raise ValueError(f"Transformer not found: {transformer_id}")
        
        return transformer.transform(result)
    
    def _get_result_key(self, workflow_id: str, task_id: Optional[str] = None) -> str:
        """
        Generate a key for storing a result.
        
        Args:
            workflow_id: ID of the workflow
            task_id: ID of the task (optional)
            
        Returns:
            Result key as a string
        """
        if task_id:
            return f"{workflow_id}_{task_id}"
        return workflow_id
    
    def _get_result_path(self, result_key: str) -> str:
        """
        Generate a file path for storing a result.
        
        Args:
            result_key: Key for the result
            
        Returns:
            File path as a string
        """
        # Use a hash of the key to avoid file system issues
        key_hash = hashlib.md5(result_key.encode()).hexdigest()
        return os.path.join(self.result_dir, f"{key_hash}.json")
    
    async def store_result(
        self,
        workflow_id: str,
        result: Dict[str, Any],
        task_id: Optional[str] = None,
        schema_id: str = "generic",
        use_circuit_breaker: bool = True
    ) -> str:
        """
        Store a workflow execution result.
        
        Args:
            workflow_id: ID of the workflow
            result: The result to store
            task_id: ID of the task (optional)
            schema_id: ID of the schema to validate against
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            Result key as a string
            
        Raises:
            ValueError: If the result is invalid
        """
        # Validate the result
        is_valid, errors = self.validate_result(result, schema_id)
        if not is_valid:
            error_message = f"Invalid result: {', '.join(errors)}"
            logger.error(error_message)
            raise ValueError(error_message)
        
        # Normalize the result
        normalized = self.normalize_result(result, schema_id)
        
        # Generate result key
        result_key = self._get_result_key(workflow_id, task_id)
        
        # Add to cache
        self.result_cache[result_key] = normalized
        
        # Trim cache if needed
        if len(self.result_cache) > self.max_cache_size:
            # Remove oldest entries
            keys_to_remove = sorted(
                self.result_cache.keys(),
                key=lambda k: self.result_cache[k].get("timestamp", ""),
                reverse=True
            )[self.max_cache_size:]
            
            for key in keys_to_remove:
                del self.result_cache[key]
        
        # Store to disk
        result_path = self._get_result_path(result_key)
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._write_result_to_disk(result_path, normalized)
                )
            else:
                await self._write_result_to_disk(result_path, normalized)
        except Exception as e:
            logger.error(f"Failed to store result to disk: {e}")
            # Still return the key even if disk storage failed
        
        return result_key
    
    async def _write_result_to_disk(self, result_path: str, result: Dict[str, Any]) -> None:
        """
        Write a result to disk.
        
        Args:
            result_path: Path to write the result to
            result: The result to write
        """
        try:
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write result to disk: {e}")
            raise IntegrationError(f"Failed to write result to disk: {e}")
    
    async def get_result(
        self,
        workflow_id: str,
        task_id: Optional[str] = None,
        use_circuit_breaker: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a workflow execution result.
        
        Args:
            workflow_id: ID of the workflow
            task_id: ID of the task (optional)
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            The result or None if not found
        """
        # Generate result key
        result_key = self._get_result_key(workflow_id, task_id)
        
        # Check cache first
        if result_key in self.result_cache:
            return self.result_cache[result_key]
        
        # Check disk
        result_path = self._get_result_path(result_key)
        if not os.path.exists(result_path):
            return None
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                result = await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._read_result_from_disk(result_path)
                )
            else:
                result = await self._read_result_from_disk(result_path)
            
            # Add to cache
            self.result_cache[result_key] = result
            
            return result
        except Exception as e:
            logger.error(f"Failed to read result from disk: {e}")
            return None
    
    async def _read_result_from_disk(self, result_path: str) -> Dict[str, Any]:
        """
        Read a result from disk.
        
        Args:
            result_path: Path to read the result from
            
        Returns:
            The result
        """
        try:
            with open(result_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read result from disk: {e}")
            raise IntegrationError(f"Failed to read result from disk: {e}")
    
    async def delete_result(
        self,
        workflow_id: str,
        task_id: Optional[str] = None,
        use_circuit_breaker: bool = True
    ) -> bool:
        """
        Delete a workflow execution result.
        
        Args:
            workflow_id: ID of the workflow
            task_id: ID of the task (optional)
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            True if the result was deleted, False otherwise
        """
        # Generate result key
        result_key = self._get_result_key(workflow_id, task_id)
        
        # Remove from cache
        if result_key in self.result_cache:
            del self.result_cache[result_key]
        
        # Remove from disk
        result_path = self._get_result_path(result_key)
        if not os.path.exists(result_path):
            return False
        
        try:
            # Use circuit breaker if enabled
            if use_circuit_breaker:
                await execute_with_circuit_breaker(
                    self.circuit_breaker,
                    lambda: self._delete_result_from_disk(result_path)
                )
            else:
                await self._delete_result_from_disk(result_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete result from disk: {e}")
            return False
    
    async def _delete_result_from_disk(self, result_path: str) -> None:
        """
        Delete a result from disk.
        
        Args:
            result_path: Path to delete the result from
        """
        try:
            os.remove(result_path)
        except Exception as e:
            logger.error(f"Failed to delete result from disk: {e}")
            raise IntegrationError(f"Failed to delete result from disk: {e}")
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self.result_cache = {}
        logger.debug("Result cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the result cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self.result_cache),
            "cache_keys": list(self.result_cache.keys())
        }


def get_result_processor(
    result_dir: Optional[str] = None,
    max_cache_size: int = 100
) -> ResultProcessor:
    """
    Get a ResultProcessor instance.
    
    Args:
        result_dir: Directory for storing results
        max_cache_size: Maximum number of results to cache in memory
        
    Returns:
        ResultProcessor instance
    """
    return ResultProcessor(result_dir, max_cache_size)
