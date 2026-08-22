# ============================================================
# app/metrics.py
# Request metrics collection and aggregation
# ============================================================

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RequestRecord:
    timestamp: float
    latency_ms: float
    tokens_used: int
    classifier_used: str
    was_blocked: bool
    was_degraded: bool
    output_filtered: bool
    error: str | None = None


class MetricsStore:
    """Rolling window metrics — last N requests."""

    def __init__(self, window: int = 500):
        self._records: deque[RequestRecord] = deque(maxlen=window)
        self._total_requests = 0
        self._total_tokens = 0
        self._start_time = time.time()

    def record(self, rec: RequestRecord) -> None:
        self._records.append(rec)
        self._total_requests += 1
        self._total_tokens += rec.tokens_used

    def summary(self) -> dict:
        records = list(self._records)
        n = len(records)

        if n == 0:
            return {
                "message": "No requests yet",
                "total_lifetime": self._total_requests,
                "uptime_seconds": round(time.time() - self._start_time, 0)
            }

        latencies = [r.latency_ms for r in records if not r.error]
        errors = [r for r in records if r.error]
        blocked = [r for r in records if r.was_blocked]
        degraded = [r for r in records if r.was_degraded]
        filtered = [r for r in records if r.output_filtered]

        lat_sorted = sorted(latencies)
        p95_idx = int(len(lat_sorted) * 0.95)
        p99_idx = int(len(lat_sorted) * 0.99)

        classifiers = {}
        for r in records:
            c = r.classifier_used
            classifiers[c] = classifiers.get(c, 0) + 1

        return {
            "window_requests": n,
            "total_lifetime": self._total_requests,
            "error_rate": round(len(errors) / n, 3),
            "block_rate": round(len(blocked) / n, 3),
            "degraded_rate": round(len(degraded) / n, 3),
            "output_filter_rate": round(len(filtered) / n, 3),
            "latency_ms": {
                "avg": round(statistics.mean(latencies), 1) if latencies else 0,
                "p50": round(statistics.median(latencies), 1) if latencies else 0,
                "p95": round(lat_sorted[p95_idx], 1) if len(lat_sorted) > 20 else None,
                "p99": round(lat_sorted[p99_idx], 1) if len(lat_sorted) > 100 else None,
            },
            "total_tokens_window": sum(r.tokens_used for r in records),
            "total_tokens_lifetime": self._total_tokens,
            "classifier_usage": classifiers,
            "est_cost_window_usd": round(
                sum(r.tokens_used for r in records) / 1000 * 0.003, 5
            ),
            "uptime_seconds": round(time.time() - self._start_time, 0)
        }