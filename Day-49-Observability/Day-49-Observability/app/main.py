# app/main.py
# Observed Task API — Day 49: Monitoring, Observability & Alerting

import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response, Query
from fastapi.responses import PlainTextResponse

from app.metrics.registry import registry
from app.metrics.collectors import (
    http_requests_total, http_request_duration_seconds,
    http_errors_total, http_active_requests,
    tasks_created_total, tasks_completed_total, tasks_in_store,
    collect_system_metrics, RequestTimer
)
from app.logging.structured import (
    logger, request_id_var, user_id_var, get_recent_logs
)
from app.tracing.tracer import (
    SpanContext, trace_id_var, span_id_var,
    get_trace, get_recent_traces
)
from app.health.checks import (
    HealthChecker, check_task_store, check_metrics_registry, check_memory
)
from app.alerts.evaluator import AlertEvaluator, AlertRule, AlertSeverity
from app import tasks as task_store
from app.tasks import Task, TaskCreate, TaskUpdate


# ── Bootstrap ─────────────────────────────────────────────────

_health_checker = HealthChecker()
_alert_evaluator = AlertEvaluator()
_alert_task: asyncio.Task = None


def _setup_health_checks():
    _health_checker.add_check(
        lambda: check_task_store(task_store.task_count),
        critical=True
    )
    _health_checker.add_check(
        lambda: check_metrics_registry(registry),
        critical=False
    )
    _health_checker.add_check(check_memory, critical=False)


def _setup_alert_rules():
    """Define alert rules based on live metrics."""

    # High error rate — page immediately
    def high_error_rate() -> bool:
        total = sum(http_requests_total.get_all().values())
        errors = sum(http_errors_total.get_all().values())
        if total < 10:
            return False
        return (errors / total) > 0.05  # > 5% error rate

    _alert_evaluator.add_rule(AlertRule(
        name="HighErrorRate",
        description="HTTP error rate exceeds 5% over the evaluation window",
        condition=high_error_rate,
        for_seconds=30.0,
        severity=AlertSeverity.PAGE,
        annotations={"runbook": "https://wiki/runbooks/high-error-rate"}
    ))

    # High latency — page if sustained
    def high_latency() -> bool:
        stats = http_request_duration_seconds.get_stats()
        return stats.get("p99", 0) > 2.0  # p99 > 2 seconds

    _alert_evaluator.add_rule(AlertRule(
        name="HighLatencyP99",
        description="p99 request latency exceeds 2000ms",
        condition=high_latency,
        for_seconds=60.0,
        severity=AlertSeverity.PAGE,
        annotations={"threshold": "2000ms"}
    ))

    # Task store nearing capacity — ticket
    def task_store_high() -> bool:
        return task_store.task_count() > 8000

    _alert_evaluator.add_rule(AlertRule(
        name="TaskStoreCapacity",
        description="Task store above 80% capacity",
        condition=task_store_high,
        for_seconds=300.0,
        severity=AlertSeverity.TICKET,
        annotations={"action": "Increase MAX_TASKS or archive old tasks"}
    ))


