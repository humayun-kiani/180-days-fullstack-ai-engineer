# ============================================================
# app/documents.py
# Load and prepare knowledge base documents for LangChain
# ============================================================

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Knowledge base articles (inline — no file loading needed)
KB_ARTICLES = [
    {
        "id": "debugging-001",
        "title": "How to Debug API 500 Errors",
        "category": "debugging",
        "content": """When your API returns HTTP 500 Internal Server Error, follow this systematic approach.

First, check the application logs immediately. In Docker: docker logs container_name --tail 100.
In production: tail -f /var/log/app/error.log.

Common causes of 500 errors:
1. Unhandled exceptions in route handlers — add try/except blocks
2. Database connection failures — check connection pool settings
3. Missing environment variables — verify .env file is loaded
4. Memory issues — check available RAM with free -h
5. Dependency failures — check if Redis, PostgreSQL are running

Add structured logging: log request_id, user_id, path, and exception traceback together.
If the error only happens in production, add temporary verbose logging and deploy a debug build to staging."""
    },
    {
        "id": "auth-001",
        "title": "JWT Token Expiration and Refresh Flow",
        "category": "authentication",
        "content": """JWT access tokens expire after 30 minutes in our system. This is by design for security.

When a request returns 401 Unauthorized, check the token expiry:
  payload = jwt.decode(token, options={"verify_exp": False})
  expired = payload.get("exp") < datetime.utcnow().timestamp()

To get a new access token without re-login, use the refresh token endpoint:
  POST /api/v1/auth/refresh
  Body: {"refresh_token": "your_refresh_token_here"}

Refresh tokens last 7 days. Store them in httpOnly cookies for security.
The refresh token is ONE-TIME USE. After refreshing, old token is invalidated.

For logout, call POST /api/v1/auth/logout — adds token JTI to Redis blacklist."""
    },
    {
        "id": "performance-001",
        "title": "Diagnosing Slow API Response Times",
        "category": "performance",
        "content": """API response times above 500ms indicate a performance problem.

Step 1: Identify the slow endpoint
Add timing middleware to log response time. Check X-Process-Time-Ms header in DevTools.

Step 2: Profile the endpoint
Database queries: Use EXPLAIN ANALYZE in PostgreSQL to see query plan.
Add indexes on columns used in WHERE and JOIN clauses.
Use joinedload to avoid N+1 queries.
Enable SQLAlchemy echo=True to see all SQL being executed.

Step 3: Caching
Cache frequently-read data in Redis with Cache-Aside pattern:
  check cache → miss → query DB → store in cache with TTL
Set appropriate TTL based on data freshness needs.

Step 4: External API calls
Use async/await for concurrent external requests.
Add timeout to all external calls: httpx.get(url, timeout=5.0)"""
    },
    {
        "id": "database-001",
        "title": "PostgreSQL Connection Pool Configuration",
        "category": "database",
        "content": """Connection pool size directly affects application performance.

SQLAlchemy pool configuration:
  pool_size=5 (persistent connections)
  max_overflow=10 (temporary extra connections)
  pool_pre_ping=True (verify connection before use)
  pool_recycle=3600 (recycle connections every hour)

Total max connections = pool_size + max_overflow = 15 per application instance.
With 4 Gunicorn workers: 4 × 15 = 60 total PostgreSQL connections.
PostgreSQL default max_connections = 100.

Signs of pool exhaustion:
- TimeoutError: QueuePool limit exceeded
- Application hangs on database operations

Fix: Reduce pool_size, use PgBouncer as a connection pooler."""
    },
    {
        "id": "docker-001",
        "title": "Docker Container Health Checks",
        "category": "devops",
        "content": """Health checks and restart policies keep your application running reliably.

HEALTHCHECK in Dockerfile:
  HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

In docker-compose.yml:
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "--fail", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3

Container states: starting → healthy → unhealthy
When unhealthy, Docker restarts automatically based on restart policy.
Restart policies: no, always, unless-stopped (recommended), on-failure:N"""
    },
    {
        "id": "redis-001",
        "title": "Redis Caching Patterns",
        "category": "caching",
        "content": """Redis caching dramatically improves API performance when used correctly.

Cache-Aside Pattern:
  def get_user(user_id):
      cached = redis.get(f"user:{user_id}")
      if cached: return json.loads(cached)
      user = db.query(User).get(user_id)
      redis.setex(f"user:{user_id}", 300, json.dumps(user.dict()))
      return user

Common pitfalls:
1. Cache stampede: many requests miss at same time, all hit DB
   Fix: use probabilistic early expiration or distributed locking
2. Stale data: cached value differs from database
   Fix: invalidate cache on write, use short TTL
3. Memory exhaustion: cache grows unbounded
   Fix: set maxmemory and maxmemory-policy allkeys-lru

TTL guidelines: user profile 300s, task list 60s, config 3600s"""
    },
    {
        "id": "celery-001",
        "title": "Celery Task Debugging",
        "category": "background-tasks",
        "content": """When Celery tasks fail silently or don't run, use these approaches.

Check worker status:
  celery -A worker.celery_app inspect active
  celery -A worker.celery_app inspect reserved

View task result:
  result = AsyncResult("task-id")
  print(result.status)    # PENDING, STARTED, SUCCESS, FAILURE
  print(result.traceback) # full traceback if failed

Common problems:
1. Task stuck in PENDING: worker not running or wrong queue
   Fix: verify worker consuming right queue with -Q flag
2. Task fails silently: check FAILURE state and traceback
3. Tasks running multiple times: use task_acks_late=True, make tasks idempotent
4. Memory growing: set --max-tasks-per-child=1000

Monitor with Flower: celery -A worker.celery_app flower --port=5555"""
    },
    {
        "id": "testing-001",
        "title": "FastAPI Testing Best Practices",
        "category": "testing",
        "content": """Writing reliable tests for FastAPI applications prevents regressions.

Key patterns:
1. Use TestClient — runs app in-process, no server needed
2. Override get_db dependency to use SQLite in-memory for isolation
3. Use conftest.py for shared fixtures
4. Clean database between every test (autouse fixture)
5. Generate test tokens programmatically

Test structure:
- One class per endpoint group
- Test success cases AND error cases (401, 403, 404, 422, 409)
- Use parametrize for testing multiple invalid inputs
- Assert on response body content, not just status code

Coverage: pytest --cov=app --cov-report=term-missing
Aim for 85%+ on routes and business logic."""
    },
]


def load_documents() -> list[Document]:
    """Load knowledge base as LangChain Documents."""
    docs = []
    for article in KB_ARTICLES:
        doc = Document(
            page_content=f"# {article['title']}\n\n{article['content']}",
            metadata={
                "id": article["id"],
                "title": article["title"],
                "category": article["category"]
            }
        )
        docs.append(doc)
    return docs


def split_documents(
    docs: list[Document],
    chunk_size: int = 400,
    chunk_overlap: int = 80
) -> list[Document]:
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(docs)
    print(f"  Split {len(docs)} docs → {len(chunks)} chunks")
    return chunks