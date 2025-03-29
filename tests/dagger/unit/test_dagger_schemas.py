"""
Unit tests for Dagger-related schemas.
"""
import pytest
from pydantic import ValidationError

from src.agent_manager.schemas import (
    AgentFramework, 
    AgentCapability, 
    AgentConfig, 
    DaggerConfig,
    DaggerContainerConfig,
    DaggerWorkflowConfig,
    DaggerWorkflowStep,
    DaggerPipelineConfig
)


def test_agent_framework_enum():
    """Test that the AgentFramework enum includes Dagger."""
    assert AgentFramework.DAGGER.value == "dagger"
    assert "dagger" in [f.value for f in AgentFramework]


def test_agent_capability_enum():
    """Test that the AgentCapability enum includes Dagger capabilities."""
    assert AgentCapability.CONTAINERIZED_WORKFLOW.value == "containerized_workflow"
    assert AgentCapability.DAGGER_PIPELINE.value == "dagger_pipeline"
    assert "containerized_workflow" in [c.value for c in AgentCapability]
    assert "dagger_pipeline" in [c.value for c in AgentCapability]


def test_dagger_container_config():
    """Test the DaggerContainerConfig schema."""
    # Valid configuration
    config = DaggerContainerConfig(
        image="python:3.9",
        environment={"ENV_VAR": "value"},
        volumes=[{"source": "/tmp", "target": "/data"}],
        command=["python", "script.py"],
        working_dir="/app",
        registry_credentials={"username": "user", "password": "pass"}
    )
    
    assert config.image == "python:3.9"
    assert config.environment == {"ENV_VAR": "value"}
    assert config.volumes == [{"source": "/tmp", "target": "/data"}]
    assert config.command == ["python", "script.py"]
    assert config.working_dir == "/app"
    assert config.registry_credentials == {"username": "user", "password": "pass"}
    
    # Missing required field (image)
    with pytest.raises(ValidationError):
        DaggerContainerConfig()
    
    # Default values
    config = DaggerContainerConfig(image="alpine")
    assert config.environment == {}
    assert config.volumes == []
    assert config.command is None
    assert config.working_dir is None
    assert config.registry_credentials is None


def test_dagger_config():
    """Test the DaggerConfig schema."""
    # Valid configuration
    config = DaggerConfig(
        name="Test Config",
        description="Test description",
        container_registry="docker.io",
        container_credentials={"username": "user", "password": "pass"},
        workflow_directory="/workflows",
        workflow_defaults={"runtime": "python"},
        max_concurrent_executions=5,
        timeout_seconds=600
    )
    
    assert config.name == "Test Config"
    assert config.description == "Test description"
    assert config.container_registry == "docker.io"
    assert config.container_credentials == {"username": "user", "password": "pass"}
    assert config.workflow_directory == "/workflows"
    assert config.workflow_defaults == {"runtime": "python"}
    assert config.max_concurrent_executions == 5
    assert config.timeout_seconds == 600
    
    # Required field (name)
    with pytest.raises(ValidationError):
        DaggerConfig()
    
    # Default values
    config = DaggerConfig(name="Test")
    assert config.description is None
    assert config.container_registry is None
    assert config.container_credentials is None
    assert config.workflow_defaults == {}
    assert config.max_concurrent_executions == 5
    assert config.timeout_seconds == 600


def test_dagger_workflow_step():
    """Test the DaggerWorkflowStep schema."""
    # Valid configuration
    container = DaggerContainerConfig(image="python:3.9")
    step = DaggerWorkflowStep(
        id="step1",
        name="Test Step",
        container=container,
        depends_on=["step0"],
        inputs={"param": "value"},
        outputs=["result"],
        timeout_seconds=300
    )
    
    assert step.id == "step1"
    assert step.name == "Test Step"
    assert step.container.image == "python:3.9"
    assert step.depends_on == ["step0"]
    assert step.inputs == {"param": "value"}
    assert step.outputs == ["result"]
    assert step.timeout_seconds == 300
    
    # Missing required fields
    with pytest.raises(ValidationError):
        DaggerWorkflowStep()
    
    # Default values
    step = DaggerWorkflowStep(id="step1", name="Test Step", container=container)
    assert step.depends_on == []
    assert step.inputs == {}
    assert step.outputs == []
    assert step.timeout_seconds == 300


