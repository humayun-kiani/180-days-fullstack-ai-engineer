# ============================================================
# app/harness.py
# The core evaluation harness
# ============================================================

import time
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.metrics import compute_metrics, EvalMetrics, format_confusion_matrix
from app.classifiers import KeywordClassifier, MLClassifier, ClaudeClassifier

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# ─── Test Cases ──────────────────────────────────────────────

@dataclass
class TestCase:
    case_id: str
    task_title: str
    expected_priority: str
    category: str       # "production_incident", "bug_fix", "feature", "maintenance"
    difficulty: str     # "easy", "medium", "hard"


@dataclass
class CaseResult:
    case_id: str
    task_title: str
    expected: str
    predicted: str
    correct: bool
    latency_ms: float
    error: str | None = None


# 50 test cases across all categories and difficulties
TEST_SUITE: list[TestCase] = [
    # ── Production Incidents (should be urgent) ───────────────
    TestCase("p001", "URGENT: Production API completely down for all users", "urgent", "production_incident", "easy"),
    TestCase("p002", "P0: Database server unreachable, entire app broken", "urgent", "production_incident", "easy"),
    TestCase("p003", "Critical security breach: user data exposed", "urgent", "production_incident", "easy"),
    TestCase("p004", "Payment service not processing transactions", "urgent", "production_incident", "medium"),
    TestCase("p005", "Authentication completely broken after deployment", "urgent", "production_incident", "medium"),
    TestCase("p006", "All API endpoints returning 500, customers affected", "urgent", "production_incident", "easy"),
    TestCase("p007", "Memory leak causing server crashes every 2 hours", "urgent", "production_incident", "hard"),
    TestCase("p008", "SSL certificate expired, HTTPS not working", "urgent", "production_incident", "medium"),
    TestCase("p009", "Data corruption detected in user orders table", "urgent", "production_incident", "hard"),
    TestCase("p010", "Redis cluster down, all cached data lost", "urgent", "production_incident", "medium"),

    # ── Bug Fixes (should be high) ────────────────────────────
    TestCase("b001", "Fix login bug causing 500 errors for some users", "high", "bug_fix", "easy"),
    TestCase("b002", "Null pointer exception in payment processing flow", "high", "bug_fix", "medium"),
    TestCase("b003", "Race condition causing duplicate task creation", "high", "bug_fix", "hard"),
    TestCase("b004", "Fix authentication failing for users with special characters in password", "high", "bug_fix", "medium"),
    TestCase("b005", "Database query timeout on reports page", "high", "bug_fix", "medium"),
    TestCase("b006", "Fix email notifications not being sent after task assignment", "high", "bug_fix", "easy"),
    TestCase("b007", "Resolve N+1 query problem causing slow dashboard", "high", "bug_fix", "hard"),
    TestCase("b008", "Fix CORS error preventing frontend from calling API", "high", "bug_fix", "medium"),
    TestCase("b009", "Incorrect calculation in invoice total", "high", "bug_fix", "hard"),
    TestCase("b010", "Fix session expiry not working correctly", "high", "bug_fix", "medium"),

    # ── Features (should be medium) ──────────────────────────
    TestCase("f001", "Add CSV export to the reports dashboard", "medium", "feature", "easy"),
    TestCase("f002", "Implement dark mode for the entire application", "medium", "feature", "easy"),
    TestCase("f003", "Build bulk task import from spreadsheet", "medium", "feature", "medium"),
    TestCase("f004", "Add Slack integration for task notifications", "medium", "feature", "medium"),
    TestCase("f005", "Create analytics dashboard showing team velocity", "medium", "feature", "medium"),
    TestCase("f006", "Implement email digest for daily task summaries", "medium", "feature", "easy"),
    TestCase("f007", "Add keyboard shortcuts for common dashboard actions", "medium", "feature", "hard"),
    TestCase("f008", "Build API rate limiting with per-user quotas", "medium", "feature", "hard"),
    TestCase("f009", "Add two-factor authentication support", "medium", "feature", "medium"),
    TestCase("f010", "Create mobile-responsive version of dashboard", "medium", "feature", "easy"),

    # ── Maintenance (should be low) ───────────────────────────
    TestCase("m001", "Update README with new setup instructions", "low", "maintenance", "easy"),
    TestCase("m002", "Refactor user model for better code organization", "low", "maintenance", "easy"),
    TestCase("m003", "Research GraphQL as alternative to REST", "low", "maintenance", "easy"),
    TestCase("m004", "Add docstrings to all public functions in auth module", "low", "maintenance", "easy"),
    TestCase("m005", "Update npm dependencies to latest versions", "low", "maintenance", "easy"),
    TestCase("m006", "Clean up unused CSS classes in stylesheet", "low", "maintenance", "easy"),
    TestCase("m007", "Archive old completed tasks from 2022", "low", "maintenance", "medium"),
    TestCase("m008", "Explore options for migrating to PostgreSQL 16", "low", "maintenance", "hard"),
    TestCase("m009", "Review and update API documentation", "low", "maintenance", "easy"),
    TestCase("m010", "Set up automated dependency vulnerability scanning", "low", "maintenance", "hard"),

    # ── Tricky edge cases ─────────────────────────────────────
    TestCase("e001", "Deploy hotfix for the registration bug", "high", "bug_fix", "hard"),
    TestCase("e002", "Nice to have: add more keyboard shortcuts", "low", "maintenance", "hard"),
    TestCase("e003", "Performance improvement for the home page load time", "high", "bug_fix", "hard"),
    TestCase("e004", "Routine database maintenance window", "low", "maintenance", "hard"),
    TestCase("e005", "Implement new required compliance feature for GDPR", "medium", "feature", "hard"),
    TestCase("e006", "Fix minor UI inconsistency in button colors", "low", "maintenance", "hard"),
    TestCase("e007", "Add support for multi-language (i18n)", "medium", "feature", "hard"),
    TestCase("e008", "Investigate intermittent timeout in background jobs", "high", "bug_fix", "hard"),
    TestCase("e009", "Write technical spec for the new reporting module", "low", "maintenance", "hard"),
    TestCase("e010", "Critical: fix data export producing wrong CSV format", "high", "bug_fix", "hard"),
]


