#!/bin/bash
# ============================================================
# scripts/deploy.sh
# First-time deployment script
#
# Run on server after git clone:
#   git clone your-repo
#   cd your-repo
#   cp .env.production.example .env
#   nano .env    # fill in all values
#   chmod +x scripts/*.sh
#   ./scripts/deploy.sh
# ============================================================

set -e

echo "================================================="
echo "  Task Manager API — First Deployment"
echo "  Day 26 — 180-Day Full Stack AI Engineer Roadmap"
echo "================================================="

# ── Validate environment ──────────────────────────────────
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Copy .env.production.example to .env and fill in values"
    exit 1
fi

source .env

if [ "${POSTGRES_PASSWORD}" = "CHANGE_ME_STRONG_PASSWORD_HERE" ]; then
    echo "❌ You haven't changed the default PostgreSQL password!"
    echo "   Edit .env and set a secure POSTGRES_PASSWORD"
    exit 1
fi

if [ "${SECRET_KEY}" = "CHANGE_ME_64_CHAR_RANDOM_HEX_STRING" ]; then
    echo "❌ You haven't set SECRET_KEY!"
    echo "   Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
    exit 1
fi

echo "✅ Environment variables validated"

# ── Create required directories ───────────────────────────
mkdir -p certbot/conf certbot/www backups/postgres reports
echo "✅ Directories created"

# ── Build images ─────────────────────────────────────────
echo ""
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache
echo "✅ Images built"

# ── Start database first, run migrations ─────────────────
echo ""
echo "Starting database and running migrations..."
docker compose -f docker-compose.prod.yml up -d db cache
sleep 10    # wait for DB to be ready

# Run Alembic migrations (if using them)
# docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head
echo "✅ Database ready"

# ── Start all services ────────────────────────────────────
echo ""
echo "Starting all services..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ All services started"

# ── Wait for health check ─────────────────────────────────
echo ""
echo "Waiting for app to be healthy..."
for i in {1..30}; do
    if docker compose -f docker-compose.prod.yml exec -T app \
        curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ App is healthy!"
        break
    fi
    echo "  Waiting... (${i}/30)"
    sleep 5
done

# ── Display status ────────────────────────────────────────
echo ""
echo "================================================="
echo "  DEPLOYMENT COMPLETE"
echo "================================================="
echo ""
echo "Service status:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Next steps:"
echo "  1. Set up SSL: ./scripts/init-ssl.sh"
echo "  2. Monitor logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  3. Check health: curl http://YOUR_SERVER_IP/health"
echo ""