"""
Monitoring routes for the AI-Orchestration-Platform.
"""

from fastapi import APIRouter, Response, Depends, HTTPException, Query
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.parser import text_string_to_metric_families
from typing import Dict, Any, List, Optional
import time

from src.monitoring.dagger_metrics import REGISTRY as DAGGER_REGISTRY
from src.monitoring.dagger_metrics import update_resource_metrics

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/metrics")
async def metrics():
    """
    Get Prometheus metrics.
    
    Returns:
        Prometheus metrics
    """
    # Update resource metrics
    update_resource_metrics()
    
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/{metric_name}", response_class=Response)
async def get_metric(metric_name: str):
    """
    Get a specific Prometheus metric.
    
    Args:
        metric_name: Name of the metric to get
        
    Returns:
        Prometheus metric in text format
    """
    # Update resource metrics
    update_resource_metrics()
    
    metrics = generate_latest(REGISTRY)
    
    # Parse metrics to find the requested one
    for family in text_string_to_metric_families(metrics.decode('utf-8')):
        if family.name == metric_name:
            # Return only this metric family
            return Response(content=family.name + " " + str(family.type) + "\n" + 
                           "\n".join([str(sample) for sample in family.samples]), 
                           media_type="text/plain")
    
    raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")


@router.get("/dagger/metrics")
async def dagger_metrics():
    """
    Get Dagger-specific Prometheus metrics.
    
    Returns:
        Prometheus metrics
    """
    # Update resource metrics
    update_resource_metrics()
    
    return Response(generate_latest(DAGGER_REGISTRY), media_type=CONTENT_TYPE_LATEST)


@router.get("/dagger/metrics/{metric_name}", response_class=Response)
async def get_dagger_metric(metric_name: str):
    """
    Get a specific Dagger Prometheus metric.
    
    Args:
        metric_name: Name of the metric to get
        
    Returns:
        Prometheus metric in text format
    """
    # Update resource metrics
    update_resource_metrics()
    
    metrics = generate_latest(DAGGER_REGISTRY)
    
    # Parse metrics to find the requested one
    for family in text_string_to_metric_families(metrics.decode('utf-8')):
        if family.name == metric_name:
            # Return only this metric family
            return Response(content=family.name + " " + str(family.type) + "\n" + 
                           "\n".join([str(sample) for sample in family.samples]), 
                           media_type="text/plain")
    
    raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found")


@router.get("/dagger/status")
async def dagger_status() -> Dict[str, Any]:
    """
    Get Dagger status.
    
    Returns:
        Dictionary with Dagger status
    """
    # Update resource metrics
    update_resource_metrics()
    
    # In a real implementation, this would query the Dagger service
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_workflows": 0,
        "active_steps": 0,
        "memory_usage_mb": 0,
        "cpu_usage_percent": 0,
        "timestamp": time.time()
    }


@router.get("/dagger/workflows/active")
async def dagger_active_workflows() -> List[Dict[str, Any]]:
    """
    Get active Dagger workflows.
    
    Returns:
        List of active workflows
    """
    # In a real implementation, this would query the Dagger service
    return []


@router.get("/health")
async def health_check():
    """
    Check the health of the Dagger system.
    
    Returns:
        Health status of the Dagger system
    """
    # Perform basic health checks
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "dagger_orchestrator": "healthy",
            "prometheus": "healthy",
            "circuit_breaker": "healthy"
        },
        "version": "1.0.0"
    }
    
    return health_status


@router.get("/health/{component}")
async def component_health_check(component: str):
    """
    Check the health of a specific component.
    
    Args:
        component: Name of the component to check
        
    Returns:
        Health status of the component
    """
    # Define component health checks
    component_checks = {
        "dagger_orchestrator": check_orchestrator_health,
        "prometheus": check_prometheus_health,
        "circuit_breaker": check_circuit_breaker_health,
        "workflow_engine": check_workflow_engine_health,
        "task_manager": check_task_manager_health
    }
    
    if component not in component_checks:
        raise HTTPException(status_code=404, detail=f"Component {component} not found")
    
    # Perform component health check
    health_result = await component_checks[component]()
    
    return health_result


