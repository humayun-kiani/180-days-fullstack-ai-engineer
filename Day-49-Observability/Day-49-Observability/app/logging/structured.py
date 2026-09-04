# app/logging/structured.py
# Structured JSON logging with correlation IDs

import json
import time
import uuid
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# ── Context Variables ─────────────────────────────────────────
# These persist across async boundaries within a request

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

SERVICE_NAME = "task-api"
LOG_LEVEL_PRIORITY = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
MIN_LEVEL = "DEBUG"


class StructuredLogger:
    """
    Emits structured JSON log entries.

    Each log line is valid JSON with standard fields:
    - timestamp: ISO 8601 UTC
    - level: DEBUG/INFO/WARNING/ERROR/CRITICAL
    - message: human-readable description
    - request_id: correlation ID (if in request context)
    - service: service name
    - plus any extra fields you pass as kwargs
    """

    def __init__(self, name: str = SERVICE_NAME, min_level: str = "DEBUG"):
        self.name = name
        self.min_level = min_level

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        if LOG_LEVEL_PRIORITY.get(level, 0) < LOG_LEVEL_PRIORITY.get(self.min_level, 0):
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "service": self.name,
            "message": message,
        }

        # Add correlation IDs from context
        request_id = request_id_var.get("")
        if request_id:
            entry["request_id"] = request_id

        user_id = user_id_var.get("")
        if user_id:
            entry["user_id"] = user_id

        # Add extra fields
        entry.update({k: v for k, v in fields.items() if v is not None})

        print(json.dumps(entry), file=sys.stderr if level in ("ERROR", "CRITICAL") else sys.stdout, flush=True)

    def debug(self, message: str, **fields) -> None:
        self._emit("DEBUG", message, **fields)

    def info(self, message: str, **fields) -> None:
        self._emit("INFO", message, **fields)

    def warning(self, message: str, **fields) -> None:
        self._emit("WARNING", message, **fields)

    def error(self, message: str, **fields) -> None:
        self._emit("ERROR", message, **fields)

    def critical(self, message: str, **fields) -> None:
        self._emit("CRITICAL", message, **fields)


# ── Log Store (for demo — in production use Elasticsearch, CloudWatch) ──

_log_store: list[dict] = []
_MAX_STORED_LOGS = 500


class StoringLogger(StructuredLogger):
    """Logger that also stores entries in memory for the /logs endpoint."""

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        super()._emit(level, message, **fields)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "service": self.name,
            "message": message,
        }
        request_id = request_id_var.get("")
        if request_id:
            entry["request_id"] = request_id
        user_id = user_id_var.get("")
        if user_id:
            entry["user_id"] = user_id
        entry.update({k: v for k, v in fields.items() if v is not None})

        _log_store.append(entry)
        if len(_log_store) > _MAX_STORED_LOGS:
            _log_store.pop(0)


def get_recent_logs(
    level: str = None,
    request_id: str = None,
    limit: int = 50
) -> list[dict]:
    """Query stored logs with filters."""
    logs = list(reversed(_log_store))  # newest first

    if level:
        logs = [l for l in logs if l.get("level") == level.upper()]

    if request_id:
        logs = [l for l in logs if l.get("request_id") == request_id]

    return logs[:limit]


# Global logger instance
logger = StoringLogger(name=SERVICE_NAME, min_level="DEBUG")