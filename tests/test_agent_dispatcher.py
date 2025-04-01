from thefactory.agent_dispatcher import execute_task

def test_known_task_dispatch():
    result = execute_task({"task": "build container"})
    assert result["status"] == "dispatched"
    assert result["agent"] == "container-builder-agent"

def test_unknown_task_dispatch():
    result = execute_task({"task": "fly to mars"})
    assert result["status"] == "error"
    assert "No known agent" in result["message"]