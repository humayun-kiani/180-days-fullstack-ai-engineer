# ============================================================
# app/schemas/project.py
# Pydantic schemas for Project
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, example="180-Day Roadmap")
    description: Optional[str] = Field(None, max_length=2000)
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: str = Field(
        default="#3B82F6",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        example="#10B981"
    )

    @validator("name")
    def strip_name(cls, v):
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Portfolio Website",
                "description": "Personal portfolio to showcase 180-day projects",
                "color": "#10B981"
            }
        }


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[ProjectStatus] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    color: str
    is_active: bool
    task_count: int = 0
    completed_task_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True