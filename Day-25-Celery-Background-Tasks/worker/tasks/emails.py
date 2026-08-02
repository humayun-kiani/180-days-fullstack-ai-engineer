# ============================================================
# worker/tasks/emails.py
# Email-related Celery tasks
# ============================================================

import time
import random
from datetime import datetime
from celery import Task
from celery.utils.log import get_task_logger

from worker.celery_app import celery_app
from app.models import USERS, get_all_users, get_pending_tasks_for_user

logger = get_task_logger(__name__)


def simulate_send_email(to: str, subject: str, body: str) -> bool:
    """
    Simulates sending an email.

    In production: use smtplib, SendGrid, Mailgun, SES, etc.
    Returns True on success, raises on failure.
    """
    logger.info(f"  📧 Simulating email send to: {to}")
    logger.info(f"     Subject: {subject}")
    logger.info(f"     Body preview: {body[:80]}...")

    # Simulate occasional network issues (for retry demo)
    if random.random() < 0.05:    # 5% failure rate
        raise ConnectionError("SMTP server temporarily unavailable")

    time.sleep(0.5)    # simulate SMTP latency
    logger.info(f"  ✅ Email sent successfully to {to}")
    return True


@celery_app.task(
    name="worker.tasks.emails.send_welcome_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="emails"
)
def send_welcome_email(self, user_id: int, email: str, full_name: str) -> dict:
    """
    Send a welcome email to a newly registered user.

    Triggered by: POST /auth/register
    Queue: emails
    Retry: up to 3 times with 30s/60s/120s delays
    """
    logger.info(f"[Task {self.request.id}] Sending welcome email to {email}")

    try:
        subject = f"Welcome to Task Manager, {full_name.split()[0]}! 🎉"
        body = f"""
Hello {full_name},

Welcome to Task Manager! Your account has been successfully created.

Getting started:
  • Create your first project at /projects
  • Add tasks to track your work
  • Set due dates and priorities
  • Mark tasks as done when complete

Your account details:
  • User ID: {user_id}
  • Email: {email}

Happy tasking!

— The Task Manager Team
        """.strip()

        simulate_send_email(email, subject, body)

        result = {
            "status": "sent",
            "recipient": email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "template": "welcome"
        }

        logger.info(f"[Task {self.request.id}] ✅ Welcome email sent to {email}")
        return result

    except ConnectionError as exc:
        logger.warning(
            f"[Task {self.request.id}] ⚠️ SMTP error, retrying... "
            f"(attempt {self.request.retries + 1}/{self.max_retries})"
        )
        raise self.retry(
            exc=exc,
            countdown=30 * (2 ** self.request.retries)    # exponential backoff
        )


@celery_app.task(
    name="worker.tasks.emails.send_task_completion_notification",
    bind=True,
    max_retries=2,
    queue="emails"
)
def send_task_completion_notification(
    self,
    task_id: int,
    task_title: str,
    completed_by_username: str,
    owner_email: str,
    owner_name: str
) -> dict:
    """
    Notify task owner when someone else completes their task.

    Only sent when completer ≠ owner.
    """
    logger.info(
        f"[Task {self.request.id}] Sending completion notification "
        f"for task '{task_title}' to {owner_email}"
    )

    try:
        subject = f"Task Completed: {task_title}"
        body = f"""
Hello {owner_name.split()[0]},

Great news! Your task has been completed.

Task: {task_title}
Task ID: #{task_id}
Completed by: {completed_by_username}
Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

View the task at: /tasks/{task_id}

Keep up the great work!

— Task Manager
        """.strip()

        simulate_send_email(owner_email, subject, body)

        return {
            "status": "sent",
            "recipient": owner_email,
            "task_id": task_id,
            "completed_by": completed_by_username
        }

    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(
    name="worker.tasks.emails.send_daily_digest_to_all_users",
    bind=True,
    queue="emails"
)
def send_daily_digest_to_all_users(self) -> dict:
    """
    Send daily task digest to all active users.

    Scheduled: every day at 8:00 AM.
    Shows each user their pending tasks for the day.
    """
    logger.info(f"[Task {self.request.id}] Starting daily digest emails...")

    users = get_all_users()
    sent_count = 0
    skipped_count = 0
    total = len(users)

    for i, user in enumerate(users):
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i,
                "total": total,
                "status": f"Sending to {user.username}..."
            }
        )

        pending_tasks = get_pending_tasks_for_user(user.id)

        if not pending_tasks:
            skipped_count += 1
            continue    # no pending tasks, skip

        # Build digest
        task_lines = "\n".join([
            f"  • [{t.priority.upper()}] {t.title}"
            + (f" (due: {t.due_date.strftime('%b %d %H:%M')})" if t.due_date else "")
            for t in pending_tasks[:10]  # max 10 per digest
        ])

        subject = f"📋 Your Daily Task Digest — {datetime.utcnow().strftime('%b %d, %Y')}"
        body = f"""
Good morning, {user.full_name.split()[0]}!

Here are your pending tasks for today:

{task_lines}

{'(+ more tasks not shown)' if len(pending_tasks) > 10 else ''}

Total pending: {len(pending_tasks)} task(s)

Log in to manage your tasks: /tasks

Have a productive day!

— Task Manager
        """.strip()

        try:
            simulate_send_email(user.email, subject, body)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send digest to {user.email}: {e}")

    result = {
        "status": "completed",
        "total_users": total,
        "emails_sent": sent_count,
        "emails_skipped": skipped_count,
        "completed_at": datetime.utcnow().isoformat()
    }

    logger.info(
        f"[Task {self.request.id}] ✅ Daily digest complete: "
        f"{sent_count} sent, {skipped_count} skipped"
    )
    return result


@celery_app.task(
    name="worker.tasks.emails.send_overdue_alert",
    bind=True,
    max_retries=2,
    queue="emails"
)
def send_overdue_alert(
    self,
    user_email: str,
    user_name: str,
    overdue_tasks: list[dict]
) -> dict:
    """Send overdue task alert to a specific user."""
    logger.info(
        f"[Task {self.request.id}] Sending overdue alert to {user_email} "
        f"({len(overdue_tasks)} overdue tasks)"
    )

    try:
        task_lines = "\n".join([
            f"  ⚠️  {t['title']} (was due: {t['due_date']})"
            for t in overdue_tasks
        ])

        subject = f"⚠️ Action Required: {len(overdue_tasks)} Overdue Task(s)"
        body = f"""
Hello {user_name.split()[0]},

You have {len(overdue_tasks)} overdue task(s) that need attention:

{task_lines}

Please update or reschedule these tasks as soon as possible.

View overdue tasks: /tasks?overdue=true

— Task Manager
        """.strip()

        simulate_send_email(user_email, subject, body)

        return {
            "status": "sent",
            "recipient": user_email,
            "overdue_count": len(overdue_tasks)
        }

    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=60)