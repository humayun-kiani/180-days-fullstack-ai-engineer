# app/main.py
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from app.models import Task, TaskCreate, TaskUpdate
from app import tasks as task_store


app = FastAPI(
    title="Task API",
    description="Task management API with CI/CD pipeline",
    version="1.0.0"
)


@app.get("/health")
def health() -> dict:
    """Health check endpoint for deployment verification."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "task_count": task_store.task_count()
    }


@app.post("/tasks", status_code=201, response_model=Task)
def create_task(body: TaskCreate) -> Task:
    """Create a new task."""
    return task_store.create_task(body)


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
) -> list[Task]:
    """List tasks with optional filters."""
    return task_store.list_tasks(status, priority)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    """Get a task by ID."""
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, body: TaskUpdate) -> Task:
    """Update a task."""
    task = task_store.update_task(task_id, body)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    """Delete a task."""
    if not task_store.delete_task(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")