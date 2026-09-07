# backend/app/main.py
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.init_db import init_db
from app.api import auth, tasks, ai, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  TaskMind Backend — Day 51")
    print("  Full Stack AI Application")
    print("=" * 60)

    await init_db()

    print(f"\n  Environment: {settings.ENVIRONMENT}")
    print(f"  AI mode: {'Real (Claude)' if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != 'your-api-key-here' else 'Mock'}")
    print(f"  Docs: http://localhost:8000/docs\n")

    yield
    print("\n  Shutting down TaskMind...")


app = FastAPI(
    title="TaskMind API",
    description="""
## TaskMind — AI-Powered Task Management

Full stack AI application with:
- JWT authentication
- CRUD task management with PostgreSQL
- Redis caching
- Claude AI for task analysis, expansion, and breakdown
- WebSocket for real-time updates

### Day 51 — Full Stack AI Application
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TaskMind API",
        "day": "Day 51 — Full Stack AI Application"
    }


@app.get("/")
async def root():
    return {
        "name": "TaskMind API",
        "docs": "/docs",
        "health": "/health"
    }