"""Health check endpoints for HippoGrid."""
from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel
from backend.db.session import check_db_connection

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    project: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> Dict[str, str]:
    """Primary health check endpoint."""
    return {
        "status": "ok",
        "project": "HippoGrid",
    }


@router.get("/health/db")
def get_db_health() -> Dict[str, Any]:
    """Diagnostic health check verifying PostgreSQL database connectivity."""
    db_status = check_db_connection()
    return {
        "project": "HippoGrid",
        "database": db_status,
    }
