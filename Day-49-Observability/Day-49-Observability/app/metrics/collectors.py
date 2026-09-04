# app/metrics/collectors.py
# Application-specific metric collectors

import time
import os
from app.metrics.registry import registry

# ── HTTP Metrics ──────────────────────────────────────────────

http_requests_total = registry.counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labels=["method", "endpoint", "status_code"]
)

http_request_duration_seconds = registry.histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    labels=["method", "endpoint"]
)

http_errors_total = registry.counter(
    "http_errors_total",
    "Total HTTP error responses (4xx + 5xx)",
    labels=["method", "endpoint", "status_code"]
)

http_active_requests = registry.gauge(
    "http_active_requests",
    "Currently in-flight HTTP requests"
)

# ── Task Business Metrics ─────────────────────────────────────

tasks_created_total = registry.counter(
    "tasks_created_total",
    "Total tasks created",
    labels=["priority"]
)

tasks_completed_total = registry.counter(
    "tasks_completed_total",
    "Total tasks marked as done",
    labels=["priority"]
)

tasks_in_store = registry.gauge(
    "tasks_in_store",
    "Current number of tasks in the task store"
)

# ── System Metrics ────────────────────────────────────────────

process_memory_bytes = registry.gauge(
    "process_memory_bytes",
    "Current process memory usage in bytes"
)


def collect_system_metrics() -> None:
    """Update system metrics from the OS."""
    try:
        import resource
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS returns bytes, Linux returns KB
        if os.uname().sysname == "Linux":
            mem *= 1024
        process_memory_bytes.set(mem)
    except Exception:
        pass


class RequestTimer:
    """Context manager to time a request and record metrics."""

    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        http_active_requests.inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        http_active_requests.dec()
        http_request_duration_seconds.observe(
            duration,
            method=self.method,
            endpoint=self.endpoint
        )
        return False  # don't suppress exceptions