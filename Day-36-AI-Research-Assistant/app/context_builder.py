# ============================================================
# app/context_builder.py
# Fuse context from multiple sources into one LLM-ready string
# ============================================================

import json
from dataclasses import dataclass, field


@dataclass
class FusedContext:
    """All context collected for a query."""
    kb_results: list[dict] = field(default_factory=list)
    weather_data: dict = field(default_factory=dict)
    github_data: dict = field(default_factory=dict)
    exchange_data: dict = field(default_factory=dict)
    news_data: dict = field(default_factory=dict)
    task_data: list[dict] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)

    def build_context_string(self, max_chars: int = 8000) -> str:
        """
        Format all context into a single string for the LLM prompt.

        Prioritizes KB results (highest quality, curated).
        Truncates aggressively to stay within token budget.
        Labels each source clearly for attribution.
        """
        parts = []

        # Knowledge base docs (highest priority)
        if self.kb_results:
            parts.append("=== KNOWLEDGE BASE DOCUMENTATION ===")
            for i, doc in enumerate(self.kb_results[:3]):
                title = doc.get("title", f"Document {i+1}")
                content = doc.get("content", "")[:500]
                parts.append(f"[Source: {title}]\n{content}")

        # Live external data
        if self.weather_data and "error" not in self.weather_data:
            parts.append("\n=== WEATHER DATA (Open-Meteo) ===")
            w = self.weather_data
            parts.append(
                f"City: {w.get('city')} | "
                f"Temp: {w.get('temperature_c')}°C | "
                f"Feels like: {w.get('feels_like_c')}°C | "
                f"Condition: {w.get('condition')} | "
                f"Humidity: {w.get('humidity_pct')}% | "
                f"Wind: {w.get('wind_speed_kmh')} km/h"
            )

        if self.github_data and "error" not in self.github_data:
            parts.append("\n=== GITHUB DATA ===")
            parts.append(json.dumps(self.github_data, indent=2)[:600])

        if self.exchange_data and "error" not in self.exchange_data:
            parts.append("\n=== EXCHANGE RATES (Open.er-api.com) ===")
            rates = self.exchange_data.get("rates", {})
            base = self.exchange_data.get("base", "USD")
            rate_str = " | ".join(f"{k}: {v}" for k, v in list(rates.items())[:8])
            parts.append(f"Base: {base} | {rate_str}")

        if self.news_data and "error" not in self.news_data:
            parts.append("\n=== HACKER NEWS TOP STORIES ===")
            for story in self.news_data.get("stories", [])[:4]:
                parts.append(
                    f"• {story.get('title')} "
                    f"(⬆{story.get('score', 0)} | "
                    f"💬{story.get('comments', 0)})"
                )

        if self.task_data:
            parts.append("\n=== CURRENT TASKS ===")
            for task in self.task_data[:6]:
                overdue = " ⚠️OVERDUE" if task.get("is_overdue") else ""
                parts.append(
                    f"• [{task['priority'].upper()}] {task['title']} "
                    f"({task['status']}){overdue}"
                )

        context = "\n".join(parts)

        # Hard truncation
        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Context truncated for brevity]"

        return context