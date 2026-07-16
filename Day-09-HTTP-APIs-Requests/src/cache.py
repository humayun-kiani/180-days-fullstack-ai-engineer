# ============================================================
# src/cache.py
# Caches weather data to avoid repeated API calls
# ============================================================

import json
from pathlib import Path
from datetime import datetime, timedelta


CACHE_FILE = Path(__file__).parent.parent / "data" / "weather_cache.json"
HISTORY_FILE = Path(__file__).parent.parent / "data" / "search_history.json"


def load_cache():
    """Load the cache file."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    """Save the cache file."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=4)
    except Exception:
        pass


def get_cached_weather(city, cache_minutes=10):
    """
    Get cached weather for a city if not expired.

    Args:
        city (str): City name (used as cache key).
        cache_minutes (int): How long cache is valid in minutes.

    Returns:
        dict or None: Cached data if fresh, None if expired or missing.
    """
    cache = load_cache()
    city_key = city.lower().strip()

    if city_key not in cache:
        return None

    cached = cache[city_key]
    cached_time = datetime.fromisoformat(cached["timestamp"])
    expiry = cached_time + timedelta(minutes=cache_minutes)

    if datetime.now() > expiry:
        return None    # cache expired

    return cached["data"]


def set_cached_weather(city, weather_data, forecast_data):
    """
    Store weather data in cache with timestamp.

    Args:
        city (str): City name.
        weather_data (dict): Current weather data.
        forecast_data (list): Forecast data.
    """
    cache = load_cache()
    city_key = city.lower().strip()

    cache[city_key] = {
        "timestamp": datetime.now().isoformat(),
        "data": {
            "weather": weather_data,
            "forecast": forecast_data
        }
    }
    save_cache(cache)


def add_to_history(city, country):
    """Add a city to search history."""
    HISTORY_FILE.parent.mkdir(exist_ok=True)

    # Load existing history
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

    # Add new entry at the beginning
    entry = {
        "city": city,
        "country": country,
        "searched_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # Remove duplicate if exists
    history = [h for h in history if h["city"].lower() != city.lower()]
    history.insert(0, entry)

    # Keep only last 10 searches
    history = history[:10]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


def get_history():
    """Return search history list."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def clear_cache():
    """Clear the weather cache."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("  Cache cleared.")