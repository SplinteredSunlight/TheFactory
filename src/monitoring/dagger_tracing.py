"""
Distributed tracing for Dagger integration.

This module provides distributed tracing for Dagger integration using OpenTelemetry.
"""

import os
import logging
import functools
from typing import Dict, Any, Optional, Callable, List, Union
import asyncio

# Import OpenTelemetry modules
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.trace.status import Status, StatusCode
    from opentelemetry.trace import SpanKind, Span
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Create dummy classes for type hints
    class TracerProvider: pass
    class Span: pass
    class SpanKind: pass
    class Status: pass
    class StatusCode: pass

from src.monitoring.dagger_logging import DaggerLogger

# Configure logging
logger = DaggerLogger("dagger_tracing")

# Constants
DEFAULT_SERVICE_NAME = "dagger-orchestration-platform"
TRACING_ENABLED = os.environ.get("DAGGER_TRACING_ENABLED", "true").lower() == "true"
OTLP_ENDPOINT = os.environ.get("DAGGER_OTLP_ENDPOINT", "localhost:4317")

# Global tracer provider
_tracer_provider: Optional[TracerProvider] = None
_tracer = None


def setup_tracing(service_name: str = DEFAULT_SERVICE_NAME, endpoint: str = OTLP_ENDPOINT) -> bool:
    """
    Set up distributed tracing.
    
    Args:
        service_name: Name of the service
        endpoint: OTLP endpoint for exporting traces
        
    Returns:
        True if tracing was set up successfully, False otherwise
    """
    global _tracer_provider, _tracer
    
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available. Tracing will be disabled.")
        return False
    
    if not TRACING_ENABLED:
        logger.info("Tracing is disabled by configuration.")
        return False
    
    try:
        # Create a resource with service name
        resource = Resource.create({SERVICE_NAME: service_name})
        
        # Create a tracer provider
        _tracer_provider = TracerProvider(resource=resource)
        
        # Set the tracer provider
        trace.set_tracer_provider(_tracer_provider)
        
        # Create exporters
        console_exporter = ConsoleSpanExporter()
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        
        # Add exporters to the tracer provider
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Create a tracer
        _tracer = trace.get_tracer(__name__)
        
        logger.info(f"Distributed tracing set up for service {service_name} with endpoint {endpoint}")
        return True
    except Exception as e:
        logger.error(f"Error setting up tracing: {e}")
        return False


def get_tracer():
    """
    Get the tracer.
    
    Returns:
        Tracer instance
    """
    global _tracer
    
    if _tracer is None and OPENTELEMETRY_AVAILABLE and TRACING_ENABLED:
        setup_tracing()
    
    return _tracer


def create_span(name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: Dict[str, Any] = None, parent: Span = None) -> Optional[Span]:
    """
    Create a new span.
    
    Args:
        name: Name of the span
        kind: Kind of span
        attributes: Attributes to add to the span
        parent: Parent span
        
    Returns:
        New span or None if tracing is not available
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return None
    
    tracer = get_tracer()
    if tracer is None:
        return None
    
    # Create a new span
    span = tracer.start_span(
        name=name,
        kind=kind,
        attributes=attributes or {}
    )
    
    return span


def trace_workflow(func):
    """
    Decorator to trace a workflow execution.
    
    Args:
        func: Function to trace
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    async def wrapper(self, workflow_id, *args, **kwargs):
        if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
            return await func(self, workflow_id, *args, **kwargs)
        
        tracer = get_tracer()
        if tracer is None:
            return await func(self, workflow_id, *args, **kwargs)
        
        # Extract workflow attributes
        workflow_name = kwargs.get("workflow_name", "unknown")
        workflow_type = kwargs.get("workflow_type", "unknown")
        
        # Create a span for the workflow execution
        with tracer.start_as_current_span(
            name=f"workflow.execute.{workflow_name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "workflow.id": workflow_id,
                "workflow.name": workflow_name,
                "workflow.type": workflow_type
            }
        ) as span:
            try:
                # Execute the function
                result = await func(self, workflow_id, *args, **kwargs)
                
                # Add result attributes to the span
                status = result.get("status", "unknown")
                span.set_attribute("workflow.status", status)
                
                if status == "failed":
                    span.set_status(Status(StatusCode.ERROR))
                    error = result.get("error", "Unknown error")
                    span.record_exception(Exception(error))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                return result
            except Exception as e:
                # Record the exception
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                
                # Re-raise the exception
                raise
    
    return wrapper


