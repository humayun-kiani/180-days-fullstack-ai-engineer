# ============================================================
# app/feature_extractor.py
# Extract numeric features from task text + metadata
# Combines Day 27's feature engineering with Day 28's NLP signals
# ============================================================

import re
from datetime import datetime


URGENCY_WORDS = {
    "urgent", "asap", "critical", "immediately", "emergency",
    "hotfix", "incident", "outage", "p0", "escalation",
    "blocking", "down", "failure", "crash", "breach"
}
HIGH_WORDS = {"fix", "deploy", "release", "deadline", "review", "security", "bug"}
LOW_WORDS = {"nice", "optional", "future", "research", "explore", "investigate"}
ACTION_VERBS = {
    "fix", "implement", "deploy", "create", "add", "update",
    "review", "resolve", "optimize", "migrate", "configure"
}

FEATURE_NAMES = [
    "title_word_count", "title_char_count", "title_upper_ratio",
    "has_exclamation", "has_colon", "starts_with_verb", "has_number",
    "urgency_word_count", "high_priority_word_count", "low_priority_word_count",
    "mentions_production", "mentions_customer", "mentions_security",
    "has_description", "description_word_count", "description_urgency_words",
    "has_due_date", "is_overdue", "days_until_due", "hours_until_due",
    "due_today", "due_this_week", "due_within_3_days",
    "tag_count", "has_estimate", "estimated_hours", "short_estimate", "long_estimate",
    "hour_of_day", "day_of_week", "is_business_hours",
    "is_monday_morning", "is_friday_afternoon", "is_weekend", "created_late_night",
]


def extract_features(task: dict) -> dict:
    """
    Extract numeric features from a task dictionary.

    Args:
        task: Task data (title, description, metadata)

    Returns:
        dict: Feature name → numeric value
    """
    now = datetime.utcnow()
    title = str(task.get("title", ""))
    title_lower = title.lower()
    description = str(task.get("description") or "")
    tags = task.get("tags", []) or []
    words = title_lower.split()
    word_set = set(words)

    has_due_date = bool(task.get("has_due_date"))
    is_overdue = bool(task.get("is_overdue"))
    days_until = float(task.get("days_until_due", 0) or 0)
    estimated = task.get("estimated_hours")
    hour = now.hour
    dow = now.weekday()

    features = {
        # Title text features
        "title_word_count": len(words),
        "title_char_count": len(title),
        "title_upper_ratio": (
            sum(1 for c in title if c.isupper()) / max(len(title), 1)
        ),
        "has_exclamation": int("!" in title),
        "has_colon": int(":" in title),
        "starts_with_verb": int(words[0] in ACTION_VERBS if words else False),
        "has_number": int(bool(re.search(r'\d', title))),

        # Keyword signals
        "urgency_word_count": sum(1 for w in word_set if w in URGENCY_WORDS),
        "high_priority_word_count": sum(1 for w in word_set if w in HIGH_WORDS),
        "low_priority_word_count": sum(1 for w in word_set if w in LOW_WORDS),

        # Topic signals
        "mentions_production": int(
            any(w in title_lower for w in ("production", "prod"))
        ),
        "mentions_customer": int(
            any(w in title_lower for w in ("customer", "client", "user"))
        ),
        "mentions_security": int(
            any(w in title_lower for w in ("security", "breach", "vulnerability"))
        ),

        # Description features
        "has_description": int(bool(description.strip())),
        "description_word_count": len(description.split()) if description else 0,
        "description_urgency_words": sum(
            1 for w in description.lower().split() if w in URGENCY_WORDS
        ),

        # Due date features
        "has_due_date": int(has_due_date),
        "is_overdue": int(is_overdue),
        "days_until_due": max(-7, min(30, days_until)),
        "hours_until_due": max(-168, min(168, days_until * 24)),
        "due_today": int(has_due_date and 0 <= days_until <= 1),
        "due_this_week": int(has_due_date and 0 <= days_until <= 7),
        "due_within_3_days": int(has_due_date and 0 <= days_until <= 3),

        # Task metadata
        "tag_count": len(tags),
        "has_estimate": int(estimated is not None),
        "estimated_hours": float(estimated or 0),
        "short_estimate": int(float(estimated or 999) <= 2),
        "long_estimate": int(float(estimated or 0) >= 8),

        # Time context
        "hour_of_day": hour,
        "day_of_week": dow,
        "is_business_hours": int(9 <= hour < 18 and dow < 5),
        "is_monday_morning": int(dow == 0 and hour < 12),
        "is_friday_afternoon": int(dow == 4 and hour >= 14),
        "is_weekend": int(dow >= 5),
        "created_late_night": int(hour >= 22 or hour < 6),
    }

    return features


def features_to_vector(features: dict) -> list[float]:
    """Convert feature dict to ordered list for ML models."""
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]