# ============================================================
# app/ensemble.py
# Ensemble logic: combine RF + NN + NLP signals
# ============================================================

from app.nlp_analyzer import NLPResult
from app.schemas import EnsembleResult

PRIORITY_NAMES = ["low", "medium", "high", "urgent"]
PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2, "urgent": 3}

# Map NLP category → base priority suggestion
CATEGORY_PRIORITY_MAP = {
    "bug": "high",
    "performance": "medium",
    "feature_request": "low",
    "question": "low",
    "maintenance": "low",
    "general": "medium",
}


def ensemble_predictions(
    rf_result: dict | None,
    nn_result: dict | None,
    nlp: NLPResult,
    rf_weight: float = 0.45,
    nn_weight: float = 0.45,
    nlp_weight: float = 0.10
) -> EnsembleResult:
    """
    Combine predictions from multiple models into a final result.

    Strategy:
    1. Soft voting from RF and NN (weighted probability average)
    2. NLP urgency/category signals as a modifier
    3. Agreement-based confidence calibration
    4. Generate human-readable explanation

    Args:
        rf_result: Random Forest prediction dict.
        nn_result: Neural Network prediction dict.
        nlp: NLP analysis result.
        rf_weight: Weight for RF in ensemble.
        nn_weight: Weight for NN in ensemble.
        nlp_weight: Weight for NLP category signal.

    Returns:
        EnsembleResult: Final ensemble prediction.
    """
    # ── Collect available predictions ────────────────────────
    model_probs = []
    model_weights = []
    model_predictions = []
    models_used = []

    if rf_result:
        model_probs.append(rf_result["probabilities"])
        model_weights.append(rf_weight)
        model_predictions.append(rf_result["predicted_priority"])
        models_used.append("Random Forest")

    if nn_result:
        model_probs.append(nn_result["probabilities"])
        model_weights.append(nn_weight)
        model_predictions.append(nn_result["predicted_priority"])
        models_used.append("Neural Network")

    # ── NLP-derived probability signal ───────────────────────
    category_priority = CATEGORY_PRIORITY_MAP.get(nlp.category, "medium")
    nlp_probs = _priority_to_soft_vector(category_priority, nlp.urgency_level)
    model_probs.append(nlp_probs)
    model_weights.append(nlp_weight)
    models_used.append("NLP Analyzer")

    # Normalize weights
    total_weight = sum(model_weights)
    normalized_weights = [w / total_weight for w in model_weights]

    # ── Soft voting (weighted average of probability distributions)
    combined_probs = {p: 0.0 for p in PRIORITY_NAMES}
    for probs, weight in zip(model_probs, normalized_weights):
        for priority in PRIORITY_NAMES:
            combined_probs[priority] += probs.get(priority, 0.0) * weight

    # ── NLP urgency modifier ──────────────────────────────────
    # Shift probabilities toward higher priority if urgency signals strong
    if nlp.urgency_level == "high" and nlp.negative_score >= 3:
        # Boost urgent + high, reduce low + medium
        urgency_shift = 0.08
        combined_probs["urgent"] += urgency_shift
        combined_probs["high"] += urgency_shift * 0.5
        combined_probs["medium"] -= urgency_shift * 0.5
        combined_probs["low"] -= urgency_shift

    if nlp.error_codes:
        # Error codes → more likely high or urgent
        combined_probs["high"] += 0.05
        combined_probs["low"] -= 0.05

    # Clamp to [0, 1]
    for p in PRIORITY_NAMES:
        combined_probs[p] = max(0.0, min(1.0, combined_probs[p]))

    # Renormalize to sum to 1
    total = sum(combined_probs.values())
    if total > 0:
        combined_probs = {p: v / total for p, v in combined_probs.items()}

    # ── Final prediction ──────────────────────────────────────
    final_priority = max(combined_probs, key=combined_probs.get)
    base_confidence = combined_probs[final_priority]

    # ── Agreement score ───────────────────────────────────────
    # How much do the individual models agree?
    agreement_score = _compute_agreement(model_predictions + [category_priority])

    # Calibrate confidence based on agreement
    calibrated_confidence = base_confidence * (0.75 + 0.25 * agreement_score)
    calibrated_confidence = min(0.97, max(0.4, calibrated_confidence))

    # ── Generate explanation ──────────────────────────────────
    explanation = _build_explanation(
        final_priority, nlp, rf_result, nn_result,
        agreement_score, combined_probs
    )

    return EnsembleResult(
        predicted_priority=final_priority,
        confidence=round(calibrated_confidence, 3),
        probabilities={k: round(v, 3) for k, v in combined_probs.items()},
        agreement_score=round(agreement_score, 3),
        explanation=explanation
    )


