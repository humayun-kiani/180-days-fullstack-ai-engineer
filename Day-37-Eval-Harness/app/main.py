# ============================================================
# app/main.py
# Evaluation Harness FastAPI Service — Day 37
# ============================================================

import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.harness import EvaluationHarness, TEST_SUITE
from app.classifiers import KeywordClassifier, MLClassifier, ClaudeClassifier
from app.data_generator import generate_training_data, save_jsonl, validate_jsonl
from app.report import save_report


_harness: EvaluationHarness = None
_classifiers: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _harness, _classifiers

    print("\n" + "=" * 60)
    print("  AI Evaluation Harness — Day 37")
    print("  Fine-Tuning Concepts & Model Evaluation")
    print("=" * 60)

    _harness = EvaluationHarness()
    _classifiers = {
        "keyword": KeywordClassifier(),
        "ml": MLClassifier(),
        "claude": ClaudeClassifier()
    }

    print(f"\n  Test suite: {len(TEST_SUITE)} cases")
    print(f"  Classifiers: {list(_classifiers.keys())}")
    print(f"  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="AI Evaluation Harness",
    description="""
## 🧪 AI Evaluation Harness — Day 37

Automated evaluation system for task priority classifiers.

### What this demonstrates
- **Evaluation-first mindset**: measure before optimizing
- **Evaluation harness**: automated test suite for AI outputs
- **Metric comparison**: accuracy, F1, per-class breakdown
- **Failure analysis**: identify which inputs fail
- **Data generation**: create JSONL training data for fine-tuning

### Classifiers compared
| Classifier | Method | Speed | Accuracy |
|-----------|--------|-------|---------|
| Keyword Rules | Pattern matching | ~0ms | ~70-75% |
| ML (TF-IDF + RF) | scikit-learn pipeline | ~5ms | ~80-85% |
| Claude (Few-Shot) | LLM with examples | ~500ms | ~85-92% |

### Key insight
Always build an eval harness BEFORE optimizing.
You can't improve what you can't measure.
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Schemas ─────────────────────────────────────────────────

class RunEvalRequest(BaseModel):
    classifier: str = Field(
        default="keyword",
        description="Which classifier to evaluate: keyword, ml, or claude"
    )
    category_filter: str | None = Field(
        None,
        description="Optional category filter: production_incident, bug_fix, feature, maintenance"
    )


class PredictRequest(BaseModel):
    task_title: str = Field(
        min_length=3,
        max_length=300,
        example="Fix login bug causing 500 errors"
    )
    classifier: str = Field(
        default="ml",
        description="Which classifier to use: keyword, ml, or claude"
    )


class GenerateDataRequest(BaseModel):
    n_per_class: int = Field(
        default=50,
        ge=10,
        le=500,
        description="Examples per priority class (total = n_per_class × 4)"
    )
    include_system_prompt: bool = Field(
        default=True,
        description="Include a system prompt in training examples"
    )


# ─── Evaluation Endpoints ─────────────────────────────────────

@app.post(
    "/eval/run",
    summary="Run evaluation for a classifier",
    description="Evaluate a classifier against the 50-case test suite."
)
async def run_eval(
    request: RunEvalRequest,
    background_tasks: BackgroundTasks
) -> dict:
    if _harness is None:
        raise HTTPException(503, "Harness not initialized")

    clf_name = request.classifier.lower()
    if clf_name not in _classifiers:
        raise HTTPException(400, f"Unknown classifier: {clf_name}. Choose: {list(_classifiers.keys())}")

    start = time.perf_counter()
    results = _harness.run_classifier(
        _classifiers[clf_name],
        subset=request.category_filter
    )
    elapsed = (time.perf_counter() - start) * 1000

    results["eval_latency_ms"] = round(elapsed, 1)

    # Save report in background
    background_tasks.add_task(
        save_report, results, f"eval_{clf_name}"
    )

    return results


@app.get(
    "/eval/compare",
    summary="Compare all classifiers",
    description="Run evaluation for all three classifiers and return side-by-side comparison."
)
async def compare_all(background_tasks: BackgroundTasks) -> dict:
    if _harness is None:
        raise HTTPException(503, "Harness not initialized")

    print("  Running comparison across all 3 classifiers...")
    start = time.perf_counter()

    all_results = {}
    for name, clf in _classifiers.items():
        results = _harness.run_classifier(clf)
        all_results[name] = {
            "accuracy": results["metrics"]["accuracy"],
            "f1_weighted": results["metrics"]["f1_weighted"],
            "f1_macro": results["metrics"]["f1_macro"],
            "avg_latency_ms": results["metrics"]["avg_latency_ms"],
            "failure_count": len(results["failures"]),
            "per_class_f1": {
                k: v["f1"] for k, v in results["metrics"]["per_class"].items()
            }
        }

    elapsed = (time.perf_counter() - start) * 1000

    # Find winner per metric
    best_accuracy = max(all_results, key=lambda k: all_results[k]["accuracy"])
    best_f1 = max(all_results, key=lambda k: all_results[k]["f1_weighted"])
    fastest = min(all_results, key=lambda k: all_results[k]["avg_latency_ms"])

    comparison = {
        "classifiers": all_results,
        "winners": {
            "accuracy": best_accuracy,
            "f1_weighted": best_f1,
            "latency": fastest
        },
        "total_eval_ms": round(elapsed, 1),
        "test_suite_size": len(TEST_SUITE)
    }

    background_tasks.add_task(save_report, comparison, "comparison")
    return comparison


@app.get(
    "/eval/test-suite",
    summary="View the test suite"
)
def get_test_suite(
    category: str | None = None,
    difficulty: str | None = None
) -> dict:
    """List all test cases, optionally filtered."""
    cases = TEST_SUITE
    if category:
        cases = [c for c in cases if c.category == category]
    if difficulty:
        cases = [c for c in cases if c.difficulty == difficulty]

    categories = list(set(c.category for c in TEST_SUITE))
    difficulties = list(set(c.difficulty for c in TEST_SUITE))

    return {
        "cases": [
            {
                "id": c.case_id,
                "title": c.task_title,
                "expected": c.expected_priority,
                "category": c.category,
                "difficulty": c.difficulty
            }
            for c in cases
        ],
        "total": len(cases),
        "available_categories": categories,
        "available_difficulties": difficulties
    }


# ─── Prediction Endpoint ──────────────────────────────────────

@app.post(
    "/predict",
    summary="Classify a single task",
    description="Get priority classification from any of the three classifiers."
)
def predict(request: PredictRequest) -> dict:
    clf_name = request.classifier.lower()
    if clf_name not in _classifiers:
        raise HTTPException(400, f"Unknown classifier: {clf_name}")

    clf = _classifiers[clf_name]
    start = time.perf_counter()
    priority = clf.predict(request.task_title)
    latency = (time.perf_counter() - start) * 1000

    return {
        "task_title": request.task_title,
        "predicted_priority": priority,
        "classifier": clf.name,
        "latency_ms": round(latency, 2)
    }


@app.post(
    "/predict/compare",
    summary="Classify with all three classifiers",
    description="See how all three classifiers predict the same task."
)
def predict_compare(task_title: str = "Fix login bug before tomorrow's demo") -> dict:
    results = {}
    for name, clf in _classifiers.items():
        start = time.perf_counter()
        pred = clf.predict(task_title)
        latency = (time.perf_counter() - start) * 1000
        results[name] = {
            "prediction": pred,
            "latency_ms": round(latency, 2)
        }

    # Check agreement
    predictions = [v["prediction"] for v in results.values()]
    all_agree = len(set(predictions)) == 1

    return {
        "task_title": task_title,
        "predictions": results,
        "all_agree": all_agree,
        "majority_vote": max(set(predictions), key=predictions.count)
    }


# ─── Data Generation Endpoint ─────────────────────────────────

@app.post(
    "/data/generate",
    summary="Generate JSONL training data",
    description="Generate fine-tuning training data in JSONL format."
)
def generate_data(request: GenerateDataRequest) -> dict:
    system_prompt = (
        "You are a task priority classifier. Classify tasks as urgent, high, medium, or low priority."
        if request.include_system_prompt else ""
    )

    examples = generate_training_data(
        n_per_class=request.n_per_class,
        system_prompt=system_prompt
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"training_data_{timestamp}.jsonl"
    filepath = save_jsonl(examples, filename)

    validation = validate_jsonl(filepath)

    return {
        "generated": len(examples),
        "filename": filename,
        "filepath": str(filepath),
        "class_distribution": validation["class_distribution"],
        "validation": {
            "is_valid": validation["is_valid"],
            "issues": validation["issues"]
        },
        "note": "Use this JSONL file with Anthropic fine-tuning API or any LLM provider"
    }


# ─── Decision Framework ───────────────────────────────────────

@app.get(
    "/framework/when-to-finetune",
    summary="Decision framework: prompting vs RAG vs fine-tuning"
)
def when_to_finetune() -> dict:
    return {
        "decision_framework": {
            "question_1": "Can the model do the task with good prompts?",
            "if_yes": "Stop here. Use better prompts or few-shot examples.",
            "if_no": "Continue to question 2.",
            "question_2": "Does the task require specific knowledge that changes frequently?",
            "if_yes_q2": "Use RAG. Fine-tuning doesn't help with current facts.",
            "if_no_q2": "Consider fine-tuning.",
            "fine_tuning_checklist": [
                "✅ You have 100+ high-quality labeled examples per class",
                "✅ The task format/style is consistent and stable",
                "✅ The base model consistently fails despite good prompts",
                "✅ You need lower latency or cost than large model + long prompt",
                "✅ You've measured the baseline accuracy with your eval harness"
            ]
        },
        "when_each_approach_wins": {
            "prompt_engineering": "Few examples, quick iteration, task already understood by model",
            "few_shot_prompting": "Need better format adherence, have 3-10 good examples",
            "rag": "Task needs current/specific knowledge, knowledge changes often",
            "fine_tuning": "Need consistent format, domain-specific style, cost/speed optimization",
            "fine_tuning_plus_rag": "Best of both: specific knowledge + consistent output format"
        },
        "eval_harness_reminder": (
            "Always build an eval harness FIRST. "
            "Measure baseline → improve → measure again. "
            "You can't know if fine-tuning helped without measurement."
        )
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "test_suite_size": len(TEST_SUITE),
        "classifiers": list(_classifiers.keys()),
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 37 — Fine-Tuning Concepts & Evaluation Harnesses"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Evaluation Harness",
        "day": "Day 37 — Fine-Tuning Concepts & Model Evaluation",
        "docs": "/docs",
        "endpoints": {
            "run_eval": "POST /eval/run",
            "compare_all": "GET /eval/compare",
            "test_suite": "GET /eval/test-suite",
            "predict": "POST /predict",
            "predict_compare": "POST /predict/compare",
            "generate_data": "POST /data/generate",
            "framework": "GET /framework/when-to-finetune"
        }
    }