# ============================================================
# app/schemas.py
# Pydantic schemas for the unified AI API
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional


class TaskAnalysisRequest(BaseModel):
    """Input for unified task analysis."""
    title: str = Field(
        min_length=1,
        max_length=500,
        example="URGENT: Production API returning HTTP 500 for all users"
    )
    description: Optional[str] = Field(
        None,
        example="All endpoints failing after today's deployment. Revenue impact."
    )
    has_due_date: bool = Field(False)
    is_overdue: bool = Field(False)
    days_until_due: float = Field(0.0, ge=-30, le=365)
    tags: list[str] = Field(default=[])
    estimated_hours: Optional[float] = Field(None, ge=0.25, le=500)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "URGENT: Production API returning HTTP 500 for all users",
                "description": "All endpoints failing after today's deployment. Customers cannot access the service. Revenue impact significant.",
                "has_due_date": True,
                "is_overdue": False,
                "days_until_due": 0.1,
                "tags": ["production", "incident"],
                "estimated_hours": 2.0
            }
        }


class ModelPrediction(BaseModel):
    """Prediction from a single model."""
    model_name: str
    predicted_priority: str
    confidence: float
    probabilities: dict[str, float]


class NLPAnalysis(BaseModel):
    """Results from NLP analysis pipeline."""
    category: str
    category_confidence: float
    sentiment: str
    urgency_level: str
    positive_score: float
    negative_score: float
    sentiment_signals: list[str]
    error_codes: list[str]
    systems: list[str]
    time_mentions: list[str]
    suggested_tags: list[str]
    action_items: list[str]


class EnsembleResult(BaseModel):
    """Final ensemble prediction."""
    predicted_priority: str
    confidence: float
    probabilities: dict[str, float]
    agreement_score: float
    explanation: list[str]


class UnifiedAnalysisResponse(BaseModel):
    """Complete analysis response from unified AI pipeline."""
    # Input summary
    task_title: str
    word_count: int

    # Individual model predictions
    random_forest: Optional[ModelPrediction] = None
    neural_network: Optional[ModelPrediction] = None

    # NLP analysis
    nlp: NLPAnalysis

    # Ensemble final result
    ensemble: EnsembleResult

    # Metadata
    models_used: list[str]
    pipeline_version: str = "1.0.0"