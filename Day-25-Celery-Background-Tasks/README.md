# Day 25 — Celery: Background Tasks, Task Queues & Scheduled Jobs

> **Phase 2 — Web Development** | Week 5 | Day 25 of 180

---

## 📌 What I Learned Today

- Why HTTP requests cannot run slow operations
- Task queue pattern: API → Broker → Worker → Result
- Celery architecture: broker, workers, result backend
- Redis as both broker and result backend
- @celery_app.task decorator — defining background tasks
- task.delay() — fire and forget task dispatch
- task.apply_async() — dispatch with countdown, priority, queue
- bind=True — access self for retry and progress update
- self.update_state(state, meta) — report progress to callers
- AsyncResult — check task status from any process
- Task states: PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
- max_retries and default_retry_delay — automatic retry config
- self.retry(exc, countdown) — retry with backoff
- Exponential backoff: 30s, 60s, 120s delays
- task_routes — send different tasks to different queues
- Multiple queues: emails, reports, notifications, maintenance
- Celery Beat — cron-style task scheduling
- crontab(hour=8, minute=0) — daily at 8 AM
- crontab(day_of_week="monday") — weekly on Monday
- celery_app.control.inspect() — inspect live workers
- Flower — real-time Celery monitoring dashboard
- worker_send_task_events=True — enable Flower monitoring
- FastAPI + Celery integration: endpoint returns task_id
- Progress tracking: poll GET /tasks/{id}/status
- task_acks_late=True — safer acknowledgment on completion

## 🔨 Project Built

**Background Email & Report Worker** — Full Celery system:

- 4 task modules with 9 distinct tasks:
  - emails: welcome email, task completion notification,
    daily digest, overdue alerts
  - reports: task report generation with progress, weekly summary
  - notifications: overdue check with grouped alerts by user
  - maintenance: health check, result cleanup, diagnostics
- Celery Beat schedule:
  - Every 30 min: check overdue tasks and send alerts
  - 8 AM daily: send daily digest emails
  - Monday 9 AM: generate weekly summary
  - 1st of month midnight: cleanup
  - Every 5 min: health check
- 4 separate queues: emails, reports, notifications, maintenance
- Task chaining for report pipeline
- Exponential backoff retry: 30s → 60s → 120s
- Progress updates via self.update_state() for long tasks
- FastAPI endpoints: register, complete task, generate report,
  trigger admin tasks, check worker stats
- Flower dashboard at port 5555

## 🚀 How to Run

```bash
# Start Redis
docker compose up -d

cd Day-25-Celery-Background-Tasks
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Terminal 1: Celery worker
celery -A worker.celery_app worker --loglevel=info \
  -Q emails,reports,notifications,maintenance

# Terminal 2: Flower monitor
celery -A worker.celery_app flower --port=5555

# Terminal 3: FastAPI
uvicorn app.main:app --reload --port 8000

# Open:
# http://localhost:8000/docs   — API docs
# http://localhost:5555        — Flower monitor
```

## 🧠 Key Celery Patterns

| Pattern         | Code                                                         |
| --------------- | ------------------------------------------------------------ |
| Define task     | `@celery_app.task(bind=True, max_retries=3)`                 |
| Fire and forget | `task.delay(arg1, arg2)`                                     |
| With options    | `task.apply_async(args=[...], queue="emails", countdown=30)` |
| Check status    | `AsyncResult(task_id, app=celery_app).status`                |
| Progress update | `self.update_state(state="PROGRESS", meta={...})`            |
| Retry           | `raise self.retry(exc=exc, countdown=60)`                    |
| Schedule        | `crontab(hour=8, minute=0)`                                  |
| Chain           | `chain(task1.s(), task2.s()).delay()`                        |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
