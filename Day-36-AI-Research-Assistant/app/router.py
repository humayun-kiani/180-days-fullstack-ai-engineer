# ============================================================
# app/router.py
# Query analysis and routing — determines which components to use
# ============================================================

from dataclasses import dataclass, field


@dataclass
class QueryIntent:
    """What a query needs to be answered."""
    original_query: str
    needs_kb: bool = False
    needs_weather: bool = False
    needs_github: bool = False
    needs_exchange_rates: bool = False
    needs_hackernews: bool = False
    needs_tasks: bool = False
    cities: list[str] = field(default_factory=list)
    github_repos: list[tuple[str, str]] = field(default_factory=list)
    currencies: list[str] = field(default_factory=list)
    kb_search_terms: list[str] = field(default_factory=list)


# Keyword sets for routing
KB_KEYWORDS = {
    "fix", "debug", "error", "how", "configure", "setup", "deploy",
    "slow", "performance", "jwt", "token", "cache", "redis", "docker",
    "test", "database", "postgresql", "connection", "health", "authentication"
}

WEATHER_KEYWORDS = {
    "weather", "temperature", "rain", "hot", "cold", "wind", "humid",
    "forecast", "sunny", "cloudy", "storm", "climate", "degrees"
}

GITHUB_KEYWORDS = {
    "github", "repo", "repository", "stars", "trending", "library",
    "framework", "open source", "project", "code", "commit", "fork"
}

RATE_KEYWORDS = {
    "currency", "exchange", "convert", "usd", "pkr", "eur", "gbp",
    "rate", "forex", "rupee", "dollar", "price", "cost", "money"
}

NEWS_KEYWORDS = {
    "news", "hacker", "hackernews", "hn", "stories", "trending",
    "tech", "today", "latest", "article"
}

TASK_KEYWORDS = {
    "task", "tasks", "overdue", "pending", "complete", "priority",
    "deadline", "work", "backlog", "sprint", "todo"
}

KNOWN_CITIES = {
    "karachi", "lahore", "islamabad", "london", "new york",
    "dubai", "san francisco", "tokyo", "paris", "sydney"
}


def analyze_query(query: str) -> QueryIntent:
    """
    Analyze a query to determine which data sources are needed.

    This is a lightweight rule-based router — fast, no LLM needed.
    In production: use a small classifier or LLM for better accuracy.
    """
    q_lower = query.lower()
    words = set(q_lower.split())
    intent = QueryIntent(original_query=query)

    # Check each data source
    if words & KB_KEYWORDS or any(kw in q_lower for kw in KB_KEYWORDS):
        intent.needs_kb = True
        # Extract KB search terms (non-stopwords)
        stopwords = {"how", "do", "i", "the", "a", "an", "is", "my", "to", "in", "of"}
        intent.kb_search_terms = [w for w in words - stopwords if len(w) > 3][:5]

    if words & WEATHER_KEYWORDS or any(kw in q_lower for kw in WEATHER_KEYWORDS):
        intent.needs_weather = True
        # Extract cities
        for city in KNOWN_CITIES:
            if city in q_lower:
                intent.cities.append(city.title())
        if not intent.cities:
            intent.cities = ["Karachi"]    # default

    if words & GITHUB_KEYWORDS or any(kw in q_lower for kw in GITHUB_KEYWORDS):
        intent.needs_github = True

    if words & RATE_KEYWORDS or any(kw in q_lower for kw in RATE_KEYWORDS):
        intent.needs_exchange_rates = True

    if words & NEWS_KEYWORDS or any(kw in q_lower for kw in NEWS_KEYWORDS):
        intent.needs_hackernews = True

    if words & TASK_KEYWORDS or any(kw in q_lower for kw in TASK_KEYWORDS):
        intent.needs_tasks = True

    # Default: if nothing matched, use KB
    if not any([
        intent.needs_kb, intent.needs_weather, intent.needs_github,
        intent.needs_exchange_rates, intent.needs_hackernews, intent.needs_tasks
    ]):
        intent.needs_kb = True
        intent.kb_search_terms = query.split()[:5]

    return intent