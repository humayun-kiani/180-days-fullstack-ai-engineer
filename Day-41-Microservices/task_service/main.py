# ============================================================
# task_service/main.py
# Task Service — CRUD operations, calls auth-service
# Port: 8002
# ============================================================

import os
import uuid
import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.tracing import (
    RequestTracingMiddleware, ServiceLogger, make_outgoing_headers
)
from shared.circuit_breaker import AUTH_CIRCUIT, AI_CIRCUIT

log = ServiceLogger("task-service")

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
AI_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8003")

# In-memory task store (use PostgreSQL in production)
TASKS: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"Task Service starting on port 8002")
    log.info(f"Auth service: {AUTH_URL}")
    log.info(f"AI service: {AI_URL}")
    yield
    log.info("Task Service shutting down")


app = FastAPI(
    title="Task Service",
    description="Task CRUD — microservice #2",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(RequestTracingMiddleware, service_name="task-service")


# ─── Auth dependency ──────────────────────────────────────────

async def get_current_user(
    request: Request,
    authorization: str | None = Header(None)
) -> dict:
    """
    Verify JWT by calling auth-service.

    This is service-to-service communication:
    task-service → auth-service
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization header required: Bearer <token>")

    token = authorization[7:]    # Remove "Bearer "

    # Check circuit breaker
    if AUTH_CIRCUIT.is_open():
        log.error("Auth circuit OPEN — rejecting request")
        raise HTTPException(503, "Auth service temporarily unavailable")

    try:
        headers = make_outgoing_headers(request)
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{AUTH_URL}/auth/verify",
                json={"token": token},
                headers=headers
            )

        if r.status_code == 401:
            AUTH_CIRCUIT.on_failure()
            raise HTTPException(401, "Invalid or expired token")

        AUTH_CIRCUIT.on_success()
        return r.json()

    except httpx.TimeoutException:
        AUTH_CIRCUIT.on_failure()
        log.error("Auth service timeout")
        raise HTTPException(503, "Auth service timeout")

    except HTTPException:
        raise

    except Exception as e:
        AUTH_CIRCUIT.on_failure()
        log.error(f"Auth service error: {e}")
        raise HTTPException(503, "Auth service unavailable")


async def get_ai_classification(
    task_title: str,
    request: Request
) -> str:
    """
    Get AI priority classification from ai-service.

    Optional — falls back to "medium" if ai-service is unavailable.
    """
    if AI_CIRCUIT.is_open():
        log.warning("AI circuit OPEN — using default priority")
        return "medium"

    try:
        headers = make_outgoing_headers(request)
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(
                f"{AI_URL}/ai/classify",
                json={"task": task_title},
                headers=headers
            )
        AI_CIRCUIT.on_success()
        return r.json().get("priority", "medium")

    except Exception as e:
        AI_CIRCUIT.on_failure()
        log.warning(f"AI service unavailable, using default: {e}")
        return "medium"    # Graceful fallback


# ─── Schemas ─────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Optional[str] = None    # if None, AI classifies it
    tags: list[str] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix login bug before Friday demo",
                "description": "Users with special chars in password cannot log in",
                "tags": ["bug", "auth"]
            }
        }


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None


# ─── Endpoints ────────────────────────────────────────────────

@app.get("/tasks")
async def list_tasks(
    status: str = "all",
    priority: str = "all",
    current_user: dict = Depends(get_current_user)
) -> dict:
    """List all tasks with optional filters."""
    tasks = list(TASKS.values())

    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]
    if priority != "all":
        tasks = [t for t in tasks if t["priority"] == priority]

    log.info(f"List tasks: {len(tasks)} results "
             f"(user={current_user.get('username')})")

    return {
        "tasks": tasks,
        "total": len(tasks),
        "filters": {"status": status, "priority": priority}
    }


@app.post("/tasks", status_code=201)
async def create_task(
    request: Request,
    body: CreateTaskRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Create a new task.

    If priority is not provided, calls ai-service to classify.
    """
    task_id = f"task-{str(uuid.uuid4())[:8]}"

    # Get priority (AI or provided)
    if body.priority:
        priority = body.priority
        classified_by = "user"
    else:
        priority = await get_ai_classification(body.title, request)
        classified_by = "ai-service"

    task = {
        "id": task_id,
        "title": body.title,
        "description": body.description,
        "priority": priority,
        "status": "pending",
        "tags": body.tags,
        "created_by": current_user.get("user_id"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "classified_by": classified_by
    }

    TASKS[task_id] = task
    log.info(f"Task created: {task_id} '{body.title}' "
             f"priority={priority} by={current_user.get('username')}")

    return task


@app.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get a specific task by ID."""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Update a task. Only provided fields are changed."""
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    updates = body.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.utcnow().isoformat()
    task.update(updates)
    TASKS[task_id] = task

    log.info(f"Task updated: {task_id} fields={list(updates.keys())}")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a task. Requires admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin role required to delete tasks")

    task = TASKS.pop(task_id, None)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    log.info(f"Task deleted: {task_id} by={current_user.get('username')}")


@app.get("/health")
def health() -> dict:
    return {
        "service": "task-service",
        "status": "healthy",
        "port": 8002,
        "task_count": len(TASKS),
        "circuit_breakers": {
            "auth": AUTH_CIRCUIT.status(),
            "ai": AI_CIRCUIT.status()
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
def root() -> dict:
    return {
        "service": "task-service",
        "version": "1.0.0",
        "dependencies": ["auth-service:8001", "ai-service:8003"],
        "endpoints": {
            "list": "GET /tasks",
            "create": "POST /tasks",
            "get": "GET /tasks/{id}",
            "update": "PATCH /tasks/{id}",
            "delete": "DELETE /tasks/{id}"
        }
    }