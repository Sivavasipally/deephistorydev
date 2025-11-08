"""FastAPI backend for Git History Analysis Dashboard."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, date
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from models import (
    get_engine, get_session,
    Repository, Commit, PullRequest, PRApproval, StaffDetails, AuthorStaffMapping
)
from backend.routers import (
    overview, commits, pull_requests, authors, staff,
    tables, sql_executor, mappings, dashboard360
)

# Initialize FastAPI app
app = FastAPI(
    title="Git History Analysis API",
    description="Backend API for Git repository analysis and visualization",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(overview.router, prefix="/api/overview", tags=["Overview"])
app.include_router(commits.router, prefix="/api/commits", tags=["Commits"])
app.include_router(pull_requests.router, prefix="/api/pull-requests", tags=["Pull Requests"])
app.include_router(authors.router, prefix="/api/authors", tags=["Authors"])
app.include_router(staff.router, prefix="/api/staff", tags=["Staff"])
app.include_router(tables.router, prefix="/api/tables", tags=["Tables"])
app.include_router(sql_executor.router, prefix="/api/sql", tags=["SQL Executor"])
app.include_router(mappings.router, prefix="/api/mappings", tags=["Author-Staff Mapping"])
app.include_router(dashboard360.router, prefix="/api/dashboard360", tags=["360 Dashboards"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Git History Analysis API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/api/docs"
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        config = Config()
        db_config = config.get_db_config()
        engine = get_engine(db_config)
        session = get_session(engine)

        # Test database connection
        session.execute("SELECT 1")
        session.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="localhost", port=8000, reload=True)
