# backend/app/api/profile.py
# Performance profiling endpoints

import time
import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.deps import DB, CurrentUser
from app.profiling.query_profiler import profiler
from app.profiling.cache_analyzer import cache_analyzer
from app.models.task import Task

router = APIRouter(prefix="/profile", tags=["profiling"])


@router.get("/queries", summary="Recent SQL query performance")
async def query_profile(current_user: CurrentUser) -> dict:
    """Show slow queries and global query statistics."""
    return {
        "slow_queries": profiler.get_slow_queries(limit=10),
        "global_stats": profiler.get_global_stats(),
        "tip": "Queries taking > 100ms are flagged as slow"
    }


@router.get("/cache", summary="Cache hit rate analysis")
async def cache_profile(current_user: CurrentUser) -> dict:
    """Show cache effectiveness by key prefix."""
    return cache_analyzer.get_report()


@router.get("/n-plus-1-demo", summary="Demonstrate N+1 problem vs solution")
async def n_plus_1_demo(current_user: CurrentUser, db: DB) -> dict:
    """
    Benchmark N+1 vs eager loading on real data.

    Creates 10 tasks, then compares query approaches.
    """
    from app.models.user import User
    from sqlalchemy.orm import selectinload

    # Ensure we have some tasks
    result = await db.execute(
        select(func.count(Task.id)).where(Task.owner_id == current_user.id)
    )
    count = result.scalar_one()

    if count < 5:
        return {
            "message": "Create at least 5 tasks first to see meaningful results",
            "your_task_count": count
        }

    # ── Approach 1: Simulate N+1 (fetch tasks, then owners one by one) ──
    profiler.start_request()
    start = time.perf_counter()

    tasks_result = await db.execute(
        select(Task).where(Task.owner_id == current_user.id).limit(10)
    )
    tasks = list(tasks_result.scalars())

    # Simulate N+1: fetch owner for each task separately
    for task in tasks:
        await db.execute(select(User).where(User.id == task.owner_id))

    n_plus_1_ms = (time.perf_counter() - start) * 1000
    n_plus_1_summary = profiler.end_request()

    # ── Approach 2: Eager loading (selectinload) ──
    profiler.start_request()
    start = time.perf_counter()

    await db.execute(
        select(Task)
        .options(selectinload(Task.owner))
        .where(Task.owner_id == current_user.id)
        .limit(10)
    )

    eager_ms = (time.perf_counter() - start) * 1000
    eager_summary = profiler.end_request()

    speedup = round(n_plus_1_ms / max(eager_ms, 0.1), 1)

    return {
        "tasks_fetched": len(tasks),
        "n_plus_1": {
            "duration_ms": round(n_plus_1_ms, 2),
            "query_count": n_plus_1_summary["query_count"],
            "description": f"1 query for tasks + {len(tasks)} queries for owners"
        },
        "eager_loading": {
            "duration_ms": round(eager_ms, 2),
            "query_count": eager_summary["query_count"],
            "description": "2 queries total (1 for tasks + 1 for all owners)"
        },
        "improvement": {
            "speedup": f"{speedup}x faster",
            "queries_saved": n_plus_1_summary["query_count"] - eager_summary["query_count"],
            "ms_saved": round(n_plus_1_ms - eager_ms, 2)
        }
    }


@router.get("/benchmark/list-tasks", summary="Benchmark task listing strategies")
async def benchmark_list_tasks(current_user: CurrentUser, db: DB) -> dict:
    """
    Compare: no cache vs cache hit vs cache miss on task listing.
    """
    from app.services.cache_service import cache_get, cache_set, cache_delete

    cache_key = f"benchmark:tasks:{current_user.id}"

    # ── Baseline: direct DB query ──
    iterations = 5
    db_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await db.execute(
            select(Task)
            .where(Task.owner_id == current_user.id)
            .order_by(Task.created_at.desc())
            .limit(20)
        )
        db_times.append((time.perf_counter() - start) * 1000)

    avg_db = sum(db_times) / len(db_times)

    # ── With cache: populate ──
    tasks_result = await db.execute(
        select(Task).where(Task.owner_id == current_user.id).limit(20)
    )
    tasks_data = [{"id": str(t.id), "title": t.title} for t in tasks_result.scalars()]
    await cache_set(cache_key, tasks_data, ttl=60)

    # ── Cache HIT ──
    cache_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await cache_get(cache_key)
        cache_times.append((time.perf_counter() - start) * 1000)

    avg_cache = sum(cache_times) / len(cache_times)

    # Cleanup
    await cache_delete(cache_key)

    speedup = round(avg_db / max(avg_cache, 0.01), 1)

    return {
        "benchmark": "Task list: DB vs cache",
        "iterations": iterations,
        "results": {
            "direct_db": {
                "avg_ms": round(avg_db, 2),
                "min_ms": round(min(db_times), 2),
                "max_ms": round(max(db_times), 2)
            },
            "cache_hit": {
                "avg_ms": round(avg_cache, 2),
                "min_ms": round(min(cache_times), 2),
                "max_ms": round(max(cache_times), 2)
            }
        },
        "improvement": {
            "speedup": f"{speedup}x faster with cache",
            "ms_saved_per_request": round(avg_db - avg_cache, 2),
            "at_100_rps": f"Saves {round((avg_db - avg_cache) * 100, 0):.0f}ms/sec of DB time"
        },
        "note": "Add more tasks for more representative results"
    }


