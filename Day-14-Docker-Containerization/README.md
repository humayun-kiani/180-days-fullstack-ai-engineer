# Day 14 — Docker: Containerization, Docker Compose & Production Deployment

> **Phase 1 — Foundations** | Week 2 | Day 14 of 180

---

## 📌 What I Learned Today

- What Docker is — containers vs virtual machines
- Images vs containers — the blueprint vs the running instance
- Essential Docker commands: pull, build, run, stop, rm, logs, exec
- Dockerfile instructions: FROM, WORKDIR, COPY, RUN, CMD, EXPOSE
- Layer caching — ordering instructions for fast rebuilds
- Multi-stage builds — builder stage vs final minimal image
- .dockerignore — exclude unnecessary files from build context
- Running as non-root user for container security
- Docker Compose — orchestrating multiple containers
- docker-compose.yml: services, ports, volumes, networks, env
- depends_on with condition: service_healthy — wait for health checks
- Health checks — test, interval, timeout, retries, start_period
- Named volumes — data persists across container restarts
- Bind mounts — mount host directory into container for dev
- Docker networking — containers talk by service name
- Environment variables — env_file and environment in compose
- profiles — optional services only started when requested

## 🔨 Project Built

**Containerized Expense Tracker with FastAPI + PostgreSQL + Redis:**

- Multi-stage Dockerfile: 180MB image vs 920MB naive build
- FastAPI API with full CRUD for expenses
- PostgreSQL: all expense data stored in containerized DB
- Redis: caches API responses for 5 minutes
- pgAdmin: web GUI for PostgreSQL (started with --profile tools)
- Health checks on all services
- api waits for db AND cache to be healthy before starting
- Data persists in named Docker volumes across restarts
- All service communication via internal Docker network
- .env file for all secrets (gitignored)
- Development override with hot reload
- Nginx reverse proxy configuration included
- Full Swagger UI at /docs

## 🚀 How to Run

```bash
cd Day-14-Docker-Containerization

# Copy and configure environment
cp .env.example .env

# Start all services (builds API image first)
docker compose up --build

# Access:
# API:     http://localhost:8000
# Swagger: http://localhost:8000/docs
# Health:  http://localhost:8000/health

# With pgAdmin database GUI:
docker compose --profile tools up -d
# pgAdmin: http://localhost:5050

# Stop everything
docker compose down

# Stop and delete all data
docker compose down -v
```

## 🧠 Key Concepts

| Concept              | Command/Syntax                   |
| -------------------- | -------------------------------- |
| Build image          | `docker build -t name .`         |
| Run container        | `docker run -p 8000:8000 name`   |
| Shell into container | `docker exec -it name bash`      |
| See logs             | `docker compose logs -f service` |
| Start compose        | `docker compose up -d`           |
| Stop compose         | `docker compose down`            |
| Named volume         | `volume_name:/path/in/container` |
| Bind mount           | `./host/path:/container/path`    |
| Service networking   | Use service name as hostname     |
| Health check         | `pg_isready -U user -d db`       |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
