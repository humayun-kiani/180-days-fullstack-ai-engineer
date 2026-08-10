# Day 30 — Week 5 Revision: AI Project Integration & Ensemble Pipeline

> **Phase 3 — AI & Machine Learning** | Week 5 Capstone | Day 30 of 180

---

## 📌 What I Learned Today

- Ensemble methods: why many models beat one
- Hard voting vs soft voting: count votes vs average probabilities
- Weighted soft voting: trust better models more
- Why ensembles work: different models make different errors
- Confidence calibration: raw probabilities ≠ reliable confidence
- Agreement score: how much models agree → adjusts confidence
- \_priority_to_soft_vector: convert label to probability distribution
- How to integrate NLP signals into a probability ensemble
- NLP urgency modifier: shift probability distribution toward higher priority
- Pipeline architecture: text → NLP → features → RF + NN → ensemble
- Auto-training models on first run (graceful degradation)
- Model caching with global singleton pattern
- FastAPI lifespan: pre-load models at startup not per-request
- Serving HTML from FastAPI with StaticFiles
- Pydantic dataclasses for structured responses
- Week 5 consolidation: ML (27) + NLP (28) + DL (29) + Integration (30)

## 🔨 Project Built

**Unified AI Task Analyzer** — Full ensemble pipeline:

- 4-stage pipeline: NLP → Features → RF + NN → Ensemble
- NLPAnalyzer: rule-based category, sentiment, urgency, entity extraction
  (no model files needed — works standalone)
- FeatureExtractor: 35 numeric features from text + metadata
- ModelsLoader: auto-trains RF + sklearn MLP on first run, caches
- Ensemble: weighted soft voting (RF 45%, NN 45%, NLP 10%)
  - urgency modifier + error code boost
  - agreement-based confidence calibration
- EnsembleResult: final priority + confidence + probabilities + explanations
- FastAPI: POST /analyze, POST /analyze/batch, GET /health, GET /models/info
- Interactive HTML demo UI with probability bars and explanations
- Auto-loads next demo example after each analysis

## 🚀 How to Run

```bash
cd Day-30-AI-Integration
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

uvicorn app.main:app --reload

# Open: http://localhost:8000       ← interactive demo
# Open: http://localhost:8000/docs  ← API documentation
```

## 🧠 Week 5 Concepts Consolidated

| Day | Topic         | Key Concept                                               |
| --- | ------------- | --------------------------------------------------------- |
| 27  | Classical ML  | Random Forest, feature engineering, cross-validation      |
| 28  | NLP           | TF-IDF, text classification, sentiment, entity extraction |
| 29  | Deep Learning | PyTorch, backpropagation, training loop, early stopping   |
| 30  | Integration   | Ensemble, confidence calibration, production pipeline     |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
