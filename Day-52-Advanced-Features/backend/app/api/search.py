# backend/app/api/search.py
# Full-text search + filtering + sorting

from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, or_, and_, func, text
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.task import Task
from app.schemas.task import TaskOut

router = APIRouter(prefix="/search", tags=["search"])

SORT_FIELDS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "priority": Task.priority,
    "title": Task.title,
    "due_date": Task.due_date
}

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


@router.get("", summary="Search tasks with full-text, filters, and sorting")
async def search_tasks(
    current_user: CurrentUser,
    db: DB,
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|priority|title|due_date)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    overdue_only: bool = Query(False)
) -> dict:
    """
    Search tasks with:
    - Full-text search on title + description
    - Filter by status, priority, overdue
    - Sort by any field (asc or desc)
    - Pagination
    """
    from datetime import datetime, timezone
    import math

    filters = [Task.owner_id == current_user.id]

    # Full-text search using ILIKE (works without pg extension)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        filters.append(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)
    if overdue_only:
        now = datetime.now(timezone.utc)
        filters.append(
            and_(Task.due_date.isnot(None), Task.due_date < now, Task.status != "done")
        )

    # Count total
    count_result = await db.execute(
        select(func.count(Task.id)).where(and_(*filters))
    )
    total = count_result.scalar_one()

    # Sort
    sort_col = SORT_FIELDS.get(sort_by, Task.created_at)
    sort_expr = sort_col.asc() if sort_dir == "asc" else sort_col.desc()

    # Fetch
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Task)
        .where(and_(*filters))
        .order_by(sort_expr)
        .offset(offset)
        .limit(per_page)
    )
    tasks = list(result.scalars().all())

    return {
        "tasks": [TaskOut.model_validate(t) for t in tasks],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 0,
        "query": q,
        "filters": {
            "status": status,
            "priority": priority,
            "overdue_only": overdue_only
        },
        "sort": {"field": sort_by, "direction": sort_dir}
    }