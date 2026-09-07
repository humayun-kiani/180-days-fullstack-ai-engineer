# backend/app/api/ai.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.deps import DB, CurrentUser
from app.schemas.ai import (
    AnalyzeRequest, AnalyzeResponse,
    ExpandRequest, ExpandResponse,
    BreakdownRequest, BreakdownResponse,
    WeeklySummaryResponse
)
from app.services import ai_service, task_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_task(body: AnalyzeRequest, current_user: CurrentUser):
    """Analyze a task title/description and get AI suggestions."""
    return await ai_service.analyze_task(body.title, body.description)


@router.post("/expand", response_model=ExpandResponse)
async def expand_task(body: ExpandRequest, current_user: CurrentUser):
    """Expand a brief task title into a full description."""
    return await ai_service.expand_task(body.title)


@router.post("/breakdown", response_model=BreakdownResponse)
async def breakdown_task(body: BreakdownRequest, current_user: CurrentUser):
    """Break a task into smaller subtasks with estimates."""
    return await ai_service.breakdown_task(body.title, body.description)


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def weekly_summary(current_user: CurrentUser, db: DB):
    """Generate an AI-powered weekly summary of all tasks."""
    tasks, _ = await task_service.list_tasks(db, current_user.id, per_page=50)
    task_dicts = [
        {"title": t.title, "status": t.status, "priority": t.priority}
        for t in tasks
    ]
    return await ai_service.weekly_summary(task_dicts)