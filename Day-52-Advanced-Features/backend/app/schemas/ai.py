# backend/app/schemas/ai.py
from typing import Optional
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    title: str
    description: Optional[str] = None


class AnalyzeResponse(BaseModel):
    suggested_priority: str
    confidence: str       # "high", "medium", "low"
    reasoning: str
    suggested_tags: list[str]
    summary: str
    estimated_hours: Optional[float]


class ExpandRequest(BaseModel):
    title: str


class ExpandResponse(BaseModel):
    description: str
    suggested_priority: str
    suggested_tags: list[str]


class BreakdownRequest(BaseModel):
    title: str
    description: Optional[str] = None


class SubTask(BaseModel):
    title: str
    estimated_hours: float
    priority: str


class BreakdownResponse(BaseModel):
    subtasks: list[SubTask]
    total_estimated_hours: float


class WeeklySummaryResponse(BaseModel):
    summary: str
    stats: dict
    highlights: list[str]
    recommendations: list[str]