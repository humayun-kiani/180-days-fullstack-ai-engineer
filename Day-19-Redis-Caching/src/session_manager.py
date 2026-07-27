# ============================================================
# src/session_manager.py
# Redis-based session management using Hashes
# ============================================================

import os
import secrets
import json
from datetime import datetime
from typing import Optional
from src.redis_client import get_redis

SESSION_TTL = 60 * 60 * 24    # 24 hours
MAX_FAVORITE_CITIES = 10


def create_session(username: str = "guest") -> str:
    """
    Create a new user session stored in a Redis Hash.

    Returns:
        str: Session ID (random token).
    """
    r = get_redis()
    session_id = secrets.token_urlsafe(16)
    session_key = f"session:{session_id}"

    # Store session data in a Hash — efficient field-level access
    r.hset(session_key, mapping={
        "username": username,
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
        "search_count": 0
    })
    r.expire(session_key, SESSION_TTL)

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Get session data and refresh TTL."""
    r = get_redis()
    session_key = f"session:{session_id}"
    data = r.hgetall(session_key)

    if not data:
        return None

    # Refresh TTL on every access (sliding expiry)
    r.expire(session_key, SESSION_TTL)

    # Update last_active
    r.hset(session_key, "last_active", datetime.utcnow().isoformat())
    r.hincrby(session_key, "search_count", 1)

    return data


def add_favorite_city(session_id: str, city: str) -> bool:
    """
    Add city to user's favorites using a Redis Set.

    Sets automatically prevent duplicates.

    Returns:
        bool: True if added (was not already a favorite).
    """
    r = get_redis()
    favorites_key = f"favorites:{session_id}"
    added = r.sadd(favorites_key, city.title())
    r.expire(favorites_key, SESSION_TTL)

    if r.scard(favorites_key) > MAX_FAVORITE_CITIES:
        # Remove a random member if over limit
        r.spop(favorites_key)

    return bool(added)


def remove_favorite_city(session_id: str, city: str) -> bool:
    """Remove city from favorites."""
    r = get_redis()
    removed = r.srem(f"favorites:{session_id}", city.title())
    return bool(removed)


def get_favorite_cities(session_id: str) -> list[str]:
    """Get all favorite cities for this session."""
    r = get_redis()
    return list(r.smembers(f"favorites:{session_id}"))


def destroy_session(session_id: str) -> None:
    """Delete session and all associated data."""
    r = get_redis()
    r.delete(f"session:{session_id}")
    r.delete(f"favorites:{session_id}")
    r.delete(f"search:history:{session_id}")