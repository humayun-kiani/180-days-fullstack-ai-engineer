# ============================================================
# app/main.py
# FastAPI application with Celery task integration
# ============================================================

import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from celery.result import AsyncResult

from worker.celery_app import celery_app
from worker.tasks.emails import (
    send_welcome_email,
    send_task_completion_notification,
    send_daily_digest_to_all_users
)
from worker.tasks.reports import generate_task_report, generate_weekly_summary
from worker.tasks.notifications import (
    check_and_notify_overdue,
    send_task_assigned_notification
)
from worker.tasks.maintenance import health_check, run_diagnostics
from app.models import USERS, TASKS, create_task


# ─── Schemas ────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: str = Field(default="medium")
    owner_id: int = Field(default=1)
    assigned_to_user_id: Optional[int] = None


class CompleteTaskRequest(BaseModel):
    completed_by_username: str
    actual_hours: Optional[float] = None


class ReportRequest(BaseModel):
    report_type: str = Field(default="summary")
    user_id: int = Field(default=1)
    date_range_days: int = Field(default=30, ge=1, le=365)


# ─── FastAPI App ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  Task Manager Background Worker Demo")
    print("  Day 25 — Celery: Task Queues & Scheduled Jobs")
    print()
    print("  FastAPI: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("  Flower: http://localhost:5555")
    print("=" * 60 + "\n")

    print("  To start Celery worker:")
    print("  celery -A worker.celery_app worker --loglevel=info -Q emails,reports,notifications,maintenance")
    print()
    print("  To start Flower monitor:")
    print("  celery -A worker.celery_app flower --port=5555")
    print()

    yield


app = FastAPI(
    title="Task Manager — Background Worker Demo",
    description="""
## Background Task Demo with Celery + Redis

This API demonstrates offloading slow work to Celery workers.

### What happens when you call these endpoints:
1. FastAPI creates a task and sends it to **Redis** (the broker)
2. API **returns immediately** with a `task_id`
3. A **Celery worker** picks up the task and processes it asynchronously
4. You can **poll** `GET /tasks/{task_id}/status` to check progress
5. **Flower** at http://localhost:5555 shows all task activity

### Setup Required
```bash
# Terminal 1: Start Redis
docker compose up -d

# Terminal 2: Start Celery worker
celery -A worker.celery_app worker --loglevel=info

# Terminal 3: Start Flower monitor
celery -A worker.celery_app flower --port=5555

# Terminal 4: Start FastAPI
uvicorn app.main:app --reload
```
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Task Status Endpoints ──────────────────────────────────

@app.get("/tasks/{task_id}/status")
def get_task_status(task_id: str):
    """
    Poll this endpoint to check the status of a background task.

    Returns status: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
    """
    result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }

    if result.status == "PROGRESS":
        response["progress"] = result.info

    elif result.status == "SUCCESS":
        response["result"] = result.result

    elif result.status == "FAILURE":
        response["error"] = str(result.result)
        response["traceback"] = result.traceback

    return response


# ─── User Endpoints ─────────────────────────────────────────

@app.post("/users/register")
def register_user(request: UserRegisterRequest):
    """
    Register a new user.

    Immediately returns success, then sends welcome email in background.
    The welcome email task runs in Celery — does NOT block this response.
    """
    # Simulate user creation
    new_id = max(USERS.keys()) + 1
    from app.models import User
    USERS[new_id] = User(
        id=new_id,
        username=request.username,
        email=request.email,
        full_name=request.full_name
    )

    # Queue welcome email in Celery — FIRE AND FORGET
    email_task = send_welcome_email.apply_async(
        args=[new_id, request.email, request.full_name],
        queue="emails",
        countdown=2    # small delay so user is definitely saved first
    )

    return {
        "user_id": new_id,
        "username": request.username,
        "email": request.email,
        "message": "Registration successful!",
        "background_tasks": {
            "welcome_email": {
                "task_id": email_task.id,
                "status_url": f"/tasks/{email_task.id}/status"
            }
        },
        "response_time_note": "This returned in ~5ms. Email sending in background."
    }


# ─── Task Completion with Notification ──────────────────────

@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, request: CompleteTaskRequest):
    """
    Mark a task as complete and notify owner.

    Returns immediately. Notification email runs in background.
    """
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")

    if task.status == "done":
        raise HTTPException(409, "Task already completed")

    # Update task status
    task.status = "done"

    # Queue notification if someone else completed the task
    owner = USERS.get(task.owner_id)
    notification_task = None

    if owner and owner.username != request.completed_by_username:
        notification_task = send_task_completion_notification.apply_async(
            args=[
                task_id,
                task.title,
                request.completed_by_username,
                owner.email,
                owner.full_name
            ],
            queue="emails"
        )

    response = {
        "task_id": task_id,
        "title": task.title,
        "status": "done",
        "completed_by": request.completed_by_username,
        "message": "Task marked as complete!"
    }

    if notification_task:
        response["notification"] = {
            "task_id": notification_task.id,
            "status_url": f"/tasks/{notification_task.id}/status",
            "recipient": owner.email
        }

    return response


# ─── Report Generation ──────────────────────────────────────

@app.post("/reports/generate")
def generate_report(request: ReportRequest):
    """
    Start report generation in background.

    Returns immediately with a task_id to poll for progress.
    Report generation takes ~5 seconds (simulate heavy work).
    """
    user = USERS.get(request.user_id)
    if not user:
        raise HTTPException(404, f"User {request.user_id} not found")

    task = generate_task_report.apply_async(
        args=[request.report_type, request.user_id, request.date_range_days],
        queue="reports"
    )

    return {
        "message": "Report generation started",
        "report_type": request.report_type,
        "requested_by": user.username,
        "task_id": task.id,
        "status_url": f"/tasks/{task.id}/status",
        "note": "Poll status_url every second to track progress (PENDING → PROGRESS → SUCCESS)"
    }


# ─── Trigger Scheduled Tasks Manually ───────────────────────

@app.post("/admin/trigger/{task_name}")
def trigger_admin_task(task_name: str):
    """
    Manually trigger a scheduled task for testing.

    Tasks normally run on a schedule (Beat), but you can trigger them here.
    """
    task_map = {
        "daily_digest": send_daily_digest_to_all_users,
        "overdue_check": check_and_notify_overdue,
        "weekly_report": generate_weekly_summary,
        "health_check": health_check,
        "diagnostics": run_diagnostics,
    }

    task_fn = task_map.get(task_name)
    if not task_fn:
        raise HTTPException(
            404,
            f"Unknown task. Available: {list(task_map.keys())}"
        )

    # Determine queue from task route
    queue_map = {
        "daily_digest": "emails",
        "overdue_check": "notifications",
        "weekly_report": "reports",
        "health_check": "maintenance",
        "diagnostics": "maintenance",
    }

    task = task_fn.apply_async(queue=queue_map.get(task_name, "default"))

    return {
        "triggered": task_name,
        "task_id": task.id,
        "status_url": f"/tasks/{task.id}/status",
        "note": "Check Flower at http://localhost:5555 to see it running"
    }


# ─── Worker Stats ────────────────────────────────────────────

@app.get("/admin/workers")
def get_worker_stats():
    """Get information about active Celery workers."""
    inspect = celery_app.control.inspect(timeout=3)

    try:
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}
        stats = inspect.stats() or {}

        return {
            "workers": list(active.keys()),
            "total_workers": len(active),
            "active_tasks": {
                worker: len(tasks)
                for worker, tasks in active.items()
            },
            "scheduled_tasks": {
                worker: len(tasks)
                for worker, tasks in scheduled.items()
            },
            "status": "ok" if active else "no_workers"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "note": "Make sure Celery worker is running"
        }


@app.get("/")
def root():
    return {
        "name": "Task Manager Background Worker Demo",
        "day": "Day 25 — Celery: Background Tasks & Scheduled Jobs",
        "docs": "/docs",
        "flower": "http://localhost:5555"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "celery_broker": "redis://localhost:6379/0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)