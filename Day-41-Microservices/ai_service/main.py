# ============================================================
# ai_service/main.py
# AI Service — Priority classification, standalone
# Port: 8003
# ============================================================

import os
import re
import time
from datetime import datetime
from contextlib import asynccontextmanager

import anthropic
from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.tracing import RequestTracingMiddleware, ServiceLogger

log = ServiceLogger("ai-service")


# ─── Keyword classifier (no LLM needed) ──────────────────────

URGENT = {"urgent", "critical", "p0", "emergency", "down", "outage",
          "breach", "all users", "production", "immediate", "incident"}
HIGH   = {"fix", "bug", "error", "broken", "failing", "crash",
          "before", "deadline", "slow", "security"}
MEDIUM = {"add", "implement", "feature", "improve", "enhance",
          "create", "build", "integrate", "new"}


def keyword_classify(task: str) -> str:
    t = task.lower()
    for kw in URGENT:
        if kw in t: return "urgent"
    for kw in HIGH:
        if kw in t: return "high"
    for kw in MEDIUM:
        if kw in t: return "medium"
    return "low"


# ─── Claude classifier ────────────────────────────────────────

_client = None

FEW_SHOT = """Classify task priority. Respond ONE WORD: urgent, high, medium, or low.

Examples:
"URGENT: Production API down" → urgent
"Fix login bug before release" → high
"Add dark mode feature" → medium
"Update README docs" → low

Task: "{task}"
Priority:"""


def claude_classify(task: str) -> tuple[str, str]:
    """Returns (priority, method_used)."""
    global _client
    if _client is None:
        return keyword_classify(task), "keyword_fallback"

    try:
        r = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=5,
            temperature=0.0,
            messages=[{"role": "user",
                       "content": FEW_SHOT.format(task=task)}]
        )
        result = re.sub(r'[^a-z]', '',
                        r.content[0].text.strip().lower())
        if result in ("urgent", "high", "medium", "low"):
            return result, "claude"
        return keyword_classify(task), "keyword_fallback"
    except Exception as e:
        log.warning(f"Claude unavailable: {e}")
        return keyword_classify(task), "keyword_fallback"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and api_key != "your-api-key-here":
        _client = anthropic.Anthropic(api_key=api_key)
        log.info("AI Service: Claude API available")
    else:
        log.info("AI Service: no API key — using keyword fallback")
    log.info("AI Service starting on port 8003")
    yield
    log.info("AI Service shutting down")


app = FastAPI(
    title="AI Service",
    description="Task priority classification — microservice #3",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(RequestTracingMiddleware, service_name="ai-service")


# ─── Schemas ─────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    task: str = Field(min_length=1, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {"task": "URGENT: Production API down for all users"}
        }


class BatchClassifyRequest(BaseModel):
    tasks: list[str] = Field(min_length=1, max_length=50)


# ─── Endpoints ────────────────────────────────────────────────

@app.post("/ai/classify")
def classify(request: ClassifyRequest) -> dict:
    """Classify task priority using AI or keyword fallback."""
    start = time.perf_counter()
    priority, method = claude_classify(request.task)
    latency = (time.perf_counter() - start) * 1000

    log.info(f"Classified '{request.task[:40]}...' → {priority} ({method})")

    return {
        "task": request.task,
        "priority": priority,
        "method": method,
        "latency_ms": round(latency, 1)
    }


@app.post("/ai/classify/batch")
def classify_batch(request: BatchClassifyRequest) -> dict:
    """Classify multiple tasks at once."""
    results = []
    for task in request.tasks:
        priority, method = claude_classify(task)
        results.append({
            "task": task[:60],
            "priority": priority,
            "method": method
        })
    return {"results": results, "count": len(results)}


@app.get("/ai/health")
def ai_health() -> dict:
    return {
        "service": "ai-service",
        "status": "healthy",
        "claude_available": _client is not None,
        "fallback": "keyword_classifier",
        "port": 8003,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health() -> dict:
    return ai_health()


@app.get("/")
def root() -> dict:
    return {
        "service": "ai-service",
        "version": "1.0.0",
        "endpoints": {
            "classify": "POST /ai/classify",
            "batch": "POST /ai/classify/batch",
            "health": "GET /health"
        }
    }