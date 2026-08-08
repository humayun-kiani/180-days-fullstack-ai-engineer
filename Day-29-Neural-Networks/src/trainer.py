# ============================================================
# src/trainer.py
# Training loop, early stopping, model checkpointing
# ============================================================

import json
import time
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


@dataclass
class TrainingHistory:
    """Records training metrics over epochs."""
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    train_accuracies: list[float] = field(default_factory=list)
    val_accuracies: list[float] = field(default_factory=list)
    learning_rates: list[float] = field(default_factory=list)
    best_epoch: int = 0
    best_val_loss: float = float('inf')
    best_val_accuracy: float = 0.0
    total_epochs: int = 0
    training_time_seconds: float = 0.0


class EarlyStopping:
    """
    Stop training when validation loss stops improving.

    Prevents overfitting by monitoring validation performance
    and stopping before the model memorizes training data.
    """

    def __init__(
        self,
        patience: int = 15,
        min_delta: float = 1e-4,
        restore_best: bool = True
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best = restore_best
        self.best_loss = float('inf')
        self.counter = 0
        self.best_state = None

    def __call__(
        self,
        val_loss: float,
        model: nn.Module
    ) -> bool:
        """
        Check if training should stop.

        Args:
            val_loss: Current validation loss.
            model: Current model (for saving best state).

        Returns:
            bool: True if training should stop.
        """
        if val_loss < self.best_loss - self.min_delta:
            # Improvement found
            self.best_loss = val_loss
            self.counter = 0
            if self.restore_best:
                # Save best model state
                self.best_state = {
                    k: v.clone() for k, v in model.state_dict().items()
                }
        else:
            self.counter += 1

        return self.counter >= self.patience

    def restore_best_weights(self, model: nn.Module) -> None:
        """Restore model to best weights found during training."""
        if self.best_state is not None:
            model.load_state_dict(self.best_state)


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: optim.Optimizer,
    loss_fn: nn.Module,
    device: torch.device,
    grad_clip: float = 1.0
) -> tuple[float, float]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        # Forward pass
        logits = model(X_batch)
        loss = loss_fn(logits, y_batch)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Gradient clipping — prevents exploding gradients
        if grad_clip > 0:
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), max_norm=grad_clip
            )

        optimizer.step()

        total_loss += loss.item()
        predictions = logits.argmax(dim=1)
        correct += (predictions == y_batch).sum().item()
        total += len(y_batch)

    return total_loss / len(loader), correct / total


