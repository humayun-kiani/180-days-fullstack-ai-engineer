# Day 21 — FastAPI + SQLAlchemy + PostgreSQL: Database-Backed APIs

> **Phase 2 — Web Development** | Week 4 | Day 21 of 180

---

## 📌 What I Learned Today

- Production FastAPI project architecture (5-layer separation)
- Why SQLAlchemy models and Pydantic schemas are separate
- Pydantic Settings (pydantic-settings) for configuration
- @property DATABASE_URL from env vars
- @lru_cache on settings to avoid repeated .env reads
- SQLAlchemy engine with pool_size, max_overflow, pool_pre_ping
- SessionLocal factory with autocommit=False, expire_on_commit=False
- get_db() dependency with commit/rollback/close lifecycle
- Generic CRUDBase class with TypeVar and Generic
- model_dump(exclude_unset=True) for PATCH updates
- db.flush() vs db.commit() — write without finalizing
- Advanced SQLAlchemy filtering: ilike, not_in, is_not, contains
- JOIN loading with joinedload() and selectinload()
- Soft delete pattern — is_deleted + status = archived
- Bulk update with db.query.update() and synchronize_session
- Alembic setup: init, env.py config, autogenerate, upgrade head
- Routers organized under /api/v1/ prefix
- Annotated type aliases for DB, CurrentUser, PageParams
- BackgroundTasks for async audit logging
- Nested resource endpoint: GET /projects/{id}/tasks
- Bulk complete endpoint: POST /tasks/bulk/complete
- PostgreSQL ILIKE for case-insensitive search
- JSON column type for tags array in PostgreSQL
- Migration versioning: alembic upgrade head / downgrade -1

## 🔨 Project Built

**Database-Backed Task Manager v2.0** — Full stack API:

- 5-layer architecture: api, schemas, crud, db/models, core
- 3 SQLAlchemy models: User, Project, Task with relationships
- Generic CRUDBase class inherited by CRUDTask and CRUDProject
- CRUDTask: 8 specialized query methods including overdue, upcoming
- CRUDProject: project stats aggregation with func.count
- Alembic migration with indexes for all FK and filter columns
- 20+ endpoints across 4 routers under /api/v1/
- Soft delete: DELETE archives task, ?hard=true removes it
- Bulk complete: POST /tasks/bulk/complete with list of IDs
- PATCH /tasks/{id}/complete shortcut
- GET /tasks/upcoming?days=7 — tasks due within N days
- GET /projects/{id}/stats — project completion analytics
- Full filtering: status, priority, project, owner, search, tag, overdue
- Pagination with has_next, has_prev, total, pages
- Request timing middleware with X-Process-Time-Ms header
- Background audit logging for all task mutations
- Seed script with 3 users, 3 projects, 8 tasks

## 🚀 How to Run

```bash
# 1. Setup PostgreSQL
psql -U postgres
CREATE DATABASE taskmanager;
CREATE USER taskuser WITH PASSWORD 'taskpass';
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskuser;
\c taskmanager
GRANT ALL ON SCHEMA public TO taskuser;
\q

# 2. Install and configure
cd Day-21-FastAPI-Database
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 3. Run migrations
alembic upgrade head

# 4. Seed data
python seed.py

# 5. Start API
uvicorn app.main:app --reload

# Open: http://localhost:8000/docs
```

## 🧠 Architecture Pattern

```
HTTP Request
    ↓
FastAPI Router (app/api/v1/)
    ↓ validates with
Pydantic Schema (app/schemas/)
    ↓ calls
CRUD Layer (app/crud/)
    ↓ queries using
SQLAlchemy Model (app/db/models/)
    ↓
PostgreSQL Database
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
