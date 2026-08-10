# ============================================================
# app/nlp_analyzer.py
# Self-contained NLP analysis (no external model files needed)
# Combines Day 28's sentiment, entity extraction, and rule-based
# classification — works without trained sklearn NLP model
# ============================================================

import re
from dataclasses import dataclass, field

# ─── Sentiment Lexicons ──────────────────────────────────────

POSITIVE_SIGNALS = {
    "excellent": 3, "perfect": 3, "outstanding": 3, "amazing": 3,
    "great": 2, "works": 1, "working": 1, "fixed": 2, "resolved": 2,
    "thanks": 1, "helpful": 2, "fast": 1, "easy": 1, "smooth": 1,
    "correct": 1, "clean": 1, "nice": 1, "improved": 2, "good": 2,
    "okay": 0.5, "fine": 0.5, "decent": 0.5,
}

NEGATIVE_SIGNALS = {
    "broken": 3, "terrible": 3, "horrible": 3, "disaster": 3,
    "error": 2, "crash": 2, "fail": 2, "failure": 2, "bug": 2,
    "wrong": 2, "bad": 2, "slow": 2, "stuck": 2, "blocked": 2,
    "frustrated": 2, "disappointed": 2, "useless": 2,
    "issue": 1, "problem": 1, "weird": 1, "unexpected": 1,
    "confusing": 1, "difficult": 1,
}

URGENCY_SIGNALS = {
    "urgent": 3, "critical": 3, "emergency": 3, "immediate": 3,
    "asap": 3, "now": 2, "today": 2, "deadline": 2, "blocking": 2,
    "priority": 1, "important": 1, "quickly": 1,
}

NEGATORS = {"not", "no", "never", "without", "cannot", "cant",
            "wont", "doesnt", "dont", "didnt", "isnt", "arent"}

# ─── Category Keywords ────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "bug": {
        "broken", "crash", "error", "fail", "null", "exception",
        "bug", "fix", "broken", "not working", "returns", "500", "404"
    },
    "performance": {
        "slow", "timeout", "latency", "memory", "cpu", "performance",
        "degraded", "optimization", "speed", "fast", "response time"
    },
    "feature_request": {
        "add", "implement", "feature", "request", "enhancement",
        "support", "allow", "enable", "integrate", "would like"
    },
    "question": {
        "how", "what", "why", "when", "where", "can i", "is it",
        "documentation", "help", "guide", "explain"
    },
    "maintenance": {
        "update", "upgrade", "migrate", "clean", "remove", "backup",
        "certificate", "renew", "maintenance", "deprecated", "archive"
    }
}

KNOWN_SYSTEMS = [
    "api", "database", "auth", "cache", "redis", "nginx", "docker",
    "postgresql", "mongodb", "celery", "rabbitmq", "elasticsearch",
    "aws", "gcp", "azure", "kubernetes", "grafana", "prometheus"
]

TAG_KEYWORDS = {
    "backend": ["api", "server", "endpoint", "service", "database"],
    "frontend": ["ui", "dashboard", "page", "button", "form"],
    "auth": ["login", "logout", "password", "token", "jwt", "oauth"],
    "database": ["sql", "query", "table", "migration", "schema", "db"],
    "performance": ["slow", "fast", "latency", "timeout", "cache", "optimize"],
    "security": ["vulnerability", "breach", "injection", "auth", "permission"],
    "devops": ["deploy", "ci", "cd", "docker", "kubernetes", "pipeline"],
    "bug": ["bug", "error", "crash", "exception", "null", "broken"],
    "urgent": ["urgent", "critical", "asap", "emergency", "blocking"],
}


@dataclass
class NLPResult:
    category: str
    category_confidence: float
    sentiment: str
    urgency_level: str
    positive_score: float
    negative_score: float
    sentiment_signals: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)
    systems: list[str] = field(default_factory=list)
    time_mentions: list[str] = field(default_factory=list)
    suggested_tags: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)


