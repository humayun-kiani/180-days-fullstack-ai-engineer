# Day 51 — Full Stack AI Application

> **Phase 7 — Full Stack Integration & Portfolio Projects** | Day 51 of 180

---

## 📌 What I Learned Today

- Full stack architecture: React → FastAPI → PostgreSQL → Redis → Claude
- Docker Compose multi-service: db + redis + backend + frontend + nginx
- SQLAlchemy async: AsyncSession, create_async_engine, async_sessionmaker
- Mapped columns: Mapped[str] = mapped_column(...) for typed ORM
- Async routes with Depends: DB = Annotated[AsyncSession, Depends(get_db)]
- JWT middleware: HTTPBearer + decode_token in every protected route
- Redis caching: cache list results, invalidate on write (cache_delete_pattern)
- AI service: analyze/expand/breakdown/weekly-summary with Claude + mock fallback
- WebSocket manager: track user connections, broadcast events
- React + Vite: modern frontend build setup with proxy to backend
- Zustand: lightweight state management (authStore)
- Axios interceptors: attach JWT, handle 401 → redirect to login
- Kanban board: three columns (To Do, In Progress, Done) from task status
- AI features: expand title → full description, prioritize, breakdown subtasks
- Nginx: proxy /api and /ws, serve React static files
- CORS: allow frontend origins in FastAPI middleware
- Pydantic-settings: read config from .env file with type validation
- Pagination: page + per_page + total + pages in list response
- Consistent error format: {detail: "message"} for all HTTPException

## 🔨 Project Built

**TaskMind** — Full Stack AI Task Manager:

**Backend (FastAPI + PostgreSQL + Redis + Claude):**

- POST /api/auth/register + login: JWT auth
- GET/POST /api/tasks: paginated task CRUD
- PATCH/DELETE /api/tasks/{id}: update + delete
- POST /api/ai/analyze: priority + tags + summary
- POST /api/ai/expand: brief title → full description
- POST /api/ai/breakdown: task → 3-6 subtasks with hours
- GET /api/ai/weekly-summary: stats + recommendations
- WS /ws?token=...: real-time task updates

**Frontend (React + Vite + TailwindCSS):**

- Login/Register page with dark theme
- Kanban board: 3 columns by status
- TaskCard: expand, change status, AI analyze, delete
- TaskForm: create with AI expand + AI prioritize buttons
- AIPanel: weekly summary + task breakdown
- WebSocket for real-time updates

## 🚀 How to Run

```bash
cd Day-51-Full-Stack-AI

# Full stack with Docker:
docker-compose up --build
# Open http://localhost (React UI)
# Open http://localhost:8000/docs (API)

# Or dev mode:
docker-compose up db redis          # Terminal 1
cd backend && uvicorn app.main:app --reload  # Terminal 2
cd frontend && npm install && npm run dev    # Terminal 3
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
