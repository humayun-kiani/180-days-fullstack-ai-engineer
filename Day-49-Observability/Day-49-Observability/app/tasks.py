# app/tasks.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    tags: list[str] = Field(default=[])


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None


class Task(BaseModel):
    task_id: str
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    tags: list[str]
    created_at: str
    updated_at: str


_TASKS: dict[str, dict] = {}


def create_task(data: TaskCreate) -> Task:
    task_id = f"task-{str(uuid.uuid4())[:8]}"
    now = datetime.utcnow().isoformat()
    task = {
        "task_id": task_id, "title": data.title,
        "description": data.description, "priority": data.priority,
        "status": Status.PENDING, "tags": data.tags,
        "created_at": now, "updated_at": now
    }
    _TASKS[task_id] = task
    return Task(**task)


def get_task(task_id: str) -> Optional[Task]:
    t = _TASKS.get(task_id)
    return Task(**t) if t else None


def list_tasks(status: str = None, priority: str = None) -> list[Task]:
    tasks = list(_TASKS.values())
    if status: tasks = [t for t in tasks if t["status"] == status]
    if priority: tasks = [t for t in tasks if t["priority"] == priority]
    return [Task(**t) for t in tasks]


def update_task(task_id: str, data: TaskUpdate) -> Optional[Task]:
    t = _TASKS.get(task_id)
    if not t: return None
    updates = data.model_dump(exclude_none=True)
    t.update(updates)
    t["updated_at"] = datetime.utcnow().isoformat()
    return Task(**t)


def delete_task(task_id: str) -> bool:
    return _TASKS.pop(task_id, None) is not None


def task_count() -> int:
    return len(_TASKS)


def clear_all(): _TASKS.clear()