# ============================================================
# worker/tasks/maintenance.py
# Maintenance and monitoring tasks
# ============================================================

import time
from datetime import datetime
from celery.utils.log import get_task_logger
from celery.result import AsyncResult

from worker.celery_app import celery_app
from app.config import config

logger = get_task_logger(__name__)


@celery_app.task(
    name="worker.tasks.maintenance.health_check",
    queue="maintenance"
)
def health_check() -> dict:
    """
    Periodic health check task.
    Scheduled: every 5 minutes.
    Verifies workers are alive and Redis is reachable.
    """
    import redis as redis_lib
    r = redis_lib.from_url(config.REDIS_URL)

    redis_ok = True
    try:
        r.ping()
    except Exception:
        redis_ok = False

    result = {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "checked_at": datetime.utcnow().isoformat(),
        "worker": "alive"
    }

    logger.info(f"Health check: {result}")
    return result


@celery_app.task(
    name="worker.tasks.maintenance.cleanup_old_results",
    queue="maintenance"
)
def cleanup_old_results() -> dict:
    """
    Clean up old Celery task results from Redis.
    Scheduled: 1st of each month at midnight.
    """
    logger.info("Starting monthly result cleanup...")
    # In a real app: query task result keys older than N days and delete
    # This is handled automatically by result_expires=3600 in config
    # This task is a placeholder for custom cleanup logic

    return {
        "status": "completed",
        "cleaned_at": datetime.utcnow().isoformat(),
        "message": "Old results cleared (handled by result_expires config)"
    }


@celery_app.task(
    name="worker.tasks.maintenance.run_diagnostics",
    bind=True,
    queue="maintenance"
)
def run_diagnostics(self) -> dict:
    """
    Run system diagnostics.
    Can be triggered manually from the API.
    """
    logger.info(f"[{self.request.id}] Running system diagnostics...")

    results = {}

    # Test 1: Redis connectivity
    import redis as redis_lib
    try:
        r = redis_lib.from_url(config.REDIS_URL)
        r.ping()
        results["redis"] = {"status": "ok", "url": config.REDIS_URL}
    except Exception as e:
        results["redis"] = {"status": "error", "error": str(e)}

    # Test 2: Task execution time
    start = time.perf_counter()
    time.sleep(0.1)    # simulate small task
    elapsed = time.perf_counter() - start
    results["task_execution"] = {"status": "ok", "latency_ms": round(elapsed * 1000, 2)}

    # Test 3: Worker count
    inspect = celery_app.control.inspect()
    active = inspect.active()
    results["workers"] = {
        "count": len(active) if active else 0,
        "active_tasks": sum(len(t) for t in active.values()) if active else 0
    }

    overall = "healthy" if all(
        v.get("status") == "ok" for v in results.values()
        if isinstance(v, dict)
    ) else "degraded"

    return {
        "overall": overall,
        "tests": results,
        "ran_at": datetime.utcnow().isoformat()
    }