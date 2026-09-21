# backend/app/main.py — Day 55: add profiling
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, get_db
from app.db.init_db import init_db
from app.profiling.query_profiler import profiler
from app.profiling.middleware import ProfilingMiddleware

# Import routers
from app.api import auth, tasks, ai, websocket, search, stats, export, audit
from app.api import profile as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  TaskMind — Day 55: Performance Optimization")
    print("=" * 60)

    await init_db()

    # Enable SQL query profiling
    profiler.enable(engine)
    print("  ✅ Query profiler enabled")
    print(f"  Docs: http://localhost:8000/docs\n")

    yield


app = FastAPI(
    title="TaskMind API — Performance Profiled",
    description="Day 55 — Performance Optimization",
    version="3.0.0",
    lifespan=lifespan
)

# ── Middleware (order matters: first added = outermost) ───────
app.add_middleware(ProfilingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Routes ────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "day": "Day 55 — Performance Optimization",
        "profiling": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    return {
        "name": "TaskMind API — Performance Edition",
        "profiling_endpoints": {
            "queries": "GET /api/profile/queries",
            "cache": "GET /api/profile/cache",
            "n_plus_1_demo": "GET /api/profile/n-plus-1-demo",
            "benchmark_list": "GET /api/profile/benchmark/list-tasks",
            "benchmark_search": "GET /api/profile/benchmark/search",
            "memory": "GET /api/profile/memory",
            "recommendations": "GET /api/profile/recommendations"
        }
    }