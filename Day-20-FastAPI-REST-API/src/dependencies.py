# ============================================================
# src/dependencies.py
# Shared dependencies for FastAPI dependency injection
# ============================================================

from fastapi import Depends, HTTPException, Header, Query
from typing import Annotated, Optional
from src.database import db, InMemoryDB


# ─── Database Dependency ────────────────────────────────────

def get_db() -> InMemoryDB:
    """
    Provide the database instance.

    In a real app this would yield a SQLAlchemy session:
        session = SessionLocal()
        try: yield session
        finally: session.close()
    """
    return db


# ─── Auth Dependency ────────────────────────────────────────

VALID_TOKENS = {
    "token-humayun-admin": {
        "id": 1,
        "username": "humayun",
        "email": "humayun@email.com",
        "role": "admin"
    },
    "token-ali-user": {
        "id": 2,
        "username": "ali",
        "email": "ali@email.com",
        "role": "user"
    },
    "token-sara-user": {
        "id": 3,
        "username": "sara",
        "email": "sara@email.com",
        "role": "user"
    },
}

# Special "no auth" token for demo purposes
DEMO_USER = {
    "id": 999,
    "username": "demo_user",
    "email": "demo@taskmanager.com",
    "role": "user"
}


def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer token")
) -> dict:
    """
    Extract and validate user from Authorization header.

    For this demo:
    - No token → demo user (so Swagger UI works without setup)
    - Bearer token-humayun-admin → admin user
    - Bearer token-ali-user → regular user

    In production: validate JWT, look up user in DB.
    """
    if authorization is None:
        return DEMO_USER    # Demo mode — no auth required

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must be 'Bearer <token>'"
        )

    token = authorization[7:]
    user = VALID_TOKENS.get(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user


def require_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Ensure the current user has admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="This endpoint requires admin privileges"
        )
    return current_user


# ─── Pagination Dependency ──────────────────────────────────

class PaginationParams:
    """Reusable pagination parameters."""
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        per_page: int = Query(
            default=20, ge=1, le=100,
            description="Items per page (max 100)"
        )
    ):
        self.page = page
        self.per_page = per_page


# ─── Type Aliases ───────────────────────────────────────────
# Makes function signatures cleaner

CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
Database = Annotated[InMemoryDB, Depends(get_db)]
Pagination = Annotated[PaginationParams, Depends(PaginationParams)]