class EvaluationHarness:
    """
    Automated evaluation harness for task priority classifiers.

    Usage:
        harness = EvaluationHarness()
        results = harness.run_classifier(KeywordClassifier())
        harness.print_report(results)
    """

    def __init__(self, test_suite: list[TestCase] = None):
        self.test_suite = test_suite or TEST_SUITE

    def run_classifier(
        self,
        classifier,
        subset: str | None = None
    ) -> dict:
        """
        Run a classifier against the full test suite.

        Args:
            classifier: Any object with a .predict(task_title) method
            subset: Optional category to filter ("production_incident", "bug_fix", "feature", "maintenance")

        Returns:
            dict: Results including metrics, per-case results, failures
        """
        cases = self.test_suite
        if subset:
            cases = [c for c in cases if c.category == subset]

        case_results: list[CaseResult] = []
        predictions = []
        labels = []
        latencies = []
        errors = []

        print(f"\n  Running {classifier.name} on {len(cases)} cases...")

        for case in cases:
            start = time.perf_counter()
            error = None
            try:
                predicted = classifier.predict(case.task_title)
            except Exception as e:
                predicted = "medium"    # default on error
                error = str(e)

            latency_ms = (time.perf_counter() - start) * 1000
            correct = predicted == case.expected_priority

            case_results.append(CaseResult(
                case_id=case.case_id,
                task_title=case.task_title,
                expected=case.expected_priority,
                predicted=predicted,
                correct=correct,
                latency_ms=latency_ms,
                error=error
            ))

            predictions.append(predicted)
            labels.append(case.expected_priority)
            latencies.append(latency_ms)
            errors.append(error)

        metrics = compute_metrics(predictions, labels, latencies, errors)

        # Failure analysis
        failures = [r for r in case_results if not r.correct]
        failure_by_category = {}
        for case in cases:
            if any(r.case_id == case.case_id and not r.correct for r in case_results):
                cat = case.category
                failure_by_category[cat] = failure_by_category.get(cat, 0) + 1

        return {
            "classifier": classifier.name,
            "metrics": metrics.to_dict(),
            "case_results": [
                {
                    "id": r.case_id,
                    "title": r.task_title[:60],
                    "expected": r.expected,
                    "predicted": r.predicted,
                    "correct": r.correct
                }
                for r in case_results
            ],
            "failures": [
                {
                    "id": r.case_id,
                    "title": r.task_title,
                    "expected": r.expected,
                    "predicted": r.predicted
                }
                for r in failures
            ],
            "failure_by_category": failure_by_category,
            "total_cases": len(cases)
        }

    def run_all_classifiers(self) -> dict:
        """Run all three classifiers and return comparison."""
        classifiers = [
            KeywordClassifier(),
            MLClassifier(),
            ClaudeClassifier()
        ]

        all_results = {}
        for clf in classifiers:
            results = self.run_classifier(clf)
            all_results[clf.name] = results

        return {
            "comparison": all_results,
            "summary": self._build_summary(all_results)
        }

    def _build_summary(self, all_results: dict) -> dict:
        """Build a comparison summary across all classifiers."""
        summary = {}
        for name, results in all_results.items():
            m = results["metrics"]
            summary[name] = {
                "accuracy": m["accuracy"],
                "f1_weighted": m["f1_weighted"],
                "avg_latency_ms": m["avg_latency_ms"],
                "failures": len(results["failures"])
            }
        return summary

    def print_report(self, results: dict) -> None:
        """Print a formatted evaluation report to terminal."""
        try:
            from colorama import Fore, Style
        except ImportError:
            class Fore:
                GREEN = YELLOW = RED = CYAN = WHITE = ""
            class Style:
                RESET_ALL = ""

        m = results["metrics"]
        name = results["classifier"]
        acc = m["accuracy"]

        print(f"\n{'═' * 65}")
        print(f"  Evaluation Report: {name}")
        print(f"{'═' * 65}")

        color = Fore.GREEN if acc >= 0.85 else Fore.YELLOW if acc >= 0.70 else Fore.RED
        print(f"\n  Accuracy:      {color}{acc:.1%}{Style.RESET_ALL}")
        print(f"  F1 (weighted): {m['f1_weighted']:.3f}")
        print(f"  F1 (macro):    {m['f1_macro']:.3f}")
        print(f"  Avg latency:   {m['avg_latency_ms']:.1f}ms")
        print(f"  Errors:        {m['error_count']}")

        print(f"\n  Per-class metrics:")
        print(f"  {'Priority':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
        print(f"  {'─' * 50}")

        for priority in ["low", "medium", "high", "urgent"]:
            if priority in m["per_class"]:
                pc = m["per_class"][priority]
                f1_color = Fore.GREEN if pc["f1"] >= 0.80 else Fore.YELLOW if pc["f1"] >= 0.60 else Fore.RED
                print(
                    f"  {priority:<12} "
                    f"{pc['precision']:>10.3f} "
                    f"{pc['recall']:>8.3f} "
                    f"{f1_color}{pc['f1']:>8.3f}{Style.RESET_ALL} "
                    f"{pc['support']:>8}"
                )

        print(f"\n  Confusion Matrix (rows=actual, cols=predicted):")
        print(f"  Predicted →  {'low':>8} {'medium':>8} {'high':>8} {'urgent':>8}")
        print(f"  {'─' * 50}")
        priority_names = ["low", "medium", "high", "urgent"]
        for i, row in enumerate(m["confusion_matrix"]):
            row_parts = []
            for j, val in enumerate(row):
                if i == j:
                    row_parts.append(f"{Fore.GREEN}{val:>8}{Style.RESET_ALL}")
                elif val > 0:
                    row_parts.append(f"{Fore.RED}{val:>8}{Style.RESET_ALL}")
                else:
                    row_parts.append(f"{val:>8}")
            print(f"  Act {priority_names[i]:<8}" + "".join(row_parts))

        failures = results.get("failures", [])
        if failures:
            print(f"\n  Top failures ({len(failures)} total):")
            for f in failures[:5]:
                print(f"    ❌ '{f['title'][:50]}' → expected {f['expected']}, got {f['predicted']}")