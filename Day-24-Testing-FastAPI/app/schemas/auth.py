# ============================================================
# app/schemas/auth.py
# Pydantic schemas for authentication endpoints
# ============================================================

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Request body for JSON-based login."""
    username: str = Field(example="humayun")
    password: str = Field(example="password123")


class RegisterRequest(BaseModel):
    """Request body for user registration."""
    username: str = Field(
        min_length=3,
        max_length=50,
        example="humayun",
        description="3-50 characters, letters/numbers/underscores only"
    )
    email: str = Field(
        example="humayun@email.com"
    )
    password: str = Field(
        min_length=8,
        max_length=100,
        example="securepassword123",
        description="Minimum 8 characters"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        example="Humayun Kiani"
    )

    @validator("username")
    def validate_username(cls, v):
        v = v.lower().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @validator("email")
    def validate_email(cls, v):
        v = v.lower().strip()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if v.isdigit():
            raise ValueError("Password cannot be all numbers")
        if v.isalpha():
            raise ValueError("Password must contain at least one number or special character")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "humayun",
                "email": "humayun@example.com",
                "password": "MySecure@Pass123",
                "full_name": "Humayun Kiani"
            }
        }


class TokenResponse(BaseModel):
    """Response from login/refresh containing tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int    # seconds until access token expires


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Request body for changing password."""
    current_password: str = Field(example="oldpassword123")
    new_password: str = Field(min_length=8, example="newpassword123")
    confirm_new_password: str = Field(example="newpassword123")

    @validator("confirm_new_password")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New password and confirmation do not match")
        return v


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    detail: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Current user's profile."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime