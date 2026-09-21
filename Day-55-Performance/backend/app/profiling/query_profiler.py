# backend/app/profiling/query_profiler.py
# SQL query profiler — counts queries, measures duration, detects N+1

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

import sqlalchemy.event as sqla_event


@dataclass
class QueryRecord:
    statement: str
    duration_ms: float
    timestamp: float
    params: Optional[str] = None

    @property
    def is_slow(self) -> bool:
        return self.duration_ms > 100  # > 100ms is slow

    def to_dict(self) -> dict:
        return {
            "statement_preview": self.statement[:200],
            "duration_ms": round(self.duration_ms, 3),
            "is_slow": self.is_slow,
            "timestamp": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat()
        }


class QueryProfiler:
    """
    Track all SQL queries for performance analysis.

    Per-request tracking via thread-local storage.
    Detects slow queries, N+1 patterns, and total query counts.
    """

    def __init__(self):
        self._local = threading.local()
        self._global_stats: dict[str, list[float]] = defaultdict(list)
        self._slow_queries: list[dict] = []
        self._enabled = False

    def enable(self, engine):
        """Attach to a SQLAlchemy engine."""
        self._enabled = True

        @sqla_event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_execute(conn, cursor, statement, params, context, executemany):
            context._query_start = time.perf_counter()

        @sqla_event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_execute(conn, cursor, statement, params, context, executemany):
            if not hasattr(context, "_query_start"):
                return
            duration = (time.perf_counter() - context._query_start) * 1000

            record = QueryRecord(
                statement=statement.strip(),
                duration_ms=duration,
                timestamp=time.time()
            )

            # Per-request tracking
            if not hasattr(self._local, "queries"):
                self._local.queries = []
            self._local.queries.append(record)

            # Global slow query log
            if record.is_slow:
                self._slow_queries.append({
                    **record.to_dict(),
                    "full_statement": statement[:1000]
                })
                if len(self._slow_queries) > 100:
                    self._slow_queries.pop(0)

            # Global aggregates
            self._global_stats[statement[:100]].append(duration)

    def start_request(self):
        """Reset per-request query tracking."""
        self._local.queries = []
        self._local.request_start = time.perf_counter()

    def end_request(self) -> dict:
        """Summarize queries for this request."""
        queries = getattr(self._local, "queries", [])
        request_duration = (
            time.perf_counter() - getattr(self._local, "request_start", time.perf_counter())
        ) * 1000

        if not queries:
            return {"query_count": 0, "total_db_ms": 0}

        total_db = sum(q.duration_ms for q in queries)
        slow = [q for q in queries if q.is_slow]

        # N+1 detection: same query pattern repeated many times
        statement_patterns = [q.statement[:80] for q in queries]
        pattern_counts = {}
        for p in statement_patterns:
            pattern_counts[p] = pattern_counts.get(p, 0) + 1
        repeated = {k: v for k, v in pattern_counts.items() if v >= 3}

        return {
            "query_count": len(queries),
            "total_db_ms": round(total_db, 2),
            "request_ms": round(request_duration, 2),
            "db_pct_of_request": round(total_db / max(request_duration, 1) * 100, 1),
            "slow_queries": [q.to_dict() for q in slow],
            "potential_n_plus_1": [
                {"pattern": k[:80], "count": v, "warning": f"Same query ran {v} times"}
                for k, v in repeated.items()
            ],
            "queries": [q.to_dict() for q in queries[:20]]  # first 20
        }

    def get_slow_queries(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._slow_queries))[:limit]

    def get_global_stats(self) -> dict:
        stats = {}
        for stmt, durations in self._global_stats.items():
            stats[stmt] = {
                "count": len(durations),
                "avg_ms": round(sum(durations) / len(durations), 2),
                "max_ms": round(max(durations), 2),
                "min_ms": round(min(durations), 2)
            }
        return dict(sorted(stats.items(), key=lambda x: x[1]["avg_ms"], reverse=True)[:20])


# Global profiler instance
profiler = QueryProfiler()