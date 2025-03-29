"""
Metrics collection for Dagger integration.

This module provides metrics collection for Dagger integration using Prometheus.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional
from functools import wraps
from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, push_to_gateway

# Configure logging
logger = logging.getLogger(__name__)

# Create a registry for Dagger metrics
REGISTRY = CollectorRegistry()

# Define metrics
WORKFLOW_EXECUTIONS = Counter(
    "dagger_workflow_executions_total",
    "Total number of Dagger workflow executions",
    ["workflow_id", "status"],
    registry=REGISTRY
)

WORKFLOW_EXECUTION_DURATION = Histogram(
    "dagger_workflow_execution_duration_seconds",
    "Duration of Dagger workflow executions in seconds",
    ["workflow_id"],
    registry=REGISTRY
)

STEP_EXECUTIONS = Counter(
    "dagger_step_executions_total",
    "Total number of Dagger step executions",
    ["workflow_id", "step_id", "status"],
    registry=REGISTRY
)

STEP_EXECUTION_DURATION = Histogram(
    "dagger_step_execution_duration_seconds",
    "Duration of Dagger step executions in seconds",
    ["workflow_id", "step_id"],
    registry=REGISTRY
)

DAGGER_ERRORS = Counter(
    "dagger_errors_total",
    "Total number of Dagger errors",
    ["error_type"],
    registry=REGISTRY
)

CONCURRENT_WORKFLOWS = Gauge(
    "dagger_concurrent_workflows",
    "Number of concurrent Dagger workflows",
    registry=REGISTRY
)

CONCURRENT_STEPS = Gauge(
    "dagger_concurrent_steps",
    "Number of concurrent Dagger steps",
    registry=REGISTRY
)

MEMORY_USAGE = Gauge(
    "dagger_memory_usage_bytes",
    "Memory usage of Dagger in bytes",
    registry=REGISTRY
)

CPU_USAGE = Gauge(
    "dagger_cpu_usage_percent",
    "CPU usage of Dagger as a percentage",
    registry=REGISTRY
)

# Variables for tracking active executions
_active_workflows: Dict[str, Dict[str, Any]] = {}
_active_steps: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()

# Pushgateway configuration
_pushgateway_url: Optional[str] = None
_push_interval_seconds = 15
_push_job_name = "dagger_metrics"
_push_thread = None
_stop_push_thread = threading.Event()


def configure_pushgateway(url: str, job_name: str = "dagger_metrics", interval_seconds: int = 15):
    """
    Configure the Pushgateway for metrics.
    
    Args:
        url: Pushgateway URL
        job_name: Job name for metrics
        interval_seconds: Interval for pushing metrics in seconds
    """
    global _pushgateway_url, _push_job_name, _push_interval_seconds, _push_thread, _stop_push_thread
    
    _pushgateway_url = url
    _push_job_name = job_name
    _push_interval_seconds = interval_seconds
    
    # Stop existing push thread if running
    if _push_thread and _push_thread.is_alive():
        _stop_push_thread.set()
        _push_thread.join()
    
    # Reset stop event
    _stop_push_thread = threading.Event()
    
    # Start push thread
    _push_thread = threading.Thread(target=_push_metrics_loop)
    _push_thread.daemon = True
    _push_thread.start()
    
    logger.info(f"Configured Pushgateway at {url} with job name {job_name} and interval {interval_seconds}s")


def _push_metrics_loop():
    """Push metrics to Pushgateway in a loop."""
    while not _stop_push_thread.is_set():
        try:
            if _pushgateway_url:
                push_to_gateway(_pushgateway_url, job=_push_job_name, registry=REGISTRY)
                logger.debug(f"Pushed metrics to Pushgateway at {_pushgateway_url}")
        except Exception as e:
            logger.error(f"Error pushing metrics: {e}")
        
        # Wait for next push interval or until stopped
        _stop_push_thread.wait(timeout=_push_interval_seconds)


def stop_metrics_collection():
    """Stop metrics collection and push thread."""
    global _push_thread, _stop_push_thread
    
    if _push_thread and _push_thread.is_alive():
        _stop_push_thread.set()
        _push_thread.join()
        _push_thread = None
        
    logger.info("Stopped metrics collection")


def update_resource_metrics():
    """Update resource usage metrics."""
    try:
        import psutil
        
        # Update memory usage
        memory_info = psutil.Process().memory_info()
        MEMORY_USAGE.set(memory_info.rss)
        
        # Update CPU usage
        CPU_USAGE.set(psutil.Process().cpu_percent())
    except ImportError:
        logger.warning("psutil not installed, resource metrics unavailable")
    except Exception as e:
        logger.error(f"Error updating resource metrics: {e}")


def track_workflow_execution(workflow_id: str, status: str = "running"):
    """
    Track the start of a workflow execution.
    
    Args:
        workflow_id: ID of the workflow being executed
        status: Status of the workflow execution
    """
    with _lock:
        if status == "running":
            _active_workflows[workflow_id] = {
                "start_time": time.time(),
                "steps": {}
            }
            CONCURRENT_WORKFLOWS.inc()
        elif status in ["completed", "failed"]:
            if workflow_id in _active_workflows:
                start_time = _active_workflows[workflow_id]["start_time"]
                duration = time.time() - start_time
                WORKFLOW_EXECUTION_DURATION.labels(workflow_id=workflow_id).observe(duration)
                CONCURRENT_WORKFLOWS.dec()
                _active_workflows.pop(workflow_id)
        
        WORKFLOW_EXECUTIONS.labels(workflow_id=workflow_id, status=status).inc()


def track_step_execution(workflow_id: str, step_id: str, status: str = "running"):
    """
    Track the execution of a workflow step.
    
    Args:
        workflow_id: ID of the workflow
        step_id: ID of the step being executed
        status: Status of the step execution
    """
    with _lock:
        step_key = f"{workflow_id}_{step_id}"
        
        if status == "running":
            _active_steps[step_key] = {
                "start_time": time.time()
            }
            CONCURRENT_STEPS.inc()
        elif status in ["completed", "failed"]:
            if step_key in _active_steps:
                start_time = _active_steps[step_key]["start_time"]
                duration = time.time() - start_time
                STEP_EXECUTION_DURATION.labels(workflow_id=workflow_id, step_id=step_id).observe(duration)
                CONCURRENT_STEPS.dec()
                _active_steps.pop(step_key)
        
        STEP_EXECUTIONS.labels(workflow_id=workflow_id, step_id=step_id, status=status).inc()


def track_error(error_type: str):
    """
    Track an error in Dagger execution.
    
    Args:
        error_type: Type of error
    """
    DAGGER_ERRORS.labels(error_type=error_type).inc()


def track_workflow_execution_time(func):
    """
    Decorator to track workflow execution time.
    
    Args:
        func: Function to track
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(self, workflow_id, *args, **kwargs):
        # Track workflow start
        track_workflow_execution(workflow_id, "running")
        
        try:
            # Execute the function
            result = await func(self, workflow_id, *args, **kwargs)
            
            # Track workflow completion
            status = result.get("status", "completed")
            track_workflow_execution(workflow_id, status)
            
            return result
        except Exception as e:
            # Track workflow failure
            track_workflow_execution(workflow_id, "failed")
            track_error(type(e).__name__)
            
            # Re-raise the exception
            raise
            
    return wrapper


def track_step_execution_time(func):
    """
    Decorator to track step execution time.
    
    Args:
        func: Function to track
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Extract workflow_id and step_id from kwargs or args
        workflow_id = kwargs.get("workflow_id", args[0] if args else "unknown")
        step_id = kwargs.get("step_id", args[1] if len(args) > 1 else "unknown")
        
        # Track step start
        track_step_execution(workflow_id, step_id, "running")
        
        try:
            # Execute the function
            result = await func(self, *args, **kwargs)
            
            # Track step completion
            status = "completed" if result.get("success", False) else "failed"
            track_step_execution(workflow_id, step_id, status)
            
            return result
        except Exception as e:
            # Track step failure
            track_step_execution(workflow_id, step_id, "failed")
            track_error(type(e).__name__)
            
            # Re-raise the exception
            raise
            
    return wrapper