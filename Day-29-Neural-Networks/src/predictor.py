# ============================================================
# src/predictor.py
# Production inference interface
# ============================================================

import numpy as np
import torch

# Priority metadata
PRIORITY_NAMES = ["low", "medium", "high", "urgent"]
PRIORITY_COLORS = {
    "low": "\033[94m",
    "medium": "\033[96m",
    "high": "\033[93m",
    "urgent": "\033[91m"
}
RESET = "\033[0m"

_model = None
_scaler = None
_meta = None


def _load():
    """Load model once, cache it."""
    global _model, _scaler, _meta
    if _model is None:
        from src.trainer import load_model
        _model, _scaler, _meta = load_model()
        _model.eval()
    return _model, _scaler, _meta


def predict(features: dict) -> dict:
    """
    Predict priority from a feature dictionary.

    Args:
        features: Dict with feature names as keys, numeric values.

    Returns:
        dict: Prediction with priority, confidence, and probabilities.
    """
    model, scaler, meta = _load()
    feature_names = meta["feature_names"]

    # Build feature vector
    feature_vector = np.array(
        [[features.get(name, 0.0) for name in feature_names]],
        dtype=np.float32
    )

    # Scale
    feature_vector_scaled = scaler.transform(feature_vector)

    # Predict
    X_tensor = torch.FloatTensor(feature_vector_scaled)
    with torch.no_grad():
        model.eval()
        logits = model(X_tensor)
        probs = torch.softmax(logits, dim=1)[0].numpy()

    predicted_idx = int(probs.argmax())
    predicted_priority = PRIORITY_NAMES[predicted_idx]
    confidence = float(probs[predicted_idx])

    probabilities = {
        name: round(float(probs[i]), 3)
        for i, name in enumerate(PRIORITY_NAMES)
    }

    return {
        "predicted_priority": predicted_priority,
        "confidence": round(confidence, 3),
        "probabilities": probabilities,
        "model": "Neural Network (PyTorch)"
    }


def predict_from_task_description(
    title: str,
    description: str = None,
    has_due_date: bool = False,
    is_overdue: bool = False,
    days_until_due: float = 0,
    tags: list = None,
    estimated_hours: float = None
) -> dict:
    """
    Predict priority from task description fields.

    Extracts features and runs prediction.
    """
    import re

    title_lower = title.lower()
    words = set(title_lower.split())
    tags = tags or []

    URGENCY_WORDS = {
        "urgent", "asap", "critical", "immediately", "emergency",
        "hotfix", "incident", "outage", "p0", "blocking", "down", "breach"
    }
    HIGH_WORDS = {"fix", "deploy", "release", "deadline", "review", "security"}
    LOW_WORDS = {"nice", "optional", "future", "research", "explore"}

    from datetime import datetime
    hour = datetime.utcnow().hour
    dow = datetime.utcnow().weekday()

    features = {
        "title_word_count": len(title.split()),
        "title_char_count": len(title),
        "title_upper_ratio": sum(1 for c in title if c.isupper()) / max(len(title), 1),
        "has_exclamation": int("!" in title),
        "has_colon": int(":" in title),
        "starts_with_verb": 0,
        "has_number": int(bool(re.search(r'\d', title))),
        "urgency_word_count": sum(1 for w in words if w in URGENCY_WORDS),
        "high_priority_word_count": sum(1 for w in words if w in HIGH_WORDS),
        "low_priority_word_count": sum(1 for w in words if w in LOW_WORDS),
        "mentions_production": int("production" in title_lower or "prod" in title_lower),
        "mentions_customer": int(any(w in title_lower for w in ("customer", "client", "user"))),
        "mentions_security": int(any(w in title_lower for w in ("security", "breach", "vulnerability"))),
        "has_description": int(bool(description)),
        "description_word_count": len(description.split()) if description else 0,
        "description_urgency_words": sum(
            1 for w in (description or "").lower().split() if w in URGENCY_WORDS
        ),
        "has_due_date": int(has_due_date),
        "is_overdue": int(is_overdue),
        "days_until_due": max(-7, min(30, days_until_due)),
        "hours_until_due": max(-168, min(168, days_until_due * 24)),
        "due_today": int(has_due_date and 0 <= days_until_due <= 1),
        "due_this_week": int(has_due_date and 0 <= days_until_due <= 7),
        "due_within_3_days": int(has_due_date and 0 <= days_until_due <= 3),
        "tag_count": len(tags),
        "has_estimate": int(estimated_hours is not None),
        "estimated_hours": float(estimated_hours or 0),
        "short_estimate": int(float(estimated_hours or 999) <= 2),
        "long_estimate": int(float(estimated_hours or 0) >= 8),
        "hour_of_day": hour,
        "day_of_week": dow,
        "is_business_hours": int(9 <= hour < 18 and dow < 5),
        "is_monday_morning": int(dow == 0 and hour < 12),
        "is_friday_afternoon": int(dow == 4 and hour >= 14),
        "is_weekend": int(dow >= 5),
        "created_late_night": int(hour >= 22 or hour < 6),
    }

    result = predict(features)
    result["task_title"] = title
    return result