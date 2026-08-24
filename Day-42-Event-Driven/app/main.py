# ============================================================
# app/main.py
# Event-Driven Task Manager — Day 42
# ============================================================

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.event_bus import event_bus
from app.event_store import event_store
from app import tasks as task_db
from consumers import notification, ai_classifier, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 65)
    print("  Event-Driven Task Manager — Day 42")
    print("  Event-Driven Architecture with Message Queue")
    print("=" * 65)

    print("\n  Registering event consumers...")
    notification.register()
    ai_classifier.register()
    audit.register()

    stats = event_bus.get_stats()
    print(f"\n  Subscribers registered: {stats['subscriber_count']}")
    print(f"  Event bus mode: {'Redis Streams' if stats['redis_available'] else 'In-Memory'}")
    print(f"\n  Docs: http://localhost:8000/docs\n")

    # Seed with demo tasks
    print("  Seeding demo tasks...")
    await task_db.create_task(
        "URGENT: Production API returning 500 errors",
        priority="medium",    # AI will reclassify to urgent
        created_by="humayun"
    )
    await task_db.create_task(
        "Add CSV export to reports dashboard",
        created_by="ali"
    )
    print(f"  Demo tasks created.\n")

    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="Event-Driven Task Manager",
    description="""
## 📨 Event-Driven Task Manager — Day 42

Every task operation publishes an event. Three consumers react asynchronously:
- **Notification Consumer**: sends email notifications
- **AI Classifier**: auto-classifies task priority
- **Audit Consumer**: logs every change for compliance

### Event Flow

### Event Types
- `task.created` — new task published
- `task.updated` — task modified
- `task.completed` — task marked done
- `task.deleted` — task removed
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Schemas ─────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Optional[str] = None    # None = let AI decide
    tags: list[str] = Field(default=[])
    created_by: str = Field(default="anonymous")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "URGENT: Production API returning 500 errors",
                "created_by": "humayun"
            }
        }


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[list[str]] = None
    updated_by: str = Field(default="anonymous")


# ─── Task Endpoints ───────────────────────────────────────────

@app.post("/tasks", status_code=201, summary="Create task + publish event")
async def create_task(body: CreateTaskRequest) -> dict:
    """
    Create a task. Automatically publishes events to:
    - Notification consumer (sends email)
    - AI classifier (may update priority)
    - Audit consumer (compliance log)
    """
    task = await task_db.create_task(
        title=body.title,
        description=body.description,
        priority=body.priority,
        tags=body.tags,
        created_by=body.created_by
    )
    return {
        "task": task,
        "message": "Task created. Events published to 3 consumers.",
        "event_bus_stats": event_bus.get_stats()
    }


@app.get("/tasks", summary="List all tasks")
def list_tasks(status: str = "all", priority: str = "all") -> dict:
    tasks = task_db.list_tasks(status, priority)
    return {"tasks": tasks, "total": len(tasks)}


@app.get("/tasks/{task_id}", summary="Get task with full event history")
def get_task(task_id: str) -> dict:
    task = task_db.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    history = event_store.get_for_task(task_id)
    return {
        "task": task,
        "event_history": history,
        "event_count": len(history)
    }


@app.patch("/tasks/{task_id}", summary="Update task + publish event")
async def update_task(task_id: str, body: UpdateTaskRequest) -> dict:
    updates = body.model_dump(exclude_none=True, exclude={"updated_by"})
    if not updates:
        raise HTTPException(400, "No fields to update")
    task = await task_db.update_task(task_id, updates, body.updated_by)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.post("/tasks/{task_id}/complete", summary="Complete task + publish event")
async def complete_task(task_id: str, completed_by: str = "anonymous") -> dict:
    task = await task_db.complete_task(task_id, completed_by)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return {"task": task, "message": "Task completed. Completion event published."}


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete task + publish event")
async def delete_task(task_id: str, deleted_by: str = "admin"):
    deleted = await task_db.delete_task(task_id, deleted_by)
    if not deleted:
        raise HTTPException(404, f"Task '{task_id}' not found")


# ─── Event Bus Observability ──────────────────────────────────

@app.get("/events", summary="View all published events")
def get_events(event_type: str | None = None) -> dict:
    """Get all events from the event store."""
    events = event_store.get_all(event_type)
    return {
        "events": events,
        "total": len(events),
        "stats": event_store.stats()
    }


@app.get("/events/replay/{task_id}", summary="Replay events to reconstruct task state")
def replay_events(task_id: str) -> dict:
    """
    Rebuild task state by replaying its events.

    This demonstrates Event Sourcing: the event log is the source of truth.
    """
    state = event_store.replay_task_state(task_id)
    history = event_store.get_for_task(task_id)
    if not history:
        raise HTTPException(404, f"No events found for task '{task_id}'")
    return {
        "task_id": task_id,
        "replayed_state": state,
        "events_replayed": len(history),
        "event_history": history
    }


@app.get("/consumers/notifications", summary="View sent notifications")
def get_notifications() -> dict:
    notifs = notification.get_notifications()
    return {"notifications": notifs, "total": len(notifs)}


@app.get("/consumers/ai", summary="View AI classifications")
def get_ai_classifications() -> dict:
    classifications = ai_classifier.get_classifications()
    return {"classifications": classifications, "total": len(classifications)}


@app.get("/consumers/audit", summary="View audit log")
def get_audit_log() -> dict:
    log = audit.get_audit_log()
    return {"audit_log": log, "total": len(log)}


@app.get("/events/dlq", summary="Dead letter queue — failed messages")
def get_dlq() -> dict:
    dlq = event_bus.get_dlq()
    return {
        "dlq_messages": dlq,
        "count": len(dlq),
        "note": "Messages here failed after max retries"
    }


@app.get("/events/bus", summary="Event bus stats and subscribers")
def get_bus_stats() -> dict:
    return {
        "stats": event_bus.get_stats(),
        "subscribers": event_bus.get_subscribers()
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    stats = event_bus.get_stats()
    return {
        "status": "healthy",
        "event_bus": stats,
        "event_store": event_store.stats(),
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 42 — Event-Driven Architecture"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "Event-Driven Task Manager",
        "day": "Day 42 — EDA with Message Queues",
        "docs": "/docs",
        "endpoints": {
            "create_task": "POST /tasks",
            "list_tasks": "GET /tasks",
            "complete_task": "POST /tasks/{id}/complete",
            "events": "GET /events",
            "replay": "GET /events/replay/{task_id}",
            "notifications": "GET /consumers/notifications",
            "ai_log": "GET /consumers/ai",
            "audit_log": "GET /consumers/audit",
            "dlq": "GET /events/dlq",
            "bus_stats": "GET /events/bus"
        }
    }