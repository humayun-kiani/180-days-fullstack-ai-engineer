# Day 49 — Monitoring, Observability & Alerting

> **Phase 6 — DevOps & Infrastructure** | Week 9 | Day 49 of 180

---

## 📌 What I Learned Today

- Three pillars of observability: metrics, logs, traces
- Metrics: WHAT is happening in aggregate (counters, gauges, histograms)
- Logs: WHAT happened for one specific request (structured JSON)
- Traces: HOW a request flowed through the system (spans)
- Counter: monotonically increasing, use for requests/errors/events
- Gauge: current value (up or down), use for connections/memory/queue depth
- Histogram: distribution of values, use for latency/request size
- histogram.observe(value): record one data point into the right bucket
- percentile(p): estimate p50/p95/p99 from bucket counts
- Prometheus text format: # HELP, # TYPE, metric_name{labels} value
- Label cardinality: don't use user_id as a label (millions of label combos = OOM)
- Structured logging: JSON lines with timestamp, level, message, request_id
- ContextVar: persist request_id across async boundaries in one request
- Log store: in-memory ring buffer (production: Elasticsearch, CloudWatch)
- Span: one operation with start_time, end_time, tags, status
- Trace: collection of related spans sharing a trace_id
- SpanContext: context manager to time and record a span
- Parent-child spans: request span contains DB span contains cache span
- HealthChecker: aggregate multiple check functions into one status
- CheckResult: name, status (healthy/degraded/unhealthy), message, duration_ms
- critical=True: unhealthy status if this check fails
- critical=False: only degraded if this check fails
- SLI: measured indicator (actual error rate = 0.003%)
- SLO: internal target (error rate < 0.1%)
- SLA: contractual commitment (error rate < 0.5%)
- Error budget: (1 - SLO) × period = allowed failure time
- Alert on symptoms not causes: error rate > 5%, not CPU > 80%
- for_seconds: require condition true for N seconds before firing
- AlertState: OK → PENDING → FIRING → RESOLVED
- AlertSeverity: PAGE (3am), TICKET (business hours), INFO (Slack)

## 🔨 Project Built

**Complete Observability Stack:**

**Metrics** (app/metrics/):
- Counter, Gauge, Histogram with label support
- Thread-safe with locks
- MetricsRegistry: central registry + Prometheus format export
- http_requests_total: labeled by method/endpoint/status_code
- http_request_duration_seconds: histogram with p50/p95/p99
- tasks_created_total: labeled by priority
- RequestTimer: context manager for latency recording

**Structured Logging** (app/logging/):
- StructuredLogger: emits JSON log lines with standard fields
- ContextVar propagates request_id across async boundaries
- StoringLogger: keeps last 500 entries in memory
- get_recent_logs(): filter by level or request_id

**Distributed Tracing** (app/tracing/):
- Span dataclass: operation, start/end time, tags, status
- SpanContext: context manager (enter=start span, exit=finish)
- Parent-child via ContextVar (span_id_var → parent_span_id)
- In-memory trace store (last 100 traces)

**Health Checks** (app/health/):
- HealthChecker: runs checks concurrently with asyncio.gather
- check_task_store: validates capacity (healthy/degraded/unhealthy)
- check_metrics_registry: verifies metrics are collecting
- check_memory: process memory vs limit

**Alert Rules** (app/alerts/):
- AlertRule: condition fn, for_seconds, severity, state machine
- AlertEvaluator: evaluates all rules, tracks state transitions
- 3 rules: HighErrorRate (PAGE), HighLatencyP99 (PAGE), TaskStoreCapacity (TICKET)
- Background task: evaluates every 15 seconds

**FastAPI endpoints:**
- GET /metrics: Prometheus text format
- GET /metrics/summary: JSON summary with computed rates
- GET /health: full health check
- GET /ready: Kubernetes readiness probe
- GET /logs: filter by level/request_id
- GET /traces: recent traces with spans
- GET /alerts: rule states + firing + history
- GET /slo: availability, latency, error rate vs targets

## 🚀 How to Run

```bash
cd Day-49-Observability
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# Generate traffic
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix production bug", "priority": "urgent"}'

# View all observability data
curl http://localhost:8000/metrics
curl http://localhost:8000/health
curl http://localhost:8000/logs
curl http://localhost:8000/traces
curl http://localhost:8000/alerts
curl http://localhost:8000/slo
```

## 🧠 The Three Pillars

| Pillar | Question | Tool | Endpoint |
|--------|---------|------|---------|
| Metrics | What's happening now? | Prometheus | /metrics |
| Logs | What happened for this request? | ELK/CloudWatch | /logs |
| Traces | How did it flow? | Jaeger/Zipkin | /traces |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)