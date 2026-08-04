# ============================================================
# src/predictor.py
# Production prediction interface
# ============================================================

from pathlib import Path
import numpy as np
from src.feature_engineering import (
    extract_features, PRIORITY_LABELS, PRIORITY_NAMES
)
from src.trainer import load_model

# Priority colors for terminal display
PRIORITY_COLORS = {
    "low": "\033[94m",      # blue
    "medium": "\033[96m",   # cyan
    "high": "\033[93m",     # yellow
    "urgent": "\033[91m",   # red
}
RESET = "\033[0m"

_model = None
_meta = None


def _get_model():
    """Load model once, cache it (singleton pattern)."""
    global _model, _meta
    if _model is None:
        _model, _meta = load_model()
    return _model, _meta


def predict_priority(task: dict) -> dict:
    """
    Predict the priority of a single task.

    Args:
        task: Dictionary with task information.

    Returns:
        dict: Prediction result with priority, confidence, and explanation.
    """
    model, meta = _get_model()
    feature_names = meta["feature_names"]

    # Extract features
    features = extract_features(task)

    # Build feature vector in correct order
    feature_vector = np.array(
        [[features.get(name, 0) for name in feature_names]]
    )

    # Predict
    numeric_pred = model.predict(feature_vector)[0]
    predicted_priority = PRIORITY_NAMES[int(numeric_pred)]

    # Get probabilities
    probabilities = {}
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(feature_vector)[0]
        classes = model.classes_
        for i, cls_idx in enumerate(classes):
            priority_name = PRIORITY_NAMES[int(cls_idx)]
            probabilities[priority_name] = round(float(probs[i]), 3)

    # Confidence
    confidence = probabilities.get(predicted_priority, 0)

    # Explanation — which features contributed most
    explanation = build_explanation(features, predicted_priority)

    return {
        "predicted_priority": predicted_priority,
        "confidence": confidence,
        "probabilities": probabilities,
        "explanation": explanation,
        "task_title": task.get("title", "Unknown"),
        "features_used": len(feature_names)
    }


def predict_batch(tasks: list[dict]) -> list[dict]:
    """Predict priority for multiple tasks at once."""
    return [predict_priority(task) for task in tasks]


def build_explanation(features: dict, predicted_priority: str) -> list[str]:
    """Build human-readable explanation for the prediction."""
    reasons = []

    if features.get("is_overdue"):
        reasons.append("⏰ Task is overdue")

    if features.get("urgency_word_count", 0) > 0:
        reasons.append(f"🔴 Contains {int(features['urgency_word_count'])} urgency word(s)")

    if features.get("due_today"):
        reasons.append("📅 Due today")

    if features.get("due_within_3_days") and not features.get("due_today"):
        reasons.append("📅 Due within 3 days")

    if features.get("mentions_production"):
        reasons.append("🖥️  Mentions production system")

    if features.get("mentions_security"):
        reasons.append("🔒 Security-related task")

    if features.get("mentions_customer"):
        reasons.append("👤 Customer-facing impact")

    if features.get("title_upper_ratio", 0) > 0.3:
        reasons.append("📣 Title uses UPPERCASE (indicating urgency)")

    if features.get("has_exclamation"):
        reasons.append("❗ Title contains exclamation mark")

    if not features.get("has_due_date"):
        reasons.append("📝 No due date set (likely lower priority)")

    if features.get("has_estimate"):
        est = features.get("estimated_hours", 0)
        if est <= 1:
            reasons.append(f"⚡ Quick task ({est}h estimate)")
        elif est >= 8:
            reasons.append(f"🔧 Large task ({est}h estimate)")

    if not reasons:
        reasons.append("📊 Based on overall task pattern analysis")

    return reasons[:4]    # return top 4 reasons