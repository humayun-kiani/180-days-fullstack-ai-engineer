# ============================================================
# app/api/v1/stats.py
# Statistics and system endpoints
# ============================================================

from datetime import datetime
from fastapi import APIRouter
from app.crud import task_crud, project_crud
from app.api.deps import DB, CurrentUser

router = APIRouter(tags=["System"])


@router.get("/stats")
def get_stats(db: DB = None, current_user: CurrentUser = None):
    """Get comprehensive statistics."""
    task_stats = task_crud.get_stats(db)
    _, total_projects = project_crud.get_multi_active(db, limit=1)

    return {
        **task_stats,
        "total_projects": total_projects,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "database": "PostgreSQL",
        "day": "Day 21 — FastAPI + SQLAlchemy + PostgreSQL"
    }