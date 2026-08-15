# ============================================================
# tools/task_tools.py
# Task management tools for the agent
# ============================================================

import json
from datetime import datetime, timedelta
from langchain_core.tools import tool

# In-memory task database (in production: real database)
_TASKS = [
    {
        "id": 1,
        "title": "Fix login bug causing 500 errors",
        "status": "in_progress",
        "priority": "high",
        "category": "bug",
        "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
        "due_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "owner": "humayun",
        "tags": ["auth", "bug", "backend"]
    },
    {
        "id": 2,
        "title": "Add CSV export to reports page",
        "status": "pending",
        "priority": "medium",
        "category": "feature",
        "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "owner": "ali",
        "tags": ["feature", "reports", "frontend"]
    },
    {
        "id": 3,
        "title": "URGENT: Production database slow",
        "status": "pending",
        "priority": "urgent",
        "category": "performance",
        "created_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
        "due_date": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
        "owner": "humayun",
        "tags": ["database", "performance", "urgent"]
    },
    {
        "id": 4,
        "title": "Update API documentation",
        "status": "done",
        "priority": "low",
        "category": "documentation",
        "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
        "due_date": None,
        "owner": "sara",
        "tags": ["docs"]
    },
    {
        "id": 5,
        "title": "Implement Redis caching for user profiles",
        "status": "pending",
        "priority": "medium",
        "category": "performance",
        "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "due_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "owner": "ali",
        "tags": ["redis", "performance", "backend"]
    },
    {
        "id": 6,
        "title": "Review PR #42: Auth module refactor",
        "status": "pending",
        "priority": "high",
        "category": "review",
        "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "owner": "humayun",
        "tags": ["auth", "review", "backend"]
    },
]


def _is_overdue(task: dict) -> bool:
    if not task.get("due_date") or task["status"] == "done":
        return False
    due = datetime.fromisoformat(task["due_date"])
    return due < datetime.utcnow()


@tool
def list_tasks(
    status: str = "all",
    priority: str = "all",
    owner: str = "all"
) -> str:
    """
    List tasks with optional filtering.

    Use this to show tasks filtered by status, priority, or owner.

    Args:
        status: Filter by status: all, pending, in_progress, done
        priority: Filter by priority: all, urgent, high, medium, low
        owner: Filter by owner username: all, humayun, ali, sara

    Returns:
        JSON list of matching tasks with their details
    """
    tasks = _TASKS.copy()

    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]
    if priority != "all":
        tasks = [t for t in tasks if t["priority"] == priority]
    if owner != "all":
        tasks = [t for t in tasks if t["owner"] == owner]

    # Add computed overdue field
    result = []
    for t in tasks:
        task_copy = t.copy()
        task_copy["is_overdue"] = _is_overdue(t)
        result.append(task_copy)

    if not result:
        return f"No tasks found matching criteria: status={status}, priority={priority}, owner={owner}"

    return json.dumps(result, indent=2, default=str)


@tool
def get_overdue_tasks() -> str:
    """
    Get all tasks that are past their due date and not yet completed.

    Use this when the user asks about overdue tasks, missed deadlines,
    or what needs urgent attention right now.

    Returns:
        JSON list of overdue tasks sorted by how overdue they are
    """
    now = datetime.utcnow()
    overdue = []

    for task in _TASKS:
        if _is_overdue(task):
            due = datetime.fromisoformat(task["due_date"])
            hours_overdue = (now - due).total_seconds() / 3600
            task_copy = task.copy()
            task_copy["hours_overdue"] = round(hours_overdue, 1)
            overdue.append(task_copy)

    if not overdue:
        return "Great news! No tasks are currently overdue."

    overdue.sort(key=lambda t: t.get("hours_overdue", 0), reverse=True)
    return json.dumps(overdue, indent=2, default=str)


@tool
def get_task_summary() -> str:
    """
    Get a summary of all tasks: counts by status and priority.

    Use this when the user asks for an overview, dashboard, or summary
    of the current task state.

    Returns:
        JSON summary with counts by status and priority
    """
    by_status = {}
    by_priority = {}
    overdue_count = 0

    for task in _TASKS:
        s = task["status"]
        p = task["priority"]
        by_status[s] = by_status.get(s, 0) + 1
        by_priority[p] = by_priority.get(p, 0) + 1
        if _is_overdue(task):
            overdue_count += 1

    total = len(_TASKS)
    done = by_status.get("done", 0)

    summary = {
        "total_tasks": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue_count": overdue_count,
        "completion_rate": f"{done/total*100:.0f}%" if total > 0 else "0%",
        "critical_attention_needed": overdue_count + by_priority.get("urgent", 0)
    }
    return json.dumps(summary, indent=2)


@tool
def create_task(
    title: str,
    priority: str = "medium",
    owner: str = "humayun",
    category: str = "general",
    tags: str = ""
) -> str:
    """
    Create a new task in the task management system.

    Use this when the user explicitly asks to create, add, or log a new task.

    Args:
        title: Clear, descriptive task title
        priority: Priority level: urgent, high, medium, or low
        owner: Username who owns this task
        category: Task category: bug, feature, performance, maintenance, review, documentation
        tags: Comma-separated tags (e.g. "backend,api,urgent")

    Returns:
        Confirmation message with the new task ID and details
    """
    valid_priorities = ["urgent", "high", "medium", "low"]
    if priority.lower() not in valid_priorities:
        priority = "medium"

    new_id = max(t["id"] for t in _TASKS) + 1
    new_task = {
        "id": new_id,
        "title": title,
        "status": "pending",
        "priority": priority.lower(),
        "category": category,
        "created_at": datetime.utcnow().isoformat(),
        "due_date": None,
        "owner": owner,
        "tags": [t.strip() for t in tags.split(",") if t.strip()]
    }
    _TASKS.append(new_task)

    return (
        f"✅ Task created successfully!\n"
        f"  ID: {new_id}\n"
        f"  Title: {title}\n"
        f"  Priority: {priority.upper()}\n"
        f"  Owner: {owner}\n"
        f"  Category: {category}"
    )


@tool
def complete_task(task_id: int) -> str:
    """
    Mark a task as completed.

    Use this when the user says a task is done, finished, or complete.

    Args:
        task_id: The numeric ID of the task to complete

    Returns:
        Confirmation that the task was marked complete
    """
    for task in _TASKS:
        if task["id"] == task_id:
            if task["status"] == "done":
                return f"Task {task_id} ('{task['title']}') is already completed."
            task["status"] = "done"
            return (
                f"✅ Task {task_id} completed!\n"
                f"  '{task['title']}' marked as done."
            )
    return f"❌ Task {task_id} not found."