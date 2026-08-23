# ============================================================
# gateway/main.py
# API Gateway — single entry point, routes to services
# Port: 8000
# ============================================================

import os
import uuid
import time
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.tracing import RequestTracingMiddleware, ServiceLogger

log = ServiceLogger("api-gateway")

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
TASK_URL = os.environ.get("TASK_SERVICE_URL", "http://localhost:8002")
AI_URL   = os.environ.get("AI_SERVICE_URL",   "http://localhost:8003")

# Route table: gateway prefix → service base URL
ROUTES = {
    "/api/auth": AUTH_URL,
    "/api/tasks": TASK_URL,
    "/api/ai": AI_URL,
}

# Simple in-memory rate limiter
_request_counts: dict[str, list[float]] = {}
RATE_LIMIT_PER_MINUTE = 60


def check_rate_limit(client_ip: str) -> bool:
    """Allow up to RATE_LIMIT_PER_MINUTE requests per minute per IP."""
    now = time.time()
    cutoff = now - 60

    counts = _request_counts.get(client_ip, [])
    counts = [t for t in counts if t > cutoff]    # keep last 60s
    counts.append(now)
    _request_counts[client_ip] = counts

    return len(counts) <= RATE_LIMIT_PER_MINUTE


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("API Gateway starting on port 8000")
    log.info(f"Routes: {list(ROUTES.keys())}")
    log.info(f"Upstream services: {AUTH_URL}, {TASK_URL}, {AI_URL}")
    yield
    log.info("API Gateway shutting down")


app = FastAPI(
    title="API Gateway",
    description="""
## 🚪 API Gateway — Day 41

Single entry point for all microservices.

### Routes
| Gateway Path | Upstream Service |
|-------------|-----------------|
| `/api/auth/*` | Auth Service :8001 |
| `/api/tasks/*` | Task Service :8002 |
| `/api/ai/*` | AI Service :8003 |

### Features
- Request routing to correct service
- X-Request-ID distributed tracing
- Rate limiting (60 req/min per IP)
- Health aggregation
- Circuit breaker status
    """,
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(RequestTracingMiddleware, service_name="api-gateway")


# ─── Main proxy ───────────────────────────────────────────────

@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Route request to appropriate microservice"
)
async def proxy(path: str, request: Request) -> Response:
    """
    Route incoming request to the correct upstream service.

    1. Rate limit check
    2. Find matching route
    3. Forward request with tracing headers
    4. Return upstream response
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        log.warning(f"Rate limited: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests", "retry_after": 60}
        )

    full_path = f"/api/{path}"

    # Find matching route
    target_base = None
    matched_prefix = None
    for prefix, base_url in ROUTES.items():
        if full_path.startswith(prefix):
            # Ensure we match on path boundary
            remaining = full_path[len(prefix):]
            if remaining == "" or remaining.startswith("/"):
                target_base = base_url
                matched_prefix = prefix
                break

    if not target_base:
        log.warning(f"No route found for: {full_path}")
        return JSONResponse(
            status_code=404,
            content={
                "error": f"No service handles {full_path}",
                "available_routes": list(ROUTES.keys())
            }
        )

    # Build target URL
    remaining_path = full_path[len(matched_prefix):]
    target_url = f"{target_base}{matched_prefix}{remaining_path}"

    # Build forwarding headers
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}

    # Add/propagate tracing headers
    if "x-request-id" not in {k.lower() for k in headers}:
        headers["x-request-id"] = str(uuid.uuid4())[:8]
    headers["x-forwarded-by"] = "api-gateway"
    headers["x-forwarded-for"] = client_ip

    start = time.perf_counter()
    log.info(f"Routing {request.method} {full_path} → {target_url}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params)
            )

        elapsed = (time.perf_counter() - start) * 1000
        log.info(f"← {upstream_response.status_code} in {elapsed:.0f}ms")

        # Build response headers
        response_headers = dict(upstream_response.headers)
        response_headers["X-Response-Time-Ms"] = str(round(elapsed, 1))
        response_headers["X-Routed-To"] = matched_prefix

        # Remove hop-by-hop headers
        for h in ("transfer-encoding", "connection"):
            response_headers.pop(h, None)

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=response_headers,
            media_type=upstream_response.headers.get("content-type")
        )

    except httpx.ConnectError:
        log.error(f"Connection refused to {target_url}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service unavailable",
                "service": matched_prefix,
                "detail": "Could not connect to upstream service"
            }
        )
    except httpx.TimeoutException:
        log.error(f"Timeout calling {target_url}")
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway timeout", "service": matched_prefix}
        )


# ─── Health aggregation ───────────────────────────────────────

@app.get("/health", summary="Aggregate health from all services")
async def gateway_health() -> dict:
    """
    Check health of all upstream services.

    Returns aggregate status: healthy if all up, degraded if some down.
    """
    service_health = {}
    statuses = []

    async with httpx.AsyncClient(timeout=3.0) as client:
        for prefix, base_url in ROUTES.items():
            service_name = prefix.lstrip("/api/")
            try:
                r = await client.get(f"{base_url}/health")
                service_health[service_name] = {
                    "status": "up" if r.status_code == 200 else "degraded",
                    "status_code": r.status_code,
                    "data": r.json() if r.status_code == 200 else {}
                }
                statuses.append("up" if r.status_code == 200 else "degraded")
            except Exception as e:
                service_health[service_name] = {
                    "status": "down",
                    "error": str(e)[:80]
                }
                statuses.append("down")

    if all(s == "up" for s in statuses):
        overall = "healthy"
    elif any(s == "down" for s in statuses):
        overall = "degraded"
    else:
        overall = "degraded"

    return {
        "gateway": "healthy",
        "overall": overall,
        "services": service_health,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/routes", summary="List all configured routes")
def list_routes() -> dict:
    return {
        "routes": [
            {"prefix": prefix, "upstream": url}
            for prefix, url in ROUTES.items()
        ]
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "API Gateway",
        "day": "Day 41 — Microservices Architecture",
        "docs": "/docs",
        "health": "/health",
        "routes": list(ROUTES.keys()),
        "usage": "All requests go through /api/* prefix"
    }