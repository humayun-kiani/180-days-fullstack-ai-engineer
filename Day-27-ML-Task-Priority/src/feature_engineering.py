# ============================================================
# src/feature_engineering.py
# Extract ML features from task data
# ============================================================

import re
import numpy as np
import pandas as pd
from datetime import datetime


# ─── Keyword Sets ────────────────────────────────────────────

URGENCY_WORDS = {
    "urgent", "asap", "critical", "immediately", "emergency",
    "hotfix", "incident", "outage", "p0", "escalation",
    "blocking", "down", "failure", "crash", "breach"
}

HIGH_PRIORITY_WORDS = {
    "fix", "deploy", "release", "deadline", "review",
    "performance", "security", "launch", "production", "bug"
}

LOW_PRIORITY_WORDS = {
    "nice", "optional", "future", "research", "explore",
    "investigate", "consider", "cleanup", "refactor"
}

ACTION_VERBS = {
    "fix", "implement", "deploy", "create", "add", "update",
    "review", "resolve", "optimize", "migrate", "set", "write",
    "design", "build", "test", "integrate", "configure"
}


def extract_features(task: dict) -> dict:
    """
    Extract numeric features from a single task dictionary.

    Args:
        task: Task data dictionary.

    Returns:
        dict: Feature dictionary with numeric values only.
    """
    now = datetime.utcnow()
    title = str(task.get("title", "")).lower()
    title_original = str(task.get("title", ""))
    description = str(task.get("description") or "")
    tags = task.get("tags", []) or []
    words = title.split()
    word_set = set(words)

    # ── Title Features ────────────────────────────────────────
    features = {
        "title_word_count": len(words),
        "title_char_count": len(title_original),
        "title_upper_ratio": (
            sum(1 for c in title_original if c.isupper()) /
            len(title_original) if title_original else 0
        ),
        "has_exclamation": int("!" in title_original),
        "has_colon": int(":" in title_original),
        "starts_with_verb": int(words[0] in ACTION_VERBS if words else False),
        "has_number": int(bool(re.search(r'\d+', title))),

        # Keyword features
        "urgency_word_count": sum(1 for w in word_set if w in URGENCY_WORDS),
        "high_priority_word_count": sum(
            1 for w in word_set if w in HIGH_PRIORITY_WORDS
        ),
        "low_priority_word_count": sum(
            1 for w in word_set if w in LOW_PRIORITY_WORDS
        ),

        # Systems mentioned
        "mentions_production": int(
            "production" in title or "prod" in title
        ),
        "mentions_customer": int(
            any(w in title for w in ("customer", "client", "user"))
        ),
        "mentions_security": int(
            any(w in title for w in ("security", "breach", "vulnerability", "auth"))
        ),
    }

    # ── Description Features ──────────────────────────────────
    features.update({
        "has_description": int(bool(description.strip())),
        "description_word_count": len(description.split()) if description else 0,
        "description_urgency_words": sum(
            1 for w in description.lower().split() if w in URGENCY_WORDS
        ),
    })

    # ── Due Date Features ─────────────────────────────────────
    due_date_str = task.get("due_date")
    has_due_date = due_date_str is not None and due_date_str != "None"

    features["has_due_date"] = int(has_due_date)
    features["is_overdue"] = 0
    features["days_until_due"] = 0
    features["hours_until_due"] = 0
    features["due_today"] = 0
    features["due_this_week"] = 0
    features["due_within_3_days"] = 0

    if has_due_date:
        try:
            if isinstance(due_date_str, str):
                due_date = datetime.fromisoformat(due_date_str)
            else:
                due_date = due_date_str

            delta_hours = (due_date - now).total_seconds() / 3600
            delta_days = delta_hours / 24

            features.update({
                "is_overdue": int(delta_hours < 0),
                "hours_until_due": max(-168, min(168, delta_hours)),  # clip to ±1 week
                "days_until_due": max(-7, min(30, delta_days)),       # clip
                "due_today": int(0 <= delta_hours <= 24),
                "due_this_week": int(0 <= delta_days <= 7),
                "due_within_3_days": int(0 <= delta_days <= 3),
            })
        except (ValueError, TypeError):
            pass

    # ── Task Metadata Features ────────────────────────────────
    features.update({
        "tag_count": len(tags),
        "has_estimate": int(task.get("estimated_hours") is not None),
        "estimated_hours": float(task.get("estimated_hours") or 0),
        "short_estimate": int(
            float(task.get("estimated_hours") or 999) <= 2
        ),
        "long_estimate": int(
            float(task.get("estimated_hours") or 0) >= 8
        ),
    })

    # ── Time Context Features ─────────────────────────────────
    hour = task.get("hour_of_day", now.hour)
    dow = task.get("day_of_week", now.weekday())

    features.update({
        "hour_of_day": int(hour),
        "day_of_week": int(dow),
        "is_business_hours": int(9 <= int(hour) < 18 and int(dow) < 5),
        "is_monday_morning": int(int(dow) == 0 and int(hour) < 12),
        "is_friday_afternoon": int(int(dow) == 4 and int(hour) >= 14),
        "is_weekend": int(int(dow) >= 5),
        "created_late_night": int(int(hour) >= 22 or int(hour) < 6),
    })

    return features


def build_feature_matrix(
    tasks: pd.DataFrame | list[dict]
) -> tuple[pd.DataFrame, list[str]]:
    """
    Build the feature matrix X from a list of task dicts or DataFrame.

    Args:
        tasks: Task data.

    Returns:
        tuple: (features_df, feature_names)
    """
    if isinstance(tasks, pd.DataFrame):
        task_list = tasks.to_dict("records")
    else:
        task_list = tasks

    feature_rows = [extract_features(task) for task in task_list]
    features_df = pd.DataFrame(feature_rows).fillna(0)

    return features_df, list(features_df.columns)


# Priority label mapping
PRIORITY_LABELS = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "urgent": 3
}

PRIORITY_NAMES = {v: k for k, v in PRIORITY_LABELS.items()}


def encode_labels(priorities: pd.Series | list) -> np.ndarray:
    """Convert priority strings to numeric labels."""
    if isinstance(priorities, pd.Series):
        return priorities.map(PRIORITY_LABELS).fillna(1).astype(int).values
    return np.array([PRIORITY_LABELS.get(p, 1) for p in priorities])


def decode_labels(numeric: np.ndarray | list) -> list[str]:
    """Convert numeric labels back to priority strings."""
    return [PRIORITY_NAMES.get(int(n), "medium") for n in numeric]