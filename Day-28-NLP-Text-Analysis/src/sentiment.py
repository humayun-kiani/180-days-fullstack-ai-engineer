# ============================================================
# src/sentiment.py
# Sentiment analysis for task descriptions and feedback
# ============================================================

import re
from dataclasses import dataclass


# ─── Sentiment Lexicons ──────────────────────────────────────

POSITIVE_SIGNALS = {
    # Strong positive
    "excellent": 3, "perfect": 3, "outstanding": 3, "amazing": 3,
    "fantastic": 3, "brilliant": 3, "love": 2, "great": 2,
    # Moderate positive
    "good": 2, "works": 1, "working": 1, "fixed": 2, "resolved": 2,
    "thanks": 1, "helpful": 2, "fast": 1, "easy": 1, "smooth": 1,
    "correct": 1, "clean": 1, "clear": 1, "nice": 1, "improved": 2,
    # Weak positive
    "okay": 0.5, "fine": 0.5, "decent": 0.5, "acceptable": 0.5,
}

NEGATIVE_SIGNALS = {
    # Strong negative
    "broken": 3, "terrible": 3, "horrible": 3, "disaster": 3,
    "catastrophe": 3, "unacceptable": 3, "completely wrong": 3,
    # Moderate negative
    "error": 2, "crash": 2, "fail": 2, "failure": 2, "bug": 2,
    "wrong": 2, "bad": 2, "slow": 2, "stuck": 2, "blocked": 2,
    "frustrated": 2, "disappointed": 2, "annoying": 2, "useless": 2,
    # Weak negative
    "issue": 1, "problem": 1, "weird": 1, "unexpected": 1,
    "confusing": 1, "unclear": 1, "difficult": 1, "concern": 1,
}

URGENCY_SIGNALS = {
    "urgent": 3, "critical": 3, "emergency": 3, "immediate": 3,
    "asap": 3, "now": 2, "today": 2, "deadline": 2, "blocking": 2,
    "priority": 1, "important": 1, "quickly": 1, "soon": 1,
}

NEGATORS = {"not", "no", "never", "without", "cannot", "cant",
            "wont", "doesnt", "dont", "didnt", "isnt", "arent"}


@dataclass
class SentimentResult:
    sentiment: str           # "positive", "negative", "neutral"
    urgency: str             # "high", "medium", "low"
    confidence: float        # 0.0 to 1.0
    positive_score: float
    negative_score: float
    urgency_score: float
    signals: list[str]       # which words triggered the analysis


def analyze_sentiment(text: str) -> SentimentResult:
    """
    Analyze sentiment and urgency of task description text.

    Uses a lexicon-based approach with negation handling.

    Args:
        text: Input text to analyze.

    Returns:
        SentimentResult: Detailed sentiment analysis.
    """
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos_score = 0.0
    neg_score = 0.0
    urgency_score = 0.0
    signals = []

    # Check for ALL_CAPS words (extra urgency signal)
    caps_words = re.findall(r'\b[A-Z]{2,}\b', text)
    if caps_words:
        urgency_score += len(caps_words) * 0.5
        signals.append(f"CAPS: {', '.join(caps_words[:3])}")

    # Check exclamation marks
    excl_count = text.count("!")
    if excl_count > 0:
        neg_score += min(excl_count * 0.5, 2)
        signals.append(f"{excl_count} exclamation mark(s)")

    # Score each word with negation detection
    negate_next = False
    for i, word in enumerate(words):
        if word in NEGATORS:
            negate_next = True
            continue

        multiplier = -1 if negate_next else 1
        negate_next = False

        if word in POSITIVE_SIGNALS:
            score = POSITIVE_SIGNALS[word]
            if multiplier == -1:
                neg_score += score
                signals.append(f"negated positive: '{word}'")
            else:
                pos_score += score
                if score >= 2:
                    signals.append(f"positive: '{word}'")

        elif word in NEGATIVE_SIGNALS:
            score = NEGATIVE_SIGNALS[word]
            if multiplier == -1:
                pos_score += score * 0.5
                signals.append(f"negated negative: '{word}'")
            else:
                neg_score += score
                if score >= 2:
                    signals.append(f"negative: '{word}'")

        if word in URGENCY_SIGNALS:
            urgency_score += URGENCY_SIGNALS[word]
            if URGENCY_SIGNALS[word] >= 2:
                signals.append(f"urgency: '{word}'")

    # Check bigrams for compound signals
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if bigram in NEGATIVE_SIGNALS:
            neg_score += NEGATIVE_SIGNALS[bigram]
            signals.append(f"negative phrase: '{bigram}'")
        elif bigram in POSITIVE_SIGNALS:
            pos_score += POSITIVE_SIGNALS[bigram]

    # Determine sentiment
    total = pos_score + neg_score
    if total == 0:
        sentiment = "neutral"
        confidence = 0.6
    elif pos_score > neg_score * 1.5:
        sentiment = "positive"
        confidence = min(0.95, 0.5 + (pos_score - neg_score) / (total + 1))
    elif neg_score > pos_score * 1.5:
        sentiment = "negative"
        confidence = min(0.95, 0.5 + (neg_score - pos_score) / (total + 1))
    else:
        sentiment = "mixed"
        confidence = 0.55

    # Determine urgency level
    if urgency_score >= 4:
        urgency = "high"
    elif urgency_score >= 2:
        urgency = "medium"
    else:
        urgency = "low"

    return SentimentResult(
        sentiment=sentiment,
        urgency=urgency,
        confidence=round(confidence, 3),
        positive_score=round(pos_score, 2),
        negative_score=round(neg_score, 2),
        urgency_score=round(urgency_score, 2),
        signals=signals[:6]    # top 6 signals
    )