# ============================================================
# app/core/security.py
# Password hashing and JWT operations
# ============================================================

import uuid
from datetime import datetime, timedelta
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ─── Password Hashing ────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    bcrypt automatically:
    - Generates a random salt
    - Applies a work factor (rounds) of 12 by default
    - Returns a 60-character hash string

    Args:
        password: Plain text password from user.

    Returns:
        str: Bcrypt hash string (safe to store in database).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.

    This is intentionally slow (~100ms) to prevent brute force attacks.

    Args:
        plain_password: The password the user entered.
        hashed_password: The stored bcrypt hash.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token Operations ────────────────────────────────────

def create_access_token(
    subject: str | int,
    extra_data: dict | None = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The token subject — typically user ID as string.
        extra_data: Additional claims to include in the token.
        expires_delta: Custom expiration. Defaults to settings value.

    Returns:
        str: Encoded JWT string.
    """
    expire = datetime.utcnow() + (
        expires_delta or
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(subject),               # subject (user ID)
        "exp": expire,                      # expiry time
        "iat": datetime.utcnow(),          # issued at
        "jti": str(uuid.uuid4()),          # unique token ID (for revocation)
        "type": "access"                   # token type
    }

    if extra_data:
        payload.update(extra_data)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    """
    Create a long-lived refresh token.

    Refresh tokens are used to get new access tokens without re-login.
    They should be stored securely (httpOnly cookie in production).

    Args:
        subject: User ID as string.

    Returns:
        str: Encoded JWT refresh token.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Verifies:
    - Signature (token was created by us)
    - Expiry (token has not expired)
    - Algorithm (correct algorithm used)

    Args:
        token: JWT token string.

    Returns:
        dict: Token payload.

    Raises:
        JWTError: If token is invalid, expired, or tampered with.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )


def get_token_expires_in(token: str) -> int:
    """Get seconds until token expires. Returns 0 if expired."""
    try:
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        remaining = int(exp - datetime.utcnow().timestamp())
        return max(0, remaining)
    except JWTError:
        return 0