# backend/app/schemas/task.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(urgent|high|medium|low)$")
    due_date: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Fix login bug before Friday demo",
                "description": "Auth fails for users with special characters",
                "priority": "high",
            }
        }
    }


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")
    priority: Optional[str] = Field(None, pattern="^(urgent|high|medium|low)$")
    due_date: Optional[datetime] = None
    ai_summary: Optional[str] = None
    ai_priority: Optional[str] = None


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    owner_id: uuid.UUID
    ai_summary: Optional[str]
    ai_priority: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskOut]
    total: int
    page: int
    per_page: int
    pages: int