"""
Validation middleware for API endpoints.

This module provides validation middleware for API endpoints using Pydantic.
"""

from typing import Callable, Dict, Type, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError
import json
import logging

logger = logging.getLogger(__name__)


class ValidationMiddleware:
    """Middleware for validating request and response data."""
    
    def __init__(
        self,
        request_model: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None
    ):
        """
        Initialize the validation middleware.
        
        Args:
            request_model: Pydantic model to validate request data against
            response_model: Pydantic model to validate response data against
        """
        self.request_model = request_model
        self.response_model = response_model
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Validate request and response data.
        
        Args:
            request: FastAPI request
            call_next: Next middleware in the chain
            
        Returns:
            Response from the next middleware
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate request data if a request model is specified
        if self.request_model and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read request body
                body = await request.body()
                if body:
                    # Parse JSON body
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=400, detail="Invalid JSON body")
                    
                    # Validate against request model
                    try:
                        self.request_model(**data)
                    except ValidationError as e:
                        errors = e.errors()
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "message": "Validation failed",
                                "errors": errors
                            }
                        )
                    
                    # Update request state with validated data
                    request.state.validated_data = data
            except Exception as e:
                logger.error(f"Request validation error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        # Process the request
        response = await call_next(request)
        
        # Validate response data if a response model is specified
        if self.response_model and response.status_code < 400:
            try:
                # Read response body
                body = response.body
                if body:
                    # Parse JSON body
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON response")
                        return Response(
                            content=json.dumps({
                                "message": "Internal server error",
                                "code": "invalid_response"
                            }),
                            status_code=500,
                            media_type="application/json"
                        )
                    
                    # Validate against response model
                    try:
                        self.response_model(**data)
                    except ValidationError as e:
                        logger.error(f"Response validation error: {e}")
                        return Response(
                            content=json.dumps({
                                "message": "Internal server error",
                                "code": "invalid_response"
                            }),
                            status_code=500,
                            media_type="application/json"
                        )
            except Exception as e:
                logger.error(f"Response validation error: {e}")
                return Response(
                    content=json.dumps({
                        "message": "Internal server error",
                        "code": "validation_error"
                    }),
                    status_code=500,
                    media_type="application/json"
                )
        
        return response


class ValidatedAPIRoute(APIRoute):
    """API route with request and response validation."""
    
    def __init__(
        self,
        *args,
        request_model: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
        **kwargs
    ):
        """
        Initialize the validated API route.
        
        Args:
            *args: Arguments to pass to APIRoute
            request_model: Pydantic model to validate request data against
            response_model: Pydantic model to validate response data against
            **kwargs: Keyword arguments to pass to APIRoute
        """
        super().__init__(*args, **kwargs)
        self.request_model = request_model
        self.response_model = response_model
        self.middleware = [
            ValidationMiddleware(request_model, response_model)
        ]
    
    async def handle(self, request: Request) -> Response:
        """
        Handle the request with validation middleware.
        
        Args:
            request: FastAPI request
            
        Returns:
            Response from the route handler
        """
        # Apply middleware
        handler = super().handle
        for middleware in reversed(self.middleware):
            handler = lambda req, middleware=middleware, handler=handler: middleware(req, handler)
        
        return await handler(request)