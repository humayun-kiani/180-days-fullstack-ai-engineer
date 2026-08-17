# ============================================================
# app/rate_limiter.py
# Rate limiting utilities
# ============================================================

import asyncio
from collections import deque
from datetime import datetime, timedelta


class AsyncRateLimiter:
    """
    Async token bucket rate limiter.

    Allows burst up to max_calls, then enforces the rate limit.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self, max_calls: int = 10, period_seconds: float = 60.0):
        self.max_calls = max_calls
        self.period = period_seconds
        self._calls: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a call slot is available."""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.period)

            # Clear expired calls
            while self._calls and self._calls[0] < cutoff:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                # Calculate wait time
                oldest = self._calls[0]
                wait_until = oldest + timedelta(seconds=self.period)
                wait_seconds = (wait_until - now).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                # Clear again after waiting
                now = datetime.utcnow()
                cutoff = now - timedelta(seconds=self.period)
                while self._calls and self._calls[0] < cutoff:
                    self._calls.popleft()

            self._calls.append(datetime.utcnow())

    @property
    def available_calls(self) -> int:
        """Number of calls available right now."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.period)
        active = sum(1 for t in self._calls if t > cutoff)
        return max(0, self.max_calls - active)


# Pre-configured limiters for each API
RATE_LIMITERS = {
    "open_meteo": AsyncRateLimiter(max_calls=60, period_seconds=60),
    "github": AsyncRateLimiter(max_calls=30, period_seconds=60),
    "exchange_rate": AsyncRateLimiter(max_calls=10, period_seconds=60),
    "hackernews": AsyncRateLimiter(max_calls=60, period_seconds=60),
    "restcountries": AsyncRateLimiter(max_calls=60, period_seconds=60),
}