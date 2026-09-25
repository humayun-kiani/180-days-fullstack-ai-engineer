# TaskMind Architecture

## Overview

TaskMind is a full stack AI application built with:
- **React 18** frontend (SPA)
- **FastAPI** backend (async Python)
- **PostgreSQL 16** primary database
- **Redis 7** cache and session store
- **Claude** (Anthropic) AI integration

## System Diagram

```mermaid
graph TD
    Browser["🌐 Browser\nReact SPA"]
    Nginx["Nginx\nReverse proxy"]
    API["FastAPI\n(Python 3.11 async)"]
    DB[("PostgreSQL 16\ntasks + users + audit")]
    Redis[("Redis 7\ncache + pub/sub")]
    Claude["Claude API\nAnthropic"]

    Browser -->|HTTP| Nginx
    Browser -->|WebSocket| Nginx
    Nginx -->|/api + /ws| API
    Nginx -->|static| Browser
    API -->|asyncpg| DB
    API -->|redis-py async| Redis
    API -->|HTTPS| Claude

    style Browser fill:#1e3a5f,color:#fff
    style API fill:#009688,color:#fff
    style DB fill:#336791,color:#fff
    style Redis fill:#DC382D,color:#fff
    style Claude fill:#FF6B35,color:#fff
```

## Request Flow — Task Creation

```mermaid
sequenceDiagram
    participant B as Browser
    participant N as Nginx
    participant A as FastAPI
    participant D as PostgreSQL
    participant R as Redis
    participant W as WebSocket

    B->>N: POST /api/tasks {title, priority}
    N->>A: Forward request
    A->>A: Validate JWT (decode_token)
    A->>D: INSERT INTO tasks (async)
    D-->>A: task row
    A->>R: DEL tasks:{user_id}:* (invalidate cache)
    A->>W: Broadcast {type: task_created, task}
    A-->>N: 201 {task}
    N-->>B: 201 {task}
    W-->>B: WS event (if other tabs open)
```

## Database Schema

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar name
        varchar password_hash
        timestamptz created_at
        timestamptz updated_at
    }

    tasks {
        uuid id PK
        varchar title
        text description
        varchar status
        varchar priority
        uuid owner_id FK
        text ai_summary
        varchar ai_priority
        timestamptz due_date
        timestamptz created_at
        timestamptz updated_at
    }

    task_audit_logs {
        uuid id PK
        uuid task_id FK
        uuid user_id FK
        varchar action
        json changed_fields
        json old_values
        json new_values
        varchar user_name
        timestamptz created_at
    }

    users ||--o{ tasks : "owns"
    tasks ||--o{ task_audit_logs : "has history"
    users ||--o{ task_audit_logs : "made change"
```

## Key Indexes

```sql
-- Task listing (most common query)
CREATE INDEX idx_tasks_owner_created
    ON tasks(owner_id, created_at DESC);

-- Status filtering
CREATE INDEX idx_tasks_status ON tasks(status);

-- Priority filtering
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Audit log lookup
CREATE INDEX idx_audit_task_id ON task_audit_logs(task_id);
CREATE INDEX idx_audit_created ON task_audit_logs(created_at DESC);
```

## Caching Strategy

```
Cache-aside pattern:

READ:
  key = "tasks:{user_id}:{status}:{priority}:{page}"
  result = cache.get(key)
  if result: return result          # cache HIT (~0.2ms)
  result = db.query(...)            # cache MISS (~15ms)
  cache.set(key, result, ttl=30)
  return result

WRITE (create/update/delete):
  db.execute(...)
  cache.delete_pattern("tasks:{user_id}:*")  # invalidate all pages

TTL by data type:
  task lists:      30s   (freshness vs load balance)
  task stats:     300s   (expensive query, slow-changing)
  AI analysis:   3600s   (same title = same result)
  weekly summary:  900s  (expensive AI call, 15min ok)
```

## AI Integration

```
All AI endpoints have a mock fallback:

if ANTHROPIC_API_KEY not set:
    return mock_response()   # keyword-based, instant, free

if api_call fails:
    return mock_response()   # graceful degradation

This means:
  - App works in local dev without any API key
  - App continues working if Anthropic has an outage
  - CI/CD tests pass without secrets
  - Demo can be run without spending API credits
```

## Authentication Flow

```
JWT (JSON Web Token) — stateless authentication

1. POST /api/auth/login {email, password}
   → verify bcrypt hash
   → create JWT: {sub: user_id, exp: now + 60min}
   → return {access_token: "eyJ..."}

2. Every protected request:
   → Authorization: Bearer eyJ...
   → decode_token(token) → user_id
   → SELECT * FROM users WHERE id = user_id

Why stateless JWT (not sessions):
   → No server-side session storage needed
   → Works with multiple API workers (no shared session state)
   → Scales horizontally
   Tradeoff: can't instantly revoke tokens (use Redis blacklist for that)
```

## WebSocket Architecture

```
Connection lifecycle:
  1. Browser connects: WS /ws?token={jwt}
  2. Server decodes token → validates user
  3. ConnectionManager.connect(ws, user_id)
  4. Keepalive: server sends "keepalive" every 30s
     Browser responds with "ping"
  5. On task change: ConnectionManager.send_to_user(user_id, event)
  6. All open tabs receive the event → React state updates

Storage:
  _connections: dict[user_id → set[WebSocket]]
  In-memory (per process)

Scale concern:
  With multiple API workers, each worker has its own ConnectionManager.
  Fix for production: use Redis pub/sub to broadcast across workers.
```