# TaskMind Technical Case Study

**Author:** Humayun Kiani  
**Built:** Days 51-55 of 180-Day Full Stack AI Engineer Journey  
**Stack:** FastAPI + React + PostgreSQL + Redis + Claude

---

## The Problem

Task management apps exist everywhere. What makes TaskMind different is the **cognitive load problem**: when you sit down to work, you spend the first 10 minutes deciding which task to work on, how long it will take, and how to break it down. This is mental overhead, not productive work. AI can handle it.

The goal was to build a task manager where:
1. You type a task title and the AI tells you the priority
2. You type 2 words and the AI writes the full description
3. You say "build checkout page" and the AI gives you 5 subtasks with time estimates

This required tight AI integration — not as a bolt-on feature, but as a core part of the create-task workflow.

---

## Decision 1: Async SQLAlchemy Over Synchronous

**Problem:** FastAPI is built on async Python (asyncio). If database queries are synchronous, they block the entire event loop while waiting for the database. With 20 concurrent users each making a 15ms query, synchronous execution means those queries serialize — the 20th user waits 300ms before their query even starts.

**Options considered:**
- A) Synchronous SQLAlchemy with `run_in_executor` (thread pool)
- B) `asyncpg` directly (no ORM)
- C) SQLAlchemy 2.0 async with asyncpg driver

**Decision: Option C**

SQLAlchemy 2.0 introduced a first-class async API that works with asyncpg — the fastest PostgreSQL driver available for Python. This gives the full ORM convenience (type-safe models, Alembic migrations, clean query building) without blocking the event loop.

```python
# Async SQLAlchemy: non-blocking, concurrent
engine = create_async_engine(DATABASE_URL, pool_size=10)

async def list_tasks(owner_id: UUID) -> list[Task]:
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Task).where(Task.owner_id == owner_id)
        )
        return list(result.scalars())
```

**Result:** Load tests (20 concurrent users, Locust) showed 340 RPS with async vs ~90 RPS with the thread-pool approach — a 3.8x improvement. The p99 latency dropped from 1,100ms to 287ms.

**Tradeoff accepted:** Every query must be awaited. Session management is slightly more complex (`async_sessionmaker`, `expire_on_commit=False`). Worth it.

---

## Decision 2: Redis Cache-Aside Over In-Process Cache

**Problem:** Task list queries hit the database on every request. With 100 users all refreshing their boards, this is ~85 unnecessary DB round trips per second for data that changes infrequently.

**Options considered:**
- A) Python dict (in-process cache, per worker)
- B) Redis (shared cache, across workers)
- C) No cache (just make queries faster)

**Decision: Option B — Redis**

The critical reason to choose Redis over an in-process dict: with multiple API workers (uvicorn workers or Docker replicas), each process has its own Python dict. When user A creates a task and worker 1 invalidates its cache, worker 2's cache still has the stale data. The next request routed to worker 2 returns stale results.

Redis is shared across all workers. A single `DEL tasks:{user_id}:*` call clears the cache for every worker simultaneously.

```python
# Cache-aside pattern
async def list_tasks_cached(user_id: str, page: int):
    key = f"tasks:{user_id}:{page}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)     # 0.1ms

    tasks = await db.query_tasks(user_id, page)  # 15ms
    await redis.setex(key, 30, json.dumps(tasks))
    return tasks
```

**Result:** Cache hit rate reached 83% under load (measured with CacheAnalyzer middleware). Average response time for task listing dropped from 18ms to 2ms for cached requests. DB load reduced by ~5x.

**Tradeoff accepted:** Redis is a network hop (~0.2ms overhead per call). Adds operational complexity (another service to run). Manageable: Docker Compose handles the dependency, and the speedup from skipping a 15ms DB query far outweighs the 0.2ms Redis overhead.

---

## Decision 3: Mock AI Fallback

**Problem:** Requiring an Anthropic API key creates friction:
- Local development: developers need to set up API keys
- CI/CD: secrets must be managed and rotated
- Demos: spending API credits for every demo run
- Outages: if Anthropic has downtime, the app goes down

**Options considered:**
- A) Require API key (fail without it)
- B) Skip AI features when no key (return empty)
- C) Keyword-based mock that returns realistic responses

**Decision: Option C — keyword-based mock**

