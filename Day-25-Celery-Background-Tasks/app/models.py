# ============================================================
# app/models.py
# In-memory models for the demo (replace with real DB in prod)
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import random


@dataclass
class User:
    id: int
    username: str
    email: str
    full_name: str
    role: str = "user"
    is_active: bool = True


@dataclass
class Task:
    id: int
    title: str
    status: str
    priority: str
    owner_id: int
    project_id: Optional[int] = None
    due_date: Optional[datetime] = None
    assigned_to_email: Optional[str] = None


# Simulated database
USERS: dict[int, User] = {
    1: User(1, "humayun", "humayun@example.com", "Humayun Kiani", "admin"),
    2: User(2, "ali", "ali@example.com", "Ali Hassan", "user"),
    3: User(3, "sara", "sara@example.com", "Sara Ahmed", "user"),
}

TASKS: dict[int, Task] = {}
_task_counter = 0


def _init_tasks():
    global _task_counter
    now = datetime.utcnow()
    sample_tasks = [
        Task(1, "Complete Day 25 Project", "in_progress", "high", 1,
             due_date=now + timedelta(hours=4), assigned_to_email="humayun@example.com"),
        Task(2, "Write tests for auth", "pending", "high", 1,
             due_date=now + timedelta(days=1), assigned_to_email="humayun@example.com"),
        Task(3, "Design portfolio header", "pending", "medium", 2,
             due_date=now - timedelta(hours=2), assigned_to_email="ali@example.com"),  # overdue!
        Task(4, "Review PR #15", "pending", "urgent", 1,
             due_date=now - timedelta(days=1), assigned_to_email="humayun@example.com"),  # overdue!
        Task(5, "Update README", "done", "low", 3,
             assigned_to_email="sara@example.com"),
        Task(6, "Configure GitHub Actions", "pending", "medium", 1,
             due_date=now + timedelta(days=3), assigned_to_email="humayun@example.com"),
        Task(7, "Deploy to Vercel", "pending", "medium", 2,
             due_date=now + timedelta(days=7), assigned_to_email="ali@example.com"),
    ]
    for t in sample_tasks:
        TASKS[t.id] = t
        _task_counter = max(_task_counter, t.id)


_init_tasks()


def get_overdue_tasks() -> list[Task]:
    now = datetime.utcnow()
    return [
        t for t in TASKS.values()
        if t.due_date and t.due_date < now
        and t.status not in ("done", "archived")
    ]


def get_pending_tasks_for_user(user_id: int) -> list[Task]:
    return [
        t for t in TASKS.values()
        if t.owner_id == user_id and t.status == "pending"
    ]


def get_all_users() -> list[User]:
    return list(USERS.values())


def create_task(title: str, priority: str, owner_id: int) -> Task:
    global _task_counter
    _task_counter += 1
    task = Task(
        id=_task_counter,
        title=title,
        status="pending",
        priority=priority,
        owner_id=owner_id,
        due_date=datetime.utcnow() + timedelta(days=7)
    )
    TASKS[_task_counter] = task
    return task