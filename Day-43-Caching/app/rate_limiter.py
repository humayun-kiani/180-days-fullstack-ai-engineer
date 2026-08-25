# ============================================================
# app/rate_limiter.py
# Sliding window rate limiter using in-memory sorted sets
# ============================================================

import time
import uuid
from collections import defaultdict


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    Maintains a sorted set of request timestamps per client.
    Requests older than window_seconds are removed on each check.
    """

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._total_limited = 0

    def check(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if client is rate limited.

        Returns: (is_limited, info_dict)
        """
        now = time.monotonic()
        window_start = now - self.window_seconds

        # Remove old entries
        window = self._windows[client_id]
        self._windows[client_id] = [t for t in window if t > window_start]
        current = len(self._windows[client_id])

        if current >= self.max_requests:
            self._total_limited += 1
            oldest = self._windows[client_id][0] if self._windows[client_id] else now
            reset_in = oldest + self.window_seconds - now
            return True, {
                "limited": True,
                "current": current,
                "limit": self.max_requests,
                "reset_in_seconds": round(reset_in, 1),
                "retry_after": int(reset_in) + 1
            }

        self._windows[client_id].append(now)
        remaining = self.max_requests - current - 1

        return False, {
            "limited": False,
            "current": current + 1,
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_in_seconds": self.window_seconds
        }

    def stats(self) -> dict:
        return {
            "active_clients": len(self._windows),
            "total_limited": self._total_limited,
            "config": {
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds
            }
        }