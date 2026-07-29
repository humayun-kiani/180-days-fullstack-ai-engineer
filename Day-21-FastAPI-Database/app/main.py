# ============================================================
# app/main.py
# FastAPI application factory
# ============================================================

import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Import all routers
from app.api.v1 import tasks, projects, users, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"\n{'=' * 60}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"  Docs: http://localhost:8000/docs")
    print(f"{'=' * 60}\n")

    # Create tables if they don't exist (dev only — use Alembic in prod)
    Base.metadata.create_all(bind=engine)
    print("  ✅ Database tables verified.")

    yield

    print("\n  Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Task Manager API v2.0

Now with **real PostgreSQL database** — data persists across restarts.

### What's new in v2.0 vs v1.0
- ✅ PostgreSQL persistence (no more in-memory storage)
- ✅ SQLAlchemy ORM models with relationships
- ✅ Proper migrations with Alembic
- ✅ Soft delete for tasks
- ✅ Bulk operations endpoint
- ✅ Upcoming tasks endpoint
- ✅ Project statistics endpoint
- ✅ Full-text search via PostgreSQL ILIKE

### Authentication
Demo tokens (add as `Authorization: Bearer <token>` header):
- `token-admin` → admin user (Humayun)
- `token-user` → regular user (Ali)
- No token → demo user (read-only)
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# ─── Middleware ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())[:8]
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.2f}"
    status = response.status_code
    icon = "✅" if status < 400 else "❌" if status >= 500 else "⚠️"
    print(f"  {icon} [{request_id}] {request.method:6} "
          f"{request.url.path:45} {status} {elapsed:.1f}ms")
    return response


# ─── Exception Handlers ─────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    errors = [
        {
            "field": " → ".join(str(l) for l in e["loc"] if l != "body"),
            "message": e["msg"]
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "validation_failed", "details": errors}
    )


# ─── Routers ────────────────────────────────────────────────

PREFIX = settings.API_V1_PREFIX

app.include_router(tasks.router, prefix=PREFIX)
app.include_router(projects.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(stats.router, prefix=PREFIX)


# ─── Root ───────────────────────────────────────────────────

@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
        "storage": "PostgreSQL"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning"
    )