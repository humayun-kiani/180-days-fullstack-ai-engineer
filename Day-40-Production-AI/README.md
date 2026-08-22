# Day 40 — Week 7 Revision: Production AI Patterns

> **Phase 4 — Advanced AI Engineering** | Week 7 Capstone | Day 40 of 180

---

## 📌 What I Learned Today

- Production AI architecture: startup → request lifecycle → failure modes
- AI health checks: LLM ping, guardrail tests, smoke tests — not just HTTP 200
- Graceful degradation: ServiceMode enum (FULL → DEGRADED on N failures)
- Consecutive failure counter: self.\_failures increments, resets on success
- Failure threshold: switch to DEGRADED after N consecutive LLM failures
- TokenBudget: daily total + per-user hourly + per-request max
- date.today() comparison for daily reset
- int(time.time() // 3600) for hourly bucket (epoch hours)
- Rolling window metrics: deque(maxlen=N) for last N requests
- Latency percentiles: p50, p95, p99 from sorted list
- Cost estimation: tokens / 1000 \* price_per_1k_tokens
- RequestRecord dataclass: full audit trail per request
- asyncio.create_task() for background periodic health check
- task.cancel() in lifespan yield for clean shutdown
- Lifespan startup phase: init → health check → register background tasks
- Filter output AFTER generation: PII can appear in LLM responses
- Service modes via admin endpoints for incident management
- Mock mode: all features work without real API key
- StreamingResponse with is_disconnected() check in generator

## 🔨 Project Built

**Production AI Service** — Week 7 integrated:

**ProductionAIService** (core):

- Three classifier tiers: keyword (0ms) → ML (5ms) → Claude (~500ms)
- Graceful degradation: N failures → ServiceMode.DEGRADED → ML fallback
- Budget enforcement before LLM call
- Guardrail validation before LLM call
- Output filtering after LLM response
- Full metrics recording per request

**HealthCheck** system:

- LLM connectivity ping (cheap 3-token call)
- Guardrail smoke test (injection blocked, safe input passed)
- Classifier smoke tests (4 labeled cases)
- Overall status: healthy | degraded | unhealthy

**TokenBudget**:

- Daily global budget (env: DAILY_TOKEN_BUDGET)
- Per-user hourly budget (env: PER_USER_HOURLY_TOKENS)
- Per-request maximum (4000 tokens)
- Epoch-hour bucket reset (no cron needed)

**MetricsStore**:

- Rolling deque of last 500 requests
- Latency: avg, p50, p95, p99
- Rates: error, block, degraded, output_filter
- Cost estimation: tokens → USD

**FastAPI**:

- POST /classify: full pipeline, guardrailed
- POST /chat/stream: SSE streaming, guardrailed
- POST /chat: non-streaming (collects full response)
- GET /health: LLM ping + smoke tests fresh
- GET /metrics: rolling window analytics
- GET /budget: current budget consumption
- GET /admin/smoke-test: 5 eval cases on demand
- GET /admin/guardrail-test: verify rules active
- POST /admin/mode/{mode}: incident management

## 🚀 How to Run

```bash
cd Day-40-Production-AI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

# Health check
curl http://localhost:8000/health

# Classify with guardrails
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"task": "Fix login bug", "user_id": "dev-1"}'

# Streaming chat
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix JWT errors?"}' \
  --no-buffer
```

## 🧠 Week 7 Integration Map

| Day | Component    | Production Role                              |
| --- | ------------ | -------------------------------------------- |
| 37  | Eval harness | Smoke tests on startup + admin endpoint      |
| 38  | Guardrails   | Input validation + output filter per request |
| 39  | Streaming    | /chat/stream SSE endpoint                    |
| 40  | Production   | Health, budget, degradation, metrics         |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
