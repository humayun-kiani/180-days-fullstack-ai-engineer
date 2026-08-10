# ============================================================
# app/models_loader.py
# Load and cache ML models for inference
# Builds and trains models if not pre-saved
# ============================================================

import json
import os
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

MODELS_DIR = Path(__file__).parent.parent / "models_cache"
MODELS_DIR.mkdir(exist_ok=True)

PRIORITY_NAMES = ["low", "medium", "high", "urgent"]
PRIORITY_LABELS = {"low": 0, "medium": 1, "high": 2, "urgent": 3}


@dataclass
class LoadedModels:
    """Container for loaded ML models."""
    random_forest: Optional[object] = None
    rf_scaler: Optional[object] = None
    neural_network: Optional[object] = None
    nn_scaler: Optional[object] = None
    feature_names: list = None
    rf_available: bool = False
    nn_available: bool = False


def _build_and_train_models() -> LoadedModels:
    """
    Build and train models fresh if no saved models found.
    This ensures the demo always works even without pre-trained models.
    """
    import random
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib

    from app.feature_extractor import FEATURE_NAMES

    print("  🔧 No saved models found — training fresh models...")
    print("  (This runs once; models are cached for future calls)")

    # Generate quick training data
    random.seed(42)
    np.random.seed(42)

    tasks = []
    n_per_class = 200

    for priority in ["urgent", "high", "medium", "low"]:
        for _ in range(n_per_class):
            days = {
                "urgent": random.uniform(-3, 0.5),
                "high": random.uniform(-0.5, 3),
                "medium": random.uniform(3, 14),
                "low": random.uniform(10, 30)
            }[priority]

            urgency_count = {"urgent": 2, "high": 1, "medium": 0, "low": 0}[priority]
            urgency_count += random.randint(0, 1)

            features = {
                "title_word_count": random.randint(4, 12),
                "title_char_count": random.randint(20, 100),
                "title_upper_ratio": {"urgent": 0.6, "high": 0.2, "medium": 0.05, "low": 0.02}[priority] + random.uniform(-0.1, 0.1),
                "has_exclamation": int(priority in ("urgent", "high") and random.random() > 0.4),
                "has_colon": int(priority in ("urgent", "high") and random.random() > 0.5),
                "starts_with_verb": int(random.random() > 0.5),
                "has_number": int(random.random() > 0.5),
                "urgency_word_count": urgency_count,
                "high_priority_word_count": int(priority in ("high", "urgent")) * random.randint(0, 2),
                "low_priority_word_count": int(priority in ("low", "medium")) * random.randint(0, 2),
                "mentions_production": int(priority in ("urgent", "high") and random.random() > 0.4),
                "mentions_customer": int(priority in ("urgent", "high") and random.random() > 0.5),
                "mentions_security": int(priority in ("urgent", "high") and random.random() > 0.5),
                "has_description": int(random.random() > (0.1 if priority in ("urgent", "high") else 0.5)),
                "description_word_count": random.randint(10, 100) if priority in ("urgent", "high") else random.randint(0, 30),
                "description_urgency_words": urgency_count if priority == "urgent" else 0,
                "has_due_date": int(days is not None),
                "is_overdue": int(days < 0),
                "days_until_due": max(-7, min(30, days)),
                "hours_until_due": max(-168, min(168, days * 24)),
                "due_today": int(0 <= days <= 1),
                "due_this_week": int(0 <= days <= 7),
                "due_within_3_days": int(0 <= days <= 3),
                "tag_count": random.randint(1, 4),
                "has_estimate": int(random.random() > 0.2),
                "estimated_hours": {"urgent": 2.0, "high": 5.0, "medium": 4.0, "low": 2.0}[priority] + random.uniform(-1, 1),
                "short_estimate": int(priority in ("urgent",) and random.random() > 0.5),
                "long_estimate": int(priority in ("medium", "low") and random.random() > 0.7),
                "hour_of_day": random.randint(0, 23),
                "day_of_week": random.randint(0, 6),
                "is_business_hours": int(random.random() > 0.3),
                "is_monday_morning": int(random.random() > 0.85),
                "is_friday_afternoon": int(random.random() > 0.85),
                "is_weekend": int(random.random() > 0.7),
                "created_late_night": int(random.random() > 0.8),
            }
            features["priority"] = priority
            tasks.append(features)

    df = pd.DataFrame(tasks)
    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = np.array([PRIORITY_LABELS[p] for p in df["priority"]])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train Random Forest
    rf_scaler = StandardScaler()
    X_train_scaled = rf_scaler.fit_transform(X_train)

    rf = RandomForestClassifier(
        n_estimators=100, max_depth=8,
        class_weight='balanced', random_state=42
    )
    rf.fit(X_train, y_train)  # RF doesn't need scaling
    rf_acc = (rf.predict(X_test) == y_test).mean()
    print(f"  ✅ Random Forest trained: {rf_acc:.1%} accuracy")

    # Save RF
    joblib.dump(rf, MODELS_DIR / "rf_model.joblib")
    joblib.dump(rf_scaler, MODELS_DIR / "rf_scaler.joblib")

    # Train simple neural network (using sklearn MLP for simplicity in integration)
    from sklearn.neural_network import MLPClassifier

    nn_scaler = StandardScaler()
    X_train_nn = nn_scaler.fit_transform(X_train)
    X_test_nn = nn_scaler.transform(X_test)

    nn = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        max_iter=200,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15
    )
    nn.fit(X_train_nn, y_train)
    nn_acc = (nn.predict(X_test_nn) == y_test).mean()
    print(f"  ✅ Neural Network trained: {nn_acc:.1%} accuracy")

    # Save NN
    joblib.dump(nn, MODELS_DIR / "nn_model.joblib")
    joblib.dump(nn_scaler, MODELS_DIR / "nn_scaler.joblib")

    # Save metadata
    meta = {"feature_names": FEATURE_NAMES, "priority_names": PRIORITY_NAMES}
    with open(MODELS_DIR / "meta.json", "w") as f:
        json.dump(meta, f)

    return LoadedModels(
        random_forest=rf,
        rf_scaler=rf_scaler,
        neural_network=nn,
        nn_scaler=nn_scaler,
        feature_names=FEATURE_NAMES,
        rf_available=True,
        nn_available=True
    )


