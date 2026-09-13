# backend/app/main.py — Day 52 update
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.api import auth, tasks, ai, websocket
from app.api import search, stats, export, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  TaskMind v2 Backend — Day 52")
    print("  Advanced Features & Polish")
    print("=" * 60)
    await init_db()
    print(f"\n  AI: {'Claude' if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != 'your-api-key-here' else 'Mock mode'}")
    print(f"  Docs: http://localhost:8000/docs\n")
    yield


app = FastAPI(
    title="TaskMind API v2",
    description="Day 52 — Advanced Features & Polish",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Day 51 routes
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(websocket.router)

# Day 52 routes
app.include_router(search.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 52 — Advanced Features & Polish"
    }


@app.get("/")
async def root():
    return {"name": "TaskMind API v2", "docs": "/docs"}