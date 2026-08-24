# ============================================================
# app/event_bus.py
# In-memory event bus with Redis Streams compatibility
# ============================================================

import asyncio
import json
import uuid
import time
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any

# Try Redis Streams, fall back to in-memory
try:
    import redis
    _r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    _r.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False


# ─── Event Schema ─────────────────────────────────────────────

@dataclass
class Event:
    """Standard event envelope."""
    event_type: str
    payload: dict
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "task-service"
    version: str = "1.0"
    correlation_id: str | None = None    # links related events

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "version": self.version,
            "correlation_id": self.correlation_id,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(
            event_type=d["event_type"],
            payload=d["payload"],
            event_id=d.get("event_id", str(uuid.uuid4())[:8]),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat()),
            source=d.get("source", "unknown"),
            version=d.get("version", "1.0"),
            correlation_id=d.get("correlation_id")
        )


# ─── Dead Letter Queue ────────────────────────────────────────

@dataclass
class DLQEntry:
    """A message that failed processing."""
    event: Event
    consumer: str
    error: str
    attempts: int
    failed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class DeadLetterQueue:
    """Stores messages that failed processing after max retries."""

    def __init__(self):
        self._entries: list[DLQEntry] = []

    def add(self, event: Event, consumer: str, error: str, attempts: int):
        entry = DLQEntry(event=event, consumer=consumer,
                        error=error, attempts=attempts)
        self._entries.append(entry)

    def get_all(self) -> list[dict]:
        return [
            {
                "event": e.event.to_dict(),
                "consumer": e.consumer,
                "error": e.error,
                "attempts": e.attempts,
                "failed_at": e.failed_at
            }
            for e in self._entries
        ]

    def count(self) -> int:
        return len(self._entries)


# ─── Event Bus ────────────────────────────────────────────────

HandlerFn = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Production-grade event bus with:
    - Subscriber registration
    - Retry with exponential backoff
    - Dead letter queue for failed messages
    - Processing statistics
    - Idempotency tracking
    """

    MAX_RETRIES = 3

    def __init__(self):
        self._subscribers: dict[str, list[tuple[str, HandlerFn]]] = defaultdict(list)
        self._processed: dict[str, set[str]] = defaultdict(set)  # consumer → event_ids
        self._dlq = DeadLetterQueue()
        self._stats = {
            "published": 0,
            "processed_ok": 0,
            "failed": 0,
            "dlq_count": 0,
            "duplicate_skipped": 0
        }
        self._redis_stream = "task-events"

    def subscribe(self, event_type: str, consumer_name: str, handler: HandlerFn) -> None:
        """
        Register a consumer handler for an event type.

        Args:
            event_type: Event type to listen for (e.g. "task.created")
            consumer_name: Unique name for this consumer (for idempotency)
            handler: Async function to call with the event
        """
        self._subscribers[event_type].append((consumer_name, handler))

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        Each subscriber runs independently — one failure doesn't
        prevent others from processing.
        """
        self._stats["published"] += 1

        if REDIS_AVAILABLE:
            await self._publish_to_redis(event)
        else:
            await self._publish_in_memory(event)

    async def _publish_to_redis(self, event: Event) -> None:
        """Publish to Redis Stream."""
        data = {"data": json.dumps(event.to_dict())}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: _r.xadd(self._redis_stream, data)
        )
        # Also deliver in-memory for immediate handlers
        await self._deliver_to_handlers(event)

    async def _publish_in_memory(self, event: Event) -> None:
        """Deliver directly to in-memory handlers."""
        await self._deliver_to_handlers(event)

    async def _deliver_to_handlers(self, event: Event) -> None:
        """Deliver event to all registered handlers."""
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            return

        tasks = [
            self._process_with_retry(event, consumer_name, handler)
            for consumer_name, handler in handlers
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_with_retry(
        self,
        event: Event,
        consumer_name: str,
        handler: HandlerFn
    ) -> None:
        """Process event with retry + idempotency + DLQ."""

        # Idempotency check
        if event.event_id in self._processed[consumer_name]:
            self._stats["duplicate_skipped"] += 1
            return

        # Retry loop
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                await handler(event)
                # Mark as processed
                self._processed[consumer_name].add(event.event_id)
                self._stats["processed_ok"] += 1
                return

            except Exception as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES - 1:
                    delay = 2 ** attempt    # 1s, 2s, 4s
                    await asyncio.sleep(delay)

        # All retries exhausted — send to DLQ
        self._dlq.add(
            event=event,
            consumer=consumer_name,
            error=last_error or "Unknown error",
            attempts=self.MAX_RETRIES
        )
        self._stats["failed"] += 1
        self._stats["dlq_count"] += 1

    def get_stats(self) -> dict:
        return {
            **self._stats,
            "subscriber_count": sum(
                len(v) for v in self._subscribers.values()
            ),
            "redis_available": REDIS_AVAILABLE,
            "dlq_messages": self._dlq.count()
        }

    def get_dlq(self) -> list[dict]:
        return self._dlq.get_all()

    def get_subscribers(self) -> dict:
        return {
            event_type: [name for name, _ in handlers]
            for event_type, handlers in self._subscribers.items()
        }


# Global event bus instance
event_bus = EventBus()