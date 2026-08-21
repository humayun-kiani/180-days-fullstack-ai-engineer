# ============================================================
# app/knowledge_base.py
# Simple keyword-based KB for Day 31 integration without ChromaDB
# ============================================================

ARTICLES = {
    "jwt": {
        "title": "JWT Token Expiration and Refresh Flow",
        "content": """JWT access tokens expire after 30 minutes. When a request returns 401 Unauthorized,
use the refresh endpoint: POST /api/v1/auth/refresh with your refresh token.
Refresh tokens last 7 days and are ONE-TIME USE. Store in httpOnly cookies.
For logout, POST /api/v1/auth/logout adds the JTI to Redis blacklist."""
    },
    "500": {
        "title": "Debugging API 500 Errors",
        "content": """Check logs immediately: docker logs container_name --tail 100.
Common causes: unhandled exceptions, database connection failures, missing env vars.
Add structured logging with request_id and exception traceback together.
If only in production: add temporary debug logging to staging."""
    },
    "performance": {
        "title": "Diagnosing Slow API Response Times",
        "content": """API response times above 500ms indicate a problem.
Use EXPLAIN ANALYZE in PostgreSQL to see query plans.
Add indexes on WHERE and JOIN columns. Use joinedload to avoid N+1 queries.
Cache frequently-read data in Redis with Cache-Aside pattern."""
    },
    "database": {
        "title": "PostgreSQL Connection Pool Configuration",
        "content": """SQLAlchemy pool: pool_size=5, max_overflow=10, pool_pre_ping=True.
Total max connections = pool_size + max_overflow = 15 per app instance.
Signs of exhaustion: TimeoutError QueuePool limit exceeded.
Fix: reduce pool_size, use PgBouncer connection pooler."""
    },
    "docker": {
        "title": "Docker Container Health Checks",
        "content": """HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3
CMD curl --fail http://localhost:8000/health.
Restart policy: unless-stopped for production.
Container states: starting → healthy → unhealthy."""
    },
    "redis": {
        "title": "Redis Caching Patterns",
        "content": """Cache-Aside Pattern: check cache → miss → query DB → store with TTL.
Pitfalls: cache stampede (use locking), stale data (short TTL), memory exhaustion.
TTL guidelines: user profile 300s, task list 60s, config 3600s."""
    },
    "deploy": {
        "title": "Production Deployment Checklist",
        "content": """Before deploying: run all tests, check for security issues, backup database.
During deploy: use rolling updates, monitor health endpoint, check error rates.
After deploy: verify metrics, watch logs for 30 minutes.
Deploy during off-peak hours."""
    },
    "testing": {
        "title": "FastAPI Testing Best Practices",
        "content": """Use TestClient — runs app in-process. Override get_db with SQLite in-memory.
Test 401, 403, 404, 422, 409 error cases.
Use pytest.mark.parametrize for multiple invalid inputs.
Coverage target: 85%+."""
    }
}


def search_kb(query: str, top_k: int = 2) -> list[dict]:
    """Simple keyword search over the knowledge base."""
    query_words = set(query.lower().split())
    scored = []

    for key, article in ARTICLES.items():
        text = f"{article['title']} {article['content']}".lower()
        score = sum(1 for w in query_words if w in text)
        if score > 0:
            scored.append((score, key, article))

    scored.sort(reverse=True)
    return [{"id": k, "title": a["title"], "content": a["content"]}
            for _, k, a in scored[:top_k]]