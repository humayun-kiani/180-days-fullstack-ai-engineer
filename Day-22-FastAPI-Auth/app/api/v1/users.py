# ============================================================
# app/api/v1/users.py
# User endpoints
# ============================================================

import hashlib
from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.db.models.user import User
from app.api.deps import DB, CurrentUser, AdminUser

router = APIRouter(prefix="/users", tags=["Users"])


def hash_password(password: str) -> str:
    """Simple password hash for demo. Use bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user_in: UserCreate, db: DB = None):
    # Check duplicate email
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(409, f"Email '{user_in.email}' is already registered")

    # Check duplicate username
    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(409, f"Username '{user_in.username}' is already taken")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


@router.get("/", response_model=list[UserResponse])
def list_users(db: DB = None, admin: AdminUser = None):
    return db.query(User).filter(User.is_active == True).all()


@router.get("/me", response_model=dict)
def get_me(current_user: CurrentUser = None):
    return {"user": current_user, "message": "Demo auth — use JWT in production"}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: DB = None, current_user: CurrentUser = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, f"User {user_id} not found")
    return user