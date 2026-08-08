# ============================================================
# src/api.py
# FastAPI inference API for the neural network
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.predictor import predict_from_task_description

app = FastAPI(
    title="Task Priority Predictor — Neural Network",
    description="""
## Deep Learning Task Priority Prediction

Predicts task priority using a **PyTorch Feed-Forward Neural Network**
with 3 hidden layers, BatchNorm, Dropout, and early stopping.

**Day 29 — Neural Networks with PyTorch**
    """,
    version="1.0.0"
)


class TaskInput(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=300,
        example="URGENT: Fix production database connection failure"
    )
    description: Optional[str] = Field(None)
    has_due_date: bool = Field(False)
    is_overdue: bool = Field(False)
    days_until_due: float = Field(0.0)
    tags: Optional[list[str]] = Field(default=[])
    estimated_hours: Optional[float] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "URGENT: Production API returning 500 errors",
                "description": "All endpoints failing after deployment",
                "has_due_date": True,
                "is_overdue": False,
                "days_until_due": 0.1,
                "tags": ["production", "incident"],
                "estimated_hours": 2.0
            }
        }


@app.post("/predict")
def predict(task: TaskInput):
    """Predict priority using the trained neural network."""
    try:
        result = predict_from_task_description(
            title=task.title,
            description=task.description,
            has_due_date=task.has_due_date,
            is_overdue=task.is_overdue,
            days_until_due=task.days_until_due,
            tags=task.tags or [],
            estimated_hours=task.estimated_hours
        )
        return result
    except FileNotFoundError:
        raise HTTPException(
            500,
            "Model not trained. Run: python src/main.py first."
        )


@app.post("/predict/batch")
def predict_batch(tasks: list[TaskInput]):
    if len(tasks) > 50:
        raise HTTPException(400, "Maximum 50 tasks per batch")
    try:
        return [
            predict_from_task_description(
                title=t.title,
                description=t.description,
                has_due_date=t.has_due_date,
                is_overdue=t.is_overdue,
                days_until_due=t.days_until_due,
                tags=t.tags or [],
                estimated_hours=t.estimated_hours
            )
            for t in tasks
        ]
    except FileNotFoundError:
        raise HTTPException(500, "Model not trained.")


@app.get("/model/info")
def model_info():
    try:
        from src.trainer import load_model
        _, _, meta = load_model()
        return {
            "architecture": meta.get("model_class"),
            "hidden_layers": meta.get("hidden_sizes"),
            "total_parameters": meta.get("total_parameters"),
            "best_val_accuracy": meta.get("best_val_accuracy"),
            "feature_count": len(meta.get("feature_names", [])),
            "classes": meta.get("class_names"),
        }
    except FileNotFoundError:
        return {"status": "not_trained", "message": "Run python src/main.py first"}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    return {
        "name": "Task Priority Predictor — Neural Network",
        "day": "Day 29 — Neural Networks with PyTorch",
        "docs": "/docs"
    }