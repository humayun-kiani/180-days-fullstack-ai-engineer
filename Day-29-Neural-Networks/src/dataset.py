# ============================================================
# src/dataset.py
# Data generation and preparation for neural network training
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import random
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# ─── Reuse Day 27's data generator (inline simplified version) ──

PRIORITY_LABELS = {"low": 0, "medium": 1, "high": 2, "urgent": 3}
PRIORITY_NAMES = {v: k for k, v in PRIORITY_LABELS.items()}

URGENCY_WORDS = {
    "urgent", "asap", "critical", "immediately", "emergency",
    "hotfix", "incident", "outage", "p0", "escalation",
    "blocking", "down", "failure", "crash", "breach"
}
HIGH_WORDS = {"fix", "deploy", "release", "deadline", "review", "bug", "security"}
LOW_WORDS = {"nice", "optional", "future", "research", "explore", "investigate"}
ACTION_VERBS = {"fix", "implement", "deploy", "create", "add", "update", "review"}


def generate_synthetic_task(priority: str, idx: int) -> dict:
    """Generate a synthetic task with realistic features."""
    from datetime import datetime, timedelta
    now = datetime.utcnow()

    # Due date based on priority
    if priority == "urgent":
        days = random.choice([-random.randint(1, 3), random.uniform(0, 0.5)])
    elif priority == "high":
        days = random.uniform(-0.5, 3)
    elif priority == "medium":
        days = random.uniform(3, 14)
    else:
        days = None if random.random() < 0.4 else random.uniform(10, 30)

    due_date = (now + timedelta(days=days)).isoformat() if days is not None else None
    is_overdue = days is not None and days < 0
    days_until = max(-7, min(30, days)) if days is not None else 0

    # Title urgency features
    urgency_count = random.randint(1, 3) if priority == "urgent" else random.randint(0, 1)
    has_caps = priority == "urgent" and random.random() > 0.3
    has_excl = priority in ("urgent", "high") and random.random() > 0.5
    mentions_prod = priority in ("urgent", "high") and random.random() > 0.4
    mentions_security = priority in ("urgent", "high") and random.random() > 0.5
    estimated = {"urgent": 2.0, "high": 5.0, "medium": 4.0, "low": 2.0}[priority]
    estimated += random.uniform(-1, 1)

    return {
        "id": idx,
        "priority": priority,
        "title_word_count": random.randint(4, 15),
        "title_char_count": random.randint(20, 100),
        "title_upper_ratio": random.uniform(0.4, 0.9) if has_caps else random.uniform(0, 0.15),
        "has_exclamation": int(has_excl),
        "has_colon": int(priority in ("urgent", "high") and random.random() > 0.5),
        "starts_with_verb": int(random.random() > 0.5),
        "has_number": int(random.random() > 0.6),
        "urgency_word_count": urgency_count,
        "high_priority_word_count": random.randint(0, 3) if priority in ("high", "urgent") else 0,
        "low_priority_word_count": random.randint(1, 3) if priority in ("low", "medium") else 0,
        "mentions_production": int(mentions_prod),
        "mentions_customer": int(priority in ("urgent", "high") and random.random() > 0.5),
        "mentions_security": int(mentions_security),
        "has_description": int(random.random() > (0.1 if priority in ("urgent", "high") else 0.5)),
        "description_word_count": random.randint(10, 100) if priority in ("urgent", "high") else random.randint(0, 40),
        "description_urgency_words": urgency_count if priority == "urgent" else 0,
        "has_due_date": int(due_date is not None),
        "is_overdue": int(is_overdue),
        "days_until_due": days_until,
        "hours_until_due": days_until * 24 if days_until else 0,
        "due_today": int(days is not None and 0 <= days <= 1),
        "due_this_week": int(days is not None and 0 <= days <= 7),
        "due_within_3_days": int(days is not None and 0 <= days <= 3),
        "tag_count": random.randint(1, 4),
        "has_estimate": int(random.random() > 0.2),
        "estimated_hours": max(0.5, estimated),
        "short_estimate": int(estimated <= 2),
        "long_estimate": int(estimated >= 8),
        "hour_of_day": random.randint(0, 23),
        "day_of_week": random.randint(0, 6),
        "is_business_hours": int(random.random() > 0.3),
        "is_monday_morning": int(random.random() > 0.85),
        "is_friday_afternoon": int(random.random() > 0.85),
        "is_weekend": int(random.random() > 0.7),
        "created_late_night": int(random.random() > 0.8),
    }


FEATURE_NAMES = [
    "title_word_count", "title_char_count", "title_upper_ratio",
    "has_exclamation", "has_colon", "starts_with_verb", "has_number",
    "urgency_word_count", "high_priority_word_count", "low_priority_word_count",
    "mentions_production", "mentions_customer", "mentions_security",
    "has_description", "description_word_count", "description_urgency_words",
    "has_due_date", "is_overdue", "days_until_due", "hours_until_due",
    "due_today", "due_this_week", "due_within_3_days",
    "tag_count", "has_estimate", "estimated_hours", "short_estimate", "long_estimate",
    "hour_of_day", "day_of_week", "is_business_hours",
    "is_monday_morning", "is_friday_afternoon", "is_weekend", "created_late_night",
]


def generate_dataset(n_samples: int = 2000) -> pd.DataFrame:
    """Generate synthetic task dataset."""
    distribution = {"urgent": 0.15, "high": 0.25, "medium": 0.40, "low": 0.20}
    tasks = []
    idx = 0
    for priority, fraction in distribution.items():
        n = int(n_samples * fraction)
        for _ in range(n):
            tasks.append(generate_synthetic_task(priority, idx))
            idx += 1

    df = pd.DataFrame(tasks).sample(frac=1, random_state=42).reset_index(drop=True)
    return df


class TaskDataset(Dataset):
    """PyTorch Dataset for task priority prediction."""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


def prepare_dataloaders(
    df: pd.DataFrame,
    batch_size: int = 64,
    test_size: float = 0.15,
    val_size: float = 0.15
) -> tuple:
    """
    Prepare train/val/test DataLoaders with feature scaling.

    Returns:
        tuple: (train_loader, val_loader, test_loader, scaler, feature_names)
    """
    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = np.array([PRIORITY_LABELS[p] for p in df["priority"]])

    # Split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    val_fraction = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_fraction, random_state=42, stratify=y_temp
    )

    # Scale features — CRITICAL for neural networks
    # Neural networks are sensitive to feature scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)   # fit ONLY on train
    X_val = scaler.transform(X_val)            # transform val
    X_test = scaler.transform(X_test)          # transform test

    # Create DataLoaders
    train_loader = DataLoader(
        TaskDataset(X_train, y_train),
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )
    val_loader = DataLoader(
        TaskDataset(X_val, y_val),
        batch_size=batch_size,
        shuffle=False
    )
    test_loader = DataLoader(
        TaskDataset(X_test, y_test),
        batch_size=batch_size,
        shuffle=False
    )

    print(f"\n  Dataset prepared:")
    print(f"  Train:      {len(X_train):5d} samples")
    print(f"  Validation: {len(X_val):5d} samples")
    print(f"  Test:       {len(X_test):5d} samples")
    print(f"  Features:   {len(FEATURE_NAMES)}")
    print(f"  Batch size: {batch_size}")

    return train_loader, val_loader, test_loader, scaler, FEATURE_NAMES