# ============================================================
# app/database.py
# Simulated database with realistic latency
# ============================================================

import asyncio
import uuid
import random
from datetime import datetime
from typing import Optional


# In-memory "database"
_TASKS: dict[str, dict] = {}
_QUERY_COUNT = 0
_QUERY_LATENCY_MS: list[float] = []


def _get_query_count() -> int:
    return _QUERY_COUNT


def reset_stats():
    global _QUERY_COUNT, _QUERY_LATENCY_MS
    _QUERY_COUNT = 0
    _QUERY_LATENCY_MS = []


async def _simulate_db_latency():
    """Simulate realistic database latency (30-80ms)."""
    global _QUERY_COUNT
    _QUERY_COUNT += 1
    # Jitter in DB latency (realistic)
    latency_ms = random.uniform(30, 80)
    _QUERY_LATENCY_MS.append(latency_ms)
    await asyncio.sleep(latency_ms / 1000)


async def db_get_task(task_id: str) -> dict | None:
    await _simulate_db_latency()
    return _TASKS.get(task_id)


async def db_list_tasks(
    status: str = "all",
    priority: str = "all",
    limit: int = 50
) -> list[dict]:
    await _simulate_db_latency()
    tasks = list(_TASKS.values())
    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]
    if priority != "all":
        tasks = [t for t in tasks if t["priority"] == priority]
    return tasks[:limit]


async def db_create_task(data: dict) -> dict:
    await _simulate_db_latency()
    task_id = f"task-{str(uuid.uuid4())[:8]}"
    task = {
        "task_id": task_id,
        "title": data["title"],
        "description": data.get("description"),
        "priority": data.get("priority", "medium"),
        "status": "pending",
        "tags": data.get("tags", []),
        "created_by": data.get("created_by", "anonymous"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "view_count": 0
    }
    _TASKS[task_id] = task
    return task


async def db_update_task(task_id: str, updates: dict) -> dict | None:
    await _simulate_db_latency()
    task = _TASKS.get(task_id)
    if not task:
        return None
    task.update(updates)
    task["updated_at"] = datetime.utcnow().isoformat()
    _TASKS[task_id] = task
    return task


async def db_delete_task(task_id: str) -> bool:
    await _simulate_db_latency()
    return _TASKS.pop(task_id, None) is not None


async def db_get_stats() -> dict:
    await _simulate_db_latency()
    from collections import Counter
    priorities = Counter(t["priority"] for t in _TASKS.values())
    statuses = Counter(t["status"] for t in _TASKS.values())
    return {
        "total_tasks": len(_TASKS),
        "by_priority": dict(priorities),
        "by_status": dict(statuses),
        "computed_at": datetime.utcnow().isoformat()
    }


def db_query_stats() -> dict:
    """Get DB query performance stats (no DB call)."""
    import statistics as st
    latencies = _QUERY_LATENCY_MS.copy()
    return {
        "total_queries": _QUERY_COUNT,
        "avg_latency_ms": round(st.mean(latencies), 1) if latencies else 0,
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 1)
                          if len(latencies) >= 20 else None
    }


# Seed with demo data
def seed_database(n: int = 20):
    """Seed with demo tasks."""
    import asyncio
    priorities = ["urgent", "high", "medium", "low"]
    statuses = ["pending", "in_progress", "done"]
    for i in range(n):
        task_id = f"task-seed-{i+1:03d}"
        _TASKS[task_id] = {
            "task_id": task_id,
            "title": f"Sample task #{i+1}: {'Fix bug' if i%3==0 else 'Add feature' if i%3==1 else 'Update docs'}",
            "description": f"Auto-generated task #{i+1}",
            "priority": priorities[i % 4],
            "status": statuses[i % 3],
            "tags": [priorities[i % 4]],
            "created_by": "system",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "view_count": random.randint(0, 1000)
        }