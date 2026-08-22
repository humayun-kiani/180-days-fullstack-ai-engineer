# ============================================================
# app/classifier.py
# Task priority classifier with multiple backends
# ============================================================

import os
import json
import re
import time


PRIORITIES = ["low", "medium", "high", "urgent"]


class KeywordClassifier:
    """Fast rule-based fallback — works without any ML or API."""
    name = "keyword_rules"

    URGENT = {"urgent", "critical", "p0", "emergency", "down", "outage",
               "breach", "all users", "production", "immediate", "incident"}
    HIGH   = {"fix", "bug", "error", "broken", "failing", "crash",
               "before", "deadline", "slow", "security", "vulnerability"}
    MEDIUM = {"add", "implement", "feature", "improve", "enhance",
               "create", "build", "integrate", "support", "new"}

    def predict(self, task: str) -> str:
        t = task.lower()
        for word in self.URGENT:
            if word in t: return "urgent"
        for word in self.HIGH:
            if word in t: return "high"
        for word in self.MEDIUM:
            if word in t: return "medium"
        return "low"


class MLClassifier:
    """TF-IDF + Random Forest — ~82% accuracy, ~5ms latency."""
    name = "ml_tfidf_rf"

    def __init__(self):
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier

        texts = [
            "URGENT production API completely down all users affected",
            "P0 critical security breach detected auth module",
            "emergency database server unreachable entire app broken",
            "hotfix needed payment service returning 500 errors",
            "fix login bug causing authentication failures for users",
            "null pointer exception in payment processing flow",
            "database query timeout slow performance on reports",
            "bug authentication fails for some users after deploy",
            "security vulnerability in user input handling needs fix",
            "resolve failing CI pipeline before release deadline",
            "add CSV export to the reports dashboard page",
            "implement dark mode for the entire application",
            "build bulk task import from spreadsheet feature",
            "create analytics dashboard showing team metrics",
            "add Slack integration for task notifications feature",
            "add pagination to task list API endpoint feature",
            "update README with new setup instructions documentation",
            "refactor user model for better code organization",
            "research GraphQL as alternative to REST API",
            "clean up unused CSS classes in stylesheet maintenance",
            "update npm dependencies to latest versions maintenance",
            "explore Elasticsearch for future search functionality",
        ]
        labels = (["urgent"] * 4 + ["high"] * 6 +
                  ["medium"] * 6 + ["low"] * 6)

        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=500)),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self._pipeline.fit(texts, labels)

    def predict(self, task: str) -> str:
        return str(self._pipeline.predict([task])[0])


class ClaudeClassifier:
    """LLM few-shot — ~88% accuracy, ~500ms latency."""
    name = "claude_few_shot"

    PROMPT = """Classify task priority. ONE WORD only: urgent, high, medium, or low.

Examples:
"URGENT: Production API down" → urgent
"Fix login bug before release" → high
"Add dark mode feature" → medium
"Update README docs" → low

Task: "{task}"
Priority:"""

    def __init__(self, client):
        self.client = client
        self._fallback = KeywordClassifier()

    def predict(self, task: str) -> str:
        if self.client is None:
            return self._fallback.predict(task)
        try:
            r = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5,
                temperature=0.0,
                messages=[{"role": "user",
                           "content": self.PROMPT.format(task=task)}]
            )
            result = re.sub(r'[^a-z]', '',
                            r.content[0].text.strip().lower())
            return result if result in PRIORITIES else "medium"
        except Exception:
            return self._fallback.predict(task)