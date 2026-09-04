# app/health/checks.py
# Health check implementations

import time
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CheckResult:
    """Result of a single health check."""
    name: str
    status: str       # "healthy", "degraded", "unhealthy"
    message: str
    duration_ms: float
    details: dict = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2),
            "details": self.details or {}
        }


class HealthChecker:
    """
    Runs multiple health checks and aggregates results.

    Healthy:   all checks pass
    Degraded:  some non-critical checks fail
    Unhealthy: critical check fails (readiness probe fails)
    """

    def __init__(self):
        self._checks: list[tuple[callable, bool]] = []  # (fn, is_critical)
        self._start_time = time.time()

    def add_check(self, check_fn, critical: bool = True):
        """Register a health check function."""
        self._checks.append((check_fn, critical))

    async def run_all(self) -> dict:
        """Run all registered checks and return aggregate result."""
        results = []
        tasks = [self._run_check(fn, critical) for fn, critical in self._checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for cr in check_results:
            if isinstance(cr, Exception):
                results.append(CheckResult(
                    name="unknown", status="unhealthy",
                    message=str(cr), duration_ms=0
                ))
            else:
                results.append(cr)

        # Aggregate status
        statuses = [r.status for r in results]
        if any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        elif any(s == "degraded" for s in statuses):
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "checks": [r.to_dict() for r in results]
        }

    async def _run_check(self, fn, critical: bool) -> CheckResult:
        start = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn()
            else:
                result = fn()
            duration = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            return CheckResult(
                name=getattr(fn, "__name__", "unknown"),
                status="unhealthy" if critical else "degraded",
                message=f"Check failed: {str(e)[:100]}",
                duration_ms=duration
            )


# ── Concrete Health Checks ────────────────────────────────────

def check_task_store(task_count_fn) -> CheckResult:
    """Check the in-memory task store."""
    start = time.perf_counter()
    try:
        count = task_count_fn()
        max_tasks = 10000
        usage_pct = count / max_tasks * 100

        if usage_pct > 95:
            status = "unhealthy"
            msg = f"Task store at {usage_pct:.0f}% capacity"
        elif usage_pct > 80:
            status = "degraded"
            msg = f"Task store at {usage_pct:.0f}% capacity"
        else:
            status = "healthy"
            msg = f"{count} tasks stored ({usage_pct:.1f}% of capacity)"

        return CheckResult(
            name="task_store",
            status=status,
            message=msg,
            duration_ms=(time.perf_counter() - start) * 1000,
            details={"count": count, "max": max_tasks, "pct": round(usage_pct, 1)}
        )
    except Exception as e:
        return CheckResult(
            name="task_store", status="unhealthy",
            message=str(e), duration_ms=(time.perf_counter() - start) * 1000
        )


def check_metrics_registry(registry) -> CheckResult:
    """Verify metrics registry is collecting data."""
    start = time.perf_counter()
    try:
        summary = registry.get_summary()
        counter_count = len(summary.get("counters", {}))
        gauge_count = len(summary.get("gauges", {}))
        return CheckResult(
            name="metrics_registry",
            status="healthy",
            message=f"{counter_count} counters, {gauge_count} gauges registered",
            duration_ms=(time.perf_counter() - start) * 1000,
            details={"counters": counter_count, "gauges": gauge_count}
        )
    except Exception as e:
        return CheckResult(
            name="metrics_registry", status="degraded",
            message=str(e), duration_ms=(time.perf_counter() - start) * 1000
        )


def check_memory() -> CheckResult:
    """Check process memory usage."""
    start = time.perf_counter()
    try:
        import os
        import resource
        mem_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if os.uname().sysname == "Linux":
            mem_bytes *= 1024
        mem_mb = mem_bytes / 1024 / 1024
        limit_mb = 512

        if mem_mb > limit_mb * 0.9:
            status = "unhealthy"
        elif mem_mb > limit_mb * 0.75:
            status = "degraded"
        else:
            status = "healthy"

        return CheckResult(
            name="memory",
            status=status,
            message=f"{mem_mb:.0f}MB used of {limit_mb}MB limit",
            duration_ms=(time.perf_counter() - start) * 1000,
            details={"used_mb": round(mem_mb, 1), "limit_mb": limit_mb}
        )
    except Exception:
        return CheckResult(
            name="memory", status="healthy",
            message="Memory check not available on this platform",
            duration_ms=(time.perf_counter() - start) * 1000
        )