# ============================================================
# app/classifiers.py
# Three classifiers to compare in evaluation
# ============================================================

import os
import re
import json
import time
from typing import Protocol


class Classifier(Protocol):
    """Interface all classifiers must implement."""
    name: str

    def predict(self, task_title: str) -> str:
        """Predict priority: urgent, high, medium, or low."""
        ...


# ─── Classifier 1: Keyword Rules ─────────────────────────────

class KeywordClassifier:
    """Rule-based classifier using keyword matching."""

    name = "Keyword Rules"

    URGENCY_WORDS = {
        "urgent", "critical", "p0", "emergency", "immediate",
        "down", "outage", "breach", "security", "hotfix",
        "production", "incident", "blocking", "all users", "revenue"
    }
    HIGH_WORDS = {
        "fix", "bug", "error", "broken", "failing", "crash",
        "before", "deadline", "release", "slow", "performance",
        "vulnerability", "regression", "customer", "client"
    }
    MEDIUM_WORDS = {
        "add", "implement", "feature", "improve", "enhance",
        "new", "create", "build", "integrate", "support"
    }

    def predict(self, task_title: str) -> str:
        title_lower = task_title.lower()
        words = set(title_lower.split())

        for kw in self.URGENCY_WORDS:
            if kw in title_lower:
                return "urgent"

        for kw in self.HIGH_WORDS:
            if kw in title_lower:
                return "high"

        for kw in self.MEDIUM_WORDS:
            if kw in title_lower:
                return "medium"

        return "low"


# ─── Classifier 2: ML Model (Day 27 Random Forest) ───────────

class MLClassifier:
    """
    scikit-learn based classifier using TF-IDF + Random Forest.
    Trains on synthetic data if no saved model found.
    """

    name = "ML (TF-IDF + Random Forest)"

    def __init__(self):
        self._pipeline = None
        self._train()

    def _train(self):
        """Train a simple text classifier on synthetic data."""
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier

        # Training data
        train_texts = [
            # urgent
            "URGENT: Production API is completely down",
            "P0: All users cannot log in, emergency",
            "Critical security breach detected in auth module",
            "Hotfix needed: payment service returning 500 errors",
            "Production database down, revenue impact",
            "Emergency: data loss detected in prod",
            "Outage: all services unresponsive",
            "CRITICAL: customer data exposed",

            # high
            "Fix login bug causing 500 errors",
            "Fix null pointer exception in payment flow",
            "Performance degradation after last deployment",
            "Bug: authentication fails for 30% of users",
            "Slow database queries on reports page",
            "Fix race condition in concurrent requests",
            "Resolve failing CI pipeline before release",
            "Fix security vulnerability in user input handling",

            # medium
            "Add CSV export to reports page",
            "Implement dark mode for dashboard",
            "Add bulk task import feature",
            "Create user profile settings page",
            "Integrate with Slack for notifications",
            "Build analytics dashboard for admins",
            "Add pagination to task list endpoint",
            "Implement email digest for daily summaries",

            # low
            "Update README with new setup instructions",
            "Refactor user model for cleaner code",
            "Research GraphQL for future API redesign",
            "Add code comments to auth module",
            "Nice to have: keyboard shortcuts for dashboard",
            "Explore alternatives to current caching approach",
            "Update npm dependencies to latest versions",
            "Clean up unused CSS classes in stylesheet",
        ]
        train_labels = (
            ["urgent"] * 8 +
            ["high"] * 8 +
            ["medium"] * 8 +
            ["low"] * 8
        )

        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=500)),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self._pipeline.fit(train_texts, train_labels)

    def predict(self, task_title: str) -> str:
        if self._pipeline is None:
            return "medium"
        result = self._pipeline.predict([task_title])[0]
        return str(result)


# ─── Classifier 3: Claude (LLM) ──────────────────────────────

class ClaudeClassifier:
    """
    LLM-based classifier using Claude with few-shot examples.
    Falls back to keyword classifier if no API key.
    """

    name = "Claude (Few-Shot)"

    FEW_SHOT_PROMPT = """Classify task priority. Respond with ONE WORD ONLY: urgent, high, medium, or low.

Examples:
"URGENT: Production API down for all users" → urgent
"Fix authentication bug causing login failures" → high
"Add dark mode to the dashboard" → medium
"Update README documentation" → low
"Critical security breach in payment module" → urgent
"Slow database queries on reports page" → high
"Implement CSV export feature" → medium
"Research GraphQL alternatives" → low

Now classify this task: "{task}"

Priority (one word):"""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key)
            self._mock = False
        else:
            self._client = None
            self._mock = True
            self._fallback = KeywordClassifier()

    def predict(self, task_title: str) -> str:
        if self._mock:
            return self._fallback.predict(task_title)

        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": self.FEW_SHOT_PROMPT.format(task=task_title)
                }]
            )
            result = response.content[0].text.strip().lower()
            result = re.sub(r'[^a-z]', '', result)    # remove punctuation
            if result in ("urgent", "high", "medium", "low"):
                return result
            return "medium"
        except Exception:
            return self._fallback.predict(task_title)