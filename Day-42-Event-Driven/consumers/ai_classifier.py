# ============================================================
# consumers/ai_classifier.py
# AI consumer — classifies task priority asynchronously
# ============================================================

import asyncio
from datetime import datetime
from app.event_bus import Event, event_bus
from app import tasks as task_store


# Simple keyword classifier (no LLM needed for demo)
def _classify(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["urgent", "critical", "down", "outage", "breach"]):
        return "urgent"
    if any(w in t for w in ["fix", "bug", "error", "before", "deadline"]):
        return "high"
    if any(w in t for w in ["add", "implement", "feature", "create"]):
        return "medium"
    return "low"


_classification_log: list[dict] = []


async def handle_task_created_for_ai(event: Event) -> None:
    """
    Asynchronously classify task priority when a task is created.

    Only reclassifies if priority was not explicitly set (default "medium").
    """
    payload = event.payload
    task_id = payload.get("task_id")
    title = payload.get("title", "")
    current_priority = payload.get("priority", "medium")

    # Small delay to simulate async processing
    await asyncio.sleep(0.01)

    suggested_priority = _classify(title)

    log_entry = {
        "task_id": task_id,
        "title": title[:50],
        "original_priority": current_priority,
        "suggested_priority": suggested_priority,
        "changed": suggested_priority != current_priority,
        "classified_at": datetime.utcnow().isoformat(),
        "event_id": event.event_id
    }
    _classification_log.append(log_entry)

    if suggested_priority != current_priority:
        # Update task with AI-suggested priority
        await task_store.update_task(
            task_id,
            {"priority": suggested_priority,
             "priority_source": "ai-classifier"},
            updated_by="ai-classifier"
        )
        print(f"  🤖 [AI] Reclassified task {task_id}: "
              f"{current_priority} → {suggested_priority}")
    else:
        print(f"  🤖 [AI] Priority confirmed: {suggested_priority} "
              f"for '{title[:30]}...'")


def get_classifications() -> list[dict]:
    return _classification_log.copy()


def register(bus=None):
    """Register all handlers with the event bus."""
    b = bus or event_bus
    b.subscribe("task.created", "ai-classifier", handle_task_created_for_ai)
    print("  ✅ AI classifier consumer registered")