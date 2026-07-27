# ============================================================
# src/analytics.py
# Redis-based analytics using various data structures
# ============================================================

from datetime import datetime
from src.redis_client import get_redis
from src.cache_manager import get_top_searched_cities, get_cache_stats


def record_weather_check(city: str, was_cached: bool, response_time_ms: float) -> None:
    """
    Record a weather check for analytics.

    Uses multiple Redis structures:
    - Hash for aggregated stats
    - Sorted Set for response time tracking
    - List for recent activity log
    """
    r = get_redis()

    # Update global stats hash
    r.hincrby("analytics:global", "total_checks", 1)
    if was_cached:
        r.hincrby("analytics:global", "cached_responses", 1)
    r.hincrbyfloat("analytics:global", "total_response_time_ms", response_time_ms)

    # Track response times in sorted set (score = response time)
    # Keep last 100 response times
    timestamp = datetime.utcnow().timestamp()
    r.zadd("analytics:response_times", {f"{city}:{timestamp}": response_time_ms})
    r.zremrangebyrank("analytics:response_times", 0, -101)    # keep last 100

    # Add to activity log (list)
    log_entry = f"{datetime.utcnow().strftime('%H:%M:%S')} | {city} | {'HIT' if was_cached else 'MISS'} | {response_time_ms:.0f}ms"
    r.lpush("analytics:activity_log", log_entry)
    r.ltrim("analytics:activity_log", 0, 49)    # keep last 50 entries


def get_analytics_summary() -> dict:
    """Get comprehensive analytics summary."""
    r = get_redis()

    # Global stats
    global_stats = r.hgetall("analytics:global")
    total_checks = int(global_stats.get("total_checks", 0))
    cached = int(global_stats.get("cached_responses", 0))
    total_time = float(global_stats.get("total_response_time_ms", 0))

    # Response times from sorted set
    times = r.zrange("analytics:response_times", 0, -1, withscores=True)
    response_times = [score for _, score in times] if times else [0]

    # Recent activity
    activity_log = r.lrange("analytics:activity_log", 0, 9)

    # Cache stats
    cache_stats = get_cache_stats()

    # Top cities
    top_cities = get_top_searched_cities(5)

    return {
        "total_checks": total_checks,
        "cached_responses": cached,
        "cache_hit_rate": round(cached / total_checks * 100, 1) if total_checks > 0 else 0,
        "avg_response_ms": round(total_time / total_checks, 1) if total_checks > 0 else 0,
        "min_response_ms": round(min(response_times), 1),
        "max_response_ms": round(max(response_times), 1),
        "top_cities": top_cities,
        "cache_stats": cache_stats,
        "recent_activity": activity_log
    }