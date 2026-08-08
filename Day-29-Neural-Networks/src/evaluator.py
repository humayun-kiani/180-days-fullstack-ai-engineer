# ============================================================
# src/evaluator.py
# Model evaluation, metrics, and reporting
# ============================================================

import json
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score
)

from src.trainer import TrainingHistory

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        GREEN = YELLOW = RED = CYAN = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

PRIORITY_NAMES = ["low", "medium", "high", "urgent"]


def get_all_predictions(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Get all predictions and probabilities from a loader."""
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device)
            logits = model(X_batch)
            probs = torch.softmax(logits, dim=1)
            preds = logits.argmax(dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(y_batch.numpy())
            all_probs.extend(probs.cpu().numpy())

    return (
        np.array(all_preds),
        np.array(all_labels),
        np.array(all_probs)
    )


def evaluate_model(
    model: nn.Module,
    test_loader: DataLoader,
    device: torch.device,
    model_name: str = "Neural Network"
) -> dict:
    """Complete model evaluation on test set."""
    preds, labels, probs = get_all_predictions(model, test_loader, device)

    accuracy = accuracy_score(labels, preds)
    f1_weighted = f1_score(labels, preds, average='weighted')
    f1_macro = f1_score(labels, preds, average='macro')
    cm = confusion_matrix(labels, preds)
    report = classification_report(
        labels, preds,
        target_names=PRIORITY_NAMES,
        output_dict=True
    )

    return {
        "model_name": model_name,
        "accuracy": accuracy,
        "f1_weighted": f1_weighted,
        "f1_macro": f1_macro,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "num_samples": len(labels)
    }


def display_evaluation(
    results: dict,
    history: TrainingHistory = None
):
    """Display evaluation results in terminal."""
    print(f"\n{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  TEST SET EVALUATION — {results['model_name']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")

    acc = results["accuracy"]
    f1 = results["f1_weighted"]
    acc_color = Fore.GREEN if acc >= 0.85 else Fore.YELLOW if acc >= 0.75 else Fore.RED
    f1_color = Fore.GREEN if f1 >= 0.85 else Fore.YELLOW if f1 >= 0.75 else Fore.RED

    print(f"\n  {'Accuracy:':<25} {acc_color}{acc:.1%}{Style.RESET_ALL}")
    print(f"  {'F1 Score (weighted):':<25} {f1_color}{f1:.3f}{Style.RESET_ALL}")
    print(f"  {'F1 Score (macro):':<25} {results['f1_macro']:.3f}")
    print(f"  {'Test samples:':<25} {results['num_samples']}")

    if history:
        print(f"  {'Best val accuracy:':<25} {history.best_val_accuracy:.1%} (epoch {history.best_epoch})")
        print(f"  {'Total epochs trained:':<25} {history.total_epochs}")
        print(f"  {'Training time:':<25} {history.training_time_seconds:.1f}s")

        # Overfitting check
        final_train_acc = history.train_accuracies[-1]
        final_val_acc = history.val_accuracies[-1]
        gap = final_train_acc - final_val_acc
        if gap > 0.1:
            print(f"\n  {Fore.YELLOW}⚠️  Overfitting detected: train={final_train_acc:.1%}, val={final_val_acc:.1%} (gap={gap:.1%}){Style.RESET_ALL}")
        else:
            print(f"\n  {Fore.GREEN}✅ Good generalization: train={final_train_acc:.1%}, val={final_val_acc:.1%}{Style.RESET_ALL}")

    # Per-class metrics
    print(f"\n  {Fore.YELLOW}Per-Class Metrics:{Style.RESET_ALL}")
    print(f"  {'Priority':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
    print(f"  {'─' * 50}")

    report = results["classification_report"]
    for name in PRIORITY_NAMES:
        if name in report:
            m = report[name]
            f1_val = m["f1-score"]
            c = Fore.GREEN if f1_val >= 0.80 else Fore.YELLOW if f1_val >= 0.65 else Fore.RED
            print(
                f"  {name:<12} "
                f"{m['precision']:>10.3f} "
                f"{m['recall']:>8.3f} "
                f"{c}{f1_val:>8.3f}{Style.RESET_ALL} "
                f"{int(m['support']):>8}"
            )

    # Confusion matrix
    print(f"\n  {Fore.YELLOW}Confusion Matrix:{Style.RESET_ALL}")
    cm = np.array(results["confusion_matrix"])
    print(f"              {'Predicted':^35}")
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
        print(f"  {'Act ' + label:<12}{''.join(row_parts)}")


def display_training_curve(history: TrainingHistory):
    """ASCII training curve."""
    print(f"\n  {Fore.YELLOW}Training Curve (Loss):{Style.RESET_ALL}")

    epochs = list(range(1, len(history.val_losses) + 1))
    max_loss = max(max(history.train_losses), max(history.val_losses))
    height = 10

    rows = []
    for row in range(height, 0, -1):
        threshold = max_loss * row / height
        line = ""
        for i in range(len(epochs)):
            train_above = history.train_losses[i] >= threshold
            val_above = history.val_losses[i] >= threshold

            if train_above and val_above:
                line += "█"
            elif train_above:
                line += "▒"    # train only
            elif val_above:
                line += "░"    # val only
            else:
                line += " "

        # Only show every 2nd row to avoid clutter
        if row % 2 == 0:
            label = f"{max_loss * row / height:.3f}"
        else:
            label = "     "
        rows.append(f"  {label:>7} │{line}")

    for row in rows:
        print(row)
    print(f"  {'':>7} └{'─' * len(epochs)}")
    print(f"  {'':>8}1{'':>{len(epochs)//2-1}}{len(epochs)//2}{'':>{len(epochs)//2-1}}{len(epochs)}")
    print(f"  {'Legend:':>10} █=both  ▒=train  ░=val")


def save_report(results: dict, history: TrainingHistory) -> Path:
    """Save evaluation report to file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"nn_evaluation_{timestamp}.json"

    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "day": "Day 29 — Neural Networks with PyTorch",
        "test_results": {
            k: v for k, v in results.items()
            if k != "classification_report"
        },
        "training_history": {
            "best_epoch": history.best_epoch,
            "best_val_accuracy": history.best_val_accuracy,
            "best_val_loss": history.best_val_loss,
            "total_epochs": history.total_epochs,
            "training_time_s": history.training_time_seconds,
            "final_train_acc": history.train_accuracies[-1],
            "final_val_acc": history.val_accuracies[-1],
        }
    }

    with open(path, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n  ✅ Report saved: {path.name}")
    return path