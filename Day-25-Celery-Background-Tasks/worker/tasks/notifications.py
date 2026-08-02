# ============================================================
# worker/tasks/notifications.py
# Notification and alert Celery tasks
# ============================================================

from datetime import datetime
from collections import defaultdict
from celery.utils.log import get_task_logger

from worker.celery_app import celery_app
from app.models import get_overdue_tasks, USERS
from worker.tasks.emails import send_overdue_alert

logger = get_task_logger(__name__)


@celery_app.task(
    name="worker.tasks.notifications.check_and_notify_overdue",
    bind=True,
    queue="notifications"
)
def check_and_notify_overdue(self) -> dict:
    """
    Check for overdue tasks and send alerts.

    Scheduled: every 30 minutes.
    Groups overdue tasks by owner and sends one email per user.
    """
    logger.info(f"[{self.request.id}] Checking for overdue tasks...")

    overdue_tasks = get_overdue_tasks()

    if not overdue_tasks:
        logger.info(f"[{self.request.id}] ✅ No overdue tasks found.")
        return {"status": "ok", "overdue_count": 0, "notifications_sent": 0}

    logger.info(f"[{self.request.id}] Found {len(overdue_tasks)} overdue tasks")

    # Group by owner
    tasks_by_owner: dict[int, list] = defaultdict(list)
    for task in overdue_tasks:
        tasks_by_owner[task.owner_id].append(task)

    notifications_sent = 0

    for owner_id, owner_tasks in tasks_by_owner.items():
        user = USERS.get(owner_id)
        if not user or not user.is_active:
            continue

        # Prepare task data for email
        task_data = [
            {
                "title": t.title,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else "N/A",
                "priority": t.priority
            }
            for t in owner_tasks
        ]

        # Queue the alert email (async)
        send_overdue_alert.apply_async(
            args=[user.email, user.full_name, task_data],
            queue="emails",
            countdown=random.uniform(0, 10)  # spread out to avoid SMTP rate limits
        )
        notifications_sent += 1
        logger.info(
            f"[{self.request.id}] Queued alert for {user.username} "
            f"({len(owner_tasks)} overdue tasks)"
        )

    result = {
        "status": "completed",
        "overdue_task_count": len(overdue_tasks),
        "users_notified": notifications_sent,
        "checked_at": datetime.utcnow().isoformat()
    }
    logger.info(f"[{self.request.id}] ✅ Overdue check complete: {result}")
    return result


import random    # needed for countdown spread


@celery_app.task(
    name="worker.tasks.notifications.send_task_assigned_notification",
    bind=True,
    max_retries=2,
    queue="notifications"
)
def send_task_assigned_notification(
    self,
    task_id: int,
    task_title: str,
    assigned_to_email: str,
    assigned_by_username: str,
    due_date: str | None
) -> dict:
    """
    Notify a user when a task is assigned to them.
    """
    logger.info(
        f"[{self.request.id}] Sending assignment notification: "
        f"task {task_id} → {assigned_to_email}"
    )

    from worker.tasks.emails import simulate_send_email
    try:
        subject = f"New Task Assigned: {task_title}"
        body = f"""
You have been assigned a new task:

Task: {task_title}
Task ID: #{task_id}
Assigned by: {assigned_by_username}
{f'Due Date: {due_date}' if due_date else ''}

View and manage this task at: /tasks/{task_id}

— Task Manager
        """.strip()

        simulate_send_email(assigned_to_email, subject, body)

        return {
            "status": "sent",
            "task_id": task_id,
            "recipient": assigned_to_email
        }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)