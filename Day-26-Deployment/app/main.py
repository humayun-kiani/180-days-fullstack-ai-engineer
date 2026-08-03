# ============================================================
# app/main.py
# Production-ready FastAPI application
# ============================================================

import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse


# ─── Settings ────────────────────────────────────────────────

class Settings:
    APP_NAME: str = os.environ.get("APP_NAME", "Task Manager API")
    APP_VERSION: str = os.environ.get("APP_VERSION", "1.0.0")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "production")
    ALLOWED_HOSTS: list[str] = os.environ.get(
        "ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    CORS_ORIGINS: list[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")


settings = Settings()


# ─── Startup/Shutdown ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"\n{'=' * 60}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  Workers: {os.environ.get('WEB_CONCURRENCY', '4')}")
    print(f"{'=' * 60}\n")
    yield
    print("\n  Application shutting down...")


# ─── FastAPI App ─────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    # In production: disable docs to avoid exposing API structure
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)


# ─── Middleware ──────────────────────────────────────────────

# Trusted host — reject requests with wrong Host header
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS — allow only specified origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600    # cache preflight for 10 minutes
)

# Gzip — compress responses > 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_security_headers_and_logging(request: Request, call_next):
    """
    Add security headers to every response and log requests.
    """
    start = time.perf_counter()
    request_id = str(uuid.uuid4())[:8]

    # Process request
    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Security headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS — force HTTPS for 1 year (only in production)
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000; includeSubDomains"

    # Log request
    print(
        f"  {response.status_code} [{request_id}] "
        f"{request.method} {request.url.path} "
        f"{elapsed_ms:.1f}ms"
    )

    return response


# ─── Routes ──────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "day": "Day 26 — 180-Day Full Stack AI Engineer Roadmap"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Used by:
    - Docker health checks
    - Load balancers
    - Monitoring systems (Uptime Robot, Better Uptime)
    - Kubernetes liveness/readiness probes
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/info")
def app_info():
    """Application information (non-sensitive)."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "python_version": "3.11",
        "framework": "FastAPI",
        "uptime": "check /health",
    }


# ─── Error Handlers ──────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": f"The path {request.url.path} does not exist",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    # In production: also log to Sentry/Datadog
    print(f"  UNHANDLED ERROR: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )