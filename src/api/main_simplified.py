"""
Simplified version of the API server that doesn't require the pydagger package.
"""

import sys
import os

# Add mock_modules to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mock_modules'))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

# Import routes (excluding dagger_routes)
from src.api.routes.project_routes import router as project_router
from src.api.routes.task_routes import router as task_router
from src.api.routes.dashboard_routes import router as dashboard_router
from src.api.routes.monitoring_routes import router as monitoring_router

# Import authentication
from src.orchestrator.auth import get_current_user

# Create FastAPI app
app = FastAPI(
    title="AI-Orchestration-Platform API",
    description="API for the AI-Orchestration-Platform (Simplified Version)",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI-Orchestration-Platform API (Simplified Version)",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "running",
            "orchestrator": "running",
            "dagger": "disabled"  # Dagger is disabled in this simplified version
        }
    }

# Protected endpoint example
@app.get("/api/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

# Include routers
app.include_router(project_router)
app.include_router(task_router)
app.include_router(dashboard_router)
app.include_router(monitoring_router)
# Dagger router is excluded in this simplified version

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.api.main_simplified:app", host="0.0.0.0", port=port, reload=True)
