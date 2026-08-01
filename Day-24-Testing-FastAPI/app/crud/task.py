# ============================================================
# app/crud/task.py
# Task-specific CRUD operations with advanced querying
# ============================================================

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc

from app.crud.base import CRUDBase
from app.db.models.task import Task
from app.db.models.project import Project
from app.schemas.task import TaskCreate, TaskUpdate


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """Task CRUD with comprehensive query support."""

    # ─── READ ─────────────────────────────────────────────────

    def get_active(self, db: Session, task_id: int) -> Optional[Task]:
        """Get a non-deleted task by ID."""
        return (
            db.query(Task)
            .options(joinedload(Task.project))
            .filter(Task.id == task_id, Task.is_deleted == False)
            .first()
        )

    def get_multi_filtered(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[int] = None,
        owner_id: Optional[int] = None,
        search: Optional[str] = None,
        overdue_only: bool = False,
        tag: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[list[Task], int]:
        """
        Get tasks with comprehensive filtering and sorting.

        Returns:
            tuple: (list of tasks, total count before pagination)
        """
        query = (
            db.query(Task)
            .options(joinedload(Task.project))
            .filter(Task.is_deleted == False)
        )

        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if owner_id:
            query = query.filter(Task.owner_id == owner_id)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )
        if overdue_only:
            now = datetime.utcnow()
            query = query.filter(
                and_(
                    Task.due_date < now,
                    Task.due_date.is_not(None),
                    Task.status.not_in(["done", "archived"])
                )
            )
        if tag:
            # PostgreSQL JSON contains — works with our JSON tags column
            query = query.filter(
                Task.tags.contains([tag.lower()])
            )

        # Apply sorting
        sort_column_map = {
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
            "due_date": Task.due_date,
            "title": Task.title,
            "priority": Task.priority,
            "status": Task.status
        }
        sort_col = sort_column_map.get(sort_by, Task.created_at)
        sort_func = desc if sort_order == "desc" else asc
        query = query.order_by(sort_func(sort_col))

        # Count before pagination
        total = query.count()

        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_overdue(self, db: Session, limit: int = 50) -> list[Task]:
        """Get all overdue active tasks."""
        now = datetime.utcnow()
        return (
            db.query(Task)
            .options(joinedload(Task.project))
            .filter(
                Task.due_date < now,
                Task.due_date.is_not(None),
                Task.status.not_in(["done", "archived"]),
                Task.is_deleted == False
            )
            .order_by(Task.due_date.asc())    # most overdue first
            .limit(limit)
            .all()
        )

    def get_upcoming(self, db: Session, days: int = 7) -> list[Task]:
        """Get tasks due within the next N days."""
        now = datetime.utcnow()
        deadline = now + timedelta(days=days)
        return (
            db.query(Task)
            .filter(
                Task.due_date >= now,
                Task.due_date <= deadline,
                Task.status.not_in(["done", "archived"]),
                Task.is_deleted == False
            )
            .order_by(Task.due_date.asc())
            .all()
        )

    def get_stats(self, db: Session) -> dict:
        """Get comprehensive task statistics."""
        base_query = db.query(Task).filter(Task.is_deleted == False)
        total = base_query.count()

        by_status = {}
        for status_val in ["pending", "in_progress", "done", "archived"]:
            by_status[status_val] = base_query.filter(
                Task.status == status_val
            ).count()

        by_priority = {}
        for priority_val in ["low", "medium", "high", "urgent"]:
            by_priority[priority_val] = base_query.filter(
                Task.priority == priority_val
            ).count()

        done = by_status.get("done", 0)
        overdue_count = len(self.get_overdue(db))
        upcoming_count = len(self.get_upcoming(db))

        return {
            "total_tasks": total,
            "tasks_by_status": by_status,
            "tasks_by_priority": by_priority,
            "completion_rate_pct": round(done / total * 100 if total > 0 else 0, 1),
            "overdue_tasks": overdue_count,
            "upcoming_tasks_7_days": upcoming_count
        }

    # ─── WRITE ────────────────────────────────────────────────

    def complete_task(
        self,
        db: Session,
        task: Task,
        actual_hours: Optional[float] = None
    ) -> Task:
        """Mark a task as done with optional actual hours."""
        task.status = "done"
        task.completed_at = datetime.utcnow()
        if actual_hours is not None:
            task.actual_hours = actual_hours
        db.flush()
        db.refresh(task)
        return task

    def soft_delete(self, db: Session, task: Task) -> Task:
        """Soft delete — mark as deleted rather than removing."""
        task.is_deleted = True
        task.status = "archived"
        db.flush()
        return task

    def bulk_update_status(
        self,
        db: Session,
        task_ids: list[int],
        new_status: str
    ) -> int:
        """Update status for multiple tasks at once. Returns count updated."""
        updated = (
            db.query(Task)
            .filter(Task.id.in_(task_ids), Task.is_deleted == False)
            .update(
                {
                    "status": new_status,
                    "updated_at": datetime.utcnow(),
                    "completed_at": datetime.utcnow() if new_status == "done" else None
                },
                synchronize_session="fetch"
            )
        )
        db.flush()
        return updated


task_crud = CRUDTask(Task)