# ============================================================
# app/main.py
# AI API Hub — Day 35
# ============================================================

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.agent import APIHubAgent
from apis.weather import get_weather
from apis.github_api import get_repo_info, get_trending_repos, get_user_profile
from apis.exchange_rates import get_exchange_rates, convert_currency
from apis.hackernews import get_top_stories
from apis.countries import get_country_info

_agent: APIHubAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    print("\n" + "=" * 60)
    print("  AI API Hub — Day 35")
    print("  Multi-Source Data Agent with 5 Real APIs")
    print("=" * 60)

    _agent = APIHubAgent()
    mode = "Mock (rule-based routing)" if _agent.mock else "Real (Claude API)"
    print(f"\n  Agent mode: {mode}")
    print(f"  APIs: Weather, GitHub, Exchange Rates, HackerNews, Countries")
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="AI API Hub",
    description="""
## 🌐 AI API Hub — Day 35

An AI agent that fetches real-time data from 5 external APIs.

### Available APIs
| API | Source | Auth |
|-----|--------|------|
| Weather | Open-Meteo | None (free) |
| GitHub | GitHub REST API | Optional token |
| Exchange Rates | Open.er-api.com | None (free) |
| HackerNews | Firebase API | None (free) |
| Countries | REST Countries | None (free) |

### How it works
1. Send a natural language query to `POST /ask`
2. The agent decides which APIs to call based on your question
3. APIs are called **in parallel** for speed
4. Results are synthesized into a coherent answer

### Example queries
- "What's the weather in Karachi and London?"
- "Show me trending Python repos on GitHub"
- "How much is 1000 USD in PKR?"
- "What are the top tech stories today?"
- "Tell me about Pakistan"
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Schemas ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    message: str = Field(
        min_length=5,
        max_length=500,
        example="What's the weather in Karachi and what are the top tech stories today?"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's the weather in Karachi and what are today's top HN stories?"
            }
        }


class AskResponse(BaseModel):
    answer: str
    tools_called: list[str]
    latency_ms: float
    agent_mode: str


# ─── Main Agent Endpoint ─────────────────────────────────────

@app.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the AI API Hub agent",
    description="""
Ask any question that requires real-time data. The agent will:
1. Determine which APIs are relevant
2. Fetch data from multiple sources in parallel
3. Synthesize a comprehensive answer

**Try these queries:**
- "What's the weather in Karachi?"
- "Show me trending Python repos this week"
- "Convert 500 EUR to PKR"
- "Top HN stories today"
- "Tell me about Japan"
    """
)
async def ask(request: AskRequest) -> AskResponse:
    if _agent is None:
        raise HTTPException(503, "Agent not initialized")

    start = time.perf_counter()
    result = await _agent.run(request.message)
    elapsed = (time.perf_counter() - start) * 1000

    return AskResponse(
        answer=result["answer"],
        tools_called=result["tools_called"],
        latency_ms=round(elapsed, 1),
        agent_mode="mock" if _agent.mock else "claude"
    )


# ─── Direct API Endpoints ─────────────────────────────────────

@app.get("/api/weather/{city}", summary="Get weather for a city")
async def weather(city: str) -> dict:
    """Get current weather directly (bypasses the agent)."""
    return await get_weather(city)


@app.get("/api/github/{owner}/{repo}", summary="Get GitHub repo info")
async def github_repo(owner: str, repo: str) -> dict:
    return await get_repo_info(owner, repo)


@app.get("/api/github/trending", summary="Get trending GitHub repos")
async def github_trending(
    language: str = Query("", description="Programming language filter"),
    since: str = Query("daily", description="Period: daily, weekly, monthly")
) -> dict:
    return await get_trending_repos(language=language, since=since)


@app.get("/api/rates/{currency}", summary="Get exchange rates")
async def exchange_rates(currency: str) -> dict:
    return await get_exchange_rates(currency.upper())


@app.get("/api/convert", summary="Convert currency")
async def currency_convert(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code")
) -> dict:
    return await convert_currency(amount, from_currency, to_currency)


@app.get("/api/hn/top", summary="Get HackerNews top stories")
async def hackernews_top(
    count: int = Query(5, ge=1, le=20),
    story_type: str = Query("top", description="top, new, best, ask, show")
) -> dict:
    return await get_top_stories(count=count, story_type=story_type)


@app.get("/api/country/{country_name}", summary="Get country information")
async def country(country_name: str) -> dict:
    return await get_country_info(country_name)


# ─── Multi-source Demo ────────────────────────────────────────

@app.get("/demo/parallel", summary="Demo — fetch 4 APIs in parallel")
async def parallel_demo() -> dict:
    """Demonstrate parallel API fetching speed."""
    start = time.perf_counter()

    results = await asyncio.gather(
        get_weather("Karachi"),
        get_exchange_rates("USD"),
        get_top_stories(count=3),
        get_country_info("Pakistan"),
        return_exceptions=True
    )

    elapsed = (time.perf_counter() - start) * 1000
    names = ["weather_karachi", "exchange_rates_usd", "hackernews_top3", "country_pakistan"]

    return {
        "message": f"Fetched 4 real APIs simultaneously in {elapsed:.0f}ms",
        "latency_ms": round(elapsed, 1),
        "results": {
            name: (r if not isinstance(r, Exception) else {"error": str(r)})
            for name, r in zip(names, results)
        }
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "agent_mode": "mock" if (_agent and _agent.mock) else "claude",
        "apis": ["open-meteo", "github", "exchange-rate", "hackernews", "restcountries"],
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 35 — AI-Powered API Integration"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "AI API Hub",
        "day": "Day 35 — Multi-Source Data Agent",
        "docs": "/docs",
        "demo": "/demo/parallel",
        "endpoints": {
            "ask_agent": "POST /ask",
            "weather": "GET /api/weather/{city}",
            "github_repo": "GET /api/github/{owner}/{repo}",
            "trending": "GET /api/github/trending",
            "rates": "GET /api/rates/{currency}",
            "convert": "GET /api/convert",
            "hackernews": "GET /api/hn/top",
            "country": "GET /api/country/{name}",
            "parallel_demo": "GET /demo/parallel"
        }
    }