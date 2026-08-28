# ============================================================
# app/profiler.py
# Query profiler — captures and analyzes query performance
# ============================================================

import time
from dataclasses import dataclass, field
from collections import defaultdict
from statistics import mean, median


@dataclass
class QueryProfile:
    """Performance profile of a single query execution."""
    query_name: str
    execution_time_ms: float
    rows_scanned: int
    rows_returned: int
    scan_type: str
    index_used: str
    filters: dict
    table: str
    is_slow: bool


class QueryProfiler:
    """
    Tracks and analyzes query performance.

    Think of this as a simplified pg_stat_statements.
    """

    SLOW_THRESHOLD_MS = 50.0

    def __init__(self):
        self._profiles: list[QueryProfile] = []
        self._by_name: dict[str, list[QueryProfile]] = defaultdict(list)

    def record(self, plan: dict) -> QueryProfile:
        """Record a query execution plan."""
        profile = QueryProfile(
            query_name=plan["query_name"],
            execution_time_ms=plan["execution_time_ms"],
            rows_scanned=plan["rows_scanned"],
            rows_returned=plan["rows_returned"],
            scan_type=plan["scan_type"],
            index_used=plan.get("index_used", "none"),
            filters=plan.get("filters", {}),
            table=plan.get("table", "unknown"),
            is_slow=plan["execution_time_ms"] > self.SLOW_THRESHOLD_MS
        )
        self._profiles.append(profile)
        self._by_name[plan["query_name"]].append(profile)
        return profile

    def top_slow_queries(self, n: int = 10) -> list[dict]:
        """Return the N slowest queries."""
        slow = sorted(self._profiles, key=lambda p: p.execution_time_ms, reverse=True)
        return [
            {
                "query": p.query_name,
                "ms": p.execution_time_ms,
                "scan_type": p.scan_type,
                "rows_scanned": p.rows_scanned,
                "index": p.index_used,
                "recommendation": self._recommend(p)
            }
            for p in slow[:n]
        ]

    def summary_by_query(self) -> list[dict]:
        """Aggregate stats per query name."""
        result = []
        for name, profiles in self._by_name.items():
            times = [p.execution_time_ms for p in profiles]
            result.append({
                "query": name,
                "calls": len(profiles),
                "avg_ms": round(mean(times), 2),
                "max_ms": round(max(times), 2),
                "total_ms": round(sum(times), 2),
                "slow_count": sum(1 for p in profiles if p.is_slow),
                "scan_types": list({p.scan_type for p in profiles})
            })
        return sorted(result, key=lambda r: r["total_ms"], reverse=True)

    def _recommend(self, p: QueryProfile) -> str:
        """Generate optimization recommendation."""
        if p.scan_type == "Seq Scan" and p.rows_scanned > 1000:
            cols = list(p.filters.keys())
            if len(cols) == 1:
                return f"CREATE INDEX idx_{p.table}_{cols[0]} ON {p.table}({cols[0]})"
            elif len(cols) > 1:
                col_str = ", ".join(cols)
                return f"CREATE INDEX idx_{p.table}_composite ON {p.table}({col_str})"
        if p.rows_scanned > p.rows_returned * 100:
            return "Consider a more selective index (partial index)"
        if p.scan_type == "Index Scan" and p.execution_time_ms > 20:
            return "Consider covering index to enable Index-Only Scan"
        return "Query looks optimized"

    def index_recommendations(self) -> list[str]:
        """Deduplicated list of recommended indexes."""
        recs = set()
        for p in self._profiles:
            rec = self._recommend(p)
            if rec.startswith("CREATE"):
                recs.add(rec)
        return sorted(recs)

    def overall_stats(self) -> dict:
        if not self._profiles:
            return {"message": "No queries profiled yet"}
        times = [p.execution_time_ms for p in self._profiles]
        sorted_times = sorted(times)
        n = len(times)
        return {
            "total_queries": n,
            "avg_ms": round(mean(times), 2),
            "p50_ms": round(median(times), 2),
            "p95_ms": round(sorted_times[int(n * 0.95)], 2) if n >= 20 else None,
            "p99_ms": round(sorted_times[int(n * 0.99)], 2) if n >= 100 else None,
            "slow_queries": sum(1 for p in self._profiles if p.is_slow),
            "seq_scans": sum(1 for p in self._profiles if p.scan_type == "Seq Scan"),
            "recommendations": len(self.index_recommendations())
        }

    def reset(self):
        self._profiles.clear()
        self._by_name.clear()


profiler = QueryProfiler()