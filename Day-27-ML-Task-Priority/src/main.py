# ============================================================
# src/main.py
# Main entry point — train, evaluate, and demo the ML model
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generator import generate_dataset
from src.feature_engineering import build_feature_matrix, encode_labels
from src.trainer import (
    prepare_data, train_and_compare, get_best_model,
    tune_best_model, get_feature_importance, save_model
)
from src.evaluator import (
    evaluate_model, display_results,
    save_evaluation_report, print_header, print_section
)
from src.predictor import predict_priority

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = ""
    class Style:
        RESET_ALL = ""


def run_pipeline():
    """Complete ML training pipeline."""

    print_header("TASK PRIORITY PREDICTOR — ML TRAINING PIPELINE")
    print(f"\n  Day 27 — Introduction to Machine Learning")
    print(f"  Model: Random Forest + 5 competing algorithms")
    print(f"  Task: Predict task priority (low/medium/high/urgent)")

    # ── Step 1: Generate Data ─────────────────────────────────
    print_section("STEP 1: GENERATING TRAINING DATA")
    print("\n  Generating 2,000 synthetic task examples...")

    df = generate_dataset(n_samples=2000)
    print(f"\n  Generated {len(df)} tasks")
    print(f"\n  Priority distribution:")
    for priority, count in df["priority"].value_counts().sort_index().items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"    {priority:<10} {count:4d} ({pct:.1f}%) {Fore.CYAN}{bar}{Style.RESET_ALL}")

    # ── Step 2: Feature Engineering ───────────────────────────
    print_section("STEP 2: FEATURE ENGINEERING")
    X_train, X_val, X_test, y_train, y_val, y_test, feature_names = prepare_data(df)
    print(f"\n  Sample features extracted from one task:")
    from src.feature_engineering import extract_features
    sample = df.iloc[0].to_dict()
    features = extract_features(sample)
    for feat, val in list(features.items())[:10]:
        print(f"    {feat:<35} {val}")
    print(f"    ... and {len(features) - 10} more features")

    # ── Step 3: Train and Compare ─────────────────────────────
    print_section("STEP 3: TRAINING AND COMPARING 5 MODELS")
    comparison_results = train_and_compare(
        X_train, y_train, X_val, y_val, feature_names
    )

    # ── Step 4: Select Best Model ─────────────────────────────
    print_section("STEP 4: SELECTING BEST MODEL")
    best_name, best_model = get_best_model(comparison_results)
    best_cv = comparison_results[best_name]["cv_mean"]
    print(f"\n  {Fore.GREEN}Best model: {best_name}{Style.RESET_ALL}")
    print(f"  CV F1 score: {best_cv:.3f}")

    # ── Step 5: Hyperparameter Tuning ─────────────────────────
    print_section("STEP 5: HYPERPARAMETER TUNING")
    tuned_model = tune_best_model(best_name, X_train, y_train)

    # ── Step 6: Final Evaluation on Test Set ──────────────────
    print_section("STEP 6: FINAL EVALUATION ON HELD-OUT TEST SET")
    print("\n  ⚠️  This is the ONLY time we touch the test set!")

    test_results = evaluate_model(tuned_model, X_test, y_test, "Test")

    feature_importance = get_feature_importance(tuned_model, feature_names)
    display_results(test_results, feature_importance)

    # ── Step 7: Save Model ────────────────────────────────────
    print_section("STEP 7: SAVING MODEL")
    save_model(tuned_model, feature_names)

    # ── Step 8: Save Report ───────────────────────────────────
    save_evaluation_report(test_results, comparison_results, feature_importance)

    # ── Step 9: Demo Predictions ──────────────────────────────
    print_section("STEP 9: DEMO PREDICTIONS")
    demo_tasks = [
        {
            "title": "URGENT: Production database is down, all users affected",
            "due_date": "2025-05-26T14:00:00",
            "tags": ["production", "incident"],
            "estimated_hours": 2.0
        },
        {
            "title": "Fix login bug before tomorrow's demo",
            "due_date": "2025-05-27T09:00:00",
            "description": "Login fails for users with special characters in username",
            "tags": ["bug", "auth"],
            "estimated_hours": 3.0
        },
        {
            "title": "Write unit tests for the payment module",
            "due_date": "2025-06-05T17:00:00",
            "tags": ["testing", "payments"],
            "estimated_hours": 6.0
        },
        {
            "title": "Research GraphQL for potential future migration",
            "tags": ["research"],
            "estimated_hours": 4.0
        },
        {
            "title": "Update README with new API documentation",
            "tags": ["docs"],
            "estimated_hours": 1.0
        }
    ]

    print()
    for task in demo_tasks:
        result = predict_priority(task)
        priority = result["predicted_priority"]
        confidence = result["confidence"]
        colors = {"urgent": "\033[91m", "high": "\033[93m",
                  "medium": "\033[96m", "low": "\033[94m"}
        color = colors.get(priority, "")
        reset = "\033[0m"

        print(f"  Task: {task['title'][:60]}")
        print(f"  → {color}[{priority.upper()}]{reset} ({confidence:.0%} confidence)")
        print(f"  → {result['explanation'][0]}")
        print()

    # ── Summary ───────────────────────────────────────────────
    print_header("TRAINING COMPLETE")
    acc = test_results["accuracy"]
    f1 = test_results["f1_weighted"]
    acc_color = Fore.GREEN if acc >= 0.85 else Fore.YELLOW if acc >= 0.75 else Fore.RED
    print(f"\n  Final Test Accuracy:  {acc_color}{acc:.1%}{Style.RESET_ALL}")
    print(f"  Final Test F1 Score:  {f1:.3f}")
    print(f"\n  Model saved to: models/task_priority_model.joblib")
    print(f"\n  Start the prediction API:")
    print(f"  {Fore.CYAN}uvicorn src.api:app --reload{Style.RESET_ALL}")
    print(f"  Then: http://localhost:8000/docs\n")


if __name__ == "__main__":
    run_pipeline()