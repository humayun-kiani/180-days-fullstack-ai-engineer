# ============================================================
# routers/tasks.py
# Task CRUD endpoints
# ============================================================

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
import math

from src.models import (
    TaskCreate, TaskUpdate, TaskResponse,
    PaginatedTasks, MessageResponse, SortOrder, TaskStatus, Priority
)
from src.dependencies import CurrentUser, Database, Pagination
from src.exceptions import TaskNotFoundError

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    responses={
        404: {"description": "Task not found"},
        422: {"description": "Validation error"}
    }
)


def simulate_notification(task_id: int, task_title: str, event: str):
    """Simulate sending a notification (background task)."""
    print(f"\n  📬 [Notification] Task '{task_title}' (ID: {task_id}) — {event}")


@router.get(
    "/",
    response_model=PaginatedTasks,
    summary="List all tasks",
    description="Get a paginated list of tasks with optional filters."
)
def list_tasks(
    # Filters
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    search: Optional[str] = Query(None, min_length=2, description="Search title/description"),
    overdue: Optional[bool] = Query(None, description="Filter overdue tasks"),
    # Sorting
    sort_by: str = Query(
        default="created_at",
        description="Sort field",
        regex="^(created_at|updated_at|due_date|priority|status|title)$"
    ),
    sort_order: SortOrder = Query(default=SortOrder.DESC, description="Sort direction"),
    # Pagination (injected)
    pagination: Pagination = None,
    # Auth and DB (injected)
    current_user: CurrentUser = None,
    db: Database = None
):
    items, total = db.get_tasks(
        status=status.value if status else None,
        priority=priority.value if priority else None,
        project_id=project_id,
        tag=tag,
        search=search,
        overdue=overdue,
        sort_by=sort_by,
        sort_order=sort_order.value,
        page=pagination.page,
        per_page=pagination.per_page
    )

    pages = math.ceil(total / pagination.per_page) if total > 0 else 1

    return PaginatedTasks(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pages,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=201,
    summary="Create a task",
    description="Create a new task. Returns the created task with its assigned ID."
)
def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = None,
    db: Database = None
):
    task = db.create_task(task_data.model_dump())

    # Fire notification in background
    background_tasks.add_task(
        simulate_notification,
        task["id"],
        task["title"],
        "created"
    )

    return task


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task",
    description="Get a specific task by its ID."
)
def get_task(
    task_id: int,
    current_user: CurrentUser = None,
    db: Database = None
):
    task = db.get_task(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Update one or more fields of a task."
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = None,
    db: Database = None
):
    # Verify task exists
    existing = db.get_task(task_id)
    if not existing:
        raise TaskNotFoundError(task_id)

    # Apply update
    updated = db.update_task(
        task_id,
        {k: v for k, v in task_data.model_dump().items() if v is not None}
    )

    # Notify if status changed to done
    if (task_data.status == TaskStatus.DONE and
            existing["status"] != "done"):
        background_tasks.add_task(
            simulate_notification,
            task_id,
            updated["title"],
            "completed! 🎉"
        )

    return updated


@router.delete(
    "/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Permanently delete a task by ID."
)
def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = None,
    db: Database = None
):
    task = db.get_task(task_id)
    if not task:
        raise TaskNotFoundError(task_id)

    db.delete_task(task_id)

    background_tasks.add_task(
        simulate_notification,
        task_id,
        task["title"],
        "deleted"
    )

    return None    # 204 No Content


@router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark task as done",
    description="Shortcut to mark a task as completed."
)
def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    actual_hours: Optional[float] = Query(None, ge=0, description="Actual hours spent"),
    current_user: CurrentUser = None,
    db: Database = None
):
    task = db.get_task(task_id)
    if not task:
        raise TaskNotFoundError(task_id)

    if task["status"] == "done":
        raise HTTPException(
            status_code=409,
            detail="Task is already marked as done"
        )

    update_data = {"status": "done"}
    if actual_hours is not None:
        update_data["actual_hours"] = actual_hours

    updated = db.update_task(task_id, update_data)

    background_tasks.add_task(
        simulate_notification,
        task_id,
        updated["title"],
        "completed! 🎉"
    )

    return updated


@router.get(
    "/overdue/list",
    response_model=list[TaskResponse],
    summary="Get overdue tasks",
    description="Get all tasks that are past their due date and not yet completed."
)
def get_overdue_tasks(
    current_user: CurrentUser = None,
    db: Database = None
):
    items, _ = db.get_tasks(overdue=True, per_page=100)
    return items