# ============================================================
# app/crud/project.py
# Project-specific CRUD operations
# ============================================================

from typing import Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.db.models.project import Project
from app.db.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """Project CRUD with project-specific queries."""

    def get_with_tasks(self, db: Session, project_id: int) -> Optional[Project]:
        """Get project with all tasks eagerly loaded."""
        return (
            db.query(Project)
            .options(selectinload(Project.tasks))
            .filter(Project.id == project_id, Project.is_active == True)
            .first()
        )

    def get_multi_active(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> tuple[list[Project], int]:
        """Get active projects with optional status filter."""
        query = (
            db.query(Project)
            .options(selectinload(Project.tasks))
            .filter(Project.is_active == True)
        )

        if status:
            query = query.filter(Project.status == status)

        total = query.count()
        items = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_project_stats(self, db: Session, project_id: int) -> dict:
        """Get aggregated task statistics for a project."""
        stats = (
            db.query(
                func.count(Task.id).label("total"),
                func.count(Task.id).filter(Task.status == "done").label("done"),
                func.count(Task.id).filter(Task.status == "pending").label("pending"),
                func.count(Task.id).filter(Task.status == "in_progress").label("in_progress"),
            )
            .filter(Task.project_id == project_id, Task.is_deleted == False)
            .one()
        )
        total = stats.total or 0
        done = stats.done or 0
        return {
            "total_tasks": total,
            "done": done,
            "pending": stats.pending or 0,
            "in_progress": stats.in_progress or 0,
            "completion_pct": round(done / total * 100 if total > 0 else 0, 1)
        }

    def soft_delete(self, db: Session, project_id: int) -> bool:
        """Soft-delete a project (mark inactive)."""
        project = self.get(db, project_id)
        if not project:
            return False
        project.is_active = False
        db.flush()
        return True


project_crud = CRUDProject(Project)