def test_dagger_workflow_config():
    """Test the DaggerWorkflowConfig schema."""
    # Valid configuration
    container = DaggerContainerConfig(image="python:3.9")
    config = DaggerWorkflowConfig(
        name="Test Workflow",
        description="Test description",
        steps=[{"id": "step1", "name": "Step 1", "container": container.dict()}],
        inputs={"param": "value"},
        outputs=["result"],
        container_config=container,
        timeout_seconds=600
    )
    
    assert config.name == "Test Workflow"
    assert config.description == "Test description"
    assert len(config.steps) == 1
    assert config.steps[0]["id"] == "step1"
    assert config.inputs == {"param": "value"}
    assert config.outputs == ["result"]
    assert config.container_config.image == "python:3.9"
    assert config.timeout_seconds == 600
    
    # Missing required fields
    with pytest.raises(ValidationError):
        DaggerWorkflowConfig()
    
    with pytest.raises(ValidationError):
        DaggerWorkflowConfig(name="Test")  # missing steps
    
    # Default values
    config = DaggerWorkflowConfig(
        name="Test",
        steps=[{"id": "step1", "name": "Step 1", "container": container.dict()}]
    )
    assert config.description is None
    assert config.inputs == {}
    assert config.outputs == []
    assert config.container_config is None
    assert config.timeout_seconds == 600


def test_dagger_pipeline_config():
    """Test the DaggerPipelineConfig schema."""
    # Valid configuration with string pipeline definition
    config = DaggerPipelineConfig(
        name="Test Pipeline",
        description="Test description",
        source_directory="/src",
        pipeline_definition="pipeline.yml",
        inputs={"param": "value"},
        caching_enabled=True,
        timeout_seconds=1800
    )
    
    assert config.name == "Test Pipeline"
    assert config.description == "Test description"
    assert config.source_directory == "/src"
    assert config.pipeline_definition == "pipeline.yml"
    assert config.inputs == {"param": "value"}
    assert config.caching_enabled is True
    assert config.timeout_seconds == 1800
    
    # Valid configuration with dict pipeline definition
    config = DaggerPipelineConfig(
        name="Test Pipeline",
        source_directory="/src",
        pipeline_definition={"steps": [{"name": "step1"}]}
    )
    
    assert config.pipeline_definition == {"steps": [{"name": "step1"}]}
    
    # Missing required fields
    with pytest.raises(ValidationError):
        DaggerPipelineConfig()
    
    with pytest.raises(ValidationError):
        DaggerPipelineConfig(name="Test")  # missing source_directory and pipeline_definition
    
    # Default values
    config = DaggerPipelineConfig(
        name="Test",
        source_directory="/src",
        pipeline_definition="pipeline.yml"
    )
    assert config.description is None
    assert config.inputs == {}
    assert config.caching_enabled is True
    assert config.timeout_seconds == 1800


def test_agent_config_with_dagger():
    """Test the AgentConfig with Dagger framework."""
    # Create a Dagger configuration
    dagger_config = DaggerConfig(
        name="Test Dagger Agent",
        description="Test description",
        container_registry="docker.io"
    )
    
    # Create an agent configuration with Dagger framework
    agent_config = AgentConfig(
        agent_id="test-agent",
        framework=AgentFramework.DAGGER,
        config=dagger_config
    )
    
    assert agent_config.agent_id == "test-agent"
    assert agent_config.framework == AgentFramework.DAGGER
    assert agent_config.config.name == "Test Dagger Agent"
    assert agent_config.config.container_registry == "docker.io"
    
    # Check default capabilities for Dagger
    assert len(agent_config.config.capabilities) == 2
    assert AgentCapability.CONTAINERIZED_WORKFLOW.value in agent_config.config.capabilities
    assert AgentCapability.DAGGER_PIPELINE.value in agent_config.config.capabilities
    
    # Wrong config type for framework
    with pytest.raises(ValueError):
        from src.agent_manager.schemas import FastAgentConfig
        AgentConfig(
            agent_id="test-agent",
            framework=AgentFramework.DAGGER,
            config=FastAgentConfig(name="Test", instruction="Test")
        )