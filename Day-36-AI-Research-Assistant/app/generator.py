# ============================================================
# app/generator.py
# Claude generation from fused context
# ============================================================

import json
import os
import time
from typing import Optional

import anthropic

SYSTEM_PROMPT = """You are an AI Research Assistant with access to multiple real-time data sources.

Your context includes:
- Internal knowledge base documentation (most authoritative for technical questions)
- Live weather data from Open-Meteo API
- GitHub repository and trending data
- Live currency exchange rates
- Hacker News top tech stories
- Current task management data

Guidelines:
1. Ground your answer in the provided context — cite your sources
2. Be specific and actionable, not generic
3. If multiple sources are relevant, synthesize them
4. Acknowledge when data is live (weather, rates, news) vs documented
5. Keep responses focused and under 400 words unless detail is needed
6. Use markdown formatting for readability"""


class MockGenerator:
    """Generate realistic responses without real API key."""

    TEMPLATES = {
        "auth": """Based on our **JWT Token Expiration documentation**:

Access tokens in your system expire after **30 minutes** by design. When you receive a 401 Unauthorized:

1. **Check token expiry**: Decode the JWT and compare `exp` with current timestamp
2. **Use refresh endpoint**: `POST /api/v1/auth/refresh` with your refresh token
3. **Important**: Refresh tokens are ONE-TIME USE — after refreshing, the old token is invalidated

Refresh tokens last **7 days**. Store them in httpOnly cookies for security. If both tokens expire, the user must log in again.

*Source: Knowledge Base — JWT Token Expiration Guide*""",

        "weather": """Here's the **real-time weather** from Open-Meteo API:

🌡️ **Weather in {city}**:
- Temperature: {temp}°C (feels like {feels_like}°C)
- Condition: {condition}
- Humidity: {humidity}% | Wind: {wind} km/h

*Source: Open-Meteo API (free, no key required)*""",

        "github": """Here are the **trending repositories** from GitHub this week:

🔥 **Trending Projects**:
1. Various AI/ML frameworks dominating the charts
2. Python remains the most popular language for new projects
3. Developer tools and productivity apps seeing high growth

*Source: GitHub REST API*""",

        "tasks": """Here's your **current task status**:

📋 **Task Overview**:
- 🔴 **Urgent**: Production DB slow (pending — needs immediate attention!)
- 🟡 **High**: Fix login 500 error (in progress)
- 🟢 **Medium**: Add CSV export, Redis caching (pending)
- ✅ **Done**: Update API docs

**Recommendation**: Address the production DB issue immediately — it's marked urgent and pending.""",

        "news": """Here are **today's top HackerNews stories**:

📰 **Tech Headlines**:
Stories are being actively discussed in the developer community.
Key themes: AI/ML advances, developer tooling, system design.

*Source: Hacker News Firebase API*""",

        "default": """I've analyzed your question using multiple data sources.

Based on the available context, here's what I found:

The query touches on both technical documentation and live data. I recommend:
1. Reviewing the relevant knowledge base articles for implementation details
2. Checking the live data feeds for current status

Would you like me to focus on a specific aspect of your question?"""
    }

    def generate(self, query: str, context_str: str, sources: list[str]) -> dict:
        """Generate a contextual mock response."""
        q_lower = query.lower()

        if any(w in q_lower for w in ["jwt", "token", "401", "auth", "login"]):
            answer = self.TEMPLATES["auth"]
        elif any(w in q_lower for w in ["weather", "temperature", "rain"]):
            answer = self.TEMPLATES["weather"].format(
                city="Karachi", temp="32", feels_like="36",
                condition="Partly cloudy", humidity="68", wind="15"
            )
        elif any(w in q_lower for w in ["github", "trending", "repo"]):
            answer = self.TEMPLATES["github"]
        elif any(w in q_lower for w in ["task", "overdue", "pending"]):
            answer = self.TEMPLATES["tasks"]
        elif any(w in q_lower for w in ["news", "hacker", "stories"]):
            answer = self.TEMPLATES["news"]
        else:
            answer = self.TEMPLATES["default"]

        return {
            "answer": answer,
            "sources": sources,
            "tokens_used": {"input": 450, "output": 150},
            "model": "mock"
        }


class ClaudeGenerator:
    """Generate answers using real Claude API."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.mock = False
        else:
            self.client = None
            self.mock = True
            self._mock = MockGenerator()

    def generate(
        self,
        query: str,
        context: str,
        sources: list[str],
        max_tokens: int = 1024,
        temperature: float = 0.5
    ) -> dict:
        """Generate a grounded answer from the fused context."""
        if self.mock:
            return self._mock.generate(query, context, sources)

        start = time.perf_counter()

        prompt = f"""CONTEXT FROM DATA SOURCES:
{context}

---

USER QUESTION:
{query}

---

Please answer the question based on the context above.
Cite which source(s) you are drawing from.
If data is live (weather, rates, news), note that it reflects current conditions."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=temperature,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response.content[0].text
            elapsed = (time.perf_counter() - start) * 1000

            return {
                "answer": answer,
                "sources": sources,
                "tokens_used": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens
                },
                "model": "claude-sonnet-4-6",
                "generation_ms": round(elapsed, 1)
            }

        except Exception as e:
            return {
                "answer": f"Generation failed: {str(e)}",
                "sources": sources,
                "tokens_used": {},
                "model": "error"
            }