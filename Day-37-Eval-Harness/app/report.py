# ============================================================
# app/report.py
# Save and load evaluation reports
# ============================================================

import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def save_report(results: dict, report_name: str = "eval") -> Path:
    """Save evaluation results to a JSON report file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{report_name}_{timestamp}.json"

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "day": "Day 37 — Fine-Tuning Concepts & Evaluation Harnesses",
        **results
    }

    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"  ✅ Report saved: {path.name}")
    return path


def load_latest_report(pattern: str = "eval_*.json") -> dict | None:
    """Load the most recent evaluation report."""
    reports = sorted(REPORTS_DIR.glob(pattern))
    if not reports:
        return None
    with open(reports[-1]) as f:
        return json.load(f)