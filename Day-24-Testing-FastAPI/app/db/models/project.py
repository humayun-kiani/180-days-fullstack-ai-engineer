# ============================================================
# app/db/models/project.py
# Project SQLAlchemy model
# ============================================================

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.task import Task


class Project(Base):
    """
    Project model — a container for related tasks.

    One project can have many tasks (one-to-many relationship).
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship — one project has many tasks
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        lazy="select"
    )

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def completed_task_count(self) -> int:
        return len([t for t in self.tasks if t.status == "done"])

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"