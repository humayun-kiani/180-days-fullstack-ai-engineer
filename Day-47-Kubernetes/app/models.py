# app/models.py
from pydantic import BaseModel, Field
from typing import Optional
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


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None


class Task(BaseModel):
    task_id: str
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    tags: list[str]
    created_at: str
    updated_at: str