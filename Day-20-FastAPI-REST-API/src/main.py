# ============================================================
# src/main.py
# FastAPI Application — Task Management REST API
# Day 20 — 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from routers import tasks, projects, tags, stats

# Import exception handlers
from src.exceptions import setup_exception_handlers


# ─── Lifespan — Startup and Shutdown ────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Modern replacement for @app.on_event("startup").
    """
    # ── STARTUP ──
    print("\n" + "=" * 60)
    print("  TASK MANAGER API — Starting up")
    print("=" * 60)
    print(f"  Docs:     http://localhost:8000/docs")
    print(f"  ReDoc:    http://localhost:8000/redoc")
    print(f"  Health:   http://localhost:8000/health")
    print(f"  Stats:    http://localhost:8000/stats")
    print("=" * 60 + "\n")

    yield    # API is running

    # ── SHUTDOWN ──
    print("\n  Task Manager API shutting down...")


# ─── Create FastAPI App ─────────────────────────────────────

app = FastAPI(
    title="Task Manager API",
    description="""
## 📋 Task Manager REST API

A complete task management system built with **FastAPI** as part of the
**180-Day Full Stack AI Engineer Roadmap**.

### Features
- ✅ Full CRUD for **Tasks**, **Projects**, and **Tags**
- 🔍 Advanced filtering, sorting, and pagination
- ✅ Pydantic validation on all inputs
- 🔒 Dependency injection for auth and database
- 📊 Statistics dashboard endpoint
- 🚀 Background tasks for notifications
- 📖 Auto-generated interactive documentation

### Authentication
For demo purposes, no auth is required. You can optionally add:
- `Authorization: Bearer token-humayun-admin` for admin access
- `Authorization: Bearer token-ali-user` for regular user

### Quick Start
1. Create a project: `POST /projects`
2. Create tasks: `POST /tasks`
3. Update status: `PUT /tasks/{id}` or `PATCH /tasks/{id}/complete`
4. View stats: `GET /stats`
    """,
    version="1.0.0",
    contact={
        "name": "Humayun Kiani",
        "url": "https://github.com/humayun-kiani/180-days-fullstack-ai-engineer"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ─── Middleware ──────────────────────────────────────────────

# CORS — allow all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    """Add timing and request ID to every response."""
    start = time.perf_counter()
    request_id = str(uuid.uuid4())[:8]

    # Add request ID to request state (accessible in endpoints)
    request.state.request_id = request_id

    # Process the request
    response = await call_next(request)

    # Add custom headers
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

    # Log request
    status = response.status_code
    method = request.method
    path = request.url.path
    color = "✅" if status < 400 else "❌" if status >= 500 else "⚠️"
    print(f"  {color} [{request_id}] {method:6} {path:40} {status} {elapsed_ms:.1f}ms")

    return response


# ─── Register Exception Handlers ───────────────────────────

setup_exception_handlers(app)


# ─── Include Routers ────────────────────────────────────────

app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(tags.router)
app.include_router(stats.router)


# ─── Root Endpoint ──────────────────────────────────────────

@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Returns basic API information."
)
def root():
    return {
        "name": "Task Manager API",
        "version": "1.0.0",
        "day": "Day 20 — FastAPI REST API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "stats": "/stats",
        "endpoints": {
            "tasks": "/tasks",
            "projects": "/projects",
            "tags": "/tags"
        }
    }


# ─── Run Directly ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning"    # suppress uvicorn's own logs (we have middleware)
    )