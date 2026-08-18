# apis/github_api.py
import os
import httpx

BASE = "https://api.github.com"

def _headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "AI-Research-Assistant"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def get_repo_info(owner: str, repo: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{BASE}/repos/{owner}/{repo}", headers=_headers())
            if r.status_code == 404:
                return {"error": f"Repo '{owner}/{repo}' not found"}
            r.raise_for_status()
            raw = r.json()
        return {
            "full_name": raw.get("full_name"),
            "description": (raw.get("description") or "")[:150],
            "stars": raw.get("stargazers_count", 0),
            "forks": raw.get("forks_count", 0),
            "open_issues": raw.get("open_issues_count", 0),
            "language": raw.get("language"),
            "last_pushed": raw.get("pushed_at", "")[:10],
            "is_archived": raw.get("archived", False),
            "topics": raw.get("topics", [])[:5],
        }
    except Exception as e:
        return {"error": str(e)}


async def get_trending_repos(language: str = "", since: str = "daily") -> dict:
    from datetime import datetime, timedelta
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 1)
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    q = f"created:>{cutoff} stars:>5"
    if language:
        q += f" language:{language}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{BASE}/search/repositories",
                headers=_headers(),
                params={"q": q, "sort": "stars", "order": "desc", "per_page": 5}
            )
            r.raise_for_status()
            data = r.json()
        return {
            "trending_repos": [
                {"name": i.get("full_name"), "stars": i.get("stargazers_count", 0),
                 "description": (i.get("description") or "")[:80], "language": i.get("language")}
                for i in data.get("items", [])
            ],
            "language_filter": language or "all", "period": since
        }
    except Exception as e:
        return {"error": str(e)}