def trace_step(func):
    """
    Decorator to trace a step execution.
    
    Args:
        func: Function to trace
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
            return await func(self, *args, **kwargs)
        
        tracer = get_tracer()
        if tracer is None:
            return await func(self, *args, **kwargs)
        
        # Extract step attributes
        workflow_id = kwargs.get("workflow_id", args[0] if args else "unknown")
        step_id = kwargs.get("step_id", args[1] if len(args) > 1 else "unknown")
        step_name = kwargs.get("step_name", "unknown")
        step_type = kwargs.get("step_type", "unknown")
        
        # Create a span for the step execution
        with tracer.start_as_current_span(
            name=f"step.execute.{step_name}",
            kind=SpanKind.INTERNAL,
            attributes={
                "workflow.id": workflow_id,
                "step.id": step_id,
                "step.name": step_name,
                "step.type": step_type
            }
        ) as span:
            try:
                # Execute the function
                result = await func(self, *args, **kwargs)
                
                # Add result attributes to the span
                success = result.get("success", False)
                span.set_attribute("step.success", success)
                
                if not success:
                    span.set_status(Status(StatusCode.ERROR))
                    error = result.get("error", "Unknown error")
                    span.record_exception(Exception(error))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                return result
            except Exception as e:
                # Record the exception
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                
                # Re-raise the exception
                raise
    
    return wrapper


def trace_function(name: str = None, attributes: Dict[str, Any] = None):
    """
    Decorator to trace a function execution.
    
    Args:
        name: Name of the span
        attributes: Attributes to add to the span
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
                return await func(*args, **kwargs)
            
            tracer = get_tracer()
            if tracer is None:
                return await func(*args, **kwargs)
            
            # Determine span name
            span_name = name or func.__name__
            
            # Create a span for the function execution
            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.INTERNAL,
                attributes=attributes or {}
            ) as span:
                try:
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Set status to OK
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                except Exception as e:
                    # Record the exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    
                    # Re-raise the exception
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
                return func(*args, **kwargs)
            
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)
            
            # Determine span name
            span_name = name or func.__name__
            
            # Create a span for the function execution
            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.INTERNAL,
                attributes=attributes or {}
            ) as span:
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Set status to OK
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                except Exception as e:
                    # Record the exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    
                    # Re-raise the exception
                    raise
        
        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def extract_context_from_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract trace context from headers.
    
    Args:
        headers: HTTP headers
        
    Returns:
        Trace context
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return {}
    
    try:
        propagator = TraceContextTextMapPropagator()
        context = {}
        propagator.extract(carrier=headers, context=context)
        return context
    except Exception as e:
        logger.error(f"Error extracting trace context: {e}")
        return {}


def inject_context_into_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers.
    
    Args:
        headers: HTTP headers
        
    Returns:
        HTTP headers with trace context
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return headers
    
    try:
        propagator = TraceContextTextMapPropagator()
        propagator.inject(carrier=headers)
        return headers
    except Exception as e:
        logger.error(f"Error injecting trace context: {e}")
        return headers


def get_current_span() -> Optional[Span]:
    """
    Get the current span.
    
    Returns:
        Current span or None if tracing is not available
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return None
    
    return trace.get_current_span()


def add_span_event(name: str, attributes: Dict[str, Any] = None) -> None:
    """
    Add an event to the current span.
    
    Args:
        name: Name of the event
        attributes: Attributes to add to the event
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return
    
    span = get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def add_span_attribute(key: str, value: Any) -> None:
    """
    Add an attribute to the current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return
    
    span = get_current_span()
    if span:
        span.set_attribute(key, value)


def set_span_status(status: StatusCode, description: str = None) -> None:
    """
    Set the status of the current span.
    
    Args:
        status: Status code
        description: Status description
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return
    
    span = get_current_span()
    if span:
        span.set_status(Status(status, description))


def record_exception(exception: Exception) -> None:
    """
    Record an exception in the current span.
    
    Args:
        exception: Exception to record
    """
    if not OPENTELEMETRY_AVAILABLE or not TRACING_ENABLED:
        return
    
    span = get_current_span()
    if span:
        span.record_exception(exception)
