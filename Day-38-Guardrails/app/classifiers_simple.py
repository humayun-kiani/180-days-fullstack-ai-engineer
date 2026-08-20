# ============================================================
# app/classifiers_simple.py
# Simple classifier for bias testing (no external deps)
# ============================================================


def keyword_classifier(task_title: str) -> str:
    """Fast keyword-based classifier for bias testing."""
    t = task_title.lower()

    # Strip name prefixes like "Ahmed says:" or "Sara from backend:"
    import re
    t = re.sub(r'^[\w\s]+(?:says?|from \w+):\s*', '', t)

    if any(w in t for w in ["urgent", "critical", "p0", "emergency", "down", "outage", "breach"]):
        return "urgent"
    if any(w in t for w in ["fix", "bug", "error", "slow", "crash", "failing", "before", "deadline"]):
        return "high"
    if any(w in t for w in ["add", "implement", "create", "build", "integrate", "feature"]):
        return "medium"
    return "low"