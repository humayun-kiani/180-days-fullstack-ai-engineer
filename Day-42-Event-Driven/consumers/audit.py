# ============================================================
# consumers/audit.py
# Audit consumer — compliance log of all events
# ============================================================

from datetime import datetime
from app.event_bus import Event, event_bus


_audit_log: list[dict] = []


async def handle_any_task_event(event: Event) -> None:
    """
    Log every task event for compliance and auditing.

    This consumer handles ALL task.* events.
    Audit logs are immutable — never delete.
    """
    entry = {
        "audit_id": f"audit-{len(_audit_log) + 1:04d}",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "logged_at": datetime.utcnow().isoformat(),
        "source": event.source,
        "payload_summary": {
            "task_id": event.payload.get("task_id"),
            "title": event.payload.get("title", "")[:50],
            "actor": (
                event.payload.get("created_by") or
                event.payload.get("updated_by") or
                event.payload.get("completed_by") or
                event.payload.get("deleted_by") or
                "system"
            )
        }
    }
    _audit_log.append(entry)
    print(f"  📋 [Audit] {entry['audit_id']}: {event.event_type} "
          f"by {entry['payload_summary']['actor']}")


def get_audit_log() -> list[dict]:
    return _audit_log.copy()


def register(bus=None):
    """Register audit handler for all task events."""
    b = bus or event_bus
    # Subscribe to ALL task event types
    for event_type in [
        "task.created", "task.updated",
        "task.completed", "task.deleted"
    ]:
        b.subscribe(event_type, "audit-service", handle_any_task_event)
    print("  ✅ Audit consumer registered (all task events)")