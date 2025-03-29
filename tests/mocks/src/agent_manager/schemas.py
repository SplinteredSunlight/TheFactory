"""
Mock Agent Manager Schemas module for testing.

This module provides mock implementations of Agent Manager schemas classes and functions
for testing purposes.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime


class AgentCapability(str, Enum):
    """Common agent capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    TEXT_PROCESSING = "text_processing"
    IMAGE_ANALYSIS = "image_analysis"
    DATA_EXTRACTION = "data_extraction"
    CONVERSATION = "conversation"
    REASONING = "reasoning"
    LONG_CONTEXT = "long_context"
    CONTAINERIZED_WORKFLOW = "containerized_workflow"
    DAGGER_PIPELINE = "dagger_pipeline"
    CUSTOM = "custom"


class AgentStatus:
    """Mock AgentStatus class."""
    
    def __init__(self, adapter_id, is_ready=True, current_load=0, max_load=10, status="running", details=None):
        """Initialize a new AgentStatus."""
        self.adapter_id = adapter_id
        self.is_ready = is_ready
        self.current_load = current_load
        self.max_load = max_load
        self.status = status
        self.details = details or {}


class AgentExecutionConfig:
    """Mock AgentExecutionConfig class."""
    
    def __init__(self, task_id, execution_type, parameters=None):
        """Initialize a new AgentExecutionConfig."""
        self.task_id = task_id
        self.execution_type = execution_type
        self.parameters = parameters or {}


class AgentExecutionResult:
    """Mock AgentExecutionResult class."""
    
    def __init__(self, success, error=None, result=None):
        """Initialize a new AgentExecutionResult."""
        self.success = success
        self.error = error
        self.result = result