_models_cache: Optional[LoadedModels] = None


def get_models() -> LoadedModels:
    """Load models once, cache globally."""
    global _models_cache
    if _models_cache is not None:
        return _models_cache

    import joblib
    from app.feature_extractor import FEATURE_NAMES

    rf_path = MODELS_DIR / "rf_model.joblib"
    nn_path = MODELS_DIR / "nn_model.joblib"
    meta_path = MODELS_DIR / "meta.json"

    # Check if models exist
    if rf_path.exists() and nn_path.exists() and meta_path.exists():
        print("  📦 Loading cached models...")
        rf = joblib.load(rf_path)
        rf_scaler = joblib.load(MODELS_DIR / "rf_scaler.joblib")
        nn = joblib.load(nn_path)
        nn_scaler = joblib.load(MODELS_DIR / "nn_scaler.joblib")
        with open(meta_path) as f:
            meta = json.load(f)

        _models_cache = LoadedModels(
            random_forest=rf,
            rf_scaler=rf_scaler,
            neural_network=nn,
            nn_scaler=nn_scaler,
            feature_names=meta.get("feature_names", FEATURE_NAMES),
            rf_available=True,
            nn_available=True
        )
    else:
        # Train fresh
        _models_cache = _build_and_train_models()

    return _models_cache


def predict_with_rf(
    models: LoadedModels,
    feature_vector: list[float]
) -> dict:
    """Get Random Forest prediction."""
    if not models.rf_available:
        return None

    X = np.array([feature_vector], dtype=np.float32)
    probs = models.random_forest.predict_proba(X)[0]
    classes = models.random_forest.classes_

    prob_dict = {}
    for i, cls_idx in enumerate(classes):
        prob_dict[PRIORITY_NAMES[int(cls_idx)]] = round(float(probs[i]), 3)

    # Ensure all classes present
    for name in PRIORITY_NAMES:
        prob_dict.setdefault(name, 0.0)

    predicted_idx = int(probs.argmax())
    predicted_class = PRIORITY_NAMES[int(classes[predicted_idx])]
    confidence = round(float(probs.max()), 3)

    return {
        "model_name": "Random Forest",
        "predicted_priority": predicted_class,
        "confidence": confidence,
        "probabilities": prob_dict
    }


def predict_with_nn(
    models: LoadedModels,
    feature_vector: list[float]
) -> dict:
    """Get Neural Network prediction."""
    if not models.nn_available:
        return None

    X = np.array([feature_vector], dtype=np.float32)
    X_scaled = models.nn_scaler.transform(X)
    probs = models.neural_network.predict_proba(X_scaled)[0]
    classes = models.neural_network.classes_

    prob_dict = {}
    for i, cls_idx in enumerate(classes):
        prob_dict[PRIORITY_NAMES[int(cls_idx)]] = round(float(probs[i]), 3)

    for name in PRIORITY_NAMES:
        prob_dict.setdefault(name, 0.0)

    predicted_idx = int(probs.argmax())
    predicted_class = PRIORITY_NAMES[int(classes[predicted_idx])]
    confidence = round(float(probs.max()), 3)

    return {
        "model_name": "Neural Network",
        "predicted_priority": predicted_class,
        "confidence": confidence,
        "probabilities": prob_dict
    }