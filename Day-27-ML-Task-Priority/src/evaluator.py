# ============================================================
# src/evaluator.py
# Comprehensive model evaluation and reporting
# ============================================================

import json
from pathlib import Path
from datetime import datetime

import numpy as np
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score, precision_score, recall_score
)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = CYAN = YELLOW = RED = BLUE = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

PRIORITY_NAMES = ["low", "medium", "high", "urgent"]


def print_header(title: str):
    print(f"\n{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")


def print_section(title: str):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    set_name: str = "Test"
) -> dict:
    """Comprehensive model evaluation."""
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    accuracy = accuracy_score(y_test, predictions)
    f1_weighted = f1_score(y_test, predictions, average="weighted")
    f1_macro = f1_score(y_test, predictions, average="macro")
    precision = precision_score(y_test, predictions, average="weighted")
    recall = recall_score(y_test, predictions, average="weighted")
    cm = confusion_matrix(y_test, predictions)
    report = classification_report(
        y_test, predictions,
        target_names=PRIORITY_NAMES,
        output_dict=True
    )

    return {
        "set_name": set_name,
        "accuracy": accuracy,
        "f1_weighted": f1_weighted,
        "f1_macro": f1_macro,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "predictions": predictions.tolist(),
        "actual": y_test.tolist()
    }


def display_results(
    eval_results: dict,
    feature_importance: list[tuple[str, float]] | None = None
):
    """Display evaluation results in terminal."""
    print_section(f"{eval_results['set_name']} SET PERFORMANCE")

    acc = eval_results["accuracy"]
    f1 = eval_results["f1_weighted"]
    p = eval_results["precision"]
    r = eval_results["recall"]

    acc_color = Fore.GREEN if acc >= 0.85 else Fore.YELLOW if acc >= 0.75 else Fore.RED
    f1_color = Fore.GREEN if f1 >= 0.85 else Fore.YELLOW if f1 >= 0.75 else Fore.RED

    print(f"\n  {'Accuracy:':<22} {acc_color}{acc:.1%}{Style.RESET_ALL}")
    print(f"  {'F1 Score (weighted):':<22} {f1_color}{f1:.3f}{Style.RESET_ALL}")
    print(f"  {'Precision (weighted):':<22} {p:.3f}")
    print(f"  {'Recall (weighted):':<22} {r:.3f}")

    # Per-class breakdown
    print_section("PER-CLASS METRICS")
    report = eval_results["classification_report"]
    print(f"\n  {'Priority':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
    print(f"  {'─' * 50}")

    for priority in PRIORITY_NAMES:
        if priority in report:
            m = report[priority]
            p_val = m["precision"]
            r_val = m["recall"]
            f1_val = m["f1-score"]
            sup = m["support"]
            color = Fore.GREEN if f1_val >= 0.80 else Fore.YELLOW if f1_val >= 0.65 else Fore.RED
            print(
                f"  {priority:<12} "
                f"{p_val:>10.3f} "
                f"{r_val:>8.3f} "
                f"{color}{f1_val:>8.3f}{Style.RESET_ALL} "
                f"{int(sup):>8}"
            )

    # Confusion matrix
    print_section("CONFUSION MATRIX")
    cm = np.array(eval_results["confusion_matrix"])

    print(f"\n              Predicted")
    print(f"  {'':12} {'Low':>8} {'Medium':>8} {'High':>8} {'Urgent':>8}")
    print(f"  {'─' * 50}")

    for i, label in enumerate(PRIORITY_NAMES):
        row_parts = []
        for j, val in enumerate(cm[i]):
            if i == j:
                row_parts.append(f"{Fore.GREEN}{val:8d}{Style.RESET_ALL}")
            elif val > 0:
                row_parts.append(f"{Fore.RED}{val:8d}{Style.RESET_ALL}")
            else:
                row_parts.append(f"{val:8d}")
        print(f"  Actual {label:<6} {''.join(row_parts)}")

    # Feature importance
    if feature_importance:
        print_section("TOP FEATURE IMPORTANCE")
        max_imp = feature_importance[0][1] if feature_importance else 1
        print()
        for feat_name, importance in feature_importance[:12]:
            bar_len = int(importance / max_imp * 30)
            bar = "█" * bar_len
            print(
                f"  {feat_name:<35} "
                f"{importance:.4f}  "
                f"{Fore.CYAN}{bar}{Style.RESET_ALL}"
            )


def save_evaluation_report(
    eval_results: dict,
    model_comparison: dict | None = None,
    feature_importance: list | None = None
) -> Path:
    """Save complete evaluation report."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"evaluation_{timestamp}.json"

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "day": "Day 27 — Introduction to Machine Learning",
        "test_performance": eval_results,
        "model_comparison": {
            name: {
                "val_accuracy": r["val_accuracy"],
                "val_f1": r["val_f1"],
                "cv_mean": r["cv_mean"],
                "cv_std": r["cv_std"]
            }
            for name, r in (model_comparison or {}).items()
        },
        "top_features": [
            {"feature": n, "importance": float(i)}
            for n, i in (feature_importance or [])[:15]
        ]
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  ✅ Report saved to: {report_path.name}")
    return report_path