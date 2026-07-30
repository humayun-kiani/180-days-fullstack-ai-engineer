# ============================================================
# app/schemas/common.py
# Shared Pydantic schema utilities
# ============================================================

from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class MessageResponse(BaseModel):
    """Simple success message."""
    message: str
    detail: str | None = None