The mock analyzes the task title for keywords and returns a plausible priority suggestion. It's not as good as Claude, but it's useful enough for development and demos:

```python
def _mock_analyze(title: str) -> AnalyzeResponse:
    t = title.lower()
    if any(w in t for w in ["urgent", "critical", "outage", "p0"]):
        return AnalyzeResponse(suggested_priority="urgent", confidence="high", ...)
    if any(w in t for w in ["fix", "bug", "security", "deadline"]):
        return AnalyzeResponse(suggested_priority="high", ...)
    ...
```

The real API is tried first. If no key is configured, or if the API call fails, the mock is returned. This means the app degrades gracefully rather than breaking.

**Result:** The app runs with `docker-compose up --build` — no configuration needed. 116 integration tests pass in CI without any API key. Demos run without spending credits. The mock was tested against real Claude output and matches priority for ~80% of common task titles.

**Tradeoff accepted:** The mock is less accurate than Claude. Users who don't set an API key get lower-quality AI suggestions. This is documented clearly and the setup to add a real key is one line in `.env`.

---

## Decision 4: WebSocket Over Polling for Real-Time

**Problem:** When a user creates a task on their phone, their desktop tab should update without a manual refresh. Options: polling (ask server repeatedly) vs WebSocket (persistent connection).

**Options considered:**
- A) Polling: fetch /api/tasks every 5 seconds
- B) Long polling: keep HTTP connection open until server has update
- C) WebSocket: persistent bidirectional connection

**Decision: Option C — WebSocket**

At 1 WebSocket connection per tab vs polling every 5 seconds:
- 100 users × 2 tabs × polling every 5s = 40 requests/second of overhead
- 100 users × 2 tabs × WebSocket = 200 idle connections (cheap)

WebSocket connections are cheap when idle — they consume a file descriptor and almost no CPU. Polling wastes CPU, DB queries, and bandwidth even when nothing has changed.

FastAPI supports WebSocket natively. The ConnectionManager tracks all open connections per user, and broadcasts are O(1) per connected client:

```python
async def send_to_user(self, user_id: str, message: dict):
    for ws in self._connections.get(user_id, set()):
        await ws.send_text(json.dumps(message))
```

**Result:** Real-time sync with zero polling overhead. Creating a task on mobile immediately updates the desktop tab.

**Tradeoff accepted:** WebSocket connections have a limit per server. For scale beyond a single process, Redis pub/sub would be needed to broadcast across workers. Noted as a future improvement — current single-process setup works for the expected user base.

---

## What I Would Do Differently

1. **Add Alembic migrations from day one.** I used `Base.metadata.create_all` for development speed, but this makes schema evolution harder. Production apps need migration files.

2. **Rate limit the AI endpoints.** Claude API calls cost money. Without rate limiting, a single bad actor can make thousands of requests. Should add per-user rate limits with Redis.

3. **Add pagination cursor instead of offset.** `OFFSET 80 LIMIT 20` gets slower as the offset increases (DB still scans 80 rows). Cursor-based pagination (`WHERE created_at < :cursor`) is O(1) regardless of page number.

4. **Use Redis pub/sub for WebSocket at scale.** The current ConnectionManager is in-process. With multiple workers, task changes only reach connections on the same process. Redis pub/sub would broadcast to all workers.

---

## Lessons Learned

**On AI integration:** The hardest part of AI features is not the API call — it's prompt engineering. Getting Claude to return consistent JSON without preamble required explicit prompt design: "Return ONLY valid JSON with these fields, no markdown, no explanation." The mock fallback was equally important: without it, every API outage or missing key would break the entire app.

**On async Python:** Async is infectious. Once you use an async DB driver, every function that touches the DB must be async, which means every route, which means every dependency. This is a good forcing function — it ensures the entire request path is non-blocking — but it requires understanding Python's event loop well enough to avoid accidentally blocking it (e.g., with `time.sleep()` instead of `asyncio.sleep()`).

**On testing philosophy:** Testing the HTTP contract (what the endpoint returns) is more valuable than testing implementation details (which service method was called). If I change how `list_tasks` works internally but the API response stays the same, my integration tests still pass — which is exactly what I want. Unit tests catch logic errors; integration tests catch API contract violations.