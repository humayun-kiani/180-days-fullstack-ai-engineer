# sample_code/good_code.py
"""
User data management module.

Provides clean, typed, and well-documented functions for
fetching and processing user data with proper error handling.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class User:
    """Represents a user entity."""
    id: int
    name: str
    email: str
    created_at: str


class UserServiceError(Exception):
    """Raised when user service operations fail."""
    pass


class UserCache:
    """Simple in-memory cache for user data with TTL support."""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: dict[int, tuple[User, float]] = {}
        self._ttl = ttl_seconds

    def get(self, user_id: int) -> Optional[User]:
        """Return cached user if not expired."""
        import time
        if user_id in self._cache:
            user, timestamp = self._cache[user_id]
            if time.time() - timestamp < self._ttl:
                return user
            del self._cache[user_id]
        return None

    def set(self, user: User) -> None:
        """Cache a user with current timestamp."""
        import time
        self._cache[user.id] = (user, time.time())


async def fetch_user(
    user_id: int,
    api_base_url: str,
    api_token: str,
    cache: Optional[UserCache] = None,
    timeout: float = 10.0
) -> Optional[User]:
    """
    Fetch a user by ID from the API.

    Args:
        user_id: The user's unique identifier.
        api_base_url: Base URL for the user API.
        api_token: Bearer token for authentication.
        cache: Optional cache instance for performance.
        timeout: Request timeout in seconds.

    Returns:
        User if found, None if not found.

    Raises:
        UserServiceError: On network errors or unexpected API responses.
    """
    # Check cache first
    if cache is not None:
        cached = cache.get(user_id)
        if cached is not None:
            logger.debug("Cache hit for user %d", user_id)
            return cached

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{api_base_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {api_token}"}
            )

        if response.status_code == 404:
            logger.info("User %d not found", user_id)
            return None

        response.raise_for_status()
        data = response.json()

        user = User(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            created_at=data["created_at"]
        )

        if cache is not None:
            cache.set(user)

        return user

    except httpx.TimeoutException as exc:
        raise UserServiceError(f"Request timed out fetching user {user_id}") from exc
    except httpx.HTTPStatusError as exc:
        raise UserServiceError(
            f"API returned {exc.response.status_code} for user {user_id}"
        ) from exc


def find_duplicates(items: list) -> list:
    """
    Find duplicate items in a list efficiently.

    Uses a set for O(n) time complexity instead of O(n²).

    Args:
        items: List to search for duplicates.

    Returns:
        List of items that appear more than once.
    """
    seen: set = set()
    duplicates: set = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)

    return sorted(duplicates)


def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    """
    Divide two numbers safely, returning None on division by zero.

    Args:
        numerator: The number to divide.
        denominator: The number to divide by.

    Returns:
        Result of division, or None if denominator is zero.
    """
    if denominator == 0:
        logger.warning("Attempted division by zero: %f / %f", numerator, denominator)
        return None
    return numerator / denominator