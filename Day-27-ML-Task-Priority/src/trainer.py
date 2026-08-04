# ============================================================
# src/trainer.py
# Train and compare multiple ML models
# ============================================================

import os
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier
)
from sklearn.metrics import (
    classification_report, accuracy_score,
    f1_score, confusion_matrix
)
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

from src.feature_engineering import (
    build_feature_matrix, encode_labels,
    PRIORITY_LABELS, PRIORITY_NAMES
)

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


# ─── Model Definitions ──────────────────────────────────────

MODELS = {
    "logistic_regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight="balanced",
            random_state=42
        ))
    ]),

    "decision_tree": DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42
    ),

    "random_forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1    # use all CPU cores
    ),

    "gradient_boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    ),

    "extra_trees": ExtraTreesClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),
}


def prepare_data(
    df: pd.DataFrame,
    test_size: float = 0.15,
    val_size: float = 0.15
) -> tuple:
    """
    Prepare features and labels, split into train/val/test.

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test, feature_names)
    """
    # Build features
    X_df, feature_names = build_feature_matrix(df)
    X = X_df.values

    # Encode labels
    y = encode_labels(df["priority"])

    # Split: first separate test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=42,
        stratify=y
    )

    # Split: separate train and validation from remaining
    val_fraction = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=val_fraction,
        random_state=42,
        stratify=y_temp
    )

    print(f"\n  Data split:")
    print(f"  Train:      {len(X_train):4d} examples ({len(X_train)/len(X)*100:.0f}%)")
    print(f"  Validation: {len(X_val):4d} examples ({len(X_val)/len(X)*100:.0f}%)")
    print(f"  Test:       {len(X_test):4d} examples ({len(X_test)/len(X)*100:.0f}%)")
    print(f"  Features:   {len(feature_names)}")

    return X_train, X_val, X_test, y_train, y_val, y_test, feature_names


def train_and_compare(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list[str]
) -> dict:
    """
    Train all models and compare on validation set.

    Returns:
        dict: Results for each model.
    """
    results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print(f"\n  {'Model':<25} {'Val Acc':>8} {'Val F1':>8} {'CV Mean':>9} {'CV Std':>7} {'Time':>7}")
    print(f"  {'─' * 68}")

    for name, model in MODELS.items():
        start_time = time.time()

        # Train
        model.fit(X_train, y_train)

        # Validate
        val_preds = model.predict(X_val)
        val_acc = accuracy_score(y_val, val_preds)
        val_f1 = f1_score(y_val, val_preds, average="weighted")

        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=cv,
            scoring="f1_weighted",
            n_jobs=-1
        )

        elapsed = time.time() - start_time

        print(
            f"  {name:<25} "
            f"{val_acc:>8.1%} "
            f"{val_f1:>8.3f} "
            f"{cv_scores.mean():>9.3f} "
            f"±{cv_scores.std():>5.3f} "
            f"{elapsed:>6.1f}s"
        )

        results[name] = {
            "model": model,
            "val_accuracy": val_acc,
            "val_f1": val_f1,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "val_predictions": val_preds,
            "train_time_seconds": elapsed
        }

    return results


def get_best_model(results: dict) -> tuple[str, object]:
    """Select best model by cross-validation F1 score."""
    best_name = max(
        results.keys(),
        key=lambda k: results[k]["cv_mean"]
    )
    return best_name, results[best_name]["model"]


def tune_best_model(
    best_model_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray
) -> object:
    """
    Run GridSearchCV on the best model to find optimal hyperparameters.
    """
    print(f"\n  Tuning {best_model_name}...")

    param_grids = {
        "random_forest": {
            "n_estimators": [100, 200, 300],
            "max_depth": [5, 8, 10, None],
            "min_samples_leaf": [1, 3, 5]
        },
        "extra_trees": {
            "n_estimators": [100, 200, 300],
            "max_depth": [8, 10, None],
        },
        "gradient_boosting": {
            "n_estimators": [100, 150, 200],
            "learning_rate": [0.05, 0.1, 0.15],
            "max_depth": [3, 5, 7]
        },
        "logistic_regression": {
            "clf__C": [0.1, 1.0, 10.0],
            "clf__max_iter": [500, 1000]
        },
        "decision_tree": {
            "max_depth": [5, 8, 10, 15],
            "min_samples_leaf": [3, 5, 10]
        }
    }

    param_grid = param_grids.get(best_model_name, {})
    if not param_grid:
        print(f"  No param grid defined for {best_model_name}, skipping tuning")
        return MODELS[best_model_name]

    base_model = MODELS[best_model_name]
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=cv,
        scoring="f1_weighted",
        n_jobs=-1,
        verbose=0
    )

    grid_search.fit(X_train, y_train)

    print(f"  Best params: {grid_search.best_params_}")
    print(f"  Best CV F1:  {grid_search.best_score_:.3f}")

    return grid_search.best_estimator_


def get_feature_importance(
    model,
    feature_names: list[str],
    top_n: int = 15
) -> list[tuple[str, float]]:
    """
    Extract feature importance from tree-based models.
    """
    # Handle pipelines
    actual_model = model
    if hasattr(model, "named_steps"):
        for step_name, step in model.named_steps.items():
            if hasattr(step, "feature_importances_"):
                actual_model = step
                break

    if hasattr(actual_model, "feature_importances_"):
        importances = actual_model.feature_importances_
        pairs = list(zip(feature_names, importances))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_n]

    return []


def save_model(
    model,
    feature_names: list[str],
    model_name: str = "task_priority_model"
) -> Path:
    """Save model and metadata."""
    model_path = MODELS_DIR / f"{model_name}.joblib"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"

    joblib.dump(model, model_path)

    meta = {
        "model_name": model_name,
        "feature_names": feature_names,
        "priority_labels": PRIORITY_LABELS,
        "priority_names": PRIORITY_NAMES,
        "saved_at": __import__("datetime").datetime.utcnow().isoformat()
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  ✅ Model saved to: {model_path}")
    return model_path


def load_model(model_name: str = "task_priority_model") -> tuple:
    """Load model and metadata."""
    model_path = MODELS_DIR / f"{model_name}.joblib"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"

    model = joblib.load(model_path)
    with open(meta_path) as f:
        meta = json.load(f)

    return model, meta