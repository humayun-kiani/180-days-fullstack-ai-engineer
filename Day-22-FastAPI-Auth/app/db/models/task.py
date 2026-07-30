# ============================================================
# app/db/models/task.py
# Task SQLAlchemy model
# ============================================================

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Float, ForeignKey, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User


class Task(Base):
    """
    Task model — the core entity.

    Belongs to a Project (optional) and a User (owner).
    Supports soft delete via is_deleted flag.
    Tags stored as a JSON array (PostgreSQL JSON type).
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    # Foreign keys
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timing
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Estimates
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="tasks"
    )
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="tasks"
    )

    # Database indexes for common queries
    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_project", "project_id"),
        Index("idx_tasks_owner", "owner_id"),
        Index("idx_tasks_deleted", "is_deleted"),
        Index("idx_tasks_due_date", "due_date"),
    )

    @property
    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.due_date < datetime.utcnow()
            and self.status not in ("done", "archived")
            and not self.is_deleted
        )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title[:30]}')>"