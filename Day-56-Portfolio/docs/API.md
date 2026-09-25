# TaskMind API Documentation

Base URL: `http://localhost:8000`  
Authentication: `Authorization: Bearer {access_token}`

---

## Authentication

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "humayun@example.com",
  "name": "Humayun",
  "password": "securepassword123"
}
```
Response `201`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "humayun@example.com",
    "name": "Humayun",
    "created_at": "2025-05-27T10:00:00Z"
  }
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/json

{"email": "humayun@example.com", "password": "securepassword123"}
```
Response `200`: same as register response.

---

## Tasks

### List Tasks
```http
GET /api/tasks?status=pending&priority=high&page=1&per_page=20
Authorization: Bearer {token}
```
Response `200`:
```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Fix auth bug",
      "description": "...",
      "status": "pending",
      "priority": "high",
      "ai_summary": "High-priority authentication fix needed",
      "due_date": null,
      "created_at": "2025-05-27T10:00:00Z",
      "updated_at": "2025-05-27T10:00:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### Create Task
```http
POST /api/tasks
Authorization: Bearer {token}

{"title": "Fix login bug", "description": "...", "priority": "high"}
```
Response `201`: task object.

### Update Task
```http
PATCH /api/tasks/{id}
Authorization: Bearer {token}

{"status": "in_progress", "priority": "urgent"}
```

### Delete Task
```http
DELETE /api/tasks/{id}
Authorization: Bearer {token}
```
Response `204`: no content.

---

## AI Features

### Analyze Task
```http
POST /api/ai/analyze
Authorization: Bearer {token}

{"title": "URGENT: Production database down", "description": "All users affected"}
```
Response `200`:
```json
{
  "suggested_priority": "urgent",
  "confidence": "high",
  "reasoning": "Title contains 'URGENT' and describes a production outage",
  "suggested_tags": ["production", "incident", "database"],
  "summary": "Critical production database outage affecting all users",
  "estimated_hours": 2.0
}
```

### Expand Task
```http
POST /api/ai/expand
Authorization: Bearer {token}

{"title": "Add dark mode"}
```
Response `200`:
```json
{
  "description": "Implement a dark color theme across all UI components...",
  "suggested_priority": "medium",
  "suggested_tags": ["ui", "design", "theme"]
}
```

### Break Down Task
```http
POST /api/ai/breakdown
Authorization: Bearer {token}

{"title": "Build checkout page", "description": "E-commerce checkout flow"}
```
Response `200`:
```json
{
  "subtasks": [
    {"title": "Design checkout layout", "estimated_hours": 2.0, "priority": "high"},
    {"title": "Implement cart summary", "estimated_hours": 3.0, "priority": "high"},
    {"title": "Add payment form", "estimated_hours": 4.0, "priority": "high"},
    {"title": "Write checkout tests", "estimated_hours": 2.0, "priority": "medium"}
  ],
  "total_estimated_hours": 11.0
}
```

---

## Search

```http
GET /api/search?q=login&priority=high&sort_by=created_at&sort_dir=desc&page=1
Authorization: Bearer {token}
```

Parameters:
| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (title + description) |
| `status` | string | Filter: pending, in_progress, done |
| `priority` | string | Filter: urgent, high, medium, low |
| `sort_by` | string | created_at, updated_at, priority, title, due_date |
| `sort_dir` | string | asc or desc |
| `overdue_only` | bool | Only show overdue tasks |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20, max: 100) |

---

## WebSocket

```
WS ws://localhost:8000/ws?token={access_token}
```

Events received:
```json
{"type": "connected", "user_id": "uuid", "timestamp": "..."}
{"type": "task_created", "task": {...}}
{"type": "task_updated", "task": {...}}
{"type": "task_deleted", "task_id": "uuid"}
{"type": "keepalive"}
```

Client should respond to `keepalive` with `{"type": "ping"}`.