async def _periodic_alert_evaluation():
    """Background task: evaluate alert rules every 15 seconds."""
    while True:
        await asyncio.sleep(15)
        try:
            collect_system_metrics()
            _alert_evaluator.evaluate_all()
        except Exception as e:
            logger.error("Alert evaluation failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _alert_task

    print("\n" + "=" * 65)
    print("  Observed Task API — Day 49")
    print("  Monitoring, Observability & Alerting")
    print("=" * 65)

    _setup_health_checks()
    _setup_alert_rules()

    _alert_task = asyncio.create_task(_periodic_alert_evaluation())

    logger.info("Task API started",
                environment="development",
                alert_rules=len(_alert_evaluator._rules),
                health_checks=len(_health_checker._checks))

    print(f"\n  Health checks:  {len(_health_checker._checks)}")
    print(f"  Alert rules:    {len(_alert_evaluator._rules)}")
    print(f"  Docs:           http://localhost:8000/docs\n")

    yield

    _alert_task.cancel()
    logger.info("Task API shutting down")


# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="Observed Task API",
    description="""
## 📊 Observed Task API — Day 49

Full observability stack: metrics, logs, traces, health checks, alerts.

### Observability Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /metrics` | Prometheus metrics (counters, gauges, histograms) |
| `GET /metrics/summary` | JSON metrics summary |
| `GET /health` | Full health check report |
| `GET /ready` | Readiness probe (Kubernetes) |
| `GET /logs` | Recent structured log entries |
| `GET /traces` | Recent distributed traces |
| `GET /alerts` | Current alert states |
| `GET /slo` | SLO compliance report |

### Task Endpoints
| Endpoint | Description |
|----------|-------------|
| `POST /tasks` | Create task (metrics + logs + trace recorded) |
| `GET /tasks` | List tasks |
| `GET /tasks/{id}` | Get task |
| `PATCH /tasks/{id}` | Update task |
| `DELETE /tasks/{id}` | Delete task |
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ── Request Middleware ────────────────────────────────────────

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """
    Middleware: adds tracing, logging, and metrics to every request.
    """
    # Generate/propagate request ID
    request_id = (
        request.headers.get("X-Request-ID") or
        str(uuid.uuid4())[:8]
    )

    # Set context variables
    rid_token = request_id_var.set(request_id)

    # Clean up endpoint path for metrics labels
    endpoint = request.url.path
    # Normalize dynamic segments: /tasks/task-abc123 → /tasks/{task_id}
    import re
    endpoint = re.sub(r'/task-[a-z0-9]+', '/{task_id}', endpoint)

    method = request.method
    start = time.perf_counter()
    http_active_requests.inc()

    logger.debug("Request started",
                 method=method,
                 path=request.url.path,
                 client=request.client.host if request.client else None)

    try:
        with SpanContext(f"{method} {endpoint}") as span_ctx:
            span_ctx.span.tags = {
                "http.method": method,
                "http.path": endpoint
            }
            response = await call_next(request)
    except Exception as e:
        duration = (time.perf_counter() - start) * 1000
        http_active_requests.dec()
        http_requests_total.inc(
            method=method, endpoint=endpoint, status_code="500"
        )
        http_errors_total.inc(
            method=method, endpoint=endpoint, status_code="500"
        )
        logger.error("Unhandled exception",
                     method=method, path=request.url.path,
                     error=str(e), duration_ms=round(duration, 1))
        request_id_var.reset(rid_token)
        raise

    duration = (time.perf_counter() - start) * 1000
    http_active_requests.dec()
    status_code = str(response.status_code)

    # Record metrics
    http_requests_total.inc(
        method=method, endpoint=endpoint, status_code=status_code
    )
    http_request_duration_seconds.observe(
        duration / 1000,
        method=method, endpoint=endpoint
    )
    if response.status_code >= 400:
        http_errors_total.inc(
            method=method, endpoint=endpoint, status_code=status_code
        )

    # Log request completion
    log_fn = logger.warning if response.status_code >= 400 else logger.info
    log_fn("Request completed",
           method=method,
           path=request.url.path,
           status_code=response.status_code,
           duration_ms=round(duration, 1))

    # Add observability headers to response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(round(duration, 1))

    request_id_var.reset(rid_token)
    return response


# ── Task Endpoints ────────────────────────────────────────────

@app.post("/tasks", status_code=201, response_model=Task)
async def create_task(body: TaskCreate) -> Task:
    with SpanContext("task.create", tags={"priority": body.priority.value}):
        task = task_store.create_task(body)

    tasks_created_total.inc(priority=task.priority.value)
    tasks_in_store.set(task_store.task_count())

    logger.info("Task created",
                task_id=task.task_id,
                priority=task.priority.value,
                title=task.title[:50])

    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
) -> list[Task]:
    return task_store.list_tasks(status, priority)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str) -> Task:
    task = task_store.get_task(task_id)
    if not task:
        logger.warning("Task not found", task_id=task_id)
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, body: TaskUpdate) -> Task:
    task = task_store.update_task(task_id, body)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")

    if body.status and body.status.value == "done":
        tasks_completed_total.inc(priority=task.priority.value)

    tasks_in_store.set(task_store.task_count())
    logger.info("Task updated", task_id=task_id, updates=body.model_dump(exclude_none=True))
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if not task_store.delete_task(task_id):
        raise HTTPException(404, f"Task '{task_id}' not found")
    tasks_in_store.set(task_store.task_count())
    logger.info("Task deleted", task_id=task_id)


# ── Observability Endpoints ───────────────────────────────────

@app.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics endpoint",
    tags=["observability"]
)
def prometheus_metrics():
    """
    Prometheus-format metrics for scraping by Grafana/Prometheus.

    In production: configure Prometheus to scrape this endpoint every 15s.
    """
    collect_system_metrics()
    return PlainTextResponse(
        content=registry.prometheus_format(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/metrics/summary", summary="JSON metrics summary", tags=["observability"])
def metrics_summary() -> dict:
    """Human-readable JSON metrics summary."""
    collect_system_metrics()
    summary = registry.get_summary()

    # Add computed rates
    total_requests = sum(http_requests_total.get_all().values())
    total_errors = sum(http_errors_total.get_all().values())
    error_rate = total_errors / total_requests if total_requests > 0 else 0.0

    summary["computed"] = {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate_pct": round(error_rate * 100, 2),
        "p50_latency_ms": round(
            http_request_duration_seconds.percentile(50) * 1000, 1
        ),
        "p99_latency_ms": round(
            http_request_duration_seconds.percentile(99) * 1000, 1
        )
    }

    return summary


@app.get("/health", summary="Full health check", tags=["observability"])
async def health() -> dict:
    """
    Run all health checks and return aggregate result.
    Used by: monitoring systems, ops dashboards.
    """
    return await _health_checker.run_all()


@app.get("/ready", summary="Kubernetes readiness probe", tags=["observability"])
async def readiness() -> dict:
    """
    Fast readiness check for Kubernetes.
    Returns 503 if pod should be taken out of rotation.
    """
    result = await _health_checker.run_all()
    if result["status"] == "unhealthy":
        raise HTTPException(503, detail=result)
    return {"ready": True, "status": result["status"]}


@app.get("/logs", summary="Recent structured logs", tags=["observability"])
def get_logs(
    level: Optional[str] = Query(None, description="Filter by level: DEBUG, INFO, WARNING, ERROR"),
    request_id: Optional[str] = Query(None, description="Filter by request_id"),
    limit: int = Query(50, ge=1, le=200)
) -> dict:
    """
    Query recent structured log entries.
    In production: use Elasticsearch, CloudWatch, or Splunk instead.
    """
    logs = get_recent_logs(level=level, request_id=request_id, limit=limit)
    return {"logs": logs, "count": len(logs), "tip": "Use request_id to trace a single request"}


@app.get("/traces", summary="Recent distributed traces", tags=["observability"])
def get_traces(limit: int = Query(10, ge=1, le=50)) -> dict:
    """
    Get recent distributed traces.
    Each trace shows how a request flowed through the system.
    """
    traces = get_recent_traces(limit=limit)
    return {"traces": traces, "count": len(traces)}


@app.get("/traces/{trace_id}", summary="Get specific trace", tags=["observability"])
def get_specific_trace(trace_id: str) -> dict:
    """Get all spans for a specific trace ID."""
    spans = get_trace(trace_id)
    if not spans:
        raise HTTPException(404, f"Trace '{trace_id}' not found")
    return {"trace_id": trace_id, "spans": spans}


@app.get("/alerts", summary="Current alert states", tags=["observability"])
def get_alerts() -> dict:
    """
    Current state of all alert rules.
    In production: use PagerDuty, OpsGenie, or Grafana Alertmanager.
    """
    result = _alert_evaluator.evaluate_all()
    result["firing_alerts"] = _alert_evaluator.get_firing_alerts()
    result["recent_history"] = _alert_evaluator.get_history(limit=10)
    return result


@app.get("/slo", summary="SLO compliance report", tags=["observability"])
def get_slo() -> dict:
    """
    Service Level Objective compliance report.
    Shows whether we're meeting our reliability targets.
    """
    total = sum(http_requests_total.get_all().values())
    errors = sum(http_errors_total.get_all().values())
    successes = total - errors

    error_rate = errors / total if total > 0 else 0.0
    availability = successes / total if total > 0 else 1.0

    # SLO targets
    availability_slo = 0.999    # 99.9%
    latency_slo_ms = 500.0      # p95 < 500ms
    error_rate_slo = 0.001      # < 0.1%

    p95_ms = http_request_duration_seconds.percentile(95) * 1000
    p99_ms = http_request_duration_seconds.percentile(99) * 1000

    # Error budget calculation (30-day window)
    period_minutes = 30 * 24 * 60
    budget_minutes = period_minutes * (1 - availability_slo)  # 43.2 minutes
    # Rough estimate: pro-rate based on observed error rate
    consumed_pct = min(100.0, (error_rate / (1 - availability_slo)) * 100) if total > 0 else 0

    return {
        "slos": {
            "availability": {
                "target": f"{availability_slo * 100:.1f}%",
                "current": f"{availability * 100:.3f}%",
                "meeting_slo": availability >= availability_slo,
                "details": {
                    "total_requests": total,
                    "successful_requests": successes,
                    "error_requests": errors
                }
            },
            "latency_p95": {
                "target": f"< {latency_slo_ms:.0f}ms",
                "current": f"{p95_ms:.0f}ms",
                "meeting_slo": p95_ms <= latency_slo_ms or total == 0
            },
            "error_rate": {
                "target": f"< {error_rate_slo * 100:.1f}%",
                "current": f"{error_rate * 100:.3f}%",
                "meeting_slo": error_rate <= error_rate_slo or total == 0
            }
        },
        "error_budget": {
            "period": "30 days",
            "total_budget_minutes": round(budget_minutes, 1),
            "consumed_pct": round(consumed_pct, 1),
            "remaining_pct": round(100 - consumed_pct, 1),
            "status": "healthy" if consumed_pct < 50 else "warning" if consumed_pct < 80 else "critical"
        },
        "p99_latency_ms": round(p99_ms, 1),
        "tip": "Make requests to /tasks endpoints to see live SLO data"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "Observed Task API",
        "day": "Day 49 — Monitoring, Observability & Alerting",
        "docs": "/docs",
        "observability": {
            "metrics": "GET /metrics (Prometheus format)",
            "metrics_json": "GET /metrics/summary",
            "health": "GET /health",
            "logs": "GET /logs",
            "traces": "GET /traces",
            "alerts": "GET /alerts",
            "slo": "GET /slo"
        },
        "tasks": {
            "create": "POST /tasks",
            "list": "GET /tasks",
            "get": "GET /tasks/{id}",
            "update": "PATCH /tasks/{id}",
            "delete": "DELETE /tasks/{id}"
        }
    }