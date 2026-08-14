# ============================================================
# data/articles.py
# Knowledge base articles for our task management system
# ============================================================

ARTICLES = [
    {
        "id": "debugging-001",
        "title": "How to Debug API 500 Errors",
        "category": "debugging",
        "content": """
When your API returns HTTP 500 Internal Server Error, follow this systematic approach.

First, check the application logs immediately. In Docker: docker logs container_name --tail 100.
In production: tail -f /var/log/app/error.log.

Common causes of 500 errors:
1. Unhandled exceptions in route handlers — add try/except blocks
2. Database connection failures — check connection pool settings
3. Missing environment variables — verify .env file is loaded
4. Memory issues — check available RAM with free -h
5. Dependency failures — check if Redis, PostgreSQL are running

To reproduce locally: copy the exact request (headers, body, method) from logs
and replay it in your dev environment with DEBUG=true enabled.

Add structured logging: log request_id, user_id, path, and exception traceback
together so you can trace the full request lifecycle.

If the error only happens in production, add temporary verbose logging
and deploy a debug build to staging to capture more context.
        """.strip(),
        "tags": ["debugging", "api", "errors", "http500"]
    },
    {
        "id": "auth-001",
        "title": "JWT Token Expiration and Refresh Flow",
        "category": "authentication",
        "content": """
JWT access tokens expire after 30 minutes in our system. This is by design for security.

When a request returns 401 Unauthorized, check the token expiry:
  payload = jwt.decode(token, options={"verify_exp": False})
  exp = payload.get("exp")
  expired = exp < datetime.utcnow().timestamp()

To get a new access token without re-login, use the refresh token endpoint:
  POST /api/v1/auth/refresh
  Body: {"refresh_token": "your_refresh_token_here"}

Refresh tokens last 7 days. Store them in httpOnly cookies for security.
Access tokens should be in memory (not localStorage) to prevent XSS.

If both tokens expire, the user must log in again. This happens after 7 days
of inactivity — this is expected behavior.

The refresh token is ONE-TIME USE. After you refresh, you receive both a new
access token and a new refresh token. The old refresh token is invalidated.

For logout, call POST /api/v1/auth/logout which adds the token JTI to the
Redis blacklist. This ensures the token is rejected even before natural expiry.
        """.strip(),
        "tags": ["auth", "jwt", "security", "tokens"]
    },
    {
        "id": "performance-001",
        "title": "Diagnosing Slow API Response Times",
        "category": "performance",
        "content": """
API response times above 500ms indicate a performance problem. Here is how to diagnose.

Step 1: Identify the slow endpoint
Add timing middleware to log response time for every request.
Our middleware adds X-Process-Time-Ms header — check this in browser DevTools.

Step 2: Profile the endpoint
Use Python's cProfile or line_profiler to find bottlenecks:
  python -m cProfile -o output.pstats your_script.py
  snakeviz output.pstats

Step 3: Common causes and fixes
Database queries:
  - Use EXPLAIN ANALYZE in PostgreSQL to see query plan
  - Add indexes on columns used in WHERE and JOIN clauses
  - Use select_related / joinedload to avoid N+1 queries
  - Enable SQLAlchemy echo=True to see all SQL being executed

Caching:
  - Cache frequently-read, rarely-changed data in Redis
  - Use Cache-Aside pattern: check cache → miss → query DB → store in cache
  - Set appropriate TTL (time-to-live) based on data freshness needs

External API calls:
  - Use async/await for concurrent external requests
  - Add timeout to all external calls: httpx.get(url, timeout=5.0)
  - Cache external API responses when possible

Step 4: Load testing
  Use locust or k6 to simulate concurrent users and find breaking points.
        """.strip(),
        "tags": ["performance", "optimization", "database", "caching"]
    },
    {
        "id": "database-001",
        "title": "PostgreSQL Connection Pool Configuration",
        "category": "database",
        "content": """
Connection pool size directly affects application performance and database stability.

SQLAlchemy pool configuration:
  engine = create_engine(
      DATABASE_URL,
      pool_size=5,          # persistent connections
      max_overflow=10,       # temporary extra connections
      pool_pre_ping=True,    # verify connection before use
      pool_recycle=3600,     # recycle connections every hour
      pool_timeout=30        # wait up to 30s for a connection
  )

Total max connections = pool_size + max_overflow = 15 per application instance.
If you run 4 Gunicorn workers: 4 × 15 = 60 total PostgreSQL connections.
PostgreSQL default max_connections = 100. Monitor with: SELECT count(*) FROM pg_stat_activity;

Signs of connection pool exhaustion:
  - TimeoutError: QueuePool limit exceeded
  - Application hangs on database operations
  - PostgreSQL logs: "too many connections"

Fixes for connection exhaustion:
  1. Reduce pool_size and max_overflow
  2. Use PgBouncer as a connection pooler (recommended for production)
  3. Reduce number of application instances
  4. Optimize queries to release connections faster

PgBouncer runs between your app and PostgreSQL and can pool thousands
of app connections into a handful of real PostgreSQL connections.
        """.strip(),
        "tags": ["database", "postgresql", "performance", "configuration"]
    },
    {
        "id": "docker-001",
        "title": "Docker Container Health Checks and Restart Policies",
        "category": "devops",
        "content": """
Health checks and restart policies keep your application running reliably in production.

HEALTHCHECK in Dockerfile:
  HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=60s \
    --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

  interval: how often to check (30s default)
  timeout: how long the check can take (10s)
  start-period: grace period after start before checking begins
  retries: failures before marked unhealthy

In docker-compose.yml:
  services:
    app:
      restart: unless-stopped    # restart on crash, not on manual stop
      healthcheck:
        test: ["CMD", "curl", "--fail", "http://localhost:8000/health"]
        interval: 30s
        timeout: 10s
        retries: 3

Container states:
  starting → healthy → unhealthy

When a container becomes unhealthy, Docker restarts it (based on restart policy).
Other services that depend_on with condition: service_healthy will wait.

Restart policies:
  no:              never restart (default)
  always:          always restart, even on manual stop
  unless-stopped:  restart unless manually stopped (recommended)
  on-failure:N:    restart only on non-zero exit, max N times
        """.strip(),
        "tags": ["docker", "devops", "health-checks", "production"]
    },
    {
        "id": "celery-001",
        "title": "Celery Task Debugging and Monitoring",
        "category": "background-tasks",
        "content": """
When Celery tasks fail silently or don't run, use these debugging approaches.

Check worker status:
  celery -A worker.celery_app inspect active
  celery -A worker.celery_app inspect reserved
  celery -A worker.celery_app inspect stats

View task result directly:
  from celery.result import AsyncResult
  result = AsyncResult("your-task-id")
  print(result.status)    # PENDING, STARTED, SUCCESS, FAILURE
  print(result.result)    # return value or exception
  print(result.traceback) # full traceback if failed

Common Celery problems:
1. Task stuck in PENDING:
   - Worker not running or not connected to broker
   - Task sent to wrong queue
   - Redis/RabbitMQ broker is down
   Fix: verify worker is consuming the right queue with -Q flag

2. Task fails silently:
   - Exception in task body not being propagated
   - Set task_always_eager=False in production
   - Check FAILURE state and read traceback

3. Tasks running multiple times:
   - Worker crashed mid-execution, task requeued
   - Set task_acks_late=True and task_reject_on_worker_lost=True
   - Make tasks idempotent (safe to run multiple times)

4. Memory growing over time:
   - Worker leak from long-running tasks
   - Set --max-tasks-per-child=1000 to recycle workers
   - Use worker_max_memory_per_child

Monitor with Flower:
  celery -A worker.celery_app flower --port=5555
        """.strip(),
        "tags": ["celery", "background-tasks", "debugging", "monitoring"]
    },
    {
        "id": "redis-001",
        "title": "Redis Caching Patterns and Pitfalls",
        "category": "caching",
        "content": """
Redis caching dramatically improves API performance when used correctly.

Cache-Aside Pattern (most common):
  def get_user(user_id: int) -> User:
      cache_key = f"user:{user_id}"
      cached = redis_client.get(cache_key)
      if cached:
          return json.loads(cached)          # cache hit!
      user = db.query(User).get(user_id)    # cache miss → DB query
      redis_client.setex(cache_key, 300, json.dumps(user.dict()))
      return user

Common pitfalls:
1. Cache stampede: many requests miss at same time, all hit DB
   Fix: use probabilistic early expiration or distributed locking

2. Stale data: cached value differs from database
   Fix: invalidate cache on write, use short TTL for changing data

3. Cache key collisions: two different data types use same key pattern
   Fix: use namespaced keys like "user:123", "task:456", "project:789"

4. Memory exhaustion: cache grows unbounded
   Fix: set maxmemory and maxmemory-policy allkeys-lru in Redis config

5. Caching exceptions or None values:
   If a user is not found, don't skip caching — cache the None!
   Otherwise every request for non-existent user hits the database.

TTL guidelines:
  User profile: 300s (5 minutes)
  Task list: 60s (1 minute)
  Config/settings: 3600s (1 hour)
  Auth tokens blacklist: match token expiry
  API rate limit counters: 60s
        """.strip(),
        "tags": ["redis", "caching", "performance", "patterns"]
    },
    {
        "id": "nginx-001",
        "title": "Nginx Rate Limiting Configuration",
        "category": "infrastructure",
        "content": """
Nginx rate limiting protects your API from abuse and brute force attacks.

Define rate limit zones in nginx.conf http block:
  limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
  limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

  api_limit:  30 requests/second per IP (burst allowed)
  auth_limit: 5 requests/minute per IP (strict for login)

Apply in server block:
  location /api/ {
      limit_req zone=api_limit burst=50 nodelay;
      proxy_pass http://app:8000;
  }

  location /api/v1/auth/login {
      limit_req zone=auth_limit burst=10 nodelay;
      proxy_pass http://app:8000;
  }

Parameters:
  burst: allows temporary spike above rate
  nodelay: return 429 immediately when burst exceeded (not queue)
  delay: delay requests instead of rejecting (omit nodelay)

HTTP 429 Too Many Requests is returned when rate exceeded.
Add Retry-After header in your application to tell clients when to retry.

For legitimate high-traffic clients, use API keys with per-key rate limits
instead of per-IP, since multiple users might share an IP (corporate NAT).
        """.strip(),
        "tags": ["nginx", "rate-limiting", "security", "infrastructure"]
    },
    {
        "id": "testing-001",
        "title": "FastAPI Testing Best Practices",
        "category": "testing",
        "content": """
Writing reliable tests for FastAPI applications prevents regressions.

Key patterns:
1. Use TestClient from fastapi.testclient — runs app in-process, no server needed
2. Override get_db dependency to use SQLite in-memory for isolation
3. Use conftest.py for shared fixtures
4. Clean database state between every test (autouse fixture)
5. Generate test tokens programmatically — don't use hardcoded strings

Database override:
  app.dependency_overrides[get_db] = override_get_db
  # This replaces the real DB with SQLite for all test requests

Test structure:
  - One class per endpoint group (TestCreateTask, TestListTasks)
  - Test success cases AND error cases (401, 403, 404, 422, 409)
  - Use pytest.mark.parametrize for testing multiple invalid inputs
  - Assert on response body content, not just status code

Common mistakes:
  - Sharing database state between tests → flaky, order-dependent tests
  - Testing with production database → destructive!
  - Not testing authentication → missing entire security layer
  - Only testing happy path → real bugs hide in edge cases

Coverage:
  pytest --cov=app --cov-report=term-missing
  Aim for 85%+ on routes and business logic
  100% is often not worth the effort on configuration code
        """.strip(),
        "tags": ["testing", "fastapi", "pytest", "best-practices"]
    },
    {
        "id": "websocket-001",
        "title": "WebSocket Connection Debugging",
        "category": "websockets",
        "content": """
WebSocket issues are harder to debug than HTTP because the protocol is persistent.

Common WebSocket problems:

1. Connection drops after timeout:
   Nginx and load balancers have read timeouts.
   For WebSocket: proxy_read_timeout 3600s; in Nginx config
   Also implement client-side reconnection with exponential backoff.

2. Messages not delivered:
   Check if connection is still open before sending:
   try: await websocket.send_json(data)
   except (RuntimeError, WebSocketDisconnect): cleanup()

3. Race conditions in connection manager:
   Multiple coroutines modifying the connection list simultaneously.
   Use asyncio.Lock() for thread-safe operations.

4. Authentication failure at connect:
   WebSocket auth happens at connection time (JWT in query param or first message).
   Close with code 4001 for auth failure: await websocket.close(code=4001)

5. Memory leak from dead connections:
   Connections that disconnect without WebSocketDisconnect exception.
   Implement periodic ping/pong to detect dead connections:
   await websocket.send_json({"type": "ping"})
   Set timeout: asyncio.wait_for(websocket.receive(), timeout=30)

Testing WebSockets:
  with client.websocket_connect("/ws?token=...") as ws:
      ws.send_json({"type": "ping"})
      response = ws.receive_json()
      assert response["type"] == "pong"
        """.strip(),
        "tags": ["websockets", "debugging", "realtime", "nginx"]
    },
    {
        "id": "git-001",
        "title": "Git Workflow for the 180-Day Project",
        "category": "workflow",
        "content": """
Consistent git practices keep your 180-day project history clean and useful.

Branch strategy (simple, solo project):
  main branch: always working, deployable code
  feature branches: day-XX-feature-name (merge when done)

Daily commit workflow:
  git status                          # see what changed
  git add Day-XX-ProjectName/         # stage only the day's folder
  git commit -m "Day XX: Add [what] - [key technologies used]"
  git push origin main

Good commit messages:
  Day 27: Add Task Priority Predictor - ML pipeline, Random Forest, 89% accuracy
  Day 28: Add NLP Text Analyzer - TF-IDF, text classification, sentiment

Bad commit messages:
  "update"
  "fix stuff"
  "day 27"

README update checklist for each day:
  - What I Learned (specific, technical)
  - What I Built (concrete, with metrics)
  - How to Run (exact commands)
  - Link back to master README

Keep .gitignore clean:
  - venv/ always excluded
  - .env always excluded (never commit secrets)
  - __pycache__/ always excluded
  - Generated files (models, reports) excluded

For large model files: use Git LFS or just add to .gitignore
and document how to regenerate them in the README.
        """.strip(),
        "tags": ["git", "workflow", "best-practices", "version-control"]
    },
    {
        "id": "logging-001",
        "title": "Structured Logging in FastAPI",
        "category": "observability",
        "content": """
Structured logging makes it possible to search and analyze logs programmatically.

Basic structured logging with Python:
  import logging
  import json

  class JSONFormatter(logging.Formatter):
      def format(self, record):
          log_data = {
              "timestamp": self.formatTime(record),
              "level": record.levelname,
              "message": record.getMessage(),
              "logger": record.name,
          }
          if hasattr(record, "extra"):
              log_data.update(record.extra)
          return json.dumps(log_data)

Adding request context to every log:
  Use a middleware that adds request_id to logging context.
  Then every log from that request includes the request_id.
  This allows tracing all logs for one request across multiple services.

Log levels:
  DEBUG:    development only, very verbose
  INFO:     normal operations (request received, task started)
  WARNING:  unexpected but handled (rate limit hit, retry)
  ERROR:    operation failed but app continues (failed request)
  CRITICAL: application cannot continue (DB unavailable)

In production:
  - Set LOG_LEVEL=WARNING to reduce noise
  - Send logs to centralized system (ELK stack, Datadog, CloudWatch)
  - Never log passwords, tokens, or PII (personal info)
  - Log request_id so you can trace issues end-to-end

Correlation IDs:
  Add X-Request-ID header to every request.
  Log this ID with every log entry.
  Pass it to downstream services.
  Now you can find all logs for one user action across all services.
        """.strip(),
        "tags": ["logging", "observability", "monitoring", "fastapi"]
    },
]