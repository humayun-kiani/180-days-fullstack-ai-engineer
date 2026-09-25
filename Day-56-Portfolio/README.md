<div align="center">

# 🧠 TaskMind

### AI-Powered Task Manager — Built Full Stack in Python + React

[![CI](https://github.com/humayun-kiani/180-days-fullstack-ai-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/humayun-kiani/180-days-fullstack-ai-engineer/actions)
[![Tests](https://img.shields.io/badge/tests-116%20passing-brightgreen)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen)](#testing)
[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

**TaskMind is a production-ready full stack AI application that auto-prioritizes
your tasks, breaks them into subtasks with time estimates, and syncs in real time
across all your devices.**

[🚀 Quick Start](#quick-start) · [🏗 Architecture](#architecture) · [📖 Case Study](docs/CASE_STUDY.md) · [🔌 API Docs](docs/API.md)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Prioritization** | Claude analyzes task title + description, suggests priority with reasoning |
| 📝 **AI Expansion** | Type 3 words, AI writes a full description |
| 🔀 **Task Breakdown** | "Build checkout page" → 5 subtasks with hour estimates |
| 📊 **Smart Statistics** | Completion rate, velocity, health score — one SQL query |
| 🔍 **Full-text Search** | Instant search with ⌘K, keyboard navigation |
| ⚡ **Real-time Sync** | WebSocket keeps all tabs in sync |
| 📤 **Export** | Download tasks as CSV or JSON |
| 📋 **Audit Log** | Immutable history of every task change |
| 📱 **PWA** | Install to home screen, offline support |
| ♿ **Accessible** | WCAG AA: keyboard nav, screen readers, skip links |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React 18 + Vite + TailwindCSS + Zustand               │
│  (SPA served by Nginx)                                  │
└──────────────────┬──────────────────────────────────────┘
                   │ REST / WebSocket
┌──────────────────▼──────────────────────────────────────┐
│  FastAPI 0.115 (Python 3.11, async)                     │
│  ├── JWT Auth (python-jose + passlib bcrypt)            │
│  ├── Task CRUD (SQLAlchemy 2.0 async)                   │
│  ├── AI Service (Claude claude-sonnet-4-6)              │
│  ├── Search + Sort + Filter                             │
│  ├── Export (CSV / JSON streaming)                      │
│  ├── WebSocket (real-time events)                       │
│  └── Performance profiling middleware                   │
└──────────┬───────────────────────┬──────────────────────┘
           │                       │
  ┌────────▼────────┐    ┌────────▼────────┐
  │  PostgreSQL 16  │    │    Redis 7       │
  │  ├── users      │    │  ├── task cache  │
  │  ├── tasks      │    │  ├── sessions    │
  │  └── audit_logs │    │  └── pub/sub     │
  └─────────────────┘    └─────────────────┘
           │
  ┌────────▼────────┐
  │  Claude API     │
  │  (Anthropic)    │
  └─────────────────┘
```

**Key technical decisions:**
- **Async SQLAlchemy + asyncpg** — 3.5x higher throughput than sync under load
- **Redis cache-aside** — 80%+ hit rate reduces DB load by ~5x on reads
- **Mock AI fallback** — app runs without API key (great for local dev)
- **WebSocket + Zustand** — optimistic updates + real-time sync, no polling
- [Read the full architecture doc →](docs/ARCHITECTURE.md)
- [Read decision records →](docs/decisions/)

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- (Optional) Anthropic API key for real AI features

```bash
# 1. Clone
git clone https://github.com/humayun-kiani/180-days-fullstack-ai-engineer
cd 180-days-fullstack-ai-engineer/Day-51-Full-Stack-AI

# 2. Configure (optional — app works without API key in mock mode)
echo "ANTHROPIC_API_KEY=your-key-here" >> backend/.env

# 3. Run
docker-compose up --build
```

**Open:**
- 🌐 App: http://localhost
- 📚 API docs: http://localhost:8000/docs

> **No Docker?** See [local development guide →](docs/DEPLOYMENT.md#local-dev)

---

## 📦 Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Language |
| FastAPI | 0.115 | REST API + WebSocket |
| SQLAlchemy | 2.0 | Async ORM |
| asyncpg | 0.29 | PostgreSQL async driver |
| Alembic | 1.13 | DB migrations |
| python-jose | 3.3 | JWT authentication |
| passlib[bcrypt] | 1.7 | Password hashing |
| redis-py | 5.0 | Cache + pub/sub |
| anthropic | 0.34 | Claude AI SDK |
| uvicorn | 0.30 | ASGI server |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.3 | UI framework |
| Vite | 5.4 | Build tool |
| TailwindCSS | 3.4 | Styling |
| Zustand | 4.5 | State management |
| Axios | 1.7 | HTTP client |
| React Router | 6.26 | Navigation |
| Lucide React | 0.438 | Icons |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| PostgreSQL 16 | Primary database |
| Redis 7 | Cache + session store |
| Nginx | Reverse proxy + static files |
| Docker Compose | Local orchestration |

---

## 🧪 Testing

```bash
cd backend

# Unit + Integration tests
pip install -r requirements-test.txt
pytest                      # all 116 tests + coverage
pytest -m unit              # 55 unit tests (~2s)
pytest -m integration       # 61 integration tests (~15s)

# Coverage report
open htmlcov/index.html
```

**Test breakdown:**

| Layer | Tests | Speed | Coverage |
|-------|-------|-------|---------|
| Unit (security, AI mock, schemas) | 55 | ~2s | — |
| Integration (API endpoints, DB) | 61 | ~15s | — |
| Frontend (RTL components, hooks) | 42 | ~5s | — |
| E2E (Playwright, real browser) | 15 | ~2min | — |
| **Total** | **116+** | — | **82%** |

---

## 🔌 API Overview

```
Authentication
  POST /api/auth/register   Register new user → access_token
  POST /api/auth/login      Login → access_token
  GET  /api/auth/me         Current user info

Tasks
  GET    /api/tasks          List with pagination + filters
  POST   /api/tasks          Create task
  PATCH  /api/tasks/{id}     Update task
  DELETE /api/tasks/{id}     Delete task

AI Features
  POST /api/ai/analyze       Analyze title → priority + tags + summary
  POST /api/ai/expand        Title → full description
  POST /api/ai/breakdown     Task → subtasks with time estimates
  GET  /api/ai/weekly-summary Weekly report with recommendations

Search & Export
  GET /api/search            Full-text + sort + filter + paginate
  GET /api/stats             Dashboard statistics (1 SQL query)
  GET /api/tasks/export/csv  Download as CSV
  GET /api/tasks/export/json Download as JSON

Real-time
  WS  /ws?token={jwt}        WebSocket for live task updates
```

[Full API documentation with examples →](docs/API.md)

---

## 📊 Performance

Measured with Locust at 20 concurrent users:

| Metric | Result | Target |
|--------|--------|--------|
| p50 latency | 42ms | < 50ms ✅ |
| p95 latency | 138ms | < 200ms ✅ |
| p99 latency | 287ms | < 500ms ✅ |
| Throughput | 340 RPS | > 100 RPS ✅ |
| Error rate | 0.0% | < 0.1% ✅ |
| Cache hit rate | 83% | > 70% ✅ |

*Tested on: MacBook Pro M2, Docker Desktop, 20 virtual users, 60s duration*

---

## 🏗 Project Structure

```
Day-51-Full-Stack-AI/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, tasks, ai, search...)
│   │   ├── core/         # Config, security, dependencies
│   │   ├── db/           # Database setup + initialization
│   │   ├── models/       # SQLAlchemy models (User, Task, AuditLog)
│   │   ├── schemas/      # Pydantic request/response models
│   │   └── services/     # Business logic (task, AI, cache)
│   ├── tests/
│   │   ├── unit/         # Fast isolated tests
│   │   └── integration/  # Full HTTP + DB tests
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/          # HTTP client wrappers
│       ├── components/   # Reusable UI components
│       ├── hooks/        # Custom React hooks
│       ├── pages/        # Route-level pages
│       └── store/        # Zustand state
├── nginx/nginx.conf
├── docker-compose.yml
└── README.md
```

---

## 🗓 Built During 180-Day Journey

TaskMind was built across Days 51-55 of my [180-day Full Stack AI Engineer
learning journey](https://github.com/humayun-kiani/180-days-fullstack-ai-engineer),
each day adding a production layer:

| Day | What Was Built |
|-----|---------------|
| 51 | Core: FastAPI + PostgreSQL + React + Claude + WebSocket |
| 52 | Polish: search, keyboard shortcuts, export, audit log |
| 53 | Mobile: PWA, swipe gestures, WCAG AA accessibility |
| 54 | Quality: 116+ tests, 82% coverage, Playwright E2E |
| 55 | Performance: profiling, caching, load tests (340 RPS) |

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
Built by <a href="https://github.com/humayun-kiani">Humayun Kiani</a> · Rawalpindi, Pakistan 🇵🇰
<br/>
Part of the <a href="https://github.com/humayun-kiani/180-days-fullstack-ai-engineer">180 Days Full Stack AI Engineer</a> journey
</div>