# ============================================================
# src/cache.py
# Async-compatible caching for API responses
# ============================================================

import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta


CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "news_cache.json"


def _load_cache():
    """Load cache from disk."""
    CACHE_DIR.mkdir(exist_ok=True)
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    """Save cache to disk."""
    CACHE_DIR.mkdir(exist_ok=True)
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def get_cached(source_name, max_age_minutes=15):
    """
    Get cached data for a source if not expired.

    Args:
        source_name (str): Identifier for the data source.
        max_age_minutes (int): Maximum age in minutes.

    Returns:
        list or None: Cached data or None if expired/missing.
    """
    cache = _load_cache()
    key = source_name.lower().replace(" ", "_")

    if key not in cache:
        return None

    entry = cache[key]
    cached_at = datetime.fromisoformat(entry["cached_at"])
    expiry = cached_at + timedelta(minutes=max_age_minutes)

    if datetime.now() > expiry:
        return None

    return entry["data"]


def set_cached(source_name, data):
    """
    Store data in cache with current timestamp.

    Args:
        source_name (str): Identifier for the data source.
        data: Data to cache (must be JSON serializable).
    """
    cache = _load_cache()
    key = source_name.lower().replace(" ", "_")
    cache[key] = {
        "cached_at": datetime.now().isoformat(),
        "data": data
    }
    _save_cache(cache)


def clear_cache():
    """Clear all cached data."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()