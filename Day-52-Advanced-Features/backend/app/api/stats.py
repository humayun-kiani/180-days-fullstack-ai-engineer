# backend/app/api/stats.py
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from sqlalchemy import select, func, and_, case

from app.core.deps import DB, CurrentUser
from app.models.task import Task

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", summary="Task statistics dashboard")
async def get_stats(current_user: CurrentUser, db: DB) -> dict:
    """
    Return comprehensive task statistics for the dashboard.

    Computed in a single SQL query using aggregations.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Single query with multiple aggregations
    result = await db.execute(
        select(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
            func.sum(case((Task.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((Task.status == "in_progress", 1), else_=0)).label("in_progress"),
            func.sum(case((Task.priority == "urgent", 1), else_=0)).label("urgent"),
            func.sum(case((Task.priority == "high", 1), else_=0)).label("high"),
            func.sum(case((Task.priority == "medium", 1), else_=0)).label("medium"),
            func.sum(case((Task.priority == "low", 1), else_=0)).label("low"),
            # Overdue: has due_date, due_date < now, not done
            func.sum(case(
                (and_(Task.due_date.isnot(None),
                      Task.due_date < now,
                      Task.status != "done"), 1),
                else_=0
            )).label("overdue"),
            # Created this week
            func.sum(case(
                (Task.created_at >= week_ago, 1), else_=0
            )).label("created_this_week"),
            # Completed this week
            func.sum(case(
                (and_(Task.status == "done", Task.updated_at >= week_ago), 1),
                else_=0
            )).label("completed_this_week"),
        ).where(Task.owner_id == current_user.id)
    )
    row = result.one()

    total = row.total or 0
    done = row.done or 0
    completion_rate = round(done / total * 100, 1) if total > 0 else 0

    return {
        "overview": {
            "total": total,
            "done": done,
            "pending": row.pending or 0,
            "in_progress": row.in_progress or 0,
            "completion_rate_pct": completion_rate,
            "overdue": row.overdue or 0
        },
        "by_priority": {
            "urgent": row.urgent or 0,
            "high": row.high or 0,
            "medium": row.medium or 0,
            "low": row.low or 0
        },
        "this_week": {
            "created": row.created_this_week or 0,
            "completed": row.completed_this_week or 0,
            "velocity": f"{row.completed_this_week or 0} tasks/week"
        },
        "health": {
            "score": _health_score(row, total),
            "issues": _identify_issues(row, total)
        }
    }


def _health_score(row, total: int) -> str:
    """Simple health score based on completion rate and overdue count."""
    if total == 0:
        return "no_data"
    completion_pct = (row.done or 0) / total * 100
    overdue = row.overdue or 0
    urgent = row.urgent or 0

    if overdue > 5 or urgent > 10:
        return "critical"
    if overdue > 2 or completion_pct < 30:
        return "warning"
    if completion_pct >= 70:
        return "healthy"
    return "ok"


def _identify_issues(row, total: int) -> list[str]:
    issues = []
    if (row.overdue or 0) > 0:
        issues.append(f"{row.overdue} overdue task(s) need attention")
    if (row.urgent or 0) > 5:
        issues.append(f"High urgent task count ({row.urgent}) — triage needed")
    if total > 0 and (row.done or 0) / total < 0.2:
        issues.append("Low completion rate — review backlog prioritization")
    if (row.pending or 0) > 50:
        issues.append("Large backlog — consider archiving old tasks")
    return issues