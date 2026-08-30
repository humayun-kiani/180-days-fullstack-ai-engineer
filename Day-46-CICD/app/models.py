# app/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    tags: list[str] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix login bug",
                "priority": "high",
                "tags": ["bug", "auth"]
            }
        }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    tags: Optional[list[str]] = None


class Task(BaseModel):
    task_id: str
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    tags: list[str]
    created_at: str
    updated_at: str