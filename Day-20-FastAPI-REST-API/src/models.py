# ============================================================
# src/models.py
# Pydantic models for request validation and response shaping
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


# ─── Enums ──────────────────────────────────────────────────

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


# ─── Task Models ────────────────────────────────────────────

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Task title",
        example="Set up CI/CD pipeline"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        example="Configure GitHub Actions for automated testing and deployment"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        example="high"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        example="pending"
    )
    project_id: Optional[int] = Field(
        default=None,
        description="Associate with a project",
        example=1
    )
    due_date: Optional[datetime] = Field(
        default=None,
        description="Task due date (ISO 8601 format)",
        example="2025-06-30T17:00:00"
    )
    tags: list[str] = Field(
        default=[],
        max_length=10,
        description="List of tag names"
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        ge=0.25,
        le=1000,
        description="Estimated hours to complete"
    )

    @validator("tags")
    def normalize_tags(cls, tags):
        return list({tag.lower().strip() for tag in tags if tag.strip()})

    @validator("title")
    def strip_title(cls, title):
        stripped = title.strip()
        if not stripped:
            raise ValueError("Title cannot be blank")
        return stripped

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Review PR #42",
                "description": "Review Ali's authentication module PR",
                "priority": "high",
                "project_id": 1,
                "tags": ["code-review", "auth"],
                "estimated_hours": 1.5
            }
        }


class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    project_id: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    estimated_hours: Optional[float] = Field(None, ge=0.25, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)

    @validator("tags")
    def normalize_tags(cls, tags):
        if tags is None:
            return None
        return list({tag.lower().strip() for tag in tags if tag.strip()})


class TaskResponse(BaseModel):
    """Schema for task responses."""
    id: int
    title: str
    description: Optional[str] = None
    priority: Priority
    status: TaskStatus
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: list[str] = []
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Project Models ─────────────────────────────────────────

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(
        min_length=1,
        max_length=100,
        example="180-Day Roadmap"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        example="Full Stack AI Engineer learning journey"
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.ACTIVE
    )
    color: str = Field(
        default="#3B82F6",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code",
        example="#10B981"
    )
    deadline: Optional[datetime] = Field(
        default=None,
        example="2025-12-31T00:00:00"
    )

    @validator("name")
    def strip_name(cls, v):
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Website Redesign",
                "description": "Redesign company website with new brand",
                "color": "#8B5CF6",
                "deadline": "2025-09-30T00:00:00"
            }
        }


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatus] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    """Schema for project responses."""
    id: int
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    color: str
    deadline: Optional[datetime] = None
    task_count: int = 0
    completed_task_count: int = 0
    completion_pct: float = 0.0
    created_at: datetime
    updated_at: datetime


# ─── Tag Models ─────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, example="urgent")
    color: str = Field(
        default="#6B7280",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        example="#EF4444"
    )

    @validator("name")
    def normalize_name(cls, v):
        return v.lower().strip()


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    task_count: int = 0
    created_at: datetime


# ─── Shared Response Models ─────────────────────────────────

class PaginatedTasks(BaseModel):
    """Paginated list of tasks."""
    items: list[TaskResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedProjects(BaseModel):
    """Paginated list of projects."""
    items: list[ProjectResponse]
    total: int
    page: int
    per_page: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    detail: Optional[str] = None


class StatsResponse(BaseModel):
    """API statistics response."""
    total_tasks: int
    tasks_by_status: dict[str, int]
    tasks_by_priority: dict[str, int]
    total_projects: int
    projects_by_status: dict[str, int]
    total_tags: int
    completion_rate_pct: float
    overdue_tasks: int
    upcoming_tasks_7_days: int