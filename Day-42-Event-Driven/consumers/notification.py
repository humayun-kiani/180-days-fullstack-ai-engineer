# ============================================================
# consumers/notification.py
# Notification consumer — sends emails for task events
# ============================================================

from datetime import datetime
from app.event_bus import Event, event_bus


# Simulated sent notifications log
_sent_notifications: list[dict] = []


async def handle_task_created(event: Event) -> None:
    """
    Send notification when a new task is created.

    In production: call email service, Slack API, push notification.
    """
    payload = event.payload
    task_title = payload.get("title", "Unknown task")
    priority = payload.get("priority", "medium")
    created_by = payload.get("created_by", "someone")

    # Simulate email sending
    notification = {
        "type": "task_created",
        "to": f"{created_by}@company.com",
        "subject": f"[{priority.upper()}] New task: {task_title}",
        "body": (
            f"A new {priority} priority task was created:\n\n"
            f"Title: {task_title}\n"
            f"ID: {payload.get('task_id')}\n"
            f"Created by: {created_by}"
        ),
        "sent_at": datetime.utcnow().isoformat(),
        "event_id": event.event_id,
        "triggered_by": event.event_type
    }

    _sent_notifications.append(notification)
    print(f"  📧 [Notification] Email sent to {notification['to']}: "
          f"'{notification['subject']}'")


async def handle_task_completed(event: Event) -> None:
    """Send congratulations notification on task completion."""
    payload = event.payload
    completed_by = payload.get("completed_by", "unknown")
    title = payload.get("title", "Task")

    notification = {
        "type": "task_completed",
        "to": f"{completed_by}@company.com",
        "subject": f"✅ Task completed: {title}",
        "body": f"Great work! '{title}' has been marked complete.",
        "sent_at": datetime.utcnow().isoformat(),
        "event_id": event.event_id,
        "triggered_by": event.event_type
    }
    _sent_notifications.append(notification)
    print(f"  📧 [Notification] Completion email to {notification['to']}")


def get_notifications() -> list[dict]:
    return _sent_notifications.copy()


def register(bus=None):
    """Register all handlers with the event bus."""
    b = bus or event_bus
    b.subscribe("task.created",   "notification-service", handle_task_created)
    b.subscribe("task.completed", "notification-service", handle_task_completed)
    print("  ✅ Notification consumer registered")