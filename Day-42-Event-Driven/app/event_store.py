# ============================================================
# app/event_store.py
# Event store — persists all events (event sourcing preview)
# ============================================================

from datetime import datetime
from app.event_bus import Event


class EventStore:
    """
    Immutable append-only log of all events.

    This is the foundation of Event Sourcing:
    "Store what HAPPENED, not what IS."

    Benefits:
    - Complete audit trail
    - Replay events to rebuild state
    - Time travel: what was the state at time X?
    - Debugging: see exactly what happened and when
    """

    def __init__(self):
        self._events: list[dict] = []

    def append(self, event: Event) -> None:
        """Append an event to the store (immutable — never delete)."""
        self._events.append({
            **event.to_dict(),
            "stored_at": datetime.utcnow().isoformat()
        })

    def get_all(self, event_type: str | None = None) -> list[dict]:
        """Return all events, optionally filtered by type."""
        if event_type:
            return [e for e in self._events if e["event_type"] == event_type]
        return self._events.copy()

    def get_for_task(self, task_id: str) -> list[dict]:
        """Return all events related to a specific task."""
        return [
            e for e in self._events
            if e.get("payload", {}).get("task_id") == task_id
        ]

    def replay_task_state(self, task_id: str) -> dict | None:
        """
        Rebuild current task state from events.

        This is the core of Event Sourcing — the event log IS the truth.
        The task table in the DB is just a read-optimized projection.
        """
        task_events = self.get_for_task(task_id)
        if not task_events:
            return None

        state = {}
        for event in sorted(task_events, key=lambda e: e["timestamp"]):
            event_type = event["event_type"]
            payload = event.get("payload", {})

            if event_type == "task.created":
                state = {
                    "task_id": task_id,
                    "title": payload.get("title"),
                    "priority": payload.get("priority"),
                    "status": "pending",
                    "created_at": event["timestamp"],
                    "events_applied": 1
                }
            elif event_type == "task.updated":
                state.update({
                    k: v for k, v in payload.items()
                    if k != "task_id"
                })
                state["events_applied"] = state.get("events_applied", 0) + 1
            elif event_type == "task.completed":
                state["status"] = "done"
                state["completed_at"] = event["timestamp"]
                state["events_applied"] = state.get("events_applied", 0) + 1
            elif event_type == "task.deleted":
                return None    # Task was deleted

        return state

    def stats(self) -> dict:
        from collections import Counter
        counts = Counter(e["event_type"] for e in self._events)
        return {
            "total_events": len(self._events),
            "by_type": dict(counts)
        }


# Global event store
event_store = EventStore()