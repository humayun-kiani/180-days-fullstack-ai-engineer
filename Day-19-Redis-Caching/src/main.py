# ============================================================
# src/main.py
# Smart Weather Caching Layer — Main Entry Point
# Day 19 — Redis: In-Memory Data Store, Caching & Pub/Sub
# ============================================================

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.redis_client import test_connection, flush_all_cache
from src.cache_manager import (
    get_weather_cached, get_forecast_cached,
    get_top_searched_cities, get_cache_stats,
    invalidate_city_cache, add_to_search_history,
    get_search_history, reset_cache_stats
)
from src.rate_limiter import check_rate_limit, get_rate_limit_status
from src.session_manager import (
    create_session, get_session,
    add_favorite_city, remove_favorite_city, get_favorite_cities
)
from src.analytics import record_weather_check, get_analytics_summary
from src.reporter import (
    header, section,
    display_redis_info, display_weather, display_forecast,
    display_cache_stats, display_top_cities,
    display_analytics, display_session_info,
    Fore, Style
)

# Current session
SESSION_ID = None


def initialize():
    """Initialize Redis connection and session."""
    global SESSION_ID

    print("\n  Connecting to Redis...")
    info = test_connection()

    if not info["success"]:
        print(f"\n  {Fore.RED}❌ Cannot connect to Redis!{Style.RESET_ALL}")
        print(f"  Error: {info.get('error', 'Unknown')}")
        print(f"\n  Start Redis with one of:")
        print(f"    brew services start redis     (Mac)")
        print(f"    sudo systemctl start redis    (Linux)")
        print(f"    docker run -d -p 6379:6379 redis:7-alpine  (Docker)")
        return False

    print(f"  {Fore.GREEN}✅ Redis connected! v{info['version']}{Style.RESET_ALL}")
    display_redis_info(info)

    # Create a session for this run
    SESSION_ID = create_session("humayun")
    print(f"\n  Session created: {SESSION_ID[:16]}...")
    return True


def search_weather(city: str, user_id: str = "default_user") -> bool:
    """Search for weather with rate limiting and caching."""
    # Check rate limit
    rate = check_rate_limit(user_id)
    if not rate.allowed:
        print(f"\n  {Fore.RED}❌ Rate limit exceeded!{Style.RESET_ALL}")
        print(f"  You have made {rate.requests_made}/{rate.limit} requests.")
        print(f"  Resets in {rate.reset_in_seconds} seconds.")
        return False

    print(f"\n  Fetching weather for {Fore.CYAN}{city}{Style.RESET_ALL}...")
    print(f"  Rate limit: {rate.remaining}/{rate.limit} requests remaining")

    # Fetch with cache timing
    start = time.perf_counter()
    weather, was_cached = get_weather_cached(city)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Display result
    display_weather(weather, was_cached)
    print(f"\n  ⚡ Response time: {Fore.GREEN if elapsed_ms < 10 else Fore.YELLOW}"
          f"{elapsed_ms:.2f}ms{Style.RESET_ALL} "
          f"({'from Redis cache' if was_cached else 'from API/simulation'})")

    # Track analytics
    record_weather_check(city, was_cached, elapsed_ms)

    # Add to session history
    if SESSION_ID:
        add_to_search_history(SESSION_ID, city)

    return True


def benchmark_cache(city: str = "Rawalpindi", rounds: int = 5):
    """Demonstrate cache speedup with a benchmark."""
    section(f"CACHE BENCHMARK — {rounds} requests for {city}")

    times = {"cold": [], "warm": []}

    # Cold cache (first requests)
    print(f"\n  First pass (populating cache):")
    invalidate_city_cache(city)    # ensure cold start

    for i in range(rounds):
        start = time.perf_counter()
        weather, cached = get_weather_cached(city)
        elapsed = (time.perf_counter() - start) * 1000
        times["cold"].append(elapsed)
        status = "HIT" if cached else "MISS"
        print(f"    Request {i+1}: {elapsed:>7.2f}ms  [{status}]")

    print(f"\n  Second pass (warm cache — all hits):")
    for i in range(rounds):
        start = time.perf_counter()
        weather, cached = get_weather_cached(city)
        elapsed = (time.perf_counter() - start) * 1000
        times["warm"].append(elapsed)
        print(f"    Request {i+1}: {elapsed:>7.2f}ms  [HIT]")

    avg_cold = sum(times["cold"]) / len(times["cold"])
    avg_warm = sum(times["warm"]) / len(times["warm"])
    speedup = avg_cold / avg_warm if avg_warm > 0 else float("inf")

    print(f"\n  {'─' * 40}")
    print(f"  Average (cold):  {Fore.RED}{avg_cold:.2f}ms{Style.RESET_ALL}")
    print(f"  Average (warm):  {Fore.GREEN}{avg_warm:.2f}ms{Style.RESET_ALL}")
    print(f"  Speedup:         {Fore.YELLOW}{speedup:.1f}x faster with cache{Style.RESET_ALL}")


def demo_all_data_structures():
    """Demo all Redis data structures in context."""
    from src.redis_client import get_redis
    r = get_redis()

    section("REDIS DATA STRUCTURES DEMO")

    print(f"\n  {Fore.CYAN}1. STRINGS — Weather Cache Keys{Style.RESET_ALL}")
    print(f"     SET weather:current:rawalpindi '{{...}}' EX 600")
    keys = r.keys("weather:current:*")
    for k in keys[:3]:
        ttl = r.ttl(k)
        print(f"     Key: {k} → TTL: {ttl}s")

    print(f"\n  {Fore.CYAN}2. HASHES — Cache Statistics{Style.RESET_ALL}")
    print(f"     HGETALL cache:stats")
    stats = r.hgetall("cache:stats")
    for field, value in stats.items():
        print(f"     {field}: {value}")

    print(f"\n  {Fore.CYAN}3. LISTS — Search History{Style.RESET_ALL}")
    print(f"     LRANGE search:history:{SESSION_ID[:8]}... 0 4")
    if SESSION_ID:
        history = get_search_history(SESSION_ID)
        print(f"     Recent searches: {' → '.join(history[:5]) if history else 'None yet'}")

    print(f"\n  {Fore.CYAN}4. SETS — Favorite Cities{Style.RESET_ALL}")
    print(f"     SMEMBERS favorites:{SESSION_ID[:8]}...")
    if SESSION_ID:
        favs = get_favorite_cities(SESSION_ID)
        print(f"     Favorites: {', '.join(favs) if favs else 'None yet'}")

    print(f"\n  {Fore.CYAN}5. SORTED SETS — City Search Leaderboard{Style.RESET_ALL}")
    print(f"     ZREVRANGE city:search_count 0 4 WITHSCORES")
    top = get_top_searched_cities(5)
    for city, count in top:
        print(f"     {city.replace('_', ' ').title()}: {count} searches")


def main():
    """Main application entry point."""
    header(
        "SMART WEATHER CACHING LAYER",
        "Day 19 — Redis: Strings, Hashes, Lists, Sets, Sorted Sets, Pub/Sub"
    )

    if not initialize():
        sys.exit(1)

    # Pre-warm cache with popular cities
    print(f"\n  Pre-warming cache with popular cities...")
    for city in ["Rawalpindi", "Lahore", "Karachi", "Islamabad"]:
        get_weather_cached(city)
    print(f"  {Fore.GREEN}✅ Cache warmed!{Style.RESET_ALL}")

    while True:
        print(f"\n{'─' * 66}")
        print("  MENU")
        print(f"{'─' * 66}")
        print("  1.  Search weather (with caching)")
        print("  2.  Get 5-day forecast (cached)")
        print("  3.  View cache statistics")
        print("  4.  Top searched cities (Sorted Set)")
        print("  5.  Cache benchmark (speed comparison)")
        print("  6.  Analytics dashboard")
        print("  7.  Add city to favorites (Set)")
        print("  8.  View session & favorites")
        print("  9.  All data structures demo")
        print("  10. Invalidate city cache")
        print("  11. Flush all cache")
        print("  12. Exit")
        print(f"{'─' * 66}")

        choice = input("  Choose (1-12): ").strip()

        if choice == "1":
            city = input("  Enter city name: ").strip()
            if city:
                search_weather(city)

        elif choice == "2":
            city = input("  Enter city name: ").strip()
            if city:
                print(f"\n  Fetching forecast for {city}...")
                forecast, was_cached = get_forecast_cached(city)
                display_forecast(forecast)
                status = "🟢 CACHED" if was_cached else "🔴 FRESH"
                print(f"\n  Cache Status: {status}")

        elif choice == "3":
            header("CACHE STATISTICS")
            stats = get_cache_stats()
            display_cache_stats(stats)

        elif choice == "4":
            header("TOP SEARCHED CITIES")
            cities = get_top_searched_cities(10)
            display_top_cities(cities)

        elif choice == "5":
            city = input("  City to benchmark (default: Rawalpindi): ").strip()
            city = city or "Rawalpindi"
            benchmark_cache(city, rounds=4)

        elif choice == "6":
            header("ANALYTICS DASHBOARD")
            analytics = get_analytics_summary()
            display_analytics(analytics)

        elif choice == "7":
            city = input("  City to add to favorites: ").strip()
            if city and SESSION_ID:
                added = add_favorite_city(SESSION_ID, city)
                if added:
                    print(f"  {Fore.GREEN}✅ Added {city} to favorites!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.YELLOW}Already in favorites.{Style.RESET_ALL}")

        elif choice == "8":
            section("SESSION INFO")
            if SESSION_ID:
                session = get_session(SESSION_ID)
                favorites = get_favorite_cities(SESSION_ID)
                history = get_search_history(SESSION_ID)
                if session:
                    display_session_info(session, favorites, history)

        elif choice == "9":
            demo_all_data_structures()

        elif choice == "10":
            city = input("  City to invalidate: ").strip()
            if city:
                count = invalidate_city_cache(city)
                print(f"  {Fore.GREEN}✅ Deleted {count} cache key(s) for {city}.{Style.RESET_ALL}")

        elif choice == "11":
            confirm = input("  Flush ALL Redis cache? (yes/no): ")
            if confirm.lower() == "yes":
                flush_all_cache()
                reset_cache_stats()
                print(f"  {Fore.GREEN}✅ All cache cleared.{Style.RESET_ALL}")

        elif choice == "12":
            print(f"\n  See you on Day 20! 💪\n")
            break

        else:
            print(f"  {Fore.RED}❌ Invalid option.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()