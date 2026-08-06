# ============================================================
# src/analyzer.py
# Complete text analysis orchestrator
# ============================================================

from dataclasses import dataclass, field
from typing import Optional

from src.preprocessor import get_text_stats, preprocess_for_model
from src.sentiment import analyze_sentiment, SentimentResult
from src.entity_extractor import extract_entities, ExtractedEntities
from src.classifiers import predict_category, load_classifier


@dataclass
class AnalysisResult:
    """Complete analysis result for a text."""
    # Input
    original_text: str
    word_count: int
    char_count: int

    # Category
    category: str
    category_confidence: float
    category_probabilities: dict

    # Sentiment
    sentiment: str
    sentiment_confidence: float
    urgency_level: str
    positive_score: float
    negative_score: float
    sentiment_signals: list[str]

    # Entities
    error_codes: list[str]
    endpoints: list[str]
    references: list[str]
    versions: list[str]
    time_mentions: list[str]
    systems: list[str]
    technologies: list[str]
    suggested_tags: list[str]
    action_items: list[str]

    # Recommendations
    recommended_priority: str
    priority_reasoning: str


# Global model cache
_classifier = None
_classifier_meta = None


def _get_classifier():
    global _classifier, _classifier_meta
    if _classifier is None:
        _classifier, _classifier_meta = load_classifier()
    return _classifier, _classifier_meta


def compute_recommended_priority(
    category: str,
    sentiment: SentimentResult,
    entities: ExtractedEntities
) -> tuple[str, str]:
    """
    Compute recommended priority based on all analysis signals.

    Returns:
        tuple: (priority_level, reasoning)
    """
    score = 0
    reasons = []

    # Category-based base score
    category_scores = {
        "bug": 3,
        "performance": 2,
        "feature_request": 1,
        "question": 1,
        "maintenance": 1
    }
    score += category_scores.get(category, 1)
    reasons.append(f"{category.replace('_', ' ')} issue")

    # Urgency from sentiment
    urgency_scores = {"high": 3, "medium": 2, "low": 0}
    score += urgency_scores.get(sentiment.urgency, 0)
    if sentiment.urgency == "high":
        reasons.append("urgent language detected")

    # Negative sentiment amplifies severity
    if sentiment.sentiment == "negative" and sentiment.negative_score > 3:
        score += 2
        reasons.append("high user frustration")

    # Entity-based signals
    if entities.error_codes:
        score += 2
        reasons.append(f"error codes: {', '.join(entities.error_codes[:2])}")

    if "production" in entities.systems or "database" in entities.systems:
        score += 2
        reasons.append(f"affects critical system: {', '.join(entities.systems[:2])}")

    if entities.time_mentions:
        score += 1
        reasons.append(f"time constraint: {entities.time_mentions[0]}")

    if "urgent" in entities.suggested_tags:
        score += 2

    # Map score to priority
    if score >= 9:
        priority = "urgent"
    elif score >= 6:
        priority = "high"
    elif score >= 3:
        priority = "medium"
    else:
        priority = "low"

    reasoning = "; ".join(reasons[:3])
    return priority, reasoning


def analyze_text(text: str) -> AnalysisResult:
    """
    Perform complete NLP analysis on a text.

    Args:
        text: Input text to analyze.

    Returns:
        AnalysisResult: Comprehensive analysis.
    """
    # Text statistics
    stats = get_text_stats(text)

    # Load classifier and predict category
    try:
        classifier, _ = _get_classifier()
        category_result = predict_category(classifier, text)
    except FileNotFoundError:
        # Model not trained yet
        category_result = {
            "category": "unknown",
            "confidence": 0.0,
            "all_probabilities": {}
        }

    # Sentiment analysis
    sentiment = analyze_sentiment(text)

    # Entity extraction
    entities = extract_entities(text)

    # Priority recommendation
    priority, reasoning = compute_recommended_priority(
        category_result["category"],
        sentiment,
        entities
    )

    return AnalysisResult(
        original_text=text,
        word_count=stats["word_count"],
        char_count=stats["char_count"],
        category=category_result["category"],
        category_confidence=category_result.get("confidence", 0),
        category_probabilities=category_result.get("all_probabilities", {}),
        sentiment=sentiment.sentiment,
        sentiment_confidence=sentiment.confidence,
        urgency_level=sentiment.urgency,
        positive_score=sentiment.positive_score,
        negative_score=sentiment.negative_score,
        sentiment_signals=sentiment.signals,
        error_codes=entities.error_codes,
        endpoints=entities.endpoints,
        references=entities.references,
        versions=entities.versions,
        time_mentions=entities.time_mentions,
        systems=entities.systems,
        technologies=entities.technologies,
        suggested_tags=entities.suggested_tags,
        action_items=entities.action_items,
        recommended_priority=priority,
        priority_reasoning=reasoning
    )