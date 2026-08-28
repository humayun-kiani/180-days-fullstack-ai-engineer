# ============================================================
# app/optimizer.py
# Query optimization demos — before and after comparisons
# ============================================================

import asyncio
import time
from app.database import db
from app.profiler import profiler


async def run_before_optimization() -> dict:
    """
    Run a realistic query workload WITHOUT indexes.
    Captures baseline performance.
    """
    profiler.reset()
    db.reset_logs()

    print("\n  Running 10 queries WITHOUT indexes...")
    start = time.perf_counter()

    # Query 1: Filter by status (common operation)
    results, plan = await db.execute(
        "get_pending_tasks",
        "tasks",
        filters={"status": "pending"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    # Query 2: Filter by priority
    results, plan = await db.execute(
        "get_urgent_tasks",
        "tasks",
        filters={"priority": "urgent"},
        limit=50
    )
    profiler.record(plan)

    # Query 3: Filter by status AND priority
    results, plan = await db.execute(
        "get_pending_high_tasks",
        "tasks",
        filters={"status": "pending", "priority": "high"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    # Query 4: Filter by owner
    results, plan = await db.execute(
        "get_user_tasks",
        "tasks",
        filters={"owner_id": "user-042"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    # Query 5: N+1 join
    task_results, task_plan = await db.execute(
        "list_tasks_for_join",
        "tasks",
        limit=50
    )
    profiler.record(task_plan)
    _, join_info = await db.execute_with_join(task_results, "n_plus_1")

    # Repeat queries 1-4 a few times (simulate traffic)
    for _ in range(5):
        await db.execute("get_pending_tasks", "tasks",
                        filters={"status": "pending"}, limit=20)

    elapsed = (time.perf_counter() - start) * 1000

    stats = profiler.overall_stats()
    slow = profiler.top_slow_queries(5)
    recommendations = profiler.index_recommendations()

    return {
        "phase": "BEFORE optimization",
        "total_time_ms": round(elapsed, 1),
        "stats": stats,
        "top_slow_queries": slow,
        "index_recommendations": recommendations,
        "join_info": join_info
    }


async def run_after_optimization() -> dict:
    """
    Run the same workload WITH indexes.
    Shows improvement.
    """
    from app.indexes import apply_optimized_indexes
    apply_optimized_indexes()

    profiler.reset()
    db.reset_logs()

    print("\n  Running 10 queries WITH indexes...")
    start = time.perf_counter()

    # Same queries as before
    results, plan = await db.execute(
        "get_pending_tasks",
        "tasks",
        filters={"status": "pending"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    results, plan = await db.execute(
        "get_urgent_tasks",
        "tasks",
        filters={"priority": "urgent"},
        limit=50
    )
    profiler.record(plan)

    results, plan = await db.execute(
        "get_pending_high_tasks",
        "tasks",
        filters={"status": "pending", "priority": "high"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    results, plan = await db.execute(
        "get_user_tasks",
        "tasks",
        filters={"owner_id": "user-042"},
        order_by="-created_at",
        limit=20
    )
    profiler.record(plan)

    # Optimized join
    task_results, task_plan = await db.execute(
        "list_tasks_for_join",
        "tasks",
        limit=50
    )
    profiler.record(task_plan)
    _, join_info = await db.execute_with_join(task_results, "batch")

    for _ in range(5):
        await db.execute("get_pending_tasks", "tasks",
                        filters={"status": "pending"}, limit=20)

    elapsed = (time.perf_counter() - start) * 1000

    stats = profiler.overall_stats()
    return {
        "phase": "AFTER optimization",
        "total_time_ms": round(elapsed, 1),
        "stats": stats,
        "indexes_applied": db.list_indexes(),
        "join_info": join_info
    }