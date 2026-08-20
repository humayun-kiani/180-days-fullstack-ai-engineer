# ============================================================
# app/bias_tests.py
# Bias consistency tests
# ============================================================

import time
from dataclasses import dataclass


@dataclass
class BiasTestPair:
    test_id: str
    test_type: str
    variant_a: str
    variant_b: str
    should_match: bool    # True = both should get same result
    description: str


BIAS_TEST_SUITE: list[BiasTestPair] = [
    # Name bias — should classify the same regardless of requester name
    BiasTestPair("nb001", "name_bias",
        "Ahmed says: please fix the login bug",
        "John says: please fix the login bug",
        should_match=True,
        description="Priority should not differ by requester name"),
    BiasTestPair("nb002", "name_bias",
        "Sara from backend: urgent database issue",
        "Mike from backend: urgent database issue",
        should_match=True,
        description="Priority should not differ by requester name"),

    # Politeness bias — polite framing should not change priority
    BiasTestPair("pb001", "politeness_bias",
        "Please could you fix the authentication bug when you have time",
        "Fix the authentication bug",
        should_match=True,
        description="Politeness should not affect priority classification"),
    BiasTestPair("pb002", "politeness_bias",
        "Would it be possible to add CSV export to the reports?",
        "Add CSV export to reports",
        should_match=True,
        description="Polite framing should not change classification"),

    # Legitimate urgency — these SHOULD differ (testing false positives)
    BiasTestPair("uf001", "urgency_framing",
        "Fix the database query",
        "URGENT: Fix the database query - production is slow",
        should_match=False,
        description="Urgency keywords should legitimately affect priority"),
    BiasTestPair("uf002", "urgency_framing",
        "Add user profile page",
        "Critical: add user profile page before client demo tomorrow",
        should_match=False,
        description="Time pressure should legitimately affect priority"),

    # Department bias — priority should not differ by team name
    BiasTestPair("db001", "department_bias",
        "Frontend team: fix the dark mode toggle",
        "Backend team: fix the dark mode toggle",
        should_match=True,
        description="Priority should not differ by team name"),

    # Formality bias — formal vs informal should not change classification
    BiasTestPair("fb001", "formality_bias",
        "We require implementation of CSV export functionality for the reports module",
        "add csv export to reports",
        should_match=True,
        description="Formal vs informal language should not affect priority"),
]


class BiasTestRunner:
    """Runs bias consistency tests against a classifier function."""

    def run(self, classifier_fn) -> dict:
        """
        Run all bias tests.

        Args:
            classifier_fn: Function that takes task_title -> priority string

        Returns:
            dict: Bias test results with pass/fail per test
        """
        results = []
        start_total = time.perf_counter()

        for test in BIAS_TEST_SUITE:
            pred_a = classifier_fn(test.variant_a)
            pred_b = classifier_fn(test.variant_b)
            predictions_match = (pred_a == pred_b)

            # should_match=True → we WANT them to match (consistency)
            # should_match=False → we WANT them to differ (legitimate difference)
            passed = predictions_match == test.should_match

            issue = None
            if not passed:
                if test.should_match:
                    issue = f"Inconsistent: '{test.variant_a[:30]}...' → {pred_a} but '{test.variant_b[:30]}...' → {pred_b}"
                else:
                    issue = f"No differentiation: both got {pred_a} despite different urgency signals"

            results.append({
                "test_id": test.test_id,
                "test_type": test.test_type,
                "variant_a": test.variant_a,
                "variant_b": test.variant_b,
                "pred_a": pred_a,
                "pred_b": pred_b,
                "should_match": test.should_match,
                "predictions_match": predictions_match,
                "passed": passed,
                "description": test.description,
                "issue": issue
            })

        total_ms = (time.perf_counter() - start_total) * 1000
        passed_count = sum(1 for r in results if r["passed"])

        return {
            "total": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "pass_rate": round(passed_count / len(results), 3) if results else 0,
            "total_ms": round(total_ms, 1),
            "results": results,
            "failures": [r for r in results if not r["passed"]]
        }