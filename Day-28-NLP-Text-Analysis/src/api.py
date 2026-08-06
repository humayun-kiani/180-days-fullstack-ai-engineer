# ============================================================
# src/api.py
# FastAPI endpoint for NLP analysis
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from dataclasses import asdict

from src.analyzer import analyze_text

app = FastAPI(
    title="Task Description Analyzer API",
    description="""
## NLP-Powered Task Text Analysis

Analyzes task descriptions to extract:
- **Issue type** classification (bug, feature, performance, etc.)
- **Sentiment** analysis (positive, negative, neutral)
- **Urgency** detection
- **Entity extraction** (error codes, endpoints, systems)
- **Auto-tagging** suggestions
- **Priority** recommendation

**Day 28 — NLP with scikit-learn**
    """,
    version="1.0.0"
)


class TextInput(BaseModel):
    text: str = Field(
        min_length=5,
        max_length=5000,
        example="URGENT: The API endpoint /api/users returns HTTP 500 error "
                "for all requests after today's deployment. All users affected."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "URGENT: The API endpoint /api/users returns HTTP 500 error for all requests. Need immediate fix!"
            }
        }


@app.post("/analyze")
def analyze(input: TextInput):
    """Analyze a task description — returns full NLP analysis."""
    try:
        result = analyze_text(input.text)
        return asdict(result)
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/analyze/batch")
def analyze_batch(inputs: list[TextInput]):
    """Analyze multiple texts at once (max 50)."""
    if len(inputs) > 50:
        raise HTTPException(400, "Maximum 50 texts per batch")
    try:
        return [asdict(analyze_text(i.text)) for i in inputs]
    except Exception as e:
        raise HTTPException(500, f"Batch analysis failed: {str(e)}")


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    return {
        "name": "Task Description Analyzer",
        "day": "Day 28 — Natural Language Processing",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /analyze",
            "batch": "POST /analyze/batch"
        }
    }