# ============================================================
# app/main.py
# Unified AI Task Analyzer API
# Day 30 — Week 5 Revision & AI Integration
# ============================================================

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import (
    TaskAnalysisRequest, UnifiedAnalysisResponse,
    ModelPrediction, NLPAnalysis, EnsembleResult
)
from app.feature_extractor import extract_features, features_to_vector, FEATURE_NAMES
from app.nlp_analyzer import analyze as nlp_analyze
from app.models_loader import get_models, predict_with_rf, predict_with_nn
from app.ensemble import ensemble_predictions


# ─── Startup ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load models at startup."""
    print("\n" + "=" * 60)
    print("  Unified AI Task Analyzer")
    print("  Day 30 — AI Pipeline Integration")
    print("=" * 60)
    print("\n  Pre-loading ML models...")
    models = get_models()
    print(f"  ✅ Random Forest: {'ready' if models.rf_available else 'unavailable'}")
    print(f"  ✅ Neural Network: {'ready' if models.nn_available else 'unavailable'}")
    print(f"  ✅ NLP Analyzer: ready (rule-based)")
    print(f"\n  Docs: http://localhost:8000/docs")
    print(f"  Demo: http://localhost:8000\n")
    yield
    print("\n  Shutting down...")


# ─── App ────────────────────────────────────────────────────

app = FastAPI(
    title="Unified AI Task Analyzer",
    description="""
## 🤖 Unified AI Task Analyzer — Day 30

Combines three AI systems into one production-ready pipeline:

| Component | Day | What it does |
|-----------|-----|--------------|
| **NLP Analyzer** | 28 | Category, sentiment, entities, tags |
| **Random Forest** | 27 | Tabular feature-based priority prediction |
| **Neural Network** | 29 | Deep learning priority prediction |
| **Ensemble** | 30 | Weighted combination with confidence calibration |

### Quick Start
Send a POST to `/analyze` with a task description.

### Example
```json
{
  "title": "URGENT: Production API returning HTTP 500 errors",
  "description": "All users affected, revenue impact",
  "has_due_date": true,
  "days_until_due": 0.1,
  "tags": ["production", "incident"]
}
```
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Core Analysis Endpoint ──────────────────────────────────

@app.post(
    "/analyze",
    response_model=UnifiedAnalysisResponse,
    summary="Analyze task — full AI pipeline",
    description="""
Run the complete AI pipeline on a task description.

Returns:
- **NLP analysis**: category, sentiment, urgency, entities, tags
- **Random Forest prediction**: priority with probabilities
- **Neural Network prediction**: priority with probabilities
- **Ensemble result**: combined prediction, confidence, explanation
    """
)
def analyze_task(request: TaskAnalysisRequest) -> UnifiedAnalysisResponse:
    """Main analysis endpoint."""
    start = time.perf_counter()

    # Combine title + description for NLP
    full_text = request.title
    if request.description:
        full_text += " " + request.description

    # ── Stage 1: NLP Analysis ─────────────────────────────────
    nlp_result = nlp_analyze(full_text)

    # ── Stage 2: Feature Extraction ───────────────────────────
    task_dict = request.model_dump()
    features = extract_features(task_dict)
    feature_vector = features_to_vector(features)

    # ── Stage 3: ML Model Predictions ────────────────────────
    models = get_models()
    rf_result = predict_with_rf(models, feature_vector)
    nn_result = predict_with_nn(models, feature_vector)

    # ── Stage 4: Ensemble ─────────────────────────────────────
    ensemble_result = ensemble_predictions(rf_result, nn_result, nlp_result)

    # ── Stage 5: Build Response ───────────────────────────────
    elapsed_ms = (time.perf_counter() - start) * 1000

    models_used = []
    if rf_result:
        models_used.append("Random Forest")
    if nn_result:
        models_used.append("Neural Network (sklearn MLP)")
    models_used.append("NLP Analyzer")

    return UnifiedAnalysisResponse(
        task_title=request.title,
        word_count=len(full_text.split()),
        random_forest=ModelPrediction(**rf_result) if rf_result else None,
        neural_network=ModelPrediction(**nn_result) if nn_result else None,
        nlp=NLPAnalysis(
            category=nlp_result.category,
            category_confidence=nlp_result.category_confidence,
            sentiment=nlp_result.sentiment,
            urgency_level=nlp_result.urgency_level,
            positive_score=nlp_result.positive_score,
            negative_score=nlp_result.negative_score,
            sentiment_signals=nlp_result.sentiment_signals,
            error_codes=nlp_result.error_codes,
            systems=nlp_result.systems,
            time_mentions=nlp_result.time_mentions,
            suggested_tags=nlp_result.suggested_tags,
            action_items=nlp_result.action_items
        ),
        ensemble=ensemble_result,
        models_used=models_used,
    )


@app.post(
    "/analyze/batch",
    summary="Analyze multiple tasks at once"
)
def analyze_batch(requests: list[TaskAnalysisRequest]) -> list[UnifiedAnalysisResponse]:
    """Analyze up to 20 tasks in one call."""
    if len(requests) > 20:
        raise HTTPException(400, "Maximum 20 tasks per batch")
    return [analyze_task(r) for r in requests]


# ─── Health and Info ─────────────────────────────────────────

@app.get("/health")
def health():
    models = get_models()
    return {
        "status": "healthy",
        "models": {
            "random_forest": models.rf_available,
            "neural_network": models.nn_available,
            "nlp_analyzer": True
        },
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 30 — AI Integration"
    }


@app.get("/models/info")
def models_info():
    """Get information about loaded models."""
    models = get_models()
    return {
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "priority_classes": ["low", "medium", "high", "urgent"],
        "models": {
            "random_forest": {
                "available": models.rf_available,
                "type": "RandomForestClassifier",
                "day": "Day 27"
            },
            "neural_network": {
                "available": models.nn_available,
                "type": "MLPClassifier (sklearn)",
                "day": "Day 29"
            },
            "nlp_analyzer": {
                "available": True,
                "type": "Rule-based (lexicon + regex)",
                "day": "Day 28"
            }
        }
    }


# ─── Demo HTML Client ────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def demo_ui():
    with open("static/index.html") as f:
        return f.read()