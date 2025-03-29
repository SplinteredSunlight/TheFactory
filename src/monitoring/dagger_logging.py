"""
Logging configuration for Dagger integration.

This module provides structured logging for Dagger integration.
"""

import os
import json
import logging
import logging.config
from typing import Dict, Any, Optional
import structlog
from datetime import datetime

# Constants
LOG_LEVEL = os.environ.get("DAGGER_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("DAGGER_LOG_FORMAT", "json")
LOG_OUTPUT = os.environ.get("DAGGER_LOG_OUTPUT", "file")
LOG_FILE = os.environ.get("DAGGER_LOG_FILE", "logs/dagger.log")


def configure_logging():
    """Configure logging for Dagger integration."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.processors.JSONRenderer(),
            },
            'console': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(),
            },
        },
        'handlers': {
            'console': {
                'level': LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'file': {
                'level': LOG_LEVEL,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_FILE,
                'maxBytes': 10485760,  # 10 MB
                'backupCount': 5,
                'formatter': 'json',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'] if LOG_OUTPUT == 'console' else ['file'],
                'level': LOG_LEVEL,
                'propagate': True,
            },
            'dagger': {
                'handlers': ['console'] if LOG_OUTPUT == 'console' else ['file'],
                'level': LOG_LEVEL,
                'propagate': False,
            },
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Configured logging with level {LOG_LEVEL}, format {LOG_FORMAT}, output {LOG_OUTPUT}")
    
    return logger


# Initialize logging
logger = configure_logging()


class DaggerLogger:
    """Logger for Dagger integration."""
    
    def __init__(self, component: str, workflow_id: Optional[str] = None):
        """
        Initialize a new DaggerLogger.
        
        Args:
            component: Component name for the logger
            workflow_id: Optional workflow ID for context
        """
        self.logger = structlog.get_logger(f"dagger.{component}")
        self.workflow_id = workflow_id
    
    def set_workflow_id(self, workflow_id: str):
        """
        Set the workflow ID for context.
        
        Args:
            workflow_id: Workflow ID
        """
        self.workflow_id = workflow_id
    
    def _get_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the context for logging.
        
        Args:
            extra: Additional context parameters
            
        Returns:
            Dictionary with context parameters
        """
        context = {}
        
        if self.workflow_id:
            context["workflow_id"] = self.workflow_id
            
        if extra:
            context.update(extra)
            
        return context
    
    def debug(self, message: str, **kwargs):
        """
        Log a debug message.
        
        Args:
            message: Message to log
            **kwargs: Additional context parameters
        """
        self.logger.debug(message, **self._get_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """
        Log an info message.
        
        Args:
            message: Message to log
            **kwargs: Additional context parameters
        """
        self.logger.info(message, **self._get_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """
        Log a warning message.
        
        Args:
            message: Message to log
            **kwargs: Additional context parameters
        """
        self.logger.warning(message, **self._get_context(kwargs))
    
    def error(self, message: str, **kwargs):
        """
        Log an error message.
        
        Args:
            message: Message to log
            **kwargs: Additional context parameters
        """
        self.logger.error(message, **self._get_context(kwargs))
    
    def critical(self, message: str, **kwargs):
        """
        Log a critical message.
        
        Args:
            message: Message to log
            **kwargs: Additional context parameters
        """
        self.logger.critical(message, **self._get_context(kwargs))
    
    def exception(self, message: str, exc_info=True, **kwargs):
        """
        Log an exception message.
        
        Args:
            message: Message to log
            exc_info: Exception info flag
            **kwargs: Additional context parameters
        """
        self.logger.exception(message, exc_info=exc_info, **self._get_context(kwargs))


class DaggerLogContext:
    """Context manager for Dagger logging."""
    
    def __init__(self, logger: DaggerLogger, context: Dict[str, Any], message: Optional[str] = None):
        """
        Initialize a new DaggerLogContext.
        
        Args:
            logger: Logger to use
            context: Context parameters
            message: Optional message to log on enter
        """
        self.logger = logger
        self.context = context
        self.message = message
        self.start_time = None
    
    def __enter__(self):
        """Enter the context manager."""
        self.start_time = datetime.now()
        
        if self.message:
            self.logger.info(f"Started: {self.message}", **self.context)
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type:
            # Log exception
            self.logger.exception(
                f"Failed: {self.message}" if self.message else "Operation failed",
                duration=duration,
                **self.context
            )
        else:
            # Log success
            self.logger.info(
                f"Completed: {self.message}" if self.message else "Operation completed",
                duration=duration,
                **self.context
            )
        
        return False  # Don't suppress exceptions