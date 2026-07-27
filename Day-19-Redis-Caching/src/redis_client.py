# ============================================================
# src/redis_client.py
# Redis connection management and low-level utilities
# ============================================================

import os
import json
import redis
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()


# ─── Connection Pool ────────────────────────────────────────

def create_redis_client() -> redis.Redis:
    """
    Create a Redis client with connection pooling.

    Uses environment variables for configuration.

    Returns:
        redis.Redis: Configured Redis client.
    """
    pool = redis.ConnectionPool(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        db=int(os.environ.get("REDIS_DB", 0)),
        password=os.environ.get("REDIS_PASSWORD") or None,
        max_connections=20,
        decode_responses=True,          # always return str, not bytes
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    return redis.Redis(connection_pool=pool)


# Global client instance
_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Get or create the Redis client singleton."""
    global _client
    if _client is None:
        _client = create_redis_client()
    return _client


# ─── Connection Testing ─────────────────────────────────────

def test_connection() -> dict:
    """Test Redis connectivity and return server info."""
    try:
        r = get_redis()
        info = r.info()
        return {
            "success": True,
            "version": info["redis_version"],
            "uptime_hours": round(info["uptime_in_seconds"] / 3600, 1),
            "used_memory": info["used_memory_human"],
            "connected_clients": info["connected_clients"],
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "total_keys": r.dbsize()
        }
    except redis.ConnectionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Generic Cache Helpers ──────────────────────────────────

def cache_get(key: str) -> Optional[Any]:
    """
    Get a JSON-serialized value from Redis.

    Returns:
        Deserialized Python object, or None if not found.
    """
    try:
        r = get_redis()
        value = r.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (redis.RedisError, json.JSONDecodeError):
        return None


def cache_set(key: str, value: Any, ttl: int) -> bool:
    """
    Store a JSON-serialized value in Redis with TTL.

    Args:
        key: Redis key.
        value: Python object (must be JSON serializable).
        ttl: Time-to-live in seconds.

    Returns:
        bool: True if stored successfully.
    """
    try:
        r = get_redis()
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        return bool(r.setex(key, ttl, serialized))
    except (redis.RedisError, TypeError):
        return False


def cache_delete(key: str) -> bool:
    """Delete a key from Redis."""
    try:
        return bool(get_redis().delete(key))
    except redis.RedisError:
        return False


def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern. Returns count deleted."""
    try:
        r = get_redis()
        keys = r.keys(pattern)
        if keys:
            return r.delete(*keys)
        return 0
    except redis.RedisError:
        return 0


def cache_exists(key: str) -> bool:
    """Check if a key exists."""
    try:
        return bool(get_redis().exists(key))
    except redis.RedisError:
        return False


def cache_ttl(key: str) -> int:
    """Get remaining TTL for a key (-1 = no expiry, -2 = not found)."""
    try:
        return get_redis().ttl(key)
    except redis.RedisError:
        return -2


def flush_all_cache() -> bool:
    """Flush the entire Redis database."""
    try:
        get_redis().flushdb()
        return True
    except redis.RedisError:
        return False