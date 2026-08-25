# ============================================================
# app/main.py
# High-Performance Task API with Multi-Layer Caching
# Day 43 — Caching Strategies & Performance Architecture
# ============================================================

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.cache import MultiLayerCache, MockRedis
from app.database import (
    db_get_task, db_list_tasks, db_create_task,
    db_update_task, db_delete_task, db_get_stats,
    db_query_stats, seed_database, reset_stats
)
from app.rate_limiter import SlidingWindowRateLimiter
from app.metrics import PerformanceMetrics, RequestRecord


# ─── Global services ──────────────────────────────────────────

_redis = MockRedis()
_cache = MultiLayerCache(_redis)
_rate_limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)
_metrics = PerformanceMetrics()

# TTL constants
TTL_TASK = 300         # 5 minutes for individual tasks
TTL_LIST = 60          # 1 minute for task lists
TTL_STATS = 600        # 10 minutes for aggregated stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 65)
    print("  High-Performance Task API — Day 43")
    print("  Caching Strategies & Performance Architecture")
    print("=" * 65)

    print("\n  Seeding database with 20 demo tasks...")
    seed_database(20)

    print("  Cache layers: L1 (in-process, 10s) → L2 (Redis mock, 300s)")
    print("  Rate limit: 100 requests/minute per client")
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Final cache stats:")
    stats = _cache.stats()
    print(f"    L1: {stats['l1']}")
    print(f"    L2: {stats['l2']}")
    print("\n  Shutting down...")


