# Day 42 — Event-Driven Architecture & Message Queues

> **Phase 5 — System Design & Architecture** | Week 8 | Day 42 of 180

---

## 📌 What I Learned Today

- EDA vs request-response: decouple producers from consumers
- Producer: publishes events, doesn't know who consumes
- Consumer: subscribes to event types, processes independently
- Topic/Stream: ordered, persistent channel for events
- Consumer group: multiple instances share work, each message once
- At-least-once delivery: duplicates possible, consumers must be idempotent
- Exactly-once: distributed transactions, too complex, use idempotency instead
- At-most-once: fire and forget, events may be lost
- Dead letter queue: failed messages after max retries
- Idempotency: safe to process same event twice (event_id as key)
- Redis XADD: append to stream, auto-generate timestamp-based ID
- Redis XREAD: read messages newer than given ID, block if empty
- Redis XREADGROUP: read for specific consumer in a group
- Redis XACK: acknowledge successful processing
- Redis XAUTOCLAIM: reclaim idle messages from crashed consumers
- Event schema: event_id, event_type, timestamp, source, version, payload
- Schema versioning: use .get() for optional new fields (backward compat)
- Event store: append-only log, never delete (immutable audit trail)
- Event Sourcing: store WHAT HAPPENED not WHAT IS
- replay_task_state(): rebuild current state by replaying all events
- asyncio.gather() with return_exceptions=True: one handler failure doesn't block others
- Exponential backoff: 2^attempt seconds between retries
- DLQEntry dataclass: store failed message + error + attempts
- Consumer registration: subscribe() with consumer_name for idempotency tracking
- InMemoryEventBus: usable without Redis, great for testing

## 🔨 Project Built

**Async Task Event System:**

**EventBus** (app/event_bus.py):

- subscribe(event_type, consumer_name, handler)
- publish(event): fan-out to all subscribers
- \_process_with_retry: 3 attempts with exponential backoff
- Idempotency: per-consumer set of processed event_ids
- DLQ: events that fail all retries
- Redis Streams mode when Redis available, in-memory otherwise
- get_stats(): published/processed/failed/dlq counts

**EventStore** (app/event_store.py):

- append(event): immutable append to log
- get_all(event_type): filtered event retrieval
- get_for_task(task_id): all events for one task
- replay_task_state(task_id): rebuild state from event history

**3 Consumers:**

- notification.py: email per task.created + task.completed
- ai_classifier.py: reclassify priority on task.created
- audit.py: immutable log entry for ALL task.\* events

**Event Types:** task.created, task.updated, task.completed, task.deleted

**FastAPI Endpoints:**

- POST /tasks: create + publish event to 3 consumers
- POST /tasks/{id}/complete: complete + publish
- GET /events: full event store
- GET /events/replay/{id}: Event Sourcing demo
- GET /consumers/notifications, /ai, /audit: consumer output
- GET /events/dlq: dead letter queue
- GET /events/bus: event bus stats + subscribers

## 🚀 How to Run

```bash
cd Day-42-Event-Driven
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# Create a task — watch 3 consumers fire in terminal output
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "URGENT: Production API down", "created_by": "humayun"}'

# See all events
curl http://localhost:8000/events

# See audit trail
curl http://localhost:8000/consumers/audit
```

## 🧠 Key Pattern: Producer → Queue → Consumers

```
task_db.create_task()
    │ publishes event
    ▼
event_bus.publish(Event("task.created", payload))
    │ fan-out
    ├──▶ notification consumer → email
    ├──▶ ai_classifier consumer → reclassify
    └──▶ audit consumer → compliance log

All 3 run concurrently. Failure in one doesn't affect others.
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
