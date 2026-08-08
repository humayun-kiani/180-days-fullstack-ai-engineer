# ============================================================
# src/main.py
# Complete deep learning training pipeline
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import numpy as np

from src.dataset import generate_dataset, prepare_dataloaders, PRIORITY_NAMES
from src.model import TaskPriorityNet, TaskPriorityResNet
from src.trainer import train_model, save_model
from src.evaluator import (
    evaluate_model, display_evaluation,
    display_training_curve, save_report
)
from src.predictor import predict_from_task_description

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = YELLOW = RED = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


def header(title: str):
    print(f"\n{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")


def section(title: str):
    print(f"\n{Fore.YELLOW}  ── {title} ──{Style.RESET_ALL}")


def main():
    torch.manual_seed(42)
    np.random.seed(42)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    header("TASK PRIORITY PREDICTOR — NEURAL NETWORK WITH PYTORCH")
    print(f"\n  Day 29 — Neural Networks & Deep Learning")
    print(f"  Device: {device}")
    print(f"  PyTorch version: {torch.__version__}")

    # ── Step 1: Generate Data ─────────────────────────────────
    section("STEP 1: GENERATING TRAINING DATA")
    print("\n  Generating 2,000 synthetic tasks...")
    df = generate_dataset(n_samples=2000)
    print(f"  Total: {len(df)} tasks")
    for priority, count in df["priority"].value_counts().sort_index().items():
        bar = Fore.CYAN + "█" * int(count / len(df) * 50) + Style.RESET_ALL
        print(f"    {priority:<10} {count:4d} ({count/len(df)*100:.0f}%)  {bar}")

    # ── Step 2: Prepare DataLoaders ───────────────────────────
    section("STEP 2: PREPARING DATALOADERS")
    train_loader, val_loader, test_loader, scaler, feature_names = prepare_dataloaders(
        df, batch_size=64
    )

    # ── Step 3: Build Model ───────────────────────────────────
    section("STEP 3: BUILDING NEURAL NETWORK")
    model = TaskPriorityNet(
        input_size=len(feature_names),
        hidden_sizes=[128, 64, 32],
        num_classes=4,
        dropout_rate=0.3
    )
    print(f"\n{model.architecture_summary()}")

    # ── Step 4: Train Model ───────────────────────────────────
    section("STEP 4: TRAINING NEURAL NETWORK")
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=100,
        learning_rate=0.001,
        weight_decay=1e-4,
        early_stopping_patience=15,
        device=device,
        verbose=True
    )

    # ── Step 5: Visualize Training ────────────────────────────
    section("STEP 5: TRAINING CURVE")
    display_training_curve(history)

    # ── Step 6: Evaluate on Test Set ──────────────────────────
    section("STEP 6: FINAL EVALUATION ON TEST SET")
    print(f"\n  ⚠️  First and only time touching the test set!")
    results = evaluate_model(
        model, test_loader, device,
        model_name="TaskPriorityNet (3 hidden layers)"
    )
    display_evaluation(results, history)

    # ── Step 7: Compare with Random Forest ───────────────────
    section("STEP 7: COMPARISON — NEURAL NETWORK vs RANDOM FOREST")
    print()

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score
    import pandas as pd

    # Reconstruct test set for sklearn
    test_X_list, test_y_list = [], []
    for X_batch, y_batch in test_loader:
        test_X_list.append(X_batch.numpy())
        test_y_list.append(y_batch.numpy())
    X_test_np = np.vstack(test_X_list)
    y_test_np = np.concatenate(test_y_list)

    # Unscale for sklearn
    X_test_original = scaler.inverse_transform(X_test_np)

    # Build and train RF on same training data
    train_X_list, train_y_list = [], []
    for X_batch, y_batch in train_loader:
        train_X_list.append(X_batch.numpy())
        train_y_list.append(y_batch.numpy())
    X_train_np = np.vstack(train_X_list)
    y_train_np = np.concatenate(train_y_list)
    X_train_original = scaler.inverse_transform(X_train_np)

    rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X_train_original, y_train_np)
    rf_preds = rf.predict(X_test_original)
    rf_acc = accuracy_score(y_test_np, rf_preds)
    rf_f1 = f1_score(y_test_np, rf_preds, average='weighted')

    nn_acc = results["accuracy"]
    nn_f1 = results["f1_weighted"]

    print(f"  {'Model':<30} {'Accuracy':>10} {'F1 (weighted)':>15}")
    print(f"  {'─' * 57}")

    winner_acc = Fore.GREEN if nn_acc >= rf_acc else Fore.RED
    winner_f1 = Fore.GREEN if nn_f1 >= rf_f1 else Fore.RED

    print(f"  {'Neural Network (PyTorch)':<30} "
          f"{winner_acc}{nn_acc:>10.1%}{Style.RESET_ALL} "
          f"{winner_f1}{nn_f1:>15.3f}{Style.RESET_ALL}")

    rf_acc_color = Fore.GREEN if rf_acc >= nn_acc else Fore.RED
    rf_f1_color = Fore.GREEN if rf_f1 >= nn_f1 else Fore.RED
    print(f"  {'Random Forest (sklearn)':<30} "
          f"{rf_acc_color}{rf_acc:>10.1%}{Style.RESET_ALL} "
          f"{rf_f1_color}{rf_f1:>15.3f}{Style.RESET_ALL}")

    print(f"\n  {Fore.WHITE}Insight:{Style.RESET_ALL} On tabular data with ~35 features, "
          f"Random Forest often matches or beats neural networks.")
    print(f"  Neural networks truly shine on:")
    print(f"  • Images (CNNs) — millions of pixels as features")
    print(f"  • Text (Transformers) — sequence of tokens")
    print(f"  • Audio (RNNs/CNNs) — temporal patterns")
    print(f"  • Large datasets (100k+ samples)")

    # ── Step 8: Save Model ────────────────────────────────────
    section("STEP 8: SAVING MODEL")
    save_model(model, history, scaler, feature_names)
    save_report(results, history)

    # ── Step 9: Demo Predictions ──────────────────────────────
    section("STEP 9: LIVE PREDICTIONS")

    demo_tasks = [
        {
            "title": "URGENT: Production database is down, all users affected",
            "has_due_date": True, "is_overdue": True, "days_until_due": -0.5,
            "tags": ["production", "incident"], "estimated_hours": 2.0
        },
        {
            "title": "Fix login bug before tomorrow's client demo",
            "has_due_date": True, "is_overdue": False, "days_until_due": 1.0,
            "tags": ["bug", "auth"], "estimated_hours": 3.0
        },
        {
            "title": "Write unit tests for the payment module",
            "has_due_date": True, "is_overdue": False, "days_until_due": 10.0,
            "tags": ["testing"], "estimated_hours": 6.0
        },
        {
            "title": "Research GraphQL for potential future API redesign",
            "has_due_date": False, "is_overdue": False, "days_until_due": 0,
            "tags": ["research"], "estimated_hours": 4.0
        },
        {
            "title": "Update README with API documentation",
            "has_due_date": False, "is_overdue": False, "days_until_due": 0,
            "tags": ["docs"], "estimated_hours": 1.0
        },
    ]

    expected = ["urgent", "high", "medium", "low", "low"]
    correct = 0
    print()

    for i, (task, expected_priority) in enumerate(zip(demo_tasks, expected), 1):
        result = predict_from_task_description(**task)
        predicted = result["predicted_priority"]
        conf = result["confidence"]
        is_correct = predicted == expected_priority

        colors = {
            "urgent": Fore.RED, "high": Fore.YELLOW,
            "medium": Fore.CYAN, "low": Fore.GREEN
        }
        color = colors.get(predicted, "")
        status = f"{Fore.GREEN}✅{Style.RESET_ALL}" if is_correct else f"{Fore.RED}❌{Style.RESET_ALL}"
        correct += int(is_correct)

        print(f"  {status} {task['title'][:55]:<55}")
        print(f"     → {color}[{predicted.upper()}]{Style.RESET_ALL} "
              f"({conf:.0%} confidence) | expected: {expected_priority}")
        print()

    # ── Final Summary ─────────────────────────────────────────
    header("COMPLETE")
    print(f"\n  {'Test Accuracy:':<30} {nn_acc:.1%}")
    print(f"  {'Test F1 Score:':<30} {nn_f1:.3f}")
    print(f"  {'Best Val Accuracy:':<30} {history.best_val_accuracy:.1%} (epoch {history.best_epoch})")
    print(f"  {'Total Parameters:':<30} {model.count_parameters():,}")
    print(f"  {'Training Time:':<30} {history.training_time_seconds:.1f}s")
    print(f"  {'Demo Correct:':<30} {correct}/{len(demo_tasks)}")
    print(f"\n  Start the API:")
    print(f"  {Fore.CYAN}uvicorn src.api:app --reload{Style.RESET_ALL}")
    print(f"  Then: http://localhost:8000/docs\n")


if __name__ == "__main__":
    main()