app = FastAPI(
    title="High-Performance Task API",
    description="""
## ⚡ High-Performance Task API — Day 43

Multi-layer caching with performance metrics.

### Cache Architecture

### Performance Targets
| Endpoint | With Cache | Without Cache |
|----------|-----------|---------------|
| GET /tasks/{id} | < 2ms | 30-80ms |
| GET /tasks | < 5ms | 50-100ms |
| GET /stats | < 2ms | 50ms |

### Cache Headers
Every response includes:
- `X-Cache`: HIT-L1, HIT-L2, or MISS
- `X-Response-Time-Ms`: actual latency
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Middleware ───────────────────────────────────────────────

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Track latency and add cache headers."""
    start = time.perf_counter()
    response = await call_next(request)
    latency = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time-Ms"] = str(round(latency, 2))
    return response


def rate_limit_check(request: Request) -> None:
    """Apply rate limiting per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    limited, info = _rate_limiter.check(client_ip)
    if limited:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests",
                "retry_after": info.get("retry_after", 60)
            }
        )


# ─── Schemas ─────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(urgent|high|medium|low)$")
    tags: list[str] = Field(default=[])
    created_by: str = Field(default="anonymous")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Fix login bug before Friday demo",
                "priority": "high",
                "created_by": "humayun"
            }
        }


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(urgent|high|medium|low)$")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|done)$")
    tags: Optional[list[str]] = None


# ─── Read Endpoints (cached) ──────────────────────────────────

@app.get(
    "/tasks/{task_id}",
    summary="Get task — L1 then L2 then DB"
)
async def get_task(task_id: str, request: Request, response: Response) -> dict:
    """
    Get a task. Checks L1 cache → L2 cache → database.

    First request: ~50ms (DB).
    Subsequent requests: <2ms (cache).
    """
    rate_limit_check(request)
    start = time.perf_counter()

    # Check L1
    val = _cache.l1.get(f"task:{task_id}")
    if val is not None:
        response.headers["X-Cache"] = "HIT-L1"
        latency = (time.perf_counter() - start) * 1000
        _metrics.record(RequestRecord("/tasks/{id}", "GET", latency, True, "L1", 200))
        return {"task": val, "cache": "L1", "latency_ms": round(latency, 2)}

    # Check L2
    raw = await _cache.l2.get(f"task:{task_id}")
    if raw:
        import json
        val = json.loads(raw)
        _cache.l1.set(f"task:{task_id}", val)    # promote to L1
        response.headers["X-Cache"] = "HIT-L2"
        latency = (time.perf_counter() - start) * 1000
        _metrics.record(RequestRecord("/tasks/{id}", "GET", latency, True, "L2", 200))
        return {"task": val, "cache": "L2", "latency_ms": round(latency, 2)}

    # DB fetch
    task = await db_get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    await _cache.set(f"task:{task_id}", task, ttl=TTL_TASK)
    response.headers["X-Cache"] = "MISS"
    latency = (time.perf_counter() - start) * 1000
    _metrics.record(RequestRecord("/tasks/{id}", "GET", latency, False, None, 200))
    return {"task": task, "cache": "MISS", "latency_ms": round(latency, 2)}


@app.get(
    "/tasks",
    summary="List tasks — cached list query"
)
async def list_tasks(
    request: Request,
    response: Response,
    status: str = "all",
    priority: str = "all",
    limit: int = 50
) -> dict:
    """List tasks with caching. Cache key includes query params."""
    rate_limit_check(request)
    start = time.perf_counter()

    cache_key = f"tasks:list:{status}:{priority}:{limit}"

    async def fetch():
        return await db_list_tasks(status, priority, limit)

    tasks = await _cache.get_or_set(cache_key, fetch, ttl=TTL_LIST)
    cache_status = "HIT" if _redis.stats()["hits"] > 0 else "MISS"
    response.headers["X-Cache"] = cache_status

    latency = (time.perf_counter() - start) * 1000
    return {
        "tasks": tasks,
        "total": len(tasks),
        "cache_key": cache_key,
        "latency_ms": round(latency, 2)
    }


@app.get(
    "/stats",
    summary="Aggregated stats — long TTL cache"
)
async def get_task_stats(request: Request, response: Response) -> dict:
    """
    Expensive aggregation query — cached for 10 minutes.
    Shows how to cache compute-heavy operations.
    """
    rate_limit_check(request)
    start = time.perf_counter()

    async def compute():
        return await db_get_stats()

    stats = await _cache.get_or_set("tasks:stats", compute, ttl=TTL_STATS)
    latency = (time.perf_counter() - start) * 1000
    return {
        "stats": stats,
        "cache_ttl": TTL_STATS,
        "latency_ms": round(latency, 2)
    }


# ─── Write Endpoints (invalidate cache) ──────────────────────

@app.post(
    "/tasks",
    status_code=201,
    summary="Create task — invalidates list caches"
)
async def create_task(body: CreateTaskRequest, request: Request) -> dict:
    """
    Create task and invalidate all list caches.

    Individual task caches don't need invalidation (new task has no cache yet).
    List caches must be invalidated because the new task would appear in them.
    """
    rate_limit_check(request)
    task = await db_create_task(body.model_dump())

    # Invalidate list caches (new task changes all lists)
    await _cache.delete_prefix("tasks:list:")
    await _cache.delete("tasks:stats")

    return {
        "task": task,
        "cache_action": "invalidated tasks:list:* and tasks:stats"
    }


@app.patch(
    "/tasks/{task_id}",
    summary="Update task — invalidates specific task + list caches"
)
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    request: Request
) -> dict:
    """Update task. Invalidates the specific task cache and all list caches."""
    rate_limit_check(request)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    task = await db_update_task(task_id, updates)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    # Invalidate this specific task's cache
    await _cache.delete(f"task:{task_id}")
    # Invalidate all list caches (task's fields may have changed filters)
    await _cache.delete_prefix("tasks:list:")
    await _cache.delete("tasks:stats")

    return {
        "task": task,
        "cache_action": f"invalidated task:{task_id} and tasks:list:*"
    }


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete task — invalidates caches"
)
async def delete_task(task_id: str, request: Request):
    """Delete task. Invalidates task cache and all list caches."""
    rate_limit_check(request)
    deleted = await db_delete_task(task_id)
    if not deleted:
        raise HTTPException(404, f"Task '{task_id}' not found")

    await _cache.delete(f"task:{task_id}")
    await _cache.delete_prefix("tasks:list:")
    await _cache.delete("tasks:stats")


# ─── Cache Management Endpoints ───────────────────────────────

@app.delete("/cache", summary="Clear all caches")
async def clear_cache() -> dict:
    """Manually clear all cache layers."""
    _cache.l1._store.clear()
    _cache.l2._store.clear()
    return {"message": "All caches cleared"}


@app.delete("/cache/{prefix}", summary="Clear cache by prefix")
async def clear_cache_prefix(prefix: str) -> dict:
    """Clear cache entries matching a prefix."""
    n = _cache.l1.delete_prefix(prefix)
    n2 = await _cache.l2.delete_pattern(prefix)
    return {"message": f"Cleared {n + n2} cache entries", "prefix": prefix}


# ─── Performance Dashboard ────────────────────────────────────

@app.get("/performance", summary="Cache and DB performance metrics")
def get_performance() -> dict:
    """
    Real-time performance dashboard.

    Shows cache hit rates, latency percentiles, DB query count.
    Use this to verify caching is working correctly.
    """
    return {
        "cache": _cache.stats(),
        "database": db_query_stats(),
        "requests": _metrics.summary(),
        "rate_limiter": _rate_limiter.stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/benchmark", summary="Run a quick performance benchmark")
async def run_benchmark(n_requests: int = 50) -> dict:
    """
    Benchmark cached vs uncached performance.

    Makes n requests against the same task to demonstrate cache speedup.
    """
    if n_requests > 200:
        raise HTTPException(400, "Max 200 requests for benchmark")

    # Get a task to benchmark
    from app.database import _TASKS
    if not _TASKS:
        raise HTTPException(400, "No tasks in database. Seed first.")

    task_id = list(_TASKS.keys())[0]
    reset_stats()

    # Clear cache for fair benchmark
    await _cache.delete(f"task:{task_id}")

    latencies_uncached = []
    latencies_cached = []

    # First request (cache miss — DB)
    start = time.perf_counter()
    await db_get_task(task_id)
    latencies_uncached.append((time.perf_counter() - start) * 1000)

    # Populate cache
    task = await db_get_task(task_id)
    await _cache.set(f"task:{task_id}", task, ttl=TTL_TASK)

    # Subsequent requests (cache hits)
    for _ in range(min(n_requests - 1, 49)):
        start = time.perf_counter()
        val = _cache.l1.get(f"task:{task_id}")
        if val is None:
            raw = await _cache.l2.get(f"task:{task_id}")
        latencies_cached.append((time.perf_counter() - start) * 1000)

    import statistics as st
    avg_uncached = st.mean(latencies_uncached) if latencies_uncached else 0
    avg_cached = st.mean(latencies_cached) if latencies_cached else 0
    speedup = avg_uncached / avg_cached if avg_cached > 0 else float("inf")

    return {
        "task_id": task_id,
        "n_requests": n_requests,
        "avg_latency_ms": {
            "cache_miss_db": round(avg_uncached, 2),
            "cache_hit": round(avg_cached, 3),
            "speedup": f"{speedup:.0f}x"
        },
        "db_queries": db_query_stats()["total_queries"],
        "cache_stats": _cache.stats()
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "cache_layers": {
            "l1": "in-process (10s TTL)",
            "l2": "redis-mock (300s TTL)"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 43 — Caching Strategies"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "High-Performance Task API",
        "day": "Day 43 — Caching Strategies & Performance Architecture",
        "docs": "/docs",
        "performance": "/performance",
        "endpoints": {
            "get_task": "GET /tasks/{id}",
            "list_tasks": "GET /tasks",
            "stats": "GET /stats",
            "create": "POST /tasks",
            "update": "PATCH /tasks/{id}",
            "benchmark": "POST /benchmark",
            "performance": "GET /performance",
            "clear_cache": "DELETE /cache"
        }
    }