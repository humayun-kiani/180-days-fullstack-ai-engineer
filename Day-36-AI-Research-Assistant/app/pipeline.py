# ============================================================
# app/pipeline.py
# Orchestrates the full research pipeline
# ============================================================

import asyncio
import time
from datetime import datetime

from app.router import QueryIntent, analyze_query
from app.context_builder import FusedContext
from data.knowledge_base import ARTICLES, TASKS
from apis.weather import get_weather
from apis.github_api import get_repo_info, get_trending_repos
from apis.exchange_rates import get_rates
from apis.hackernews import get_top_stories


def _keyword_kb_search(query: str, top_k: int = 3) -> list[dict]:
    """
    Simple keyword-based KB search.
    In production: use ChromaDB from Day 31.
    """
    q_words = set(query.lower().split())
    scored = []
    for article in ARTICLES:
        text = f"{article['title']} {article['content']}".lower()
        score = sum(1 for w in q_words if w in text)
        if score > 0:
            scored.append((score, article))
    scored.sort(reverse=True)
    return [a for _, a in scored[:top_k]]


def _get_task_data(include_overdue_only: bool = False) -> list[dict]:
    """Get tasks from the simulated task database."""
    tasks = []
    for task in TASKS:
        t = task.copy()
        # Simulate overdue check
        t["is_overdue"] = (
            task["priority"] == "urgent" and task["status"] == "pending"
        )
        tasks.append(t)
    if include_overdue_only:
        tasks = [t for t in tasks if t.get("is_overdue")]
    return tasks


class ResearchPipeline:
    """
    Orchestrates the full research pipeline.

    For each query:
    1. Analyze intent (router)
    2. Fetch all needed data in parallel
    3. Fuse into context
    4. Return FusedContext ready for generation
    """

    async def run(self, query: str) -> tuple[QueryIntent, FusedContext, float]:
        """
        Run the pipeline for a query.

        Returns:
            tuple: (intent, fused_context, elapsed_ms)
        """
        start = time.perf_counter()

        # Step 1: Route
        intent = analyze_query(query)

        # Step 2: Build coroutines for all needed data sources
        coros = {}

        if intent.needs_kb:
            # Synchronous — wrapped to be awaitable
            async def fetch_kb():
                return _keyword_kb_search(
                    " ".join(intent.kb_search_terms) or query
                )
            coros["kb"] = fetch_kb()

        if intent.needs_weather:
            city = intent.cities[0] if intent.cities else "Karachi"
            coros["weather"] = get_weather(city)

        if intent.needs_github:
            # Try trending or default to FastAPI repo
            coros["github"] = get_trending_repos(since="weekly")

        if intent.needs_exchange_rates:
            coros["rates"] = get_rates("USD")

        if intent.needs_hackernews:
            coros["news"] = get_top_stories(count=5)

        if intent.needs_tasks:
            async def fetch_tasks():
                return _get_task_data()
            coros["tasks"] = fetch_tasks()

        # Step 3: Execute all in parallel
        if coros:
            keys = list(coros.keys())
            results = await asyncio.gather(
                *coros.values(),
                return_exceptions=True
            )
            results_dict = {
                k: (v if not isinstance(v, Exception) else {"error": str(v)})
                for k, v in zip(keys, results)
            }
        else:
            results_dict = {}

        # Step 4: Build FusedContext
        context = FusedContext()
        sources = []

        if "kb" in results_dict:
            context.kb_results = results_dict["kb"] or []
            if context.kb_results:
                sources.append("Knowledge Base")

        if "weather" in results_dict:
            context.weather_data = results_dict["weather"]
            if "error" not in context.weather_data:
                sources.append("Open-Meteo Weather API")

        if "github" in results_dict:
            context.github_data = results_dict["github"]
            if "error" not in context.github_data:
                sources.append("GitHub API")

        if "rates" in results_dict:
            context.exchange_data = results_dict["rates"]
            if "error" not in context.exchange_data:
                sources.append("Exchange Rate API")

        if "news" in results_dict:
            context.news_data = results_dict["news"]
            if "error" not in context.news_data:
                sources.append("HackerNews API")

        if "tasks" in results_dict:
            context.task_data = results_dict["tasks"] or []
            if context.task_data:
                sources.append("Task Database")

        context.sources_used = sources

        elapsed = (time.perf_counter() - start) * 1000
        return intent, context, elapsed