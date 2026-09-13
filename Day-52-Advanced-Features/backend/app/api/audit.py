# backend/app/api/audit.py
import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.audit import TaskAuditLog
from app.models.task import Task
from app.services.audit_service import get_task_audit_log, get_user_audit_log

router = APIRouter(tags=["audit"])


@router.get(
    "/tasks/{task_id}/audit",
    summary="Get audit log for a specific task"
)
async def task_audit(task_id: uuid.UUID, current_user: CurrentUser, db: DB) -> dict:
    """View the complete change history for a task."""
    # Verify task ownership
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    logs = await get_task_audit_log(db, task_id)

    return {
        "task_id": str(task_id),
        "task_title": task.title,
        "total_changes": len(logs),
        "history": [
            {
                "id": str(log.id),
                "action": log.action,
                "user": log.user_name,
                "changed_fields": log.changed_fields,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "timestamp": log.created_at.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/audit/recent", summary="Recent changes by current user")
async def recent_audit(current_user: CurrentUser, db: DB, limit: int = 50) -> dict:
    """View recent changes made by the current user."""
    logs = await get_user_audit_log(db, current_user.id, limit=limit)
    return {
        "total": len(logs),
        "history": [
            {
                "id": str(log.id),
                "task_id": str(log.task_id),
                "action": log.action,
                "changed_fields": list(log.changed_fields.keys()) if log.changed_fields else [],
                "timestamp": log.created_at.isoformat()
            }
            for log in logs
        ]
    }