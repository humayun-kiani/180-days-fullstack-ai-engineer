# backend/app/services/audit_service.py
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit import TaskAuditLog
from app.models.task import Task


async def log_change(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    user_name: str,
    action: str,
    old_values: dict,
    new_values: dict
) -> TaskAuditLog:
    """
    Append an audit log entry for a task change.

    Immutable: we only ever INSERT here, never UPDATE or DELETE.
    """
    # Compute what actually changed
    changed_fields = {
        k: {"from": old_values.get(k), "to": new_values.get(k)}
        for k in set(list(old_values.keys()) + list(new_values.keys()))
        if old_values.get(k) != new_values.get(k)
    }

    entry = TaskAuditLog(
        task_id=task_id,
        user_id=user_id,
        user_name=user_name,
        action=action,
        changed_fields=changed_fields,
        old_values=old_values,
        new_values=new_values
    )
    db.add(entry)
    await db.flush()    # flush without committing (caller handles commit)
    return entry


async def get_task_audit_log(
    db: AsyncSession,
    task_id: uuid.UUID,
    limit: int = 50
) -> list[TaskAuditLog]:
    result = await db.execute(
        select(TaskAuditLog)
        .where(TaskAuditLog.task_id == task_id)
        .order_by(TaskAuditLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 100
) -> list[TaskAuditLog]:
    result = await db.execute(
        select(TaskAuditLog)
        .where(TaskAuditLog.user_id == user_id)
        .order_by(TaskAuditLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())