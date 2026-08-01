# ============================================================
# app/core/token_blacklist.py
# Redis-based JWT token blacklist for logout functionality
# ============================================================

import redis
from typing import Optional
from app.core.config import settings

# Redis client for token blacklist
# Uses a separate Redis DB (DB=1) from the cache (DB=0)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2
            )
            _redis_client.ping()    # test connection
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None    # Redis not available — graceful fallback
    return _redis_client


def revoke_token(jti: str, expires_in_seconds: int) -> bool:
    """
    Add a token JTI (JWT ID) to the blacklist.

    The key expires at the same time as the token would have,
    so the blacklist is self-cleaning.

    Args:
        jti: Unique JWT token ID from the token payload.
        expires_in_seconds: How long until the blacklist entry expires.

    Returns:
        bool: True if successfully added to blacklist.
    """
    r = get_redis_client()
    if r is None:
        return False    # Redis not available — can't revoke

    try:
        r.setex(f"revoked_token:{jti}", max(expires_in_seconds, 1), "1")
        return True
    except redis.RedisError:
        return False


def is_token_revoked(jti: str) -> bool:
    """
    Check if a token has been revoked (is in the blacklist).

    Args:
        jti: Unique JWT token ID.

    Returns:
        bool: True if token is revoked, False if valid or Redis unavailable.
    """
    r = get_redis_client()
    if r is None:
        return False    # Redis not available — assume valid

    try:
        return bool(r.exists(f"revoked_token:{jti}"))
    except redis.RedisError:
        return False    # fail open — don't deny on Redis error


def clear_user_tokens(user_id: int) -> None:
    """
    Utility to revoke all tokens for a user.
    Requires storing user→token mapping (not implemented here).
    In production: store token JTIs per user in a Redis set.
    """
    pass    # left as a production enhancement exercise