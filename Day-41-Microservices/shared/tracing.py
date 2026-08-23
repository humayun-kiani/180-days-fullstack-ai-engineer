# ============================================================
# shared/tracing.py
# Distributed tracing utilities shared across services
# ============================================================

import uuid
import logging
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request ID — survives async boundaries
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get("") or "no-id"


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware: extract or generate X-Request-ID.
    Sets it in context variable so all log lines include it.
    Forwards it in response headers.
    """

    def __init__(self, app, service_name: str = "unknown"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        # Use existing request ID from gateway or generate new one
        request_id = (
            request.headers.get("X-Request-ID") or
            str(uuid.uuid4())[:8]
        )

        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Served-By"] = self.service_name
            return response
        finally:
            request_id_var.reset(token)


class ServiceLogger:
    """Logger that automatically includes service name and request ID."""

    def __init__(self, service_name: str):
        self.service = service_name
        self._log = logging.getLogger(service_name)
        if not self._log.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                f"%(asctime)s [{service_name}] %(levelname)s %(message)s",
                datefmt="%H:%M:%S"
            ))
            self._log.addHandler(handler)
            self._log.setLevel(logging.INFO)

    def _prefix(self) -> str:
        rid = get_request_id()
        return f"[{rid}] " if rid and rid != "no-id" else ""

    def info(self, msg: str):
        self._log.info(f"{self._prefix()}{msg}")

    def warning(self, msg: str):
        self._log.warning(f"{self._prefix()}{msg}")

    def error(self, msg: str):
        self._log.error(f"{self._prefix()}{msg}")

    def debug(self, msg: str):
        self._log.debug(f"{self._prefix()}{msg}")


def make_outgoing_headers(request: Request = None) -> dict:
    """
    Build headers for outgoing service-to-service calls.
    Propagates tracing context.
    """
    headers = {"X-Request-ID": get_request_id()}
    if request:
        # Forward auth token if present
        auth = request.headers.get("Authorization")
        if auth:
            headers["Authorization"] = auth
    return headers