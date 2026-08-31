# app/main.py
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from app.models import Task, TaskCreate, TaskUpdate
from app import tasks as task_store

app = FastAPI(
    title="Task API",
    description="Task management API running on Kubernetes",
    version="1.0.0"
)

# Read config from environment (injected by Kubernetes ConfigMap)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_TASKS = int(os.environ.get("MAX_TASKS", "10000"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
POD_NAME = os.environ.get("POD_NAME", "unknown")      # Injected via Downward API
NODE_NAME = os.environ.get("NODE_NAME", "unknown")


@app.get("/health")
def health() -> dict:
    """
    Health check endpoint.
    
    Kubernetes readiness and liveness probes hit this endpoint.
    Returns 200 when the application is healthy.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "environment": ENVIRONMENT,
        "pod_name": POD_NAME,      # Shows which pod served the request!
        "node_name": NODE_NAME,    # Shows which node
        "task_count": task_store.task_count(),
        "max_tasks": MAX_TASKS
    }


@app.get("/ready")
def readiness() -> dict:
    """
    Readiness probe endpoint.
    
    Returns 503 if the pod should be taken out of rotation.
    Different from /health: could check DB connection, cache, etc.
    """
    # Simulate readiness check (in production: check DB connectivity)
    if task_store.task_count() >= MAX_TASKS:
        raise HTTPException(503, "Task store at maximum capacity")
    return {"ready": True, "pod": POD_NAME}


@app.post("/tasks", status_code=201, response_model=Task)
def create_task(body: TaskCreate) -> Task:
    if task_store.task_count() >= MAX_TASKS:
        raise HTTPException(507, "Storage capacity exceeded")
    return task_store.create_task(body)


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
) -> list[Task]:
    return task_store.list_tasks(status, priority)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    task = task_store.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, body: TaskUpdate) -> Task:
    task = task_store.update_task(task_id, body)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if not task_store.delete_task(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")


@app.get("/info")
def cluster_info() -> dict:
    """Show Kubernetes environment info — useful for demos."""
    return {
        "pod_name": POD_NAME,
        "node_name": NODE_NAME,
        "environment": ENVIRONMENT,
        "log_level": LOG_LEVEL,
        "max_tasks": MAX_TASKS,
        "tip": "Make multiple requests and watch pod_name change (load balancing!)"
    }