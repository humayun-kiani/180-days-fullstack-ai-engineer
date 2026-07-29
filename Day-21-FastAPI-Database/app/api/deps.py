# ============================================================
# app/api/deps.py
# FastAPI dependencies shared across all routes
# ============================================================

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.core.config import settings

# ─── Database Dependency ────────────────────────────────────

DB = Annotated[Session, Depends(get_db)]


# ─── Pagination Dependency ──────────────────────────────────

class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(
            settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description=f"Items per page (max {settings.MAX_PAGE_SIZE})"
        )
    ):
        self.page = page
        self.per_page = per_page

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


PageParams = Annotated[Pagination, Depends(Pagination)]


# ─── Auth Dependency ────────────────────────────────────────
# Simplified auth for this demo
# In production: validate JWT token, look up user in DB

DEMO_TOKENS = {
    "token-admin": {"id": 1, "username": "humayun", "role": "admin"},
    "token-user": {"id": 2, "username": "ali", "role": "user"},
}

DEMO_USER = {"id": 0, "username": "demo", "role": "user"}


def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """Extract current user from Authorization header."""
    if not authorization:
        return DEMO_USER

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")

    token = authorization[7:]
    user = DEMO_TOKENS.get(token)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, "Admin privileges required")
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]