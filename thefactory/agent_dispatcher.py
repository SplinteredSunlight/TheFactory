def execute_task(task_payload: dict) -> dict:
    task_type = task_payload.get("task")

    agent_registry = {
        "build container": "container-builder-agent",
        "scan image": "security-scanner-agent",
        "deploy service": "deployer-agent",
    }

    if task_type in agent_registry:
        return {
            "status": "dispatched",
            "agent": agent_registry[task_type],
            "message": f"{task_type} task sent to {agent_registry[task_type]}"
        }
    else:
        return {
            "status": "error",
            "message": f"No known agent for task: {task_type}"
        }