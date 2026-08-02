# ============================================================
# worker/tasks/reports.py
# Report generation Celery tasks
# ============================================================

import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from celery.utils.log import get_task_logger

from worker.celery_app import celery_app
from app.models import TASKS, USERS

logger = get_task_logger(__name__)

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@celery_app.task(
    name="worker.tasks.reports.generate_task_report",
    bind=True,
    max_retries=2,
    queue="reports"
)
def generate_task_report(
    self,
    report_type: str,
    user_id: int,
    date_range_days: int = 30
) -> dict:
    """
    Generate a detailed task analytics report.

    Shows progress tracking with self.update_state().
    Takes ~5 seconds to simulate heavy processing.
    """
    task_id = self.request.id
    logger.info(
        f"[{task_id}] Starting {report_type} report "
        f"for user {user_id} ({date_range_days} days)"
    )

    try:
        # Stage 1: Fetch data (0-25%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "stage": "Fetching data..."}
        )
        time.sleep(0.8)

        tasks = list(TASKS.values())
        user = USERS.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Stage 2: Calculate statistics (25-60%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 25, "total": 100, "stage": "Calculating statistics..."}
        )
        time.sleep(1.0)

        # Compute stats
        total = len(tasks)
        by_status = {}
        by_priority = {}
        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

        done = by_status.get("done", 0)
        completion_rate = round(done / total * 100 if total > 0 else 0, 1)

        overdue = [
            t for t in tasks
            if t.due_date and t.due_date < datetime.utcnow()
            and t.status not in ("done", "archived")
        ]

        # Stage 3: Generate content (60-85%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "stage": "Generating report content..."}
        )
        time.sleep(0.8)

        report_content = f"""
TASK MANAGER REPORT
===================
Type: {report_type.upper()}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
Requested by: {user.full_name} ({user.email})
Period: Last {date_range_days} days

SUMMARY
-------
Total Tasks:      {total}
Completed:        {done}  ({completion_rate}%)
In Progress:      {by_status.get('in_progress', 0)}
Pending:          {by_status.get('pending', 0)}
Archived:         {by_status.get('archived', 0)}
Overdue:          {len(overdue)}

PRIORITY BREAKDOWN
------------------
Urgent:           {by_priority.get('urgent', 0)}
High:             {by_priority.get('high', 0)}
Medium:           {by_priority.get('medium', 0)}
Low:              {by_priority.get('low', 0)}

OVERDUE TASKS
-------------
{chr(10).join(f'  - {t.title} (due: {t.due_date.strftime("%Y-%m-%d")})' for t in overdue) if overdue else '  None! Great job!'}

COMPLETION RATE: {completion_rate}%
{"🎉 Excellent!" if completion_rate >= 80 else "📈 Keep going!" if completion_rate >= 50 else "⚠️ Needs attention"}
        """.strip()

        # Stage 4: Save report file (85-100%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 85, "total": 100, "stage": "Saving report..."}
        )
        time.sleep(0.5)

        filename = f"report_{report_type}_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = REPORTS_DIR / filename
        filepath.write_text(report_content)

        logger.info(f"[{task_id}] ✅ Report saved to {filepath}")

        return {
            "status": "completed",
            "report_type": report_type,
            "file": filename,
            "filepath": str(filepath),
            "stats": {
                "total_tasks": total,
                "completed": done,
                "completion_rate_pct": completion_rate,
                "overdue_count": len(overdue)
            },
            "generated_at": datetime.utcnow().isoformat(),
            "requested_by": user.username
        }

    except Exception as exc:
        logger.error(f"[{task_id}] ❌ Report failed: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        raise


@celery_app.task(
    name="worker.tasks.reports.generate_weekly_summary",
    bind=True,
    queue="reports"
)
def generate_weekly_summary(self) -> dict:
    """
    Generate weekly summary report for all users.
    Scheduled: every Monday at 9:00 AM.
    """
    logger.info(f"[{self.request.id}] Generating weekly summary...")

    tasks = list(TASKS.values())
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    pending = sum(1 for t in tasks if t.status == "pending")

    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    report = {
        "week": f"{week_start} to {week_end}",
        "total_tasks": total,
        "completed": done,
        "in_progress": in_progress,
        "pending": pending,
        "completion_rate_pct": round(done / total * 100 if total > 0 else 0, 1)
    }

    logger.info(f"[{self.request.id}] ✅ Weekly summary: {report}")
    return report