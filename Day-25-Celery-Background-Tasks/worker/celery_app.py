# ============================================================
# worker/celery_app.py
# Celery application configuration
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from celery import Celery
from celery.schedules import crontab
from app.config import config

# ─── Create Celery App ──────────────────────────────────────

celery_app = Celery(
    "task_manager_worker",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=[
        "worker.tasks.emails",
        "worker.tasks.reports",
        "worker.tasks.notifications",
        "worker.tasks.maintenance"
    ]
)

# ─── Configuration ──────────────────────────────────────────

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone=config.TIMEZONE,
    enable_utc=True,

    # Task behavior
    task_track_started=True,          # track STARTED state
    task_acks_late=True,              # ack after completion (safer)
    worker_prefetch_multiplier=1,     # take 1 task at a time
    task_reject_on_worker_lost=True,  # requeue if worker dies

    # Results
    result_expires=3600,              # results kept for 1 hour
    task_ignore_result=False,         # keep all results

    # Queues — different queues for different task types
    task_routes={
        "worker.tasks.emails.*": {"queue": "emails"},
        "worker.tasks.reports.*": {"queue": "reports"},
        "worker.tasks.notifications.*": {"queue": "notifications"},
        "worker.tasks.maintenance.*": {"queue": "maintenance"},
    },

    # Retry defaults
    task_max_retries=3,
    task_default_retry_delay=30,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# ─── Scheduled Tasks (Celery Beat) ──────────────────────────

celery_app.conf.beat_schedule = {

    # Check for overdue tasks every 30 minutes
    "check-overdue-tasks": {
        "task": "worker.tasks.notifications.check_and_notify_overdue",
        "schedule": 1800,    # every 30 minutes
    },

    # Send daily digest at 8:00 AM
    "daily-digest": {
        "task": "worker.tasks.emails.send_daily_digest_to_all_users",
        "schedule": crontab(hour=8, minute=0),
    },

    # Weekly report every Monday at 9:00 AM
    "weekly-report": {
        "task": "worker.tasks.reports.generate_weekly_summary",
        "schedule": crontab(hour=9, minute=0, day_of_week="monday"),
    },

    # Database cleanup on 1st of each month at midnight
    "monthly-cleanup": {
        "task": "worker.tasks.maintenance.cleanup_old_results",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),
    },

    # Health check every 5 minutes
    "health-check": {
        "task": "worker.tasks.maintenance.health_check",
        "schedule": 300,    # every 5 minutes
    },
}