# Day 35 — AI-Powered API Integration: Multi-Source Data Agent

> **Phase 3 — AI & Machine Learning** | Week 6 | Day 35 of 180

---

## 📌 What I Learned Today

- External API authentication patterns: API key, Bearer token, query param
- httpx.AsyncClient: async HTTP client for non-blocking API calls
- asyncio.gather(): run multiple coroutines simultaneously
- return_exceptions=True: don't fail all if one request fails
- response.raise_for_status(): raise on 4xx/5xx responses
- httpx.TimeoutException, HTTPStatusError, RequestError — specific error types
- Rate limiting: token bucket algorithm with asyncio.Lock
- asyncio.Lock: prevent race conditions in async code
- RateLimiter.acquire(): wait if rate limit exceeded
- Response transformation: extract relevant fields, reduce token count
- WMO weather codes → human-readable conditions
- Open-Meteo: free weather API, no key, 60 req/min
- REST Countries: country data by name
- HackerNews Firebase: nested API calls for stories + details
- Parallel tool execution in agent: asyncio.gather on tool calls
- Claude tool_use with parallel calls: multiple tool_use blocks in one response
- CITY_COORDS dict: precomputed lat/lon for common cities
- Graceful degradation: return error dict, never raise to caller
- MockAPIHubAgent: keyword routing to real API calls for dev

## 🔨 Project Built

**AI API Hub** — 5 real external API integrations:

**APIs (all free, 4 require no key):**

- Open-Meteo: weather by city with WMO code mapping
- GitHub REST: repo info, trending via search, user profiles
- Open.er-api.com: exchange rates and currency conversion
- HackerNews Firebase: top/new/best stories with parallel detail fetch
- REST Countries: population, capital, languages, currencies

**AsyncRateLimiter:**

- Token bucket algorithm
- asyncio.Lock for thread safety
- Per-API limiter configuration
- Available calls property

**APIHubAgent (2 modes):**

- MockAPIHubAgent: keyword-based routing to real APIs
- APIHubAgent: Claude routes tool calls via tool_use API
- Parallel execution: asyncio.gather on ALL tool calls simultaneously

**FastAPI endpoints:**

- POST /ask: agent (Claude or mock) answers any question
- GET /api/weather/{city}: direct weather endpoint
- GET /api/github/{owner}/{repo}: repo info
- GET /api/github/trending: trending repos with language filter
- GET /api/rates/{currency}: exchange rates
- GET /api/convert: currency conversion
- GET /api/hn/top: HackerNews stories
- GET /api/country/{name}: country data
- GET /demo/parallel: fetch 4 APIs simultaneously in one request

## 🚀 How to Run

```bash
cd Day-35-AI-API-Hub
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Optional: echo "ANTHROPIC_API_KEY=your-key" > .env

uvicorn app.main:app --reload

# Ask the agent
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Karachi?"}'

# Parallel demo
curl http://localhost:8000/demo/parallel
```

## 🧠 Why Parallel API Calls Matter

| Approach                  | Time for 4 APIs |
| ------------------------- | --------------- |
| Sequential (one by one)   | ~3200ms         |
| Parallel (asyncio.gather) | ~800ms          |
| **Speedup**               | **4x faster**   |

asyncio.gather() is the key: all HTTP requests fly simultaneously.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
