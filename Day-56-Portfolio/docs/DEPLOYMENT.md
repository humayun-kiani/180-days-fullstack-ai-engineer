# TaskMind Deployment Guide

## Local Development (Docker)

```bash
# Clone and start
git clone https://github.com/humayun-kiani/180-days-fullstack-ai-engineer
cd Day-51-Full-Stack-AI

# Optional: configure AI
echo "ANTHROPIC_API_KEY=sk-ant-..." >> backend/.env

# Start everything
docker-compose up --build
```

Services:
| Service | URL |
|---------|-----|
| React App | http://localhost |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## Local Development (without Docker)

**Prerequisites:** Python 3.11+, Node 20+, PostgreSQL, Redis

```bash
# Terminal 1: PostgreSQL + Redis (Docker for just these)
docker-compose up db redis

# Terminal 2: Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # edit DATABASE_URL, REDIS_URL
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Environment Variables

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/taskmind
REDIS_URL=redis://localhost:6379
SECRET_KEY=change-this-to-random-256-bit-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ANTHROPIC_API_KEY=sk-ant-...     # optional — mock mode if not set
ENVIRONMENT=development
DEBUG=true
```

## Production Checklist

- [ ] Change `SECRET_KEY` to a cryptographically random value
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Configure PostgreSQL with proper credentials
- [ ] Set up Redis with authentication
- [ ] Add HTTPS (Let's Encrypt + Certbot)
- [ ] Configure rate limiting on AI endpoints
- [ ] Set up log aggregation (CloudWatch, Datadog)
- [ ] Add database backups
- [ ] Configure HPA in Kubernetes for auto-scaling