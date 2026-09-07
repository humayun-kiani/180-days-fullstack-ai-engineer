# backend/app/services/cache_service.py
import json
from typing import Any, Optional
import redis.asyncio as aioredis

from app.core.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        await r.delete(key)
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception:
        pass