from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Optional

# Import routes
from src.api.routes.project_routes import router as project_router
from src.api.routes.task_routes import router as task_router
from src.api.routes.dashboard_routes import router as dashboard_router
from src.api.routes.dagger_routes import dagger_router
from src.api.routes.monitoring_routes import router as monitoring_router
from src.api.routes.progress_routes import router as progress_router
from src.api.routes.auth_routes import router as auth_router

# Import authentication
from src.security.rbac import get_current_active_user

# Create FastAPI app
app = FastAPI(
    title="AI-Orchestration-Platform API",
    description="API for the AI-Orchestration-Platform",
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
        "message": "Welcome to the AI-Orchestration-Platform API",
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
            "dagger": "running"
        }
    }

# Protected endpoint example
@app.get("/api/me")
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    return current_user

# Include routers
app.include_router(project_router)
app.include_router(task_router)
app.include_router(dashboard_router)
app.include_router(dagger_router)
app.include_router(monitoring_router)
app.include_router(progress_router)
app.include_router(auth_router)

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)
