# backend/app/profiling/middleware.py
# FastAPI middleware for request-level profiling

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.profiling.query_profiler import profiler


class ProfilingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that profiles every request:
    - Query count and total DB time
    - Request duration
    - Slow query detection
    - N+1 detection

    Adds X-Query-Count and X-DB-Time-Ms headers to every response.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        profiler.start_request()
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        summary = profiler.end_request()

        # Add profiling headers to response
        response.headers["X-Request-Time-Ms"] = str(round(duration_ms, 1))
        response.headers["X-Query-Count"] = str(summary.get("query_count", 0))
        response.headers["X-DB-Time-Ms"] = str(summary.get("total_db_ms", 0))

        # Log slow requests
        if duration_ms > 500 or summary.get("query_count", 0) > 10:
            print(
                f"\n  ⚠️  SLOW REQUEST: {request.method} {request.url.path}\n"
                f"     Duration: {duration_ms:.0f}ms\n"
                f"     Queries: {summary.get('query_count', 0)}\n"
                f"     DB time: {summary.get('total_db_ms', 0)}ms\n"
                f"     N+1 warnings: {len(summary.get('potential_n_plus_1', []))}"
            )

        # Store in request state for profile endpoint
        request.state.profile = summary

        return response