@router.get("/benchmark/search", summary="Benchmark search query performance")
async def benchmark_search(current_user: CurrentUser, db: DB) -> dict:
    """
    Compare: ILIKE search vs no search (full table scan cost).
    """
    from sqlalchemy import or_

    iterations = 3
    results = {}

    # Full list (no search)
    full_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await db.execute(
            select(Task)
            .where(Task.owner_id == current_user.id)
            .limit(20)
        )
        full_times.append((time.perf_counter() - start) * 1000)

    results["full_list"] = {
        "avg_ms": round(sum(full_times) / len(full_times), 2),
        "description": "No search filter"
    }

    # ILIKE search
    ilike_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await db.execute(
            select(Task)
            .where(
                Task.owner_id == current_user.id,
                or_(
                    Task.title.ilike("%fix%"),
                    Task.description.ilike("%fix%")
                )
            )
            .limit(20)
        )
        ilike_times.append((time.perf_counter() - start) * 1000)

    results["ilike_search"] = {
        "avg_ms": round(sum(ilike_times) / len(ilike_times), 2),
        "description": "ILIKE search on title + description"
    }

    return {
        "benchmark": "Search query strategies",
        "results": results,
        "recommendation": (
            "At < 10,000 rows: ILIKE is fast enough. "
            "At > 10,000 rows: add GIN tsvector index or use PostgreSQL FTS."
        )
    }


@router.get("/memory", summary="Process memory usage")
async def memory_usage(current_user: CurrentUser) -> dict:
    """Show current process memory consumption."""
    import os
    import resource
    import sys

    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname == "Linux":
        mem_mb = mem / 1024  # Linux: KB → MB
    else:
        mem_mb = mem / 1024 / 1024  # macOS: bytes → MB

    return {
        "process_memory_mb": round(mem_mb, 1),
        "python_version": sys.version.split()[0],
        "pid": os.getpid(),
        "assessment": (
            "healthy" if mem_mb < 200
            else "warning" if mem_mb < 500
            else "high"
        )
    }


@router.get("/recommendations", summary="Performance recommendations")
async def recommendations(current_user: CurrentUser, db: DB) -> dict:
    """
    Analyze current state and give specific optimization recommendations.
    """
    from sqlalchemy import inspect

    recs = []

    # Check task count for index recommendation
    result = await db.execute(
        select(func.count(Task.id)).where(Task.owner_id == current_user.id)
    )
    task_count = result.scalar_one()

    if task_count > 1000:
        recs.append({
            "priority": "high",
            "category": "database",
            "issue": f"You have {task_count} tasks — make sure composite index exists",
            "fix": "CREATE INDEX idx_tasks_owner_created ON tasks(owner_id, created_at DESC)",
            "impact": "50-100x faster for task listing queries"
        })

    if task_count == 0:
        recs.append({
            "priority": "info",
            "category": "data",
            "issue": "No tasks yet — create tasks to see performance data",
            "fix": "POST /api/tasks with various priorities",
            "impact": "Enables meaningful benchmark results"
        })

    # Cache recommendations from analyzer
    cache_report = cache_analyzer.get_report()
    global_stats = cache_report.get("global", {})
    if global_stats.get("hits", 0) + global_stats.get("misses", 0) > 0:
        hit_rate = global_stats.get("hit_rate_pct", 0)
        if hit_rate < 50:
            recs.append({
                "priority": "medium",
                "category": "caching",
                "issue": f"Cache hit rate is {hit_rate}% (target: > 70%)",
                "fix": "Increase TTL for task lists or add cache warming",
                "impact": "Reduce DB load by 2-3x"
            })
        else:
            recs.append({
                "priority": "info",
                "category": "caching",
                "issue": f"Cache hit rate is {hit_rate}% — performing well",
                "fix": "No action needed",
                "impact": "Continue monitoring"
            })

    # Slow query recommendations
    slow = profiler.get_slow_queries(5)
    if slow:
        recs.append({
            "priority": "high",
            "category": "database",
            "issue": f"{len(slow)} slow queries detected (> 100ms)",
            "fix": "Run EXPLAIN ANALYZE on the queries shown at /profile/queries",
            "impact": "Potentially 10-100x improvement with proper indexes"
        })

    if not recs:
        recs.append({
            "priority": "info",
            "category": "general",
            "issue": "No critical issues detected",
            "fix": "Run load tests with Locust to find bottlenecks under load",
            "impact": "Proactive optimization"
        })

    return {
        "task_count": task_count,
        "recommendations": sorted(
            recs, key=lambda r: {"high": 0, "medium": 1, "info": 2}[r["priority"]]
        ),
        "next_steps": [
            "GET /profile/n-plus-1-demo — see N+1 vs eager loading",
            "GET /profile/benchmark/list-tasks — cache vs DB comparison",
            "cd load_tests && locust -f locustfile.py — load test"
        ]
    }