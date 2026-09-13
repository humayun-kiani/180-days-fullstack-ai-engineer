# backend/app/api/export.py
import csv
import json
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_

from app.core.deps import DB, CurrentUser
from app.models.task import Task

router = APIRouter(prefix="/tasks", tags=["export"])

EXPORT_FIELDS = [
    "id", "title", "description", "status", "priority",
    "ai_summary", "due_date", "created_at", "updated_at"
]


async def _get_tasks_for_export(
    db, owner_id, status: Optional[str], priority: Optional[str]
) -> list[Task]:
    filters = [Task.owner_id == owner_id]
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)

    result = await db.execute(
        select(Task)
        .where(and_(*filters))
        .order_by(Task.created_at.desc())
        .limit(5000)  # safety limit
    )
    return list(result.scalars().all())


@router.get("/export/csv", summary="Export tasks as CSV")
async def export_csv(
    current_user: CurrentUser,
    db: DB,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Download all tasks as a CSV file."""
    tasks = await _get_tasks_for_export(db, current_user.id, status, priority)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_FIELDS)
    writer.writeheader()

    for task in tasks:
        writer.writerow({
            "id": str(task.id),
            "title": task.title,
            "description": task.description or "",
            "status": task.status,
            "priority": task.priority,
            "ai_summary": task.ai_summary or "",
            "due_date": task.due_date.isoformat() if task.due_date else "",
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        })

    output.seek(0)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"taskmind-export-{ts}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/json", summary="Export tasks as JSON")
async def export_json(
    current_user: CurrentUser,
    db: DB,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Download all tasks as a JSON file."""
    tasks = await _get_tasks_for_export(db, current_user.id, status, priority)

    data = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "exported_by": current_user.email,
        "total_tasks": len(tasks),
        "filters": {"status": status, "priority": priority},
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "ai_summary": t.ai_summary,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat()
            }
            for t in tasks
        ]
    }

    content = json.dumps(data, indent=2)
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"taskmind-export-{ts}.json"

    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )