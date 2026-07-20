# ============================================================
# src/fetcher.py
# Async HTTP fetching with rate limiting and error handling
# ============================================================

import asyncio
import aiohttp
import requests
import time
from datetime import datetime


# ─────────────────────────────────────────
# FREE API SOURCES (no key required)
# ─────────────────────────────────────────

# We use JSONPlaceholder and other free APIs that simulate news data
# In a real project you would use NewsAPI, Guardian API, etc.

FREE_SOURCES = [
    {
        "name": "Tech Posts",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"_limit": 8},
        "category": "Technology",
        "parser": "jsonplaceholder_posts"
    },
    {
        "name": "Science Updates",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"userId": 1, "_limit": 8},
        "category": "Science",
        "parser": "jsonplaceholder_posts"
    },
    {
        "name": "World News",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"userId": 2, "_limit": 8},
        "category": "World",
        "parser": "jsonplaceholder_posts"
    },
    {
        "name": "Business News",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"userId": 3, "_limit": 8},
        "category": "Business",
        "parser": "jsonplaceholder_posts"
    },
    {
        "name": "Sports Headlines",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "params": {"userId": 4, "_limit": 8},
        "category": "Sports",
        "parser": "jsonplaceholder_posts"
    },
    {
        "name": "User Activity Feed",
        "url": "https://jsonplaceholder.typicode.com/todos",
        "params": {"_limit": 10, "completed": True},
        "category": "Updates",
        "parser": "jsonplaceholder_todos"
    },
    {
        "name": "Comments Feed",
        "url": "https://jsonplaceholder.typicode.com/comments",
        "params": {"_limit": 6},
        "category": "Discussion",
        "parser": "jsonplaceholder_comments"
    },
]


# ─────────────────────────────────────────
# DATA PARSERS — Convert raw API → headlines
# ─────────────────────────────────────────

def parse_jsonplaceholder_posts(data, source):
    """Parse JSONPlaceholder posts as news headlines."""
    headlines = []
    for item in data:
        headlines.append({
            "title": item["title"].title(),
            "summary": item["body"][:120].replace("\n", " ") + "...",
            "source": source["name"],
            "category": source["category"],
            "url": f"https://jsonplaceholder.typicode.com/posts/{item['id']}",
            "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "post_id": item["id"]
        })
    return headlines


def parse_jsonplaceholder_todos(data, source):
    """Parse JSONPlaceholder todos as update headlines."""
    headlines = []
    for item in data:
        headlines.append({
            "title": f"Update: {item['title'].title()}",
            "summary": f"Task completed successfully. ID: {item['id']}",
            "source": source["name"],
            "category": source["category"],
            "url": f"https://jsonplaceholder.typicode.com/todos/{item['id']}",
            "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "post_id": item["id"]
        })
    return headlines


def parse_jsonplaceholder_comments(data, source):
    """Parse JSONPlaceholder comments as discussion headlines."""
    headlines = []
    for item in data:
        headlines.append({
            "title": f"Discussion: {item['name'].title()}",
            "summary": item["body"][:120].replace("\n", " ") + "...",
            "source": source["name"],
            "category": source["category"],
            "url": f"https://jsonplaceholder.typicode.com/comments/{item['id']}",
            "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "post_id": item["id"]
        })
    return headlines


PARSERS = {
    "jsonplaceholder_posts": parse_jsonplaceholder_posts,
    "jsonplaceholder_todos": parse_jsonplaceholder_todos,
    "jsonplaceholder_comments": parse_jsonplaceholder_comments,
}


# ─────────────────────────────────────────
# ASYNC FETCHING
# ─────────────────────────────────────────

class RateLimiter:
    """
    Async rate limiter — limits concurrent requests.

    Uses a semaphore to allow max N concurrent requests at once.
    """

    def __init__(self, max_concurrent=5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *args):
        self._semaphore.release()


async def fetch_source_async(
    session,
    source,
    rate_limiter,
    timeout_seconds=10
):
    """
    Fetch headlines from a single source asynchronously.

    Args:
        session: aiohttp.ClientSession
        source (dict): Source configuration dictionary.
        rate_limiter: RateLimiter instance.
        timeout_seconds (int): Request timeout.

    Returns:
        dict: Result with source name, headlines, timing, and status.
    """
    start = asyncio.get_event_loop().time()

    async with rate_limiter:
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with session.get(
                source["url"],
                params=source.get("params"),
                timeout=timeout
            ) as response:

                if response.status != 200:
                    return {
                        "source": source["name"],
                        "category": source["category"],
                        "headlines": [],
                        "error": f"HTTP {response.status}",
                        "fetch_time": asyncio.get_event_loop().time() - start,
                        "success": False
                    }

                data = await response.json()

                # Parse the data using the appropriate parser
                parser = PARSERS.get(source["parser"])
                headlines = parser(data, source) if parser else []

                return {
                    "source": source["name"],
                    "category": source["category"],
                    "headlines": headlines,
                    "error": None,
                    "fetch_time": asyncio.get_event_loop().time() - start,
                    "success": True
                }

        except asyncio.TimeoutError:
            return {
                "source": source["name"],
                "category": source["category"],
                "headlines": [],
                "error": f"Timeout after {timeout_seconds}s",
                "fetch_time": asyncio.get_event_loop().time() - start,
                "success": False
            }

        except aiohttp.ClientConnectorError:
            return {
                "source": source["name"],
                "category": source["category"],
                "headlines": [],
                "error": "Connection failed — check internet",
                "fetch_time": asyncio.get_event_loop().time() - start,
                "success": False
            }

        except Exception as e:
            return {
                "source": source["name"],
                "category": source["category"],
                "headlines": [],
                "error": str(e),
                "fetch_time": asyncio.get_event_loop().time() - start,
                "success": False
            }


async def fetch_all_async(sources, max_concurrent=5, timeout=10):
    """
    Fetch from all sources concurrently.

    Args:
        sources (list): List of source config dicts.
        max_concurrent (int): Max simultaneous requests.
        timeout (int): Per-request timeout in seconds.

    Returns:
        tuple: (list of results, total elapsed time)
    """
    rate_limiter = RateLimiter(max_concurrent)

    connector = aiohttp.TCPConnector(
        limit=max_concurrent,    # max simultaneous connections
        limit_per_host=10        # max per host
    )

    start = asyncio.get_event_loop().time()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_source_async(session, source, rate_limiter, timeout)
            for source in sources
        ]
        # return_exceptions=True prevents one failure from cancelling others
        results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = asyncio.get_event_loop().time() - start

    # Handle any exceptions from gather
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append({
                "source": sources[i]["name"],
                "category": sources[i]["category"],
                "headlines": [],
                "error": str(result),
                "fetch_time": 0,
                "success": False
            })
        else:
            processed.append(result)

    return processed, elapsed


# ─────────────────────────────────────────
# SEQUENTIAL FETCHING (for comparison)
# ─────────────────────────────────────────

def fetch_source_sync(source, timeout=10):
    """Fetch a single source synchronously."""
    start = time.time()
    try:
        response = requests.get(
            source["url"],
            params=source.get("params"),
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()

        parser = PARSERS.get(source["parser"])
        headlines = parser(data, source) if parser else []

        return {
            "source": source["name"],
            "category": source["category"],
            "headlines": headlines,
            "error": None,
            "fetch_time": time.time() - start,
            "success": True
        }
    except Exception as e:
        return {
            "source": source["name"],
            "category": source["category"],
            "headlines": [],
            "error": str(e),
            "fetch_time": time.time() - start,
            "success": False
        }


def fetch_all_sequential(sources, timeout=10):
    """Fetch from all sources one by one (sequential)."""
    start = time.time()
    results = [fetch_source_sync(source, timeout) for source in sources]
    elapsed = time.time() - start
    return results, elapsed