@router.get("/workflows/status")
async def get_workflow_status(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get the status of workflows.
    
    Args:
        workflow_id: Optional workflow ID to filter by
        status: Optional status to filter by (running, completed, failed)
        limit: Maximum number of workflows to return
        
    Returns:
        List of workflow statuses
    """
    # This is a placeholder implementation
    workflows = []
    
    # Add some sample data
    for i in range(min(10, limit)):
        workflow = {
            "id": f"workflow-{i}" if not workflow_id else workflow_id,
            "status": "running" if not status else status,
            "start_time": time.time() - 3600,
            "duration": 3600,
            "steps_total": 10,
            "steps_completed": 5,
            "steps_failed": 0
        }
        workflows.append(workflow)
        
        # If workflow_id is specified, return only that workflow
        if workflow_id:
            break
    
    return workflows


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get active alerts.
    
    Args:
        severity: Optional severity to filter by (critical, warning, info)
        status: Optional status to filter by (firing, resolved)
        limit: Maximum number of alerts to return
        
    Returns:
        List of alerts
    """
    # This is a placeholder implementation
    alerts = []
    
    # Add some sample data
    severities = ["critical", "warning", "info"]
    statuses = ["firing", "resolved"]
    
    for i in range(min(10, limit)):
        alert_severity = severity if severity else severities[i % len(severities)]
        alert_status = status if status else statuses[i % len(statuses)]
        
        alert = {
            "id": f"alert-{i}",
            "name": f"Test Alert {i}",
            "severity": alert_severity,
            "status": alert_status,
            "start_time": time.time() - 3600,
            "description": f"This is a test alert {i}",
            "labels": {
                "instance": f"instance-{i}",
                "job": f"job-{i}"
            }
        }
        alerts.append(alert)
    
    return alerts


@router.get("/stats")
async def get_stats():
    """
    Get system statistics.
    
    Returns:
        System statistics
    """
    # This is a placeholder implementation
    stats = {
        "workflows": {
            "total": 100,
            "running": 10,
            "completed": 80,
            "failed": 10
        },
        "steps": {
            "total": 1000,
            "running": 100,
            "completed": 800,
            "failed": 100
        },
        "resources": {
            "cpu_usage": 50.0,
            "memory_usage": 1024 * 1024 * 1024,  # 1 GB
            "disk_usage": 10 * 1024 * 1024 * 1024  # 10 GB
        },
        "uptime": 86400  # 1 day
    }
    
    return stats


# Health check implementations
async def check_orchestrator_health() -> Dict[str, Any]:
    """Check the health of the Dagger orchestrator."""
    # This is a placeholder implementation
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "details": {
            "api_status": "up",
            "database_connection": "up",
            "message_queue": "up"
        }
    }


async def check_prometheus_health() -> Dict[str, Any]:
    """Check the health of Prometheus."""
    # This is a placeholder implementation
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "details": {
            "api_status": "up",
            "scrape_targets": 10,
            "scrape_interval": "15s"
        }
    }


async def check_circuit_breaker_health() -> Dict[str, Any]:
    """Check the health of the circuit breaker."""
    # This is a placeholder implementation
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "details": {
            "total_circuit_breakers": 5,
            "open_circuit_breakers": 0,
            "half_open_circuit_breakers": 1,
            "closed_circuit_breakers": 4
        }
    }


async def check_workflow_engine_health() -> Dict[str, Any]:
    """Check the health of the workflow engine."""
    # This is a placeholder implementation
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "details": {
            "active_workflows": 10,
            "queued_workflows": 5,
            "worker_status": "up"
        }
    }


async def check_task_manager_health() -> Dict[str, Any]:
    """Check the health of the task manager."""
    # This is a placeholder implementation
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "details": {
            "active_tasks": 20,
            "queued_tasks": 10,
            "worker_status": "up"
        }
    }
