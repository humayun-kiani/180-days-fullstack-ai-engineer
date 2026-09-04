# app/tracing/tracer.py
# Lightweight distributed tracing

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional

# Context vars for current trace
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")

# In-memory trace store (in production: send to Jaeger, Zipkin, Datadog)
_traces: dict[str, list] = {}
_MAX_TRACES = 100


@dataclass
class Span:
    """A single operation within a trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation: str
    service: str = "task-api"
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    tags: dict = field(default_factory=dict)
    error: Optional[str] = None
    status: str = "in_progress"

    def finish(self, error: str = None) -> None:
        self.end_time = time.perf_counter()
        self.error = error
        self.status = "error" if error else "ok"

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "service": self.service,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error": self.error,
            "tags": self.tags
        }


class SpanContext:
    """Context manager for a span."""

    def __init__(self, operation: str, tags: dict = None):
        self.operation = operation
        self.tags = tags or {}
        self.span: Optional[Span] = None
        self._trace_token = None
        self._span_token = None

    def __enter__(self) -> "SpanContext":
        trace_id = trace_id_var.get("") or str(uuid.uuid4())[:8]
        parent_span_id = span_id_var.get("") or None
        span_id = str(uuid.uuid4())[:8]

        self._trace_token = trace_id_var.set(trace_id)
        self._span_token = span_id_var.set(span_id)

        self.span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=self.operation,
            tags=self.tags
        )

        # Store span
        if trace_id not in _traces:
            _traces[trace_id] = []
            if len(_traces) > _MAX_TRACES:
                oldest = next(iter(_traces))
                del _traces[oldest]
        _traces[trace_id].append(self.span)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            error = str(exc_val) if exc_val else None
            self.span.finish(error=error)

        if self._trace_token:
            trace_id_var.reset(self._trace_token)
        if self._span_token:
            span_id_var.reset(self._span_token)

        return False


def get_trace(trace_id: str) -> list[dict]:
    """Get all spans for a trace ID."""
    spans = _traces.get(trace_id, [])
    return [s.to_dict() for s in sorted(spans, key=lambda s: s.start_time)]


def get_recent_traces(limit: int = 10) -> list[dict]:
    """Get the most recent traces."""
    result = []
    for trace_id, spans in list(_traces.items())[-limit:]:
        if not spans:
            continue
        root = min(spans, key=lambda s: s.start_time)
        total_ms = sum(s.duration_ms for s in spans)
        has_error = any(s.error for s in spans)
        result.append({
            "trace_id": trace_id,
            "root_operation": root.operation,
            "span_count": len(spans),
            "total_ms": round(total_ms, 2),
            "has_error": has_error,
            "spans": [s.to_dict() for s in sorted(spans, key=lambda s: s.start_time)]
        })
    return list(reversed(result))