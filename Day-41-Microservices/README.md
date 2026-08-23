# Day 41 — Microservices Architecture

> **Phase 5 — System Design & Architecture** | Week 8 | Day 41 of 180

---

## 📌 What I Learned Today

- Monolith vs microservices: when each is appropriate (start monolith!)
- Martin Fowler rule: don't start with microservices on a new project
- Service decomposition: split by business capability, not technical layer
- High cohesion within service, loose coupling between services
- Each service owns its data (no cross-service database queries)
- Two-pizza team rule: ~5-8 engineers per service
- Synchronous communication: REST for "I need the answer NOW"
- Asynchronous communication: events for "notify all interested parties"
- API Gateway: single entry point, routes to services, auth once
- Service-to-service calls: httpx.AsyncClient with timeout
- Auth dependency: task-service calls auth-service to verify JWT
- Circuit breaker: stop calling a failing service (CLOSED→OPEN→HALF_OPEN)
- CircuitState enum: CLOSED, OPEN, HALF_OPEN
- consecutive failures: increment counter, reset on success
- last_failure_time: track when OPEN state should transition to HALF_OPEN
- Distributed tracing: X-Request-ID propagated through all services
- ContextVar: persists request ID across async boundaries
- BaseHTTPMiddleware: intercept all requests in a FastAPI app
- Request ID in every log line: find all logs for one request across services
- Graceful fallback: task-service uses "medium" if ai-service is down
- Rate limiting at gateway: per-IP request counts with 60s rolling window
- Health aggregation: gateway /health pings all upstream services
- httpx.ConnectError vs TimeoutException: different failure modes

## 🔨 Project Built

**Three-Service Task Manager + API Gateway:**

**Auth Service** (port 8001):

- POST /auth/login: username/password → JWT
- POST /auth/verify: token → user info (called by task-service)
- GET /auth/users: list users (demo only)
- JWT with python-jose, base64 mock fallback

**Task Service** (port 8002):

- GET /tasks: list with status/priority filter
- POST /tasks: create (calls auth-service + ai-service)
- GET /tasks/{id}: get one
- PATCH /tasks/{id}: update
- DELETE /tasks/{id}: admin only
- Circuit breakers for auth-service + ai-service
- Falls back to "medium" if ai-service unavailable

**AI Service** (port 8003):

- POST /ai/classify: single task → priority
- POST /ai/classify/batch: multiple tasks at once
- keyword_classify fallback when no API key

**API Gateway** (port 8000):

- Proxy all /api/\* to correct upstream
- Rate limiting: 60 req/min per IP
- X-Request-ID tracing propagation
- Health aggregation: pings all 3 services
- ConnectError → 503, TimeoutException → 504

**Shared module:**

- RequestTracingMiddleware: extract/generate X-Request-ID
- ServiceLogger: includes request_id in every log line
- ContextVar: request_id persists across async boundaries
- CircuitBreaker dataclass with state machine

## 🚀 How to Run

```bash
cd Day-41-Microservices
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start all 4 services
./start_all.sh

# Or manually (4 separate terminals):
uvicorn auth_service.main:app --port 8001
uvicorn ai_service.main:app --port 8003
uvicorn task_service.main:app --port 8002
uvicorn gateway.main:app --port 8000

# Test
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d '{"username":"humayun","password":"password"}' \
  -H "Content-Type: application/json" | python3 -c \
  "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "URGENT: Production API is down"}'
```

## 🧠 Service Communication Map

```
Client
  │
  ▼
Gateway :8000
  ├── /api/auth/*  → Auth Service :8001
  ├── /api/tasks/* → Task Service :8002
  │                    └── calls → Auth Service :8001 (verify JWT)
  │                    └── calls → AI Service :8003 (classify priority)
  └── /api/ai/*   → AI Service :8003
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
