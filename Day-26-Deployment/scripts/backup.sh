#!/bin/bash
# ============================================================
# scripts/backup.sh
# PostgreSQL database backup
#
# Add to server crontab:
# 0 3 * * * /home/appuser/taskmanager/scripts/backup.sh
# (runs every day at 3 AM)
# ============================================================

set -e

source .env

BACKUP_DIR="./backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/taskmanager_${DATE}.sql.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "Creating PostgreSQL backup: ${BACKUP_FILE}"

# Dump and compress
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
    | gzip > "${BACKUP_FILE}"

echo "✅ Backup created: ${BACKUP_FILE}"
echo "   Size: $(du -sh ${BACKUP_FILE} | cut -f1)"

# Delete backups older than 7 days
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +7 -delete
echo "✅ Old backups cleaned up"

# List remaining backups
echo ""
echo "Current backups:"
ls -lh "${BACKUP_DIR}"