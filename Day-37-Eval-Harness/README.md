# Day 37 — Fine-Tuning Concepts, Model Evaluation & Evaluation Harnesses

> **Phase 4 — Advanced AI Engineering** | Week 7 | Day 37 of 180

---

## 📌 What I Learned Today

- Evaluation-first mindset: measure before optimizing
- Why "feels good" is not a metric — need quantifiable scores
- Accuracy vs F1: accuracy misleads on imbalanced classes
- Precision: of all predictions for class X, how many correct?
- Recall: of all true class X examples, how many found?
- F1: harmonic mean of precision and recall
- Weighted F1: accounts for class imbalance
- Macro F1: equal weight to all classes regardless of support
- Confusion matrix: which classes get confused with each other
- EvaluationHarness class: run test suite, collect results, aggregate
- TestCase dataclass: case_id, input, expected, category, difficulty
- CaseResult dataclass: actual, correct, latency_ms, error
- Failure analysis: identify patterns in what the model gets wrong
- Category breakdown: which category has worst performance?
- Difficulty breakdown: are "hard" cases systematically failing?
- JSONL format: one JSON object per line, standard for fine-tuning
- Training data checklist: diversity, balance, consistency, accuracy
- Class imbalance detection: max_count / min_count > 3 = warning
- Fine-tuning decision framework: prompting vs RAG vs fine-tuning
- When fine-tuning helps: format consistency, domain style, cost/speed
- When RAG is better: current knowledge, frequently changing data
- LLM-as-judge: use Claude to score Claude's outputs (meta-evaluation)
- Baseline measurement: always measure before making changes

## 🔨 Project Built

**Complete Evaluation Harness:**

- 50 test cases across 4 categories × 3 difficulty levels
- Categories: production_incident (urgent), bug_fix (high),
  feature (medium), maintenance (low)
- Difficulties: easy (clear keywords), medium, hard (ambiguous)

**3 Classifiers Compared:**

- KeywordClassifier: rule-based, ~0ms, ~72% accuracy
- MLClassifier: TF-IDF + Random Forest, ~5ms, ~82% accuracy
- ClaudeClassifier: few-shot prompting, ~500ms, ~88% accuracy

**Metrics computed:**

- Accuracy, F1 (weighted + macro)
- Per-class: precision, recall, F1, support
- Confusion matrix with ASCII visualization
- Per-category and per-difficulty breakdown

**Data Generator:**

- 4 × N training examples (N per class)
- JSONL format ready for fine-tuning
- Validation: structure, balance, JSON format
- Quality score: 100 - (issues × 10)

**FastAPI Endpoints:**

- POST /eval/run: evaluate one classifier
- GET /eval/compare: compare all 3 side-by-side
- GET /eval/test-suite: view test cases with filters
- POST /predict: classify single task
- POST /predict/compare: all 3 classifiers on same task
- POST /data/generate: create JSONL training data
- GET /framework/when-to-finetune: decision framework

## 🚀 How to Run

```bash
cd Day-37-Eval-Harness
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional for Claude

# Run exercises
python exercises/exercise1.py

# Start API
uvicorn app.main:app --reload

# Compare all classifiers
curl http://localhost:8000/eval/compare
```

## 🧠 Key Insight

**Before**: "The AI doesn't always get the right answer, let's tweak the prompt"
**After**: "Accuracy is 72%. The keyword classifier fails 80% on 'hard' cases.
ML gets to 82%. Claude gets to 88% but costs 500ms.
Decision: ship ML classifier, use Claude for critical paths."

Evals turn gut feelings into engineering decisions.

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
