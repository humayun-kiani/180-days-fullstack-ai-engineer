# ============================================================
# app/api/v1/tasks.py
# Task endpoints — full CRUD with filtering
# ============================================================

import math
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus, Priority
from app.schemas.common import PaginatedResponse
from app.crud import task_crud, project_crud
from app.api.deps import DB, CurrentUser, AdminUser, PageParams

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def log_task_event(task_id: int, title: str, event: str, user: str):
    """Background task for audit logging."""
    print(f"  📋 [Audit] {datetime.utcnow().strftime('%H:%M:%S')} | "
          f"User '{user}' {event} task #{task_id}: '{title[:40]}'")


@router.get("/", response_model=PaginatedResponse[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[Priority] = Query(None),
    project_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, min_length=2),
    tag: Optional[str] = Query(None),
    overdue: bool = Query(False, description="Show only overdue tasks"),
    sort_by: str = Query(
        "created_at",
        regex="^(created_at|updated_at|due_date|title|priority|status)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    pagination: PageParams = None,
    db: DB = None,
    current_user: CurrentUser = None
):
    items, total = task_crud.get_multi_filtered(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        project_id=project_id,
        owner_id=owner_id,
        search=search,
        overdue_only=overdue,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order
    )
    pages = math.ceil(total / pagination.per_page) if total > 0 else 1
    return PaginatedResponse(
        items=items, total=total,
        page=pagination.page, per_page=pagination.per_page,
        pages=pages, has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    db: DB = None,
    current_user: CurrentUser = None
):
    # Validate project exists if provided
    if task_in.project_id:
        if not project_crud.exists(db, task_in.project_id):
            raise HTTPException(404, f"Project {task_in.project_id} not found")

    # Set owner to current user if not specified
    task_data = task_in.model_dump()
    if not task_data.get("owner_id") and current_user.get("id"):
        task_data["owner_id"] = current_user["id"]

    # Create the task
    from app.db.models.task import Task
    task = Task(**task_data)
    db.add(task)
    db.flush()
    db.refresh(task)

    # Log in background
    background_tasks.add_task(
        log_task_event,
        task.id, task.title, "created", current_user.get("username", "demo")
    )

    return task


@router.get("/overdue", response_model=list[TaskResponse])
def get_overdue_tasks(
    db: DB = None,
    current_user: CurrentUser = None
):
    """Get all overdue tasks sorted by most overdue first."""
    return task_crud.get_overdue(db)


@router.get("/upcoming", response_model=list[TaskResponse])
def get_upcoming_tasks(
    days: int = Query(7, ge=1, le=30, description="Days ahead to look"),
    db: DB = None,
    current_user: CurrentUser = None
):
    """Get tasks due in the next N days."""
    return task_crud.get_upcoming(db, days=days)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: DB = None,
    current_user: CurrentUser = None
):
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: DB = None,
    current_user: CurrentUser = None
):
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")

    # Validate project if being changed
    if task_in.project_id and not project_crud.exists(db, task_in.project_id):
        raise HTTPException(404, f"Project {task_in.project_id} not found")

    updated = task_crud.update(db, task, task_in)

    background_tasks.add_task(
        log_task_event,
        task.id, task.title, "updated", current_user.get("username", "demo")
    )

    return updated


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    actual_hours: Optional[float] = Query(None, ge=0),
    db: DB = None,
    current_user: CurrentUser = None
):
    """Mark a task as completed."""
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    if task.status == "done":
        raise HTTPException(409, "Task is already completed")

    completed = task_crud.complete_task(db, task, actual_hours)

    background_tasks.add_task(
        log_task_event,
        task.id, task.title, "completed ✅",
        current_user.get("username", "demo")
    )

    return completed


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    hard: bool = Query(False, description="Hard delete (admin only)"),
    db: DB = None,
    current_user: CurrentUser = None
):
    """Soft delete a task (or hard delete with ?hard=true for admins)."""
    task = task_crud.get_active(db, task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")

    if hard:
        if current_user.get("role") != "admin":
            raise HTTPException(403, "Hard delete requires admin privileges")
        task_crud.delete(db, task_id)
    else:
        task_crud.soft_delete(db, task)

    background_tasks.add_task(
        log_task_event,
        task_id, task.title,
        f"{'hard' if hard else 'soft'} deleted",
        current_user.get("username", "demo")
    )

    return None


@router.post("/bulk/complete", response_model=dict)
def bulk_complete_tasks(
    task_ids: list[int],
    db: DB = None,
    current_user: CurrentUser = None
):
    """Complete multiple tasks at once."""
    if not task_ids:
        raise HTTPException(400, "task_ids list cannot be empty")
    if len(task_ids) > 50:
        raise HTTPException(400, "Cannot bulk update more than 50 tasks at once")

    count = task_crud.bulk_update_status(db, task_ids, "done")
    return {"updated": count, "message": f"Marked {count} task(s) as done"}