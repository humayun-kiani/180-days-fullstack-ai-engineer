# ============================================================
# app/metrics.py
# Request performance metrics
# ============================================================

import time
import statistics
from collections import deque
from dataclasses import dataclass


@dataclass
class RequestRecord:
    path: str
    method: str
    latency_ms: float
    cache_hit: bool
    cache_layer: str | None    # "L1", "L2", or None
    status_code: int


class PerformanceMetrics:
    """Track request latency and cache performance."""

    def __init__(self, window: int = 1000):
        self._records: deque[RequestRecord] = deque(maxlen=window)
        self._start = time.time()

    def record(self, rec: RequestRecord) -> None:
        self._records.append(rec)

    def summary(self) -> dict:
        records = list(self._records)
        n = len(records)
        if n == 0:
            return {"message": "No requests yet"}

        latencies = [r.latency_ms for r in records]
        cache_hits = [r for r in records if r.cache_hit]
        l1_hits = [r for r in records if r.cache_layer == "L1"]
        l2_hits = [r for r in records if r.cache_layer == "L2"]
        db_hits  = [r for r in records if r.cache_layer is None and not r.cache_hit]

        lat_sorted = sorted(latencies)

        return {
            "total_requests": n,
            "cache_hit_rate": round(len(cache_hits) / n, 3),
            "cache_breakdown": {
                "L1_hits": len(l1_hits),
                "L2_hits": len(l2_hits),
                "DB_fetches": len(db_hits)
            },
            "latency_ms": {
                "avg": round(statistics.mean(latencies), 2),
                "p50": round(statistics.median(latencies), 2),
                "p95": round(lat_sorted[int(n * 0.95)], 2) if n >= 20 else None,
                "p99": round(lat_sorted[int(n * 0.99)], 2) if n >= 100 else None,
                "max": round(max(latencies), 2),
                "min": round(min(latencies), 2)
            },
            "uptime_seconds": round(time.time() - self._start, 0)
        }