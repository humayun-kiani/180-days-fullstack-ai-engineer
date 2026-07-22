# ============================================================
# src/cache.py
# Redis cache operations
# ============================================================

import json
import os
import redis
from typing import Optional, Any


# Redis connection
REDIS_URL = (
    f"redis://"
    f"{os.environ.get('REDIS_HOST', 'localhost')}:"
    f"{os.environ.get('REDIS_PORT', '6379')}/"
    f"{os.environ.get('REDIS_DB', '0')}"
)


def get_redis_client():
    """Get Redis client with connection pooling."""
    return redis.from_url(
        REDIS_URL,
        decode_responses=True,    # return strings instead of bytes
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )


def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from Redis cache.

    Args:
        key (str): Cache key.

    Returns:
        The cached value (deserialized from JSON), or None if not found.
    """
    try:
        client = get_redis_client()
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"Cache GET error for key '{key}': {e}")
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """
    Store a value in Redis cache.

    Args:
        key (str): Cache key.
        value: Value to cache (must be JSON serializable).
        ttl_seconds (int): Time to live in seconds (default: 5 minutes).

    Returns:
        bool: True if stored successfully.
    """
    try:
        client = get_redis_client()
        serialized = json.dumps(value, default=str)
        client.setex(key, ttl_seconds, serialized)
        return True
    except (redis.RedisError, TypeError) as e:
        print(f"Cache SET error for key '{key}': {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete a key from cache."""
    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except redis.RedisError as e:
        print(f"Cache DELETE error for key '{key}': {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern. Returns count deleted."""
    try:
        client = get_redis_client()
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except redis.RedisError as e:
        print(f"Cache DELETE PATTERN error for '{pattern}': {e}")
        return 0


def is_redis_available() -> bool:
    """Check if Redis is reachable."""
    try:
        client = get_redis_client()
        return client.ping()
    except redis.RedisError:
        return False


# Cache key constants
CACHE_KEYS = {
    "all_expenses": "expenses:all",
    "expense": lambda id: f"expenses:{id}",
    "budget": "budget:current",
    "stats": "expenses:stats",
    "category": lambda cat: f"expenses:category:{cat.lower()}",
}