def classify_category(text: str) -> tuple[str, float]:
    """Rule-based category classification."""
    text_lower = text.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score

    total = sum(scores.values())
    if total == 0:
        return "general", 0.5

    best = max(scores, key=scores.get)
    confidence = min(0.95, 0.5 + scores[best] / max(total, 1) * 0.5)
    return best, round(confidence, 3)


def analyze_sentiment_and_urgency(text: str) -> tuple:
    """Analyze sentiment and urgency from text."""
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos_score = 0.0
    neg_score = 0.0
    urgency_score = 0.0
    signals = []

    # CAPS and exclamation marks
    caps = re.findall(r'\b[A-Z]{2,}\b', text)
    if caps:
        urgency_score += len(caps) * 0.5
        signals.append(f"CAPS: {', '.join(caps[:3])}")
    excl = text.count("!")
    if excl:
        neg_score += min(excl * 0.5, 2)
        signals.append(f"{excl} exclamation mark(s)")

    negate = False
    for word in words:
        if word in NEGATORS:
            negate = True
            continue
        mult = -1 if negate else 1
        negate = False

        if word in POSITIVE_SIGNALS:
            s = POSITIVE_SIGNALS[word]
            if mult == -1:
                neg_score += s
                signals.append(f"negated positive: '{word}'")
            else:
                pos_score += s
                if s >= 2:
                    signals.append(f"positive: '{word}'")

        elif word in NEGATIVE_SIGNALS:
            s = NEGATIVE_SIGNALS[word]
            if mult == -1:
                pos_score += s * 0.5
                signals.append(f"negated negative: '{word}'")
            else:
                neg_score += s
                if s >= 2:
                    signals.append(f"negative: '{word}'")

        if word in URGENCY_SIGNALS:
            urgency_score += URGENCY_SIGNALS[word]
            if URGENCY_SIGNALS[word] >= 2:
                signals.append(f"urgency: '{word}'")

    # Sentiment
    total = pos_score + neg_score
    if total == 0:
        sentiment = "neutral"
    elif pos_score > neg_score * 1.5:
        sentiment = "positive"
    elif neg_score > pos_score * 1.5:
        sentiment = "negative"
    else:
        sentiment = "mixed"

    urgency = "high" if urgency_score >= 4 else "medium" if urgency_score >= 2 else "low"

    return sentiment, urgency, round(pos_score, 2), round(neg_score, 2), signals[:6]


def extract_entities_and_tags(text: str) -> tuple:
    """Extract entities and suggest tags from text."""
    text_lower = text.lower()

    error_codes = list(set(re.findall(r'\b([4-5]\d{2})\b', text)))
    systems = [s for s in KNOWN_SYSTEMS if re.search(r'\b' + s + r'\b', text_lower)]
    time_mentions = list(set(re.findall(
        r'\b(today|tomorrow|asap|urgent|immediately|by\s+\w+day|eod)\b',
        text, re.IGNORECASE
    )))

    tags = set()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.add(tag)

    action_items = []
    for match in re.findall(
        r'(?:need\s+to|must|should|please|fix|implement|add)\s+([\w\s]+?)(?:\.|,|$)',
        text_lower
    ):
        item = match.strip()
        if 3 < len(item) < 50:
            action_items.append(item)

    return (
        error_codes,
        systems[:5],
        time_mentions[:3],
        sorted(tags),
        action_items[:3]
    )


def analyze(text: str) -> NLPResult:
    """Run complete NLP analysis on text."""
    category, cat_conf = classify_category(text)
    sentiment, urgency, pos, neg, signals = analyze_sentiment_and_urgency(text)
    errors, systems, times, tags, actions = extract_entities_and_tags(text)

    return NLPResult(
        category=category,
        category_confidence=cat_conf,
        sentiment=sentiment,
        urgency_level=urgency,
        positive_score=pos,
        negative_score=neg,
        sentiment_signals=signals,
        error_codes=errors,
        systems=systems,
        time_mentions=times,
        suggested_tags=tags,
        action_items=actions
    )