def evaluate_epoch(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device
) -> tuple[float, float]:
    """Evaluate on a data loader."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            logits = model(X_batch)
            loss = loss_fn(logits, y_batch)

            total_loss += loss.item()
            predictions = logits.argmax(dim=1)
            correct += (predictions == y_batch).sum().item()
            total += len(y_batch)

    return total_loss / len(loader), correct / total


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 0.001,
    weight_decay: float = 1e-4,
    early_stopping_patience: int = 15,
    device: torch.device = None,
    verbose: bool = True
) -> TrainingHistory:
    """
    Complete training loop with early stopping.

    Args:
        model: PyTorch model to train.
        train_loader: Training data loader.
        val_loader: Validation data loader.
        num_epochs: Maximum training epochs.
        learning_rate: Initial learning rate.
        weight_decay: L2 regularization strength.
        early_stopping_patience: Epochs to wait before stopping.
        device: torch.device (cpu or cuda).
        verbose: Print training progress.

    Returns:
        TrainingHistory: Complete training history.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = model.to(device)

    # Loss function with class weighting (handles imbalanced data)
    # Weights are inverse of class frequency
    loss_fn = nn.CrossEntropyLoss()

    # Optimizer: AdamW (Adam with better weight decay)
    optimizer = optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )

    # Learning rate scheduler
    # Reduces LR when validation loss plateaus
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=7,
        min_lr=1e-6
    )

    early_stopping = EarlyStopping(
        patience=early_stopping_patience,
        restore_best=True
    )

    history = TrainingHistory()
    start_time = time.time()

    if verbose:
        print(f"\n  Training on: {device}")
        print(f"  Max epochs:  {num_epochs}")
        print(f"  Patience:    {early_stopping_patience}")
        print()
        print(f"  {'Epoch':>6} {'Train Loss':>11} {'Val Loss':>9} "
              f"{'Train Acc':>10} {'Val Acc':>9} {'LR':>10}")
        print(f"  {'─' * 65}")

    for epoch in range(num_epochs):
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, loss_fn, device
        )

        # Validate
        val_loss, val_acc = evaluate_epoch(
            model, val_loader, loss_fn, device
        )

        # Update scheduler
        current_lr = optimizer.param_groups[0]['lr']
        scheduler.step(val_loss)

        # Record history
        history.train_losses.append(train_loss)
        history.val_losses.append(val_loss)
        history.train_accuracies.append(train_acc)
        history.val_accuracies.append(val_acc)
        history.learning_rates.append(current_lr)

        # Track best epoch
        if val_loss < history.best_val_loss:
            history.best_val_loss = val_loss
            history.best_val_accuracy = val_acc
            history.best_epoch = epoch + 1

        # Print progress
        if verbose and (epoch % 10 == 0 or epoch < 5 or epoch == num_epochs - 1):
            overfit_flag = " ⚠️" if train_acc - val_acc > 0.1 else ""
            best_flag = " ★" if epoch + 1 == history.best_epoch else ""
            print(
                f"  {epoch+1:>6} "
                f"{train_loss:>11.4f} "
                f"{val_loss:>9.4f} "
                f"{train_acc:>10.1%} "
                f"{val_acc:>9.1%} "
                f"{current_lr:>10.6f}"
                f"{best_flag}{overfit_flag}"
            )

        # Early stopping check
        if early_stopping(val_loss, model):
            if verbose:
                print(f"\n  Early stopping at epoch {epoch + 1}")
                print(f"  Best epoch: {history.best_epoch} "
                      f"(val_loss={history.best_val_loss:.4f}, "
                      f"val_acc={history.best_val_accuracy:.1%})")
            break

    # Restore best weights
    early_stopping.restore_best_weights(model)

    history.total_epochs = epoch + 1
    history.training_time_seconds = time.time() - start_time

    if verbose:
        print(f"\n  Training complete in {history.training_time_seconds:.1f}s")
        print(f"  Best validation accuracy: {history.best_val_accuracy:.1%} "
              f"(epoch {history.best_epoch})")

    return history


def save_model(
    model: nn.Module,
    history: TrainingHistory,
    scaler,
    feature_names: list[str],
    model_name: str = "task_priority_nn"
) -> Path:
    """Save model weights and metadata."""
    weights_path = MODELS_DIR / f"{model_name}.pth"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"
    import joblib
    scaler_path = MODELS_DIR / f"{model_name}_scaler.joblib"

    # Save weights
    torch.save(model.state_dict(), weights_path)

    # Save scaler
    joblib.dump(scaler, scaler_path)

    # Save metadata
    meta = {
        "model_class": model.__class__.__name__,
        "input_size": model.input_size if hasattr(model, 'input_size') else len(feature_names),
        "hidden_sizes": model.hidden_sizes if hasattr(model, 'hidden_sizes') else [],
        "num_classes": model.num_classes if hasattr(model, 'num_classes') else 4,
        "dropout_rate": model.dropout_rate if hasattr(model, 'dropout_rate') else 0.3,
        "feature_names": feature_names,
        "class_names": ["low", "medium", "high", "urgent"],
        "best_val_accuracy": history.best_val_accuracy,
        "best_epoch": history.best_epoch,
        "total_epochs": history.total_epochs,
        "total_parameters": sum(p.numel() for p in model.parameters()),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  ✅ Model saved: {weights_path.name}")
    return weights_path


def load_model(model_name: str = "task_priority_nn") -> tuple:
    """Load model, scaler, and metadata."""
    import joblib
    from src.model import TaskPriorityNet

    weights_path = MODELS_DIR / f"{model_name}.pth"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"
    scaler_path = MODELS_DIR / f"{model_name}_scaler.joblib"

    with open(meta_path) as f:
        meta = json.load(f)

    model = TaskPriorityNet(
        input_size=meta["input_size"],
        hidden_sizes=meta["hidden_sizes"],
        num_classes=meta["num_classes"],
        dropout_rate=meta["dropout_rate"]
    )
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    scaler = joblib.load(scaler_path)

    return model, scaler, meta