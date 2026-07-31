# ============================================================
# app/fake_db.py
# In-memory data for the WebSocket demo
# (In production this would connect to the Day 21/22 database)
# ============================================================

from datetime import datetime, timedelta
import random

# Simulated users
USERS = {
    "demo_token_humayun": {
        "id": 1,
        "username": "humayun",
        "role": "admin",
        "full_name": "Humayun Kiani"
    },
    "demo_token_ali": {
        "id": 2,
        "username": "ali",
        "role": "editor",
        "full_name": "Ali Hassan"
    },
    "demo_token_sara": {
        "id": 3,
        "username": "sara",
        "role": "user",
        "full_name": "Sara Ahmed"
    },
}

# Simulated projects
PROJECTS = {
    1: {"id": 1, "name": "180-Day Roadmap", "color": "#3B82F6"},
    2: {"id": 2, "name": "Portfolio Website", "color": "#10B981"},
    3: {"id": 3, "name": "Open Source", "color": "#8B5CF6"},
}

# Simulated tasks (in-memory — updates are live!)
TASKS: dict[int, dict] = {}
_task_counter = 0


def _init_tasks():
    """Initialize with sample tasks."""
    global _task_counter
    now = datetime.utcnow()
    sample_tasks = [
        {"title": "Complete Day 23 WebSockets", "status": "in_progress",
         "priority": "high", "project_id": 1, "assigned_to": "humayun"},
        {"title": "Write unit tests for auth", "status": "pending",
         "priority": "high", "project_id": 1, "assigned_to": "ali"},
        {"title": "Design portfolio header", "status": "pending",
         "priority": "medium", "project_id": 2, "assigned_to": "sara"},
        {"title": "Set up GitHub Actions", "status": "pending",
         "priority": "medium", "project_id": 2, "assigned_to": "humayun"},
        {"title": "Find OSS issues", "status": "done",
         "priority": "low", "project_id": 3, "assigned_to": "ali"},
        {"title": "Review PR #15", "status": "pending",
         "priority": "urgent", "project_id": 1, "assigned_to": "humayun"},
        {"title": "Update README", "status": "done",
         "priority": "low", "project_id": 1, "assigned_to": "sara"},
        {"title": "Deploy to Vercel", "status": "pending",
         "priority": "medium", "project_id": 2, "assigned_to": "humayun"},
    ]
    for task_data in sample_tasks:
        _task_counter += 1
        TASKS[_task_counter] = {
            "id": _task_counter,
            "created_at": (now - timedelta(days=random.randint(1, 10))).isoformat(),
            "updated_at": now.isoformat(),
            **task_data
        }


_init_tasks()


def get_user_by_token(token: str) -> dict | None:
    """Simulate JWT verification — in production use real JWT."""
    return USERS.get(token)


def get_task(task_id: int) -> dict | None:
    return TASKS.get(task_id)


def get_tasks(project_id: int | None = None) -> list[dict]:
    tasks = list(TASKS.values())
    if project_id:
        tasks = [t for t in tasks if t.get("project_id") == project_id]
    return sorted(tasks, key=lambda t: t["id"])


def complete_task(task_id: int, username: str) -> dict | None:
    task = TASKS.get(task_id)
    if not task:
        return None
    task["status"] = "done"
    task["completed_by"] = username
    task["updated_at"] = datetime.utcnow().isoformat()
    return task


def create_task(
    title: str,
    project_id: int,
    priority: str,
    created_by: str
) -> dict:
    global _task_counter
    _task_counter += 1
    task = {
        "id": _task_counter,
        "title": title,
        "status": "pending",
        "priority": priority,
        "project_id": project_id,
        "assigned_to": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    TASKS[_task_counter] = task
    return task


def update_task_status(task_id: int, new_status: str, username: str) -> dict | None:
    task = TASKS.get(task_id)
    if not task:
        return None
    task["status"] = new_status
    task["updated_at"] = datetime.utcnow().isoformat()
    if new_status == "done":
        task["completed_by"] = username
    return task