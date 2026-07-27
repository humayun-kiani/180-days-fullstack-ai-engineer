# ============================================================
# src/reporter.py
# Terminal display functions
# ============================================================

from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = BLUE = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


def header(title, subtitle=None):
    print(f"\n{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    if subtitle:
        print(f"{Fore.CYAN}  {subtitle}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")


def section(title):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def bar(value, max_val, width=20):
    filled = int(value / max_val * width) if max_val > 0 else 0
    return "█" * filled + "░" * (width - filled)


def display_redis_info(info: dict):
    """Display Redis connection info."""
    section("REDIS SERVER INFO")
    print(f"\n  {'Version:':<28} Redis {info['version']}")
    print(f"  {'Uptime:':<28} {info['uptime_hours']:.1f} hours")
    print(f"  {'Memory Used:':<28} {info['used_memory']}")
    print(f"  {'Connected Clients:':<28} {info['connected_clients']}")
    print(f"  {'Total Keys:':<28} {info['total_keys']}")

    hits = info["keyspace_hits"]
    misses = info["keyspace_misses"]
    total = hits + misses
    rate = round(hits / total * 100, 1) if total > 0 else 0
    print(f"  {'Cache Hit Rate:':<28} {Fore.GREEN}{rate}%{Style.RESET_ALL} "
          f"({hits:,} hits / {misses:,} misses)")


def display_weather(weather: dict, was_cached: bool):
    """Display weather data with cache status."""
    section(f"WEATHER — {weather.get('city', 'Unknown').upper()}")

    status = (f"{Fore.GREEN}🟢 CACHE HIT" if was_cached
              else f"{Fore.YELLOW}🔴 CACHE MISS")
    print(f"\n  Cache Status:  {status}{Style.RESET_ALL}")

    if "cache_ttl_remaining" in weather:
        ttl = weather["cache_ttl_remaining"]
        print(f"  Cache TTL:     {ttl}s remaining ({ttl // 60}m {ttl % 60}s)")

    print(f"\n  🌡️  Temperature:  {weather.get('temperature', 0)}°C "
          f"(feels like {weather.get('feels_like', 0)}°C)")
    print(f"  ☁️  Condition:    {weather.get('condition', 'Unknown')}")
    print(f"  💧 Humidity:     {weather.get('humidity', 0)}%")
    print(f"  💨 Wind:         {weather.get('wind_speed', 0)} km/h {weather.get('wind_direction', '')}")
    print(f"  👁️  Visibility:   {weather.get('visibility_km', 0)} km")
    print(f"  📊 Pressure:     {weather.get('pressure_hpa', 0)} hPa")
    print(f"  🕐 Fetched at:   {weather.get('fetched_at', 'N/A')[:19]}")
    print(f"  📡 Source:       {weather.get('source', 'unknown')}")


def display_forecast(forecast: dict):
    """Display weather forecast."""
    city = forecast.get("city", "Unknown")
    section(f"5-DAY FORECAST — {city.upper()}")

    print(f"\n  {'Day':<12} {'Condition':<16} {'High':>6} {'Low':>6} {'Humidity':>9} {'Rain':>6}")
    print(f"  {'─' * 60}")

    for day in forecast.get("days", []):
        high = day.get("high", 0)
        rain = day.get("rain_chance_pct", 0)
        temp_color = (Fore.RED if high > 38 else
                      Fore.YELLOW if high > 30 else Fore.CYAN)
        print(
            f"  {day['day']:<12} "
            f"{day.get('condition', 'N/A'):<16} "
            f"{temp_color}{high:>5.1f}°{Style.RESET_ALL} "
            f"{day.get('low', 0):>5.1f}° "
            f"{day.get('humidity', 0):>8}% "
            f"{rain:>5}%"
        )


def display_cache_stats(stats: dict):
    """Display cache performance statistics."""
    section("CACHE PERFORMANCE")

    total = stats["total_requests"]
    hits = stats["hits"]
    misses = stats["misses"]
    rate = stats["hit_rate_pct"]

    print(f"\n  {'Total Requests:':<28} {total:,}")
    print(f"  {'Cache Hits:':<28} {Fore.GREEN}{hits:,}{Style.RESET_ALL}")
    print(f"  {'Cache Misses:':<28} {Fore.YELLOW}{misses:,}{Style.RESET_ALL}")

    rate_color = Fore.GREEN if rate >= 70 else Fore.YELLOW if rate >= 40 else Fore.RED
    hit_bar = bar(hits, total, width=25) if total > 0 else ""
    print(f"  {'Hit Rate:':<28} {rate_color}{rate}%{Style.RESET_ALL}  {Fore.GREEN}{hit_bar}{Style.RESET_ALL}")

    print(f"\n  {'Cached Weather Keys:':<28} {stats['cached_cities_count']}")
    print(f"  {'Cached Forecast Keys:':<28} {stats['cached_forecasts_count']}")
    print(f"  {'Total Redis Keys:':<28} {stats['total_keys']}")

    if stats["cached_cities"]:
        print(f"\n  Active Cache Entries:")
        print(f"  {'City':<22} {'TTL Remaining':>15}")
        print(f"  {'─' * 38}")
        for city_info in stats["cached_cities"][:8]:
            ttl = city_info["ttl_remaining"]
            mins = ttl // 60
            secs = ttl % 60
            color = Fore.GREEN if ttl > 300 else Fore.YELLOW if ttl > 60 else Fore.RED
            print(
                f"  {city_info['city']:<22} "
                f"{color}{mins}m {secs:02d}s{Style.RESET_ALL}"
            )


def display_top_cities(cities: list):
    """Display most searched cities leaderboard."""
    section("MOST SEARCHED CITIES (Sorted Set Leaderboard)")

    if not cities:
        print(f"  {Fore.YELLOW}No searches yet.{Style.RESET_ALL}")
        return

    max_searches = cities[0][1] if cities else 1
    medals = ["🥇", "🥈", "🥉"]

    print(f"\n  {'#':<4} {'City':<20} {'Searches':>9}  Chart")
    print(f"  {'─' * 50}")

    for i, (city, count) in enumerate(cities):
        medal = medals[i] if i < 3 else f"  {i+1}."
        b = bar(count, max_searches, width=18)
        print(
            f"  {medal:<4} "
            f"{city.replace('_', ' ').title():<20} "
            f"{count:>9}  "
            f"{Fore.CYAN}{b}{Style.RESET_ALL}"
        )


def display_analytics(analytics: dict):
    """Display full analytics dashboard."""
    section("ANALYTICS DASHBOARD")

    total = analytics["total_checks"]
    print(f"\n  {'Total API Checks:':<30} {total:,}")
    print(f"  {'Cached Responses:':<30} {analytics['cached_responses']:,}")
    rate = analytics["cache_hit_rate"]
    color = Fore.GREEN if rate >= 70 else Fore.YELLOW if rate >= 40 else Fore.RED
    print(f"  {'Cache Hit Rate:':<30} {color}{rate}%{Style.RESET_ALL}")
    print(f"  {'Avg Response Time:':<30} {analytics['avg_response_ms']:.1f}ms")
    print(f"  {'Min Response Time:':<30} {analytics['min_response_ms']:.1f}ms")
    print(f"  {'Max Response Time:':<30} {analytics['max_response_ms']:.1f}ms")

    if analytics.get("top_cities"):
        print()
        display_top_cities(analytics["top_cities"])

    if analytics.get("recent_activity"):
        section("RECENT ACTIVITY LOG (Redis List)")
        for entry in analytics["recent_activity"][:10]:
            is_hit = "HIT" in entry
            color = Fore.GREEN if is_hit else Fore.YELLOW
            print(f"  {color}{entry}{Style.RESET_ALL}")


def display_session_info(session_data: dict, favorites: list, history: list):
    """Display current session information."""
    section("YOUR SESSION")
    print(f"\n  Username:      {session_data.get('username', 'guest')}")
    print(f"  Searches:      {session_data.get('search_count', 0)}")
    print(f"  Last Active:   {session_data.get('last_active', 'N/A')[:19]}")

    if favorites:
        print(f"\n  ❤️  Favorite Cities: {', '.join(favorites)}")
    if history:
        print(f"  🕐 Recent Searches: {' → '.join(history[:5])}")