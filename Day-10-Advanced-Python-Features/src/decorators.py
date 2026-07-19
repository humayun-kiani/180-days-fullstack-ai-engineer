# ============================================================
# src/decorators.py
# Reusable decorators for the data pipeline
# ============================================================

import time
import functools
from datetime import datetime


def timer(func):
    """Measure and print execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  ⏱️  {func.__name__}() completed in {elapsed:.4f}s")
        return result
    return wrapper


def retry(max_attempts=3, delay=1.0, exceptions=(Exception,)):
    """
    Retry a function on specified exceptions.

    Args:
        max_attempts (int): Maximum number of attempts.
        delay (float): Seconds to wait between attempts.
        exceptions (tuple): Exception types to catch and retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(
                            f"  ⚠️  {func.__name__} attempt "
                            f"{attempt}/{max_attempts} failed: {e}"
                        )
                        time.sleep(delay)
                    else:
                        print(
                            f"  ❌ {func.__name__} failed after "
                            f"{max_attempts} attempts."
                        )
            raise last_exception
        return wrapper
    return decorator


def log_calls(func):
    """Log function calls with timestamp."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{timestamp}] 📝 Calling {func.__name__}()")
        result = func(*args, **kwargs)
        return result
    return wrapper


def cache_result(func):
    """Simple in-memory cache for function results."""
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    wrapper.cache = cache
    wrapper.clear_cache = lambda: cache.clear()
    return wrapper


def validate_not_empty(func):
    """Ensure the first argument is not empty."""
    @functools.wraps(func)
    def wrapper(data, *args, **kwargs):
        if not data:
            raise ValueError(
                f"{func.__name__}() received empty data."
            )
        return func(data, *args, **kwargs)
    return wrapper