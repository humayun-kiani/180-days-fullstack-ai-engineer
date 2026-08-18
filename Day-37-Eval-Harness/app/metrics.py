# ============================================================
# app/metrics.py
# Evaluation metrics computation
# ============================================================

import numpy as np
from collections import Counter, defaultdict
from dataclasses import dataclass, field


PRIORITIES = ["low", "medium", "high", "urgent"]
PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITIES)}


@dataclass
class PerClassMetrics:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvalMetrics:
    """Complete evaluation metrics."""
    accuracy: float
    f1_weighted: float
    f1_macro: float
    per_class: dict[str, PerClassMetrics]
    confusion_matrix: list[list[int]]
    avg_latency_ms: float
    total_cases: int
    error_count: int

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "f1_weighted": round(self.f1_weighted, 4),
            "f1_macro": round(self.f1_macro, 4),
            "per_class": {
                k: {
                    "precision": round(v.precision, 4),
                    "recall": round(v.recall, 4),
                    "f1": round(v.f1, 4),
                    "support": v.support
                }
                for k, v in self.per_class.items()
            },
            "confusion_matrix": self.confusion_matrix,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_cases": self.total_cases,
            "error_count": self.error_count
        }


def compute_metrics(
    predictions: list[str],
    labels: list[str],
    latencies: list[float],
    errors: list[str | None]
) -> EvalMetrics:
    """
    Compute full suite of evaluation metrics.

    Args:
        predictions: Model predictions
        labels: Ground truth labels
        latencies: Per-prediction latency in ms
        errors: Per-prediction errors (None if no error)

    Returns:
        EvalMetrics: Complete metrics object
    """
    n = len(labels)
    error_count = sum(1 for e in errors if e is not None)

    # Accuracy
    correct = sum(1 for p, l in zip(predictions, labels) if p == l)
    accuracy = correct / n if n > 0 else 0

    # Per-class metrics
    per_class = {}
    for cls in PRIORITIES:
        tp = sum(1 for p, l in zip(predictions, labels) if p == cls and l == cls)
        fp = sum(1 for p, l in zip(predictions, labels) if p == cls and l != cls)
        fn = sum(1 for p, l in zip(predictions, labels) if p != cls and l == cls)
        support = sum(1 for l in labels if l == cls)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[cls] = PerClassMetrics(
            precision=precision, recall=recall, f1=f1, support=support
        )

    # Weighted F1
    total = sum(m.support for m in per_class.values())
    if total > 0:
        f1_weighted = sum(
            m.f1 * m.support / total
            for m in per_class.values()
        )
        f1_macro = sum(m.f1 for m in per_class.values()) / len(per_class)
    else:
        f1_weighted = f1_macro = 0.0

    # Confusion matrix (rows = actual, cols = predicted)
    label_to_idx = {l: i for i, l in enumerate(PRIORITIES)}
    cm = [[0] * len(PRIORITIES) for _ in range(len(PRIORITIES))]
    for pred, label in zip(predictions, labels):
        if pred in label_to_idx and label in label_to_idx:
            cm[label_to_idx[label]][label_to_idx[pred]] += 1

    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    return EvalMetrics(
        accuracy=accuracy,
        f1_weighted=f1_weighted,
        f1_macro=f1_macro,
        per_class=per_class,
        confusion_matrix=cm,
        avg_latency_ms=avg_latency,
        total_cases=n,
        error_count=error_count
    )


def format_confusion_matrix(cm: list[list[int]]) -> str:
    """Format confusion matrix as ASCII table."""
    labels = PRIORITIES
    header = f"{'':12} " + " ".join(f"{l:>8}" for l in labels)
    rows = [header, "─" * (12 + 9 * len(labels))]
    for i, row in enumerate(cm):
        row_str = f"Act {labels[i]:<8} " + " ".join(
            f"\033[92m{v:>8}\033[0m" if j == i else f"{v:>8}"
            for j, v in enumerate(row)
        )
        rows.append(row_str)
    return "\n".join(rows)