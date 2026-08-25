# ============================================================
# app/cache.py
# Multi-layer cache: L1 (in-process) + L2 (simulated Redis)
# ============================================================

import json
import time
import asyncio
import random
import math
from typing import Any, Optional
from dataclasses import dataclass, field


# ─── Mock Redis (in-process simulation) ──────────────────────

class MockRedis:
    """
    Simulates Redis with realistic latency (~1ms).
    Use real Redis in production: pip install redis
    """

    def __init__(self):
        self._store: dict[str, tuple[str, float]] = {}  # key → (value, expires_at)
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    async def get(self, key: str) -> str | None:
        await asyncio.sleep(0.001)    # 1ms Redis latency
        entry = self._store.get(key)
        if entry:
            value, expires_at = entry
            if time.monotonic() < expires_at:
                self._stats["hits"] += 1
                return value
            del self._store[key]
        self._stats["misses"] += 1
        return None

    async def setex(self, key: str, ttl: int, value: str) -> None:
        await asyncio.sleep(0.001)
        self._store[key] = (value, time.monotonic() + ttl)
        self._stats["sets"] += 1

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                count += 1
        self._stats["deletes"] += count
        return count

    async def delete_pattern(self, prefix: str) -> int:
        await asyncio.sleep(0.002)    # Pattern delete is slightly slower
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        self._stats["deletes"] += len(keys)
        return len(keys)

    async def exists(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry:
            _, expires_at = entry
            return time.monotonic() < expires_at
        return False

    async def set_nx(self, key: str, value: str, ttl: int) -> bool:
        """SET if Not eXists — used for distributed locks."""
        await asyncio.sleep(0.001)
        if key in self._store:
            _, expires_at = self._store[key]
            if time.monotonic() < expires_at:
                return False    # Key exists and not expired
        self._store[key] = (value, time.monotonic() + ttl)
        return True

    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            **self._stats,
            "total_ops": total,
            "hit_rate": round(hit_rate, 3),
            "keys_stored": len(self._store)
        }


# ─── L1: In-Process Cache ─────────────────────────────────────

@dataclass
class L1Entry:
    value: Any
    expires_at: float
    hits: int = 0


class L1Cache:
    """
    In-process LRU cache.
    Fastest possible reads (~microseconds).
    Limited to one process — not shared between instances.
    """

    def __init__(self, max_size: int = 500, default_ttl: int = 10):
        self._store: dict[str, L1Entry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry:
            if time.monotonic() < entry.expires_at:
                entry.hits += 1
                self._stats["hits"] += 1
                return entry.value
            del self._store[key]
        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self._default_ttl
        if len(self._store) >= self._max_size:
            self._evict()
        self._store[key] = L1Entry(
            value=value,
            expires_at=time.monotonic() + ttl
        )

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def delete_prefix(self, prefix: str) -> int:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def _evict(self) -> None:
        """Evict the least-recently-used entry."""
        if not self._store:
            return
        lru_key = min(self._store, key=lambda k: self._store[k].hits)
        del self._store[lru_key]
        self._stats["evictions"] += 1

    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "hit_rate": round(self._stats["hits"] / total, 3) if total > 0 else 0,
            "size": len(self._store),
            "max_size": self._max_size
        }


# ─── Multi-Layer Cache ────────────────────────────────────────

class MultiLayerCache:
    """
    Production-style multi-layer cache.

    L1 (in-process, 10s TTL) → L2 (Redis, 300s TTL) → DB

    Features:
    - Automatic L1 population from L2 hits
    - Cache stampede protection via distributed lock
    - TTL jitter to prevent thundering herd
    - Comprehensive hit/miss statistics
    """

    def __init__(self, redis: MockRedis):
        self.l1 = L1Cache(max_size=500, default_ttl=10)
        self.l2 = redis
        self._jitter_pct = 0.1    # ±10% TTL jitter

    def _jitter(self, ttl: int) -> int:
        """Add random jitter to TTL to spread cache expiry."""
        jitter = int(ttl * self._jitter_pct)
        return ttl + random.randint(-jitter, jitter)

    async def get(self, key: str) -> Any:
        """Get from L1 → L2 → None."""
        # L1 check (microseconds)
        val = self.l1.get(key)
        if val is not None:
            return val

        # L2 check (milliseconds)
        raw = await self.l2.get(key)
        if raw:
            val = json.loads(raw)
            self.l1.set(key, val)    # populate L1 from L2
            return val

        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set in both L1 and L2."""
        ttl_jittered = self._jitter(ttl)
        serialized = json.dumps(value, default=str)
        self.l1.set(key, value, min(ttl, 10))
        await self.l2.setex(key, ttl_jittered, serialized)

    async def delete(self, key: str) -> None:
        """Delete from all layers."""
        self.l1.delete(key)
        await self.l2.delete(key)

    async def delete_prefix(self, prefix: str) -> None:
        """Delete all keys with prefix from all layers."""
        self.l1.delete_prefix(prefix)
        await self.l2.delete_pattern(prefix)

    async def get_or_set(
        self,
        key: str,
        fetch_fn,
        ttl: int = 300
    ) -> Any:
        """
        Cache-aside pattern in one call.

        If key in cache: return cached value
        If not: call fetch_fn(), cache the result, return it
        """
        val = await self.get(key)
        if val is not None:
            return val

        # Stampede protection: acquire lock before fetching
        lock_key = f"__lock:{key}"
        lock_acquired = await self.l2.set_nx(lock_key, "1", ttl=10)

        if lock_acquired:
            try:
                val = await fetch_fn()
                if val is not None:
                    await self.set(key, val, ttl)
                return val
            finally:
                await self.l2.delete(lock_key)
        else:
            # Wait for lock holder to populate cache
            for _ in range(20):    # up to 2 seconds
                await asyncio.sleep(0.1)
                val = await self.get(key)
                if val is not None:
                    return val
            # Fallback: fetch directly
            return await fetch_fn()

    def stats(self) -> dict:
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats()
        }