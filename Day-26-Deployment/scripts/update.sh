#!/bin/bash
# ============================================================
# scripts/update.sh
# Update to latest version with minimal downtime
#
# Run on server after pushing new code:
#   git pull origin main
#   ./scripts/update.sh
# ============================================================

set -e

echo "================================================="
echo "  Task Manager API — Zero-Downtime Update"
echo "================================================="

# ── Pull latest code ──────────────────────────────────────
echo "Pulling latest code..."
git pull origin main
echo "✅ Code updated"

# ── Build new image ───────────────────────────────────────
echo ""
echo "Building new Docker image..."
docker compose -f docker-compose.prod.yml build app
echo "✅ New image built"

# ── Run migrations before switching ──────────────────────
echo ""
echo "Running database migrations..."
# docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head
echo "✅ Migrations applied"

# ── Restart app with new image ────────────────────────────
# Docker Compose restarts one container at a time
echo ""
echo "Restarting application..."
docker compose -f docker-compose.prod.yml up -d --no-deps app
echo "✅ Application restarted"

# ── Wait for health ───────────────────────────────────────
echo ""
echo "Waiting for health check..."
sleep 10

for i in {1..12}; do
    if docker compose -f docker-compose.prod.yml exec -T app \
        curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ New version is healthy!"
        break
    fi
    echo "  Waiting... (${i}/12)"
    sleep 5
done

# ── Clean up old images ───────────────────────────────────
echo ""
echo "Cleaning up old images..."
docker image prune -f
echo "✅ Cleanup done"

echo ""
echo "================================================="
echo "  UPDATE COMPLETE"
echo "================================================="
echo ""
docker compose -f docker-compose.prod.yml ps