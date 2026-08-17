# ============================================================
# apis/github_api.py
# GitHub REST API integration
# ============================================================

import os
import httpx
from typing import Optional
from app.rate_limiter import RATE_LIMITERS

BASE_URL = "https://api.github.com"


def _get_headers() -> dict:
    """Get headers, using token if available for higher rate limits."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-API-Hub-Day35"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def get_repo_info(owner: str, repo: str) -> dict:
    """
    Get information about a GitHub repository.

    Args:
        owner: Repository owner (user or organization)
        repo: Repository name

    Returns:
        dict: Repository information
    """
    await RATE_LIMITERS["github"].acquire()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/repos/{owner}/{repo}",
                headers=_get_headers()
            )

            if response.status_code == 404:
                return {"error": f"Repository '{owner}/{repo}' not found"}
            response.raise_for_status()
            raw = response.json()

        # Transform to relevant fields only
        return {
            "full_name": raw.get("full_name"),
            "description": raw.get("description", "No description"),
            "stars": raw.get("stargazers_count", 0),
            "forks": raw.get("forks_count", 0),
            "open_issues": raw.get("open_issues_count", 0),
            "language": raw.get("language"),
            "last_pushed": raw.get("pushed_at", "")[:10],
            "is_archived": raw.get("archived", False),
            "license": raw.get("license", {}).get("name") if raw.get("license") else None,
            "topics": raw.get("topics", [])[:8],
            "homepage": raw.get("homepage"),
            "watchers": raw.get("watchers_count", 0),
        }

    except httpx.TimeoutException:
        return {"error": "GitHub API timed out"}
    except Exception as e:
        return {"error": str(e)}


async def get_trending_repos(
    language: str = "",
    since: str = "daily"
) -> dict:
    """
    Get trending GitHub repositories.

    Note: GitHub doesn't have an official trending API.
    We use a workaround via the search API.

    Args:
        language: Programming language filter (optional)
        since: Time period — "daily", "weekly", "monthly"

    Returns:
        dict: List of trending repos
    """
    await RATE_LIMITERS["github"].acquire()

    # Build search query to simulate trending
    from datetime import datetime, timedelta
    days_map = {"daily": 1, "weekly": 7, "monthly": 30}
    days = days_map.get(since, 1)
    date_cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    query = f"created:>{date_cutoff} stars:>10"
    if language:
        query += f" language:{language}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/search/repositories",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()

        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item.get("full_name"),
                "description": (item.get("description") or "")[:100],
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language"),
                "url": item.get("html_url"),
            })

        return {
            "trending_repos": repos,
            "total_found": data.get("total_count", 0),
            "language_filter": language or "all languages",
            "period": since
        }

    except httpx.TimeoutException:
        return {"error": "GitHub API timed out"}
    except Exception as e:
        return {"error": str(e)}


async def get_user_profile(username: str) -> dict:
    """Get public information about a GitHub user."""
    await RATE_LIMITERS["github"].acquire()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/users/{username}",
                headers=_get_headers()
            )
            if response.status_code == 404:
                return {"error": f"GitHub user '{username}' not found"}
            response.raise_for_status()
            raw = response.json()

        return {
            "username": raw.get("login"),
            "name": raw.get("name"),
            "bio": raw.get("bio"),
            "location": raw.get("location"),
            "company": raw.get("company"),
            "public_repos": raw.get("public_repos", 0),
            "followers": raw.get("followers", 0),
            "following": raw.get("following", 0),
            "joined": raw.get("created_at", "")[:10],
        }

    except Exception as e:
        return {"error": str(e)}