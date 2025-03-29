"""
Unit tests for Dagger integration in the orchestrator engine.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.orchestrator.engine import OrchestrationEngine, Workflow, Task


def test_workflow_execute_with_default_engine():
    """Test that the workflow execute method uses the default engine when not specified."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks to the workflow
    workflow.add_task(name="task1", agent="agent1")
    workflow.add_task(name="task2", agent="agent2")
    
    # Execute the workflow
    result = workflow.execute()
    
    assert result["workflow_id"] == workflow.id
    assert result["status"] == "success"
    assert len(result["tasks"]) == 2
    assert "placeholder" in result["results"]


def test_workflow_execute_with_dagger_engine():
    """Test that the workflow execute method uses the Dagger engine when specified."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks to the workflow
    workflow.add_task(name="task1", agent="agent1")
    workflow.add_task(name="task2", agent="agent2")
    
    # Execute the workflow with Dagger engine
    with patch.object(workflow, '_execute_with_dagger') as mock_execute_dagger:
        mock_execute_dagger.return_value = {"status": "success", "engine": "dagger"}
        result = workflow.execute(engine_type="dagger")
    
    assert result["status"] == "success"
    assert result["engine"] == "dagger"
    mock_execute_dagger.assert_called_once()


def test_workflow_execute_with_dagger():
    """Test the _execute_with_dagger method."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks to the workflow
    task1_id = workflow.add_task(name="task1", agent="agent1")
    task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
    
    # Execute the workflow with Dagger
    result = workflow._execute_with_dagger(
        container_registry="docker.io",
        workflow_directory="/tmp/workflows",
        workflow_defaults={"inputs": {"param": "value"}}
    )
    
    assert result["workflow_id"] == workflow.id
    assert result["status"] == "success"
    assert result["engine"] == "dagger"
    assert len(result["tasks"]) == 2
    assert "message" in result["results"]


def test_workflow_execute_with_dagger_exception():
    """Test that _execute_with_dagger handles exceptions."""
    workflow = Workflow(name="test-workflow")
    
    # Mock _get_tasks_in_execution_order to raise an exception
    with patch.object(workflow, '_get_tasks_in_execution_order', side_effect=Exception("Test error")):
        result = workflow._execute_with_dagger()
    
    assert result["workflow_id"] == workflow.id
    assert result["status"] == "error"
    assert result["engine"] == "dagger"
    assert "error" in result
    assert "Test error" in result["error"]


def test_get_tasks_in_execution_order_simple():
    """Test the _get_tasks_in_execution_order method with simple dependencies."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks with dependencies
    task1_id = workflow.add_task(name="task1", agent="agent1")
    task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
    task3_id = workflow.add_task(name="task3", agent="agent3", depends_on=[task2_id])
    
    # Get tasks in execution order
    ordered_tasks = workflow._get_tasks_in_execution_order()
    
    # Check that tasks are in correct order
    assert len(ordered_tasks) == 3
    assert ordered_tasks[0].id == task1_id
    assert ordered_tasks[1].id == task2_id
    assert ordered_tasks[2].id == task3_id


def test_get_tasks_in_execution_order_complex():
    """Test the _get_tasks_in_execution_order method with complex dependencies."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks with complex dependencies
    # A -> B
    # A -> C
    # B -> D
    # C -> D
    task_a_id = workflow.add_task(name="task_a", agent="agent1")
    task_b_id = workflow.add_task(name="task_b", agent="agent2", depends_on=[task_a_id])
    task_c_id = workflow.add_task(name="task_c", agent="agent3", depends_on=[task_a_id])
    task_d_id = workflow.add_task(name="task_d", agent="agent4", depends_on=[task_b_id, task_c_id])
    
    # Get tasks in execution order
    ordered_tasks = workflow._get_tasks_in_execution_order()
    
    # Check that tasks are in valid order
    assert len(ordered_tasks) == 4
    assert ordered_tasks[0].id == task_a_id
    
    # B and C can be in any order, but must be before D
    b_index = next(i for i, task in enumerate(ordered_tasks) if task.id == task_b_id)
    c_index = next(i for i, task in enumerate(ordered_tasks) if task.id == task_c_id)
    d_index = next(i for i, task in enumerate(ordered_tasks) if task.id == task_d_id)
    
    assert b_index > 0  # B comes after A
    assert c_index > 0  # C comes after A
    assert d_index > b_index  # D comes after B
    assert d_index > c_index  # D comes after C


def test_get_tasks_in_execution_order_circular():
    """Test that _get_tasks_in_execution_order detects circular dependencies."""
    workflow = Workflow(name="test-workflow")
    
    # Add some tasks with circular dependencies
    # A -> B -> C -> A
    task_a_id = workflow.add_task(name="task_a", agent="agent1")
    task_b_id = workflow.add_task(name="task_b", agent="agent2", depends_on=[task_a_id])
    task_c_id = workflow.add_task(name="task_c", agent="agent3", depends_on=[task_b_id])
    
    # Manually add a circular dependency
    task_a = workflow.tasks[task_a_id]
    task_a.add_dependency(task_c_id)
    
    # Try to get tasks in execution order
    with pytest.raises(ValueError) as excinfo:
        workflow._get_tasks_in_execution_order()
    
    assert "Circular dependency detected" in str(excinfo.value)


def test_orchestration_engine_execute_workflow():
    """Test the execute_workflow method of OrchestrationEngine."""
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(name="test-workflow")
    
    # Mock the workflow execute method
    with patch.object(workflow, 'execute') as mock_execute:
        mock_execute.return_value = {"status": "success"}
        
        # Execute the workflow
        result = engine.execute_workflow(workflow.id)
    
    assert result["status"] == "success"
    mock_execute.assert_called_once_with()


def test_orchestration_engine_execute_workflow_with_dagger():
    """Test the execute_workflow method of OrchestrationEngine with Dagger engine type."""
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(name="test-workflow")
    
    # Mock the workflow execute method
    with patch.object(workflow, 'execute') as mock_execute:
        mock_execute.return_value = {"status": "success", "engine": "dagger"}
        
        # Execute the workflow with Dagger engine
        result = engine.execute_workflow(workflow.id, engine_type="dagger", param="value")
    
    assert result["status"] == "success"
    assert result["engine"] == "dagger"
    mock_execute.assert_called_once_with(engine_type="dagger", param="value")


def test_orchestration_engine_execute_workflow_invalid_engine():
    """Test that execute_workflow raises an error for invalid engine types."""
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(name="test-workflow")
    
    # Try to execute with an invalid engine type
    with pytest.raises(ValueError) as excinfo:
        engine.execute_workflow(workflow.id, engine_type="invalid")
    
    assert "Unsupported execution engine" in str(excinfo.value)