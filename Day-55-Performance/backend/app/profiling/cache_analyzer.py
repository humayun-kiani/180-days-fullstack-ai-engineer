# backend/app/profiling/cache_analyzer.py
# Analyze cache effectiveness

import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    total_hit_time_ms: float = 0.0
    total_miss_time_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return round(self.hits / total * 100, 1) if total > 0 else 0.0

    @property
    def avg_hit_ms(self) -> float:
        return round(self.total_hit_time_ms / self.hits, 2) if self.hits > 0 else 0.0

    @property
    def avg_miss_ms(self) -> float:
        return round(self.total_miss_time_ms / self.misses, 2) if self.misses > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate_pct": self.hit_rate,
            "avg_hit_ms": self.avg_hit_ms,
            "avg_miss_ms": self.avg_miss_ms,
            "speedup_factor": round(self.avg_miss_ms / self.avg_hit_ms, 1)
                if self.avg_hit_ms > 0 else 0,
            "assessment": self._assess()
        }

    def _assess(self) -> str:
        if self.hits + self.misses < 10:
            return "insufficient_data"
        if self.hit_rate >= 80:
            return "excellent"
        if self.hit_rate >= 60:
            return "good"
        if self.hit_rate >= 40:
            return "fair"
        return "poor — consider increasing TTL or caching more aggressively"


class CacheAnalyzer:
    """
    Wraps the cache service to measure hit rates and timing.
    """

    def __init__(self):
        self._stats_by_prefix: dict[str, CacheStats] = defaultdict(CacheStats)
        self._global = CacheStats()

    def _prefix(self, key: str) -> str:
        return key.split(":")[0] if ":" in key else key

    def record_hit(self, key: str, duration_ms: float):
        prefix = self._prefix(key)
        self._stats_by_prefix[prefix].hits += 1
        self._stats_by_prefix[prefix].total_hit_time_ms += duration_ms
        self._global.hits += 1
        self._global.total_hit_time_ms += duration_ms

    def record_miss(self, key: str, duration_ms: float):
        prefix = self._prefix(key)
        self._stats_by_prefix[prefix].misses += 1
        self._stats_by_prefix[prefix].total_miss_time_ms += duration_ms
        self._global.misses += 1
        self._global.total_miss_time_ms += duration_ms

    def record_set(self, key: str):
        self._stats_by_prefix[self._prefix(key)].sets += 1
        self._global.sets += 1

    def record_delete(self, key: str):
        self._stats_by_prefix[self._prefix(key)].deletes += 1
        self._global.deletes += 1

    def get_report(self) -> dict:
        return {
            "global": self._global.to_dict(),
            "by_prefix": {
                prefix: stats.to_dict()
                for prefix, stats in sorted(
                    self._stats_by_prefix.items(),
                    key=lambda x: x[1].hits + x[1].misses,
                    reverse=True
                )
            },
            "recommendations": self._recommendations()
        }

    def _recommendations(self) -> list[str]:
        recs = []
        for prefix, stats in self._stats_by_prefix.items():
            if stats.hit_rate < 40 and stats.hits + stats.misses > 10:
                recs.append(
                    f"'{prefix}' cache hit rate is {stats.hit_rate}% — "
                    f"increase TTL or cache at a higher level"
                )
            if stats.avg_miss_ms > 200:
                recs.append(
                    f"'{prefix}' cache misses average {stats.avg_miss_ms}ms — "
                    f"these DB queries need optimization"
                )
        if self._global.hit_rate > 80:
            recs.append("Cache is performing well overall")
        return recs or ["Need more traffic data for recommendations"]


# Global analyzer
cache_analyzer = CacheAnalyzer()