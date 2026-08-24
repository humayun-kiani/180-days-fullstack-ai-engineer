# ============================================================
# app/tasks.py
# Task management with event publishing
# ============================================================

import uuid
from datetime import datetime
from typing import Optional

from app.event_bus import Event, event_bus
from app.event_store import event_store

# In-memory task database
_TASKS: dict[str, dict] = {}


async def create_task(
    title: str,
    description: str | None = None,
    priority: str | None = None,
    tags: list[str] | None = None,
    created_by: str = "anonymous"
) -> dict:
    """
    Create a task and publish task.created event.

    The actual notification, AI classification, and audit
    all happen asynchronously via the event bus.
    """
    task_id = f"task-{str(uuid.uuid4())[:8]}"

    task = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "priority": priority or "medium",
        "status": "pending",
        "tags": tags or [],
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    _TASKS[task_id] = task

    # Publish event — async consumers handle notifications, AI, audit
    event = Event(
        event_type="task.created",
        payload=task.copy(),
        source="task-service"
    )
    event_store.append(event)
    await event_bus.publish(event)

    return task


async def update_task(
    task_id: str,
    updates: dict,
    updated_by: str = "anonymous"
) -> dict | None:
    """Update a task and publish task.updated event."""
    task = _TASKS.get(task_id)
    if not task:
        return None

    old_task = task.copy()
    task.update(updates)
    task["updated_at"] = datetime.utcnow().isoformat()
    _TASKS[task_id] = task

    event = Event(
        event_type="task.updated",
        payload={
            "task_id": task_id,
            "updated_by": updated_by,
            "changes": {
                k: {"old": old_task.get(k), "new": v}
                for k, v in updates.items()
            },
            **task
        },
        source="task-service"
    )
    event_store.append(event)
    await event_bus.publish(event)

    return task


async def complete_task(task_id: str, completed_by: str = "anonymous") -> dict | None:
    """Mark a task complete and publish task.completed event."""
    task = _TASKS.get(task_id)
    if not task:
        return None

    task["status"] = "done"
    task["completed_at"] = datetime.utcnow().isoformat()
    task["updated_at"] = task["completed_at"]
    _TASKS[task_id] = task

    event = Event(
        event_type="task.completed",
        payload={
            "task_id": task_id,
            "title": task["title"],
            "priority": task["priority"],
            "completed_by": completed_by,
            "completed_at": task["completed_at"]
        },
        source="task-service"
    )
    event_store.append(event)
    await event_bus.publish(event)

    return task


async def delete_task(task_id: str, deleted_by: str = "admin") -> bool:
    """Delete a task and publish task.deleted event."""
    task = _TASKS.pop(task_id, None)
    if not task:
        return False

    event = Event(
        event_type="task.deleted",
        payload={"task_id": task_id, "title": task["title"],
                 "deleted_by": deleted_by},
        source="task-service"
    )
    event_store.append(event)
    await event_bus.publish(event)

    return True


def get_task(task_id: str) -> dict | None:
    return _TASKS.get(task_id)


def list_tasks(status: str = "all", priority: str = "all") -> list[dict]:
    tasks = list(_TASKS.values())
    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]
    if priority != "all":
        tasks = [t for t in tasks if t["priority"] == priority]
    return tasks