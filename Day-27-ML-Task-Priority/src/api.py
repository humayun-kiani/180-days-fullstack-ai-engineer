# ============================================================
# src/api.py
# FastAPI endpoint for priority prediction
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.predictor import predict_priority, predict_batch

app = FastAPI(
    title="Task Priority Predictor API",
    description="""
## ML-Powered Task Priority Prediction

Predicts task priority using a Random Forest classifier trained on
synthetic task data.

**Day 27 — 180-Day Full Stack AI Engineer Roadmap**
    """,
    version="1.0.0"
)


class TaskInput(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=300,
        example="URGENT: Fix production database connection failure"
    )
    description: Optional[str] = Field(
        None,
        example="Database is rejecting connections, all users affected"
    )
    due_date: Optional[str] = Field(
        None,
        example="2025-05-26T18:00:00"
    )
    tags: Optional[list[str]] = Field(
        default=[],
        example=["production", "database", "critical"]
    )
    estimated_hours: Optional[float] = Field(
        None,
        example=2.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "URGENT: Fix production API returning 500 errors",
                "description": "All API endpoints failing, customers cannot access service",
                "due_date": "2025-05-26T17:00:00",
                "tags": ["production", "incident"],
                "estimated_hours": 1.5
            }
        }


class PredictionResponse(BaseModel):
    predicted_priority: str
    confidence: float
    probabilities: dict[str, float]
    explanation: list[str]
    task_title: str


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict task priority",
    description="Predict the priority of a task using the trained ML model."
)
def predict(task_input: TaskInput):
    """Predict priority for a single task."""
    try:
        task_dict = task_input.model_dump()
        result = predict_priority(task_dict)
        return result
    except FileNotFoundError:
        raise HTTPException(
            500,
            "Model not trained yet. Run: python src/main.py first."
        )
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")


@app.post(
    "/predict/batch",
    response_model=list[PredictionResponse],
    summary="Predict priority for multiple tasks"
)
def predict_batch_endpoint(tasks: list[TaskInput]):
    """Predict priority for multiple tasks at once."""
    if len(tasks) > 100:
        raise HTTPException(400, "Maximum 100 tasks per batch request")
    try:
        task_dicts = [t.model_dump() for t in tasks]
        return predict_batch(task_dicts)
    except FileNotFoundError:
        raise HTTPException(500, "Model not trained yet.")


@app.get("/model/info")
def model_info():
    """Get information about the loaded model."""
    try:
        from src.trainer import load_model
        _, meta = load_model()
        return {
            "model_loaded": True,
            "feature_count": len(meta["feature_names"]),
            "priorities": list(meta["priority_labels"].keys()),
            "saved_at": meta.get("saved_at", "unknown"),
            "day": "Day 27 — Introduction to Machine Learning"
        }
    except FileNotFoundError:
        return {
            "model_loaded": False,
            "message": "Run python src/main.py to train the model first"
        }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    return {
        "name": "Task Priority Predictor",
        "day": "Day 27 — Introduction to Machine Learning",
        "docs": "/docs",
        "endpoints": {
            "predict": "POST /predict",
            "batch": "POST /predict/batch",
            "info": "GET /model/info"
        }
    }