def _priority_to_soft_vector(
    priority: str,
    urgency: str = "low"
) -> dict[str, float]:
    """Convert a priority label to a soft probability vector."""
    base_vectors = {
        "urgent": {"low": 0.02, "medium": 0.05, "high": 0.20, "urgent": 0.73},
        "high":   {"low": 0.05, "medium": 0.15, "high": 0.70, "urgent": 0.10},
        "medium": {"low": 0.10, "medium": 0.65, "high": 0.20, "urgent": 0.05},
        "low":    {"low": 0.70, "medium": 0.20, "high": 0.08, "urgent": 0.02},
    }
    vector = base_vectors.get(priority, base_vectors["medium"]).copy()

    # Urgency modifier
    if urgency == "high":
        vector["urgent"] += 0.05
        vector["high"] += 0.03
        vector["low"] -= 0.05
        vector["medium"] -= 0.03

    # Renormalize
    total = sum(vector.values())
    return {k: v / total for k, v in vector.items()}


def _compute_agreement(predictions: list[str]) -> float:
    """
    Compute agreement score (0 to 1) across predictions.

    1.0 = all models agree
    0.0 = maximally disagree
    """
    if not predictions:
        return 0.5

    from collections import Counter
    counts = Counter(predictions)
    most_common_count = counts.most_common(1)[0][1]
    return most_common_count / len(predictions)


def _build_explanation(
    priority: str,
    nlp: NLPResult,
    rf_result: dict | None,
    nn_result: dict | None,
    agreement_score: float,
    combined_probs: dict
) -> list[str]:
    """Build human-readable explanation for the final prediction."""
    explanations = []

    # Model agreement
    if agreement_score >= 0.8:
        explanations.append(
            f"✅ Strong model agreement ({agreement_score:.0%}) — all models align"
        )
    elif agreement_score >= 0.5:
        explanations.append(
            f"⚖️  Partial model agreement ({agreement_score:.0%}) — models mostly align"
        )
    else:
        explanations.append(
            f"⚠️  Models disagree ({agreement_score:.0%}) — using ensemble average"
        )

    # NLP signals
    if nlp.urgency_level == "high":
        explanations.append(
            f"🔴 High urgency detected in text (urgency signals: "
            f"{', '.join(nlp.sentiment_signals[:2]) if nlp.sentiment_signals else 'CAPS/exclamation'})"
        )

    if nlp.error_codes:
        explanations.append(f"💥 Error codes found: {', '.join(nlp.error_codes[:3])}")

    if nlp.systems:
        explanations.append(f"🖥️  Critical systems mentioned: {', '.join(nlp.systems[:3])}")

    if nlp.category in ("bug",) and priority in ("high", "urgent"):
        explanations.append("🐛 Issue classified as bug — elevated priority")

    if nlp.sentiment == "negative":
        explanations.append(
            f"😤 Negative sentiment detected "
            f"(neg_score={nlp.negative_score:.1f})"
        )

    if nlp.time_mentions:
        explanations.append(
            f"⏰ Time pressure: {', '.join(nlp.time_mentions[:2])}"
        )

    # Individual model results
    if rf_result and nn_result:
        if rf_result["predicted_priority"] == nn_result["predicted_priority"]:
            explanations.append(
                f"🤝 RF and NN both predict "
                f"[{rf_result['predicted_priority'].upper()}]"
            )
        else:
            explanations.append(
                f"🔀 RF→[{rf_result['predicted_priority'].upper()}] "
                f"NN→[{nn_result['predicted_priority'].upper()}] "
                f"— ensemble resolves to [{priority.upper()}]"
            )

    return explanations[:5]