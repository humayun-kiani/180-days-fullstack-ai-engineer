# ============================================================
# apis/hackernews.py
# Hacker News Firebase API (free, no key required)
# ============================================================

import asyncio
import httpx
from app.rate_limiter import RATE_LIMITERS

BASE_URL = "https://hacker-news.firebaseio.com/v0"


async def get_top_stories(count: int = 5, story_type: str = "top") -> dict:
    """
    Get top stories from Hacker News.

    Args:
        count: Number of stories to return (max 20)
        story_type: "top", "new", "best", "ask", "show", "job"

    Returns:
        dict: List of HN stories
    """
    await RATE_LIMITERS["hackernews"].acquire()

    count = min(count, 20)    # cap at 20

    valid_types = ["top", "new", "best", "ask", "show", "job"]
    if story_type not in valid_types:
        story_type = "top"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get story IDs
            stories_response = await client.get(
                f"{BASE_URL}/{story_type}stories.json"
            )
            stories_response.raise_for_status()
            story_ids = stories_response.json()[:count]

            # Fetch story details in parallel
            async def fetch_story(story_id: int) -> dict | None:
                try:
                    r = await client.get(f"{BASE_URL}/item/{story_id}.json")
                    return r.json()
                except Exception:
                    return None

            stories_data = await asyncio.gather(
                *[fetch_story(sid) for sid in story_ids],
                return_exceptions=True
            )

        stories = []
        for story in stories_data:
            if not story or isinstance(story, Exception):
                continue
            stories.append({
                "title": story.get("title", "No title"),
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}"),
                "score": story.get("score", 0),
                "comments": story.get("descendants", 0),
                "author": story.get("by", "unknown"),
                "type": story.get("type", "story"),
                "hn_id": story.get("id"),
            })

        return {
            "stories": stories,
            "type": story_type,
            "count": len(stories)
        }

    except httpx.TimeoutException:
        return {"error": "HackerNews API timed out"}
    except Exception as e:
        return {"error": str(e)}