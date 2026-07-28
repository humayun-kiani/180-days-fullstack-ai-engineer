# ============================================================
# routers/stats.py
# Statistics and health endpoints
# ============================================================

from fastapi import APIRouter
from src.models import StatsResponse, MessageResponse
from src.dependencies import CurrentUser, Database

router = APIRouter(tags=["System"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get statistics",
    description="Returns comprehensive statistics about tasks and projects."
)
def get_stats(
    current_user: CurrentUser = None,
    db: Database = None
):
    return db.get_stats()


@router.get(
    "/health",
    response_model=dict,
    summary="Health check",
    description="Returns API health status. Used by load balancers and monitoring."
)
def health_check():
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "day": "Day 20 — 180-Day Full Stack AI Engineer Roadmap"
    }