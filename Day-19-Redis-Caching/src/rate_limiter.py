# ============================================================
# src/rate_limiter.py
# Redis-based rate limiting
# ============================================================

import os
import time
from dataclasses import dataclass
from dotenv import load_dotenv
from src.redis_client import get_redis

load_dotenv()

RATE_LIMIT = int(os.environ.get("RATE_LIMIT_REQUESTS", 20))
RATE_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))


@dataclass
class RateLimitResult:
    allowed: bool
    requests_made: int
    limit: int
    remaining: int
    window_seconds: int
    reset_in_seconds: int


def check_rate_limit(
    identifier: str,
    limit: int = None,
    window: int = None
) -> RateLimitResult:
    """
    Fixed window rate limiter using Redis INCR and EXPIRE.

    Algorithm:
    1. Increment a counter for this identifier
    2. If first request, set expiry for the window
    3. If counter exceeds limit, reject request

    Args:
        identifier: Unique identifier (user ID, IP, API key)
        limit: Max requests per window (default from env)
        window: Window size in seconds (default from env)

    Returns:
        RateLimitResult with allow/deny decision and metadata
    """
    r = get_redis()
    limit = limit or RATE_LIMIT
    window = window or RATE_WINDOW
    key = f"rate_limit:{identifier}"

    # Atomic increment
    current = r.incr(key)

    # Set expiry only on first request in window
    if current == 1:
        r.expire(key, window)

    ttl = r.ttl(key)

    return RateLimitResult(
        allowed=current <= limit,
        requests_made=current,
        limit=limit,
        remaining=max(0, limit - current),
        window_seconds=window,
        reset_in_seconds=ttl if ttl > 0 else 0
    )


def get_rate_limit_status(identifier: str) -> dict:
    """Get current rate limit status without incrementing."""
    r = get_redis()
    key = f"rate_limit:{identifier}"
    current = int(r.get(key) or 0)
    ttl = r.ttl(key)

    return {
        "identifier": identifier,
        "requests_in_window": current,
        "limit": RATE_LIMIT,
        "remaining": max(0, RATE_LIMIT - current),
        "reset_in_seconds": ttl if ttl > 0 else RATE_WINDOW
    }


def reset_rate_limit(identifier: str) -> None:
    """Reset rate limit for an identifier (admin use)."""
    get_redis().delete(f"rate_limit:{identifier}")