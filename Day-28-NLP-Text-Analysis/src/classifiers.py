# ============================================================
# src/classifiers.py
# Text classification models for issue type detection
# ============================================================

import json
from pathlib import Path

import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, accuracy_score, f1_score, confusion_matrix
)

from src.preprocessor import preprocess_for_model

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

CATEGORY_LABELS = {
    "bug": 0,
    "feature_request": 1,
    "performance": 2,
    "question": 3,
    "maintenance": 4
}
LABEL_CATEGORIES = {v: k for k, v in CATEGORY_LABELS.items()}


def build_pipeline(classifier_type: str = "logistic") -> Pipeline:
    """
    Build a text classification pipeline.

    Args:
        classifier_type: One of 'logistic', 'svm', 'random_forest', 'gradient_boosting'

    Returns:
        sklearn.pipeline.Pipeline
    """
    # TF-IDF with bigrams
    tfidf = TfidfVectorizer(
        preprocessor=preprocess_for_model,  # apply our custom preprocessing
        ngram_range=(1, 2),
        max_features=8000,
        min_df=2,
        max_df=0.90,
        sublinear_tf=True,
        strip_accents='unicode',
        analyzer='word'
    )

    classifiers = {
        "logistic": LogisticRegression(
            max_iter=1000,
            C=5.0,
            class_weight='balanced',
            random_state=42,
            solver='lbfgs',
            multi_class='multinomial'
        ),
        "svm": CalibratedClassifierCV(
            LinearSVC(
                max_iter=2000,
                class_weight='balanced',
                random_state=42,
                C=1.0
            )
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
    }

    clf = classifiers.get(classifier_type, classifiers["logistic"])
    return Pipeline([('tfidf', tfidf), ('clf', clf)])


def train_classifier(
    texts: list[str],
    labels: list[str],
    classifier_type: str = "logistic"
) -> tuple[Pipeline, dict]:
    """
    Train a text classifier and return model with evaluation results.

    Args:
        texts: List of text samples.
        labels: List of category labels.
        classifier_type: Algorithm to use.

    Returns:
        tuple: (trained_pipeline, evaluation_dict)
    """
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )

    # Build and train pipeline
    pipeline = build_pipeline(classifier_type)
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        pipeline, X_train, y_train,
        cv=cv,
        scoring='f1_weighted',
        n_jobs=-1
    )

    results = {
        "classifier": classifier_type,
        "test_accuracy": accuracy,
        "test_f1_weighted": f1,
        "cv_mean": cv_scores.mean(),
        "cv_std": cv_scores.std(),
        "test_samples": len(X_test),
        "train_samples": len(X_train),
        "classification_report": classification_report(
            y_test, y_pred,
            target_names=list(CATEGORY_LABELS.keys()),
            output_dict=True
        )
    }

    return pipeline, results


def compare_classifiers(
    texts: list[str],
    labels: list[str]
) -> tuple[Pipeline, str, dict]:
    """
    Train and compare multiple classifiers.

    Returns the best performing model.

    Returns:
        tuple: (best_pipeline, best_classifier_name, all_results)
    """
    classifier_types = ["logistic", "svm", "random_forest"]
    all_results = {}
    best_model = None
    best_score = 0
    best_name = ""

    print(f"\n  {'Classifier':<20} {'Accuracy':>10} {'F1 (weighted)':>14} {'CV Mean':>9}")
    print(f"  {'─' * 57}")

    for clf_type in classifier_types:
        pipeline, results = train_classifier(texts, labels, clf_type)
        all_results[clf_type] = results

        acc = results["test_accuracy"]
        f1 = results["test_f1_weighted"]
        cv = results["cv_mean"]

        print(f"  {clf_type:<20} {acc:>10.1%} {f1:>14.3f} {cv:>9.3f}")

        if cv > best_score:
            best_score = cv
            best_model = pipeline
            best_name = clf_type

    return best_model, best_name, all_results


def save_classifier(
    pipeline: Pipeline,
    classifier_name: str,
    results: dict,
    model_name: str = "issue_classifier"
) -> Path:
    """Save classifier and metadata."""
    model_path = MODELS_DIR / f"{model_name}.joblib"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"

    joblib.dump(pipeline, model_path)

    meta = {
        "model_name": model_name,
        "classifier_type": classifier_name,
        "categories": CATEGORY_LABELS,
        "test_accuracy": results.get("test_accuracy"),
        "test_f1": results.get("test_f1_weighted"),
        "cv_mean": results.get("cv_mean"),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return model_path


def load_classifier(model_name: str = "issue_classifier") -> tuple[Pipeline, dict]:
    """Load classifier and metadata."""
    model_path = MODELS_DIR / f"{model_name}.joblib"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"
    pipeline = joblib.load(model_path)
    with open(meta_path) as f:
        meta = json.load(f)
    return pipeline, meta


def predict_category(
    pipeline: Pipeline,
    text: str
) -> dict:
    """Predict category for a single text."""
    prediction = pipeline.predict([text])[0]
    probabilities = {}

    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba([text])[0]
        classes = pipeline.classes_
        probabilities = {
            str(cls): round(float(prob), 3)
            for cls, prob in zip(classes, probs)
        }

    return {
        "category": prediction,
        "confidence": probabilities.get(prediction, 0),
        "all_probabilities": probabilities
    }