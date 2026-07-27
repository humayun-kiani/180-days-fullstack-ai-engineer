# ============================================================
# src/cache_manager.py
# Weather-specific caching logic using Redis
# ============================================================

import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from src.redis_client import get_redis, cache_get, cache_set, cache_ttl
from src.weather_api import get_current_weather, get_forecast

load_dotenv()

# TTL settings from environment
CURRENT_TTL = int(os.environ.get("CURRENT_WEATHER_TTL", 600))     # 10 minutes
FORECAST_TTL = int(os.environ.get("FORECAST_TTL", 1800))           # 30 minutes
HISTORY_TTL = int(os.environ.get("HISTORY_TTL", 86400))            # 24 hours
SEARCH_HISTORY_MAX = 50    # max items in search history list


# ─── Cache Key Schema ────────────────────────────────────────
# Using a consistent naming convention:
# weather:current:{city}         → current weather (string/JSON)
# weather:forecast:{city}        → 5-day forecast (string/JSON)
# city:search_count              → sorted set of search counts
# search:history:{session_id}    → list of searched cities
# cache:stats                    → hash of hit/miss counts

def _city_key(city: str) -> str:
    """Normalize city name for cache key."""
    return city.lower().strip().replace(" ", "_")


def get_weather_cached(city: str) -> tuple[dict, bool]:
    """
    Get current weather with Cache-Aside pattern.

    Args:
        city: City name.

    Returns:
        tuple: (weather_data, was_cached)
    """
    r = get_redis()
    city_key = _city_key(city)
    cache_key = f"weather:current:{city_key}"

    # Track analytics
    r.hincrby("cache:stats", "total_requests", 1)

    # Check cache
    cached = cache_get(cache_key)
    if cached:
        r.hincrby("cache:stats", "hits", 1)
        cached["cache_status"] = "HIT"
        cached["cache_ttl_remaining"] = cache_ttl(cache_key)
        _track_city_search(city_key)
        return cached, True

    # Cache MISS — fetch from API/simulation
    r.hincrby("cache:stats", "misses", 1)
    weather = get_current_weather(city)
    weather["cache_status"] = "MISS"

    # Store in cache
    cache_set(cache_key, weather, CURRENT_TTL)
    _track_city_search(city_key)

    return weather, False


def get_forecast_cached(city: str, days: int = 5) -> tuple[dict, bool]:
    """
    Get weather forecast with caching.

    Returns:
        tuple: (forecast_data, was_cached)
    """
    r = get_redis()
    city_key = _city_key(city)
    cache_key = f"weather:forecast:{city_key}"

    r.hincrby("cache:stats", "total_requests", 1)

    cached = cache_get(cache_key)
    if cached:
        r.hincrby("cache:stats", "hits", 1)
        return cached, True

    r.hincrby("cache:stats", "misses", 1)
    forecast = get_forecast(city, days)
    cache_set(cache_key, forecast, FORECAST_TTL)

    return forecast, False


def invalidate_city_cache(city: str) -> int:
    """
    Invalidate all cache entries for a city.

    Returns:
        int: Number of keys deleted.
    """
    city_key = _city_key(city)
    r = get_redis()
    keys = r.keys(f"weather:*:{city_key}")
    if keys:
        return r.delete(*keys)
    return 0


def _track_city_search(city_key: str) -> None:
    """
    Track city search frequency using a Sorted Set.

    Uses ZINCRBY to atomically increment the city's score.
    This gives us a real-time "most searched cities" leaderboard.
    """
    r = get_redis()
    r.zincrby("city:search_count", 1, city_key)


def get_top_searched_cities(top_n: int = 10) -> list[tuple[str, int]]:
    """
    Get most searched cities from the Sorted Set leaderboard.

    Returns:
        list: [(city_name, search_count), ...]
    """
    r = get_redis()
    results = r.zrevrange("city:search_count", 0, top_n - 1, withscores=True)
    return [(city, int(score)) for city, score in results]


def add_to_search_history(session_id: str, city: str) -> None:
    """
    Add city to user's search history using a Redis List.

    Keeps only the last SEARCH_HISTORY_MAX searches.
    """
    r = get_redis()
    history_key = f"search:history:{session_id}"

    r.lpush(history_key, city)                     # push to front
    r.ltrim(history_key, 0, SEARCH_HISTORY_MAX - 1) # keep max items
    r.expire(history_key, 60 * 60 * 24)            # 24 hour TTL


def get_search_history(session_id: str) -> list[str]:
    """Get user's recent search history."""
    r = get_redis()
    return r.lrange(f"search:history:{session_id}", 0, 19)    # last 20


def get_cache_stats() -> dict:
    """
    Get cache performance statistics.

    Returns:
        dict: Hits, misses, hit rate, and other stats.
    """
    r = get_redis()

    # Get hit/miss counts from the stats hash
    stats = r.hgetall("cache:stats")
    hits = int(stats.get("hits", 0))
    misses = int(stats.get("misses", 0))
    total = hits + misses

    # Get all cached weather keys
    weather_keys = r.keys("weather:current:*")
    forecast_keys = r.keys("weather:forecast:*")

    # Get TTLs for cached cities
    cached_cities = []
    for key in weather_keys:
        city = key.replace("weather:current:", "")
        ttl = r.ttl(key)
        if ttl > 0:
            cached_cities.append({
                "city": city.replace("_", " ").title(),
                "ttl_remaining": ttl
            })

    return {
        "total_requests": total,
        "hits": hits,
        "misses": misses,
        "hit_rate_pct": round(hits / total * 100, 1) if total > 0 else 0,
        "cached_cities_count": len(weather_keys),
        "cached_forecasts_count": len(forecast_keys),
        "cached_cities": sorted(cached_cities, key=lambda x: x["ttl_remaining"]),
        "total_keys": r.dbsize()
    }


def reset_cache_stats() -> None:
    """Reset hit/miss counters."""
    get_redis().delete("cache:stats")