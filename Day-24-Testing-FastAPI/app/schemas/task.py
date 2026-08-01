# ============================================================
# app/schemas/task.py
# Pydantic schemas for Task
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, example="Set up CI/CD")
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    project_id: Optional[int] = None
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: list[str] = Field(default=[], max_length=10)
    estimated_hours: Optional[float] = Field(None, ge=0.25, le=1000)

    @validator("tags")
    def normalize_tags(cls, tags):
        return list({t.lower().strip() for t in tags if t.strip()})

    @validator("title")
    def strip_title(cls, v):
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete FastAPI tutorial",
                "description": "Work through Day 21 of the roadmap",
                "priority": "high",
                "tags": ["learning", "backend"],
                "estimated_hours": 4.0
            }
        }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    project_id: Optional[int] = None
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    estimated_hours: Optional[float] = Field(None, ge=0.25, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)

    @validator("tags")
    def normalize_tags(cls, tags):
        if tags is None:
            return None
        return list({t.lower().strip() for t in tags if t.strip()})


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    project_id: Optional[int] = None
    owner_id: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: list[str] = []
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True