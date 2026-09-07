# backend/app/api/tasks.py
import math
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DB, CurrentUser
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskListResponse
from app.services import task_service
from app.services.cache_service import cache_get, cache_set, cache_delete_pattern

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: CurrentUser,
    db: DB,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List tasks with optional filters and pagination."""
    cache_key = f"tasks:{current_user.id}:{status}:{priority}:{page}:{per_page}"
    cached = await cache_get(cache_key)
    if cached:
        return TaskListResponse(**cached)

    tasks, total = await task_service.list_tasks(
        db, current_user.id,
        status=status, priority=priority,
        page=page, per_page=per_page
    )

    response = TaskListResponse(
        tasks=[TaskOut.model_validate(t) for t in tasks],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0
    )

    await cache_set(cache_key, response.model_dump(), ttl=30)
    return response


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(body: TaskCreate, current_user: CurrentUser, db: DB):
    task = await task_service.create_task(db, body, current_user.id)
    # Invalidate list cache
    await cache_delete_pattern(f"tasks:{current_user.id}:*")
    return TaskOut.model_validate(task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, current_user: CurrentUser, db: DB):
    task = await task_service.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(404, f"Task not found")
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: uuid.UUID, body: TaskUpdate, current_user: CurrentUser, db: DB):
    task = await task_service.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(404, "Task not found")
    updated = await task_service.update_task(db, task, body)
    await cache_delete_pattern(f"tasks:{current_user.id}:*")
    return TaskOut.model_validate(updated)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: uuid.UUID, current_user: CurrentUser, db: DB):
    task = await task_service.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(404, "Task not found")
    await task_service.delete_task(db, task)
    await cache_delete_pattern(f"tasks:{current_user.id}:*")