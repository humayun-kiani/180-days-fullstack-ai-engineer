# ============================================================
# data/knowledge_base.py
# In-memory knowledge base articles (Days 31/32 content)
# ============================================================

ARTICLES = [
    {
        "id": "auth-001",
        "title": "JWT Token Expiration and Refresh Flow",
        "category": "authentication",
        "content": """JWT access tokens expire after 30 minutes. When a request returns 401 Unauthorized,
check the token expiry. Use the refresh endpoint: POST /api/v1/auth/refresh with your refresh token.
Refresh tokens last 7 days and are ONE-TIME USE. Store refresh tokens in httpOnly cookies.
For logout, POST /api/v1/auth/logout adds the JTI to Redis blacklist."""
    },
    {
        "id": "debug-001",
        "title": "Debugging API 500 Errors",
        "category": "debugging",
        "content": """When your API returns HTTP 500, check logs immediately: docker logs container_name --tail 100.
Common causes: unhandled exceptions, database connection failures, missing environment variables.
Add structured logging with request_id and exception traceback together."""
    },
    {
        "id": "perf-001",
        "title": "Diagnosing Slow API Response Times",
        "category": "performance",
        "content": """API response times above 500ms indicate a problem. Use EXPLAIN ANALYZE in PostgreSQL.
Add indexes on WHERE and JOIN columns. Use joinedload to avoid N+1 queries.
Cache frequently-read data in Redis with Cache-Aside pattern. Add timeout to all external calls."""
    },
    {
        "id": "db-001",
        "title": "PostgreSQL Connection Pool Configuration",
        "category": "database",
        "content": """SQLAlchemy pool: pool_size=5, max_overflow=10, pool_pre_ping=True.
Total max = pool_size + max_overflow = 15 per app instance.
With 4 Gunicorn workers: 60 total PostgreSQL connections.
Signs of exhaustion: TimeoutError QueuePool limit exceeded. Fix: use PgBouncer."""
    },
    {
        "id": "docker-001",
        "title": "Docker Container Health Checks",
        "category": "devops",
        "content": """HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3
CMD curl --fail http://localhost:8000/health.
In docker-compose: restart: unless-stopped.
Container states: starting → healthy → unhealthy. Docker restarts unhealthy containers."""
    },
    {
        "id": "deploy-001",
        "title": "Production Deployment Checklist",
        "category": "deployment",
        "content": """Before deploying: run all tests (pytest --cov=app), check for security issues,
review environment variables, backup database. During deploy: use rolling updates,
monitor health endpoint, check error rates. After deploy: verify metrics, watch logs for 30 minutes.
Deploy during off-peak hours (early morning local time)."""
    },
    {
        "id": "redis-001",
        "title": "Redis Caching Patterns",
        "category": "caching",
        "content": """Cache-Aside Pattern: check cache → miss → query DB → store with TTL.
Pitfalls: cache stampede (use locking), stale data (short TTL), memory exhaustion (maxmemory-policy allkeys-lru).
TTL guidelines: user profile 300s, task list 60s, config 3600s."""
    },
    {
        "id": "test-001",
        "title": "FastAPI Testing Best Practices",
        "category": "testing",
        "content": """Use TestClient — runs app in-process. Override get_db with SQLite in-memory.
Use conftest.py for shared fixtures. Clean database between every test.
Test 401, 403, 404, 422, 409 error cases. Coverage target: 85%+."""
    },
]

# Simulated task database
TASKS = [
    {"id": 1, "title": "Fix login 500 error", "status": "in_progress", "priority": "high", "owner": "humayun"},
    {"id": 2, "title": "Add CSV export", "status": "pending", "priority": "medium", "owner": "ali"},
    {"id": 3, "title": "Production DB slow", "status": "pending", "priority": "urgent", "owner": "humayun"},
    {"id": 4, "title": "Update API docs", "status": "done", "priority": "low", "owner": "sara"},
    {"id": 5, "title": "Redis caching for profiles", "status": "pending", "priority": "medium", "owner": "ali"},
]