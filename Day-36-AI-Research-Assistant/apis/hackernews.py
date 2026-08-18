# apis/hackernews.py
import asyncio
import httpx

BASE = "https://hacker-news.firebaseio.com/v0"


async def get_top_stories(count: int = 5) -> dict:
    count = min(count, 10)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            ids_r = await client.get(f"{BASE}/topstories.json")
            ids_r.raise_for_status()
            ids = ids_r.json()[:count]

            async def fetch(sid):
                try:
                    r = await client.get(f"{BASE}/item/{sid}.json")
                    return r.json()
                except Exception:
                    return None

            stories_data = await asyncio.gather(*[fetch(i) for i in ids])

        return {
            "stories": [
                {"title": s.get("title"), "score": s.get("score", 0),
                 "url": s.get("url", f"https://news.ycombinator.com/item?id={s.get('id')}"),
                 "comments": s.get("descendants", 0)}
                for s in stories_data if s and not isinstance(s, Exception)
            ]
        }
    except Exception as e:
        return {"error": str(e)}