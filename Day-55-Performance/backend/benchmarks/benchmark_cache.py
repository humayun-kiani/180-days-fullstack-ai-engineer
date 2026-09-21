# backend/benchmarks/benchmark_cache.py
# Measure cache hit vs miss performance

import asyncio
import time
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def benchmark_cache():
    """
    Demonstrate cache speedup: in-memory dict vs simulated DB call.
    Works without Redis (uses dict as stand-in cache).
    """
    print("\n" + "=" * 60)
    print("  CACHE PERFORMANCE BENCHMARK")
    print("=" * 60)

    # Simulate a cache with a dict
    _cache: dict = {}

    def cache_get(key: str):
        return _cache.get(key)

    def cache_set(key: str, value, ttl: int = 60):
        _cache[key] = value

    async def simulate_db_query(delay_ms: float = 15.0):
        """Simulate a DB query taking ~15ms (realistic fast query)."""
        await asyncio.sleep(delay_ms / 1000)
        return [{"id": f"task-{i}", "title": f"Task {i}"} for i in range(20)]

    print("\n📊 Scenario: Task list endpoint (20 tasks, 15ms DB query)\n")

    N = 20  # number of requests to simulate

    # ── Without cache ──
    print(f"1. No caching ({N} requests)")
    times_no_cache = []
    for i in range(N):
        start = time.perf_counter()
        await simulate_db_query(15.0)  # always hits DB
        times_no_cache.append((time.perf_counter() - start) * 1000)
    avg_no_cache = sum(times_no_cache) / len(times_no_cache)
    total_no_cache = sum(times_no_cache)
    print(f"  avg={avg_no_cache:.1f}ms  total={total_no_cache:.0f}ms")

    # ── With cache (first request: miss, rest: hits) ──
    print(f"\n2. With caching ({N} requests, first is miss)")
    times_cached = []
    _cache.clear()

    for i in range(N):
        start = time.perf_counter()
        key = "tasks:user-1:page:1"
        result = cache_get(key)
        if result is None:
            result = await simulate_db_query(15.0)  # cache miss
            cache_set(key, result, ttl=60)
        times_cached.append((time.perf_counter() - start) * 1000)

    avg_cached = sum(times_cached) / len(times_cached)
    total_cached = sum(times_cached)
    hits = N - 1
    misses = 1
    hit_rate = hits / N * 100

    print(f"  avg={avg_cached:.2f}ms  total={total_cached:.1f}ms")
    print(f"  hits={hits}  misses={misses}  hit_rate={hit_rate:.0f}%")

    # ── Comparison ──
    speedup = avg_no_cache / max(avg_cached, 0.001)
    time_saved = total_no_cache - total_cached
    print(f"\n{'─'*40}")
    print(f"  Speedup:    {speedup:.0f}x faster with cache")
    print(f"  Time saved: {time_saved:.0f}ms over {N} requests")
    print(f"  At 100 RPS: saves {time_saved / N * 100:.0f}ms/sec of DB time")

    print("\n📊 Scenario: Cache TTL tradeoffs\n")

    ttl_scenarios = [
        (5,   "5s TTL  — very fresh, many misses"),
        (30,  "30s TTL — balanced"),
        (300, "5m TTL  — fewer misses, data may be stale"),
    ]

    for ttl, label in ttl_scenarios:
        # Simulate 60 requests over 60 seconds (1 RPS)
        # Assume cache expires every TTL seconds
        total_requests = 60
        cache_misses = max(1, total_requests // ttl)
        cache_hits = total_requests - cache_misses
        total_time = (cache_hits * 0.1 + cache_misses * 15.0)
        avg_time = total_time / total_requests
        print(f"  {label}")
        print(f"    misses={cache_misses}  avg={avg_time:.1f}ms/req")

    print("\n  → Longer TTL = better performance, potentially stale data")
    print("  → Shorter TTL = fresher data, more DB load")
    print("  → TaskMind uses 30s for task lists (good balance)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(benchmark_cache())