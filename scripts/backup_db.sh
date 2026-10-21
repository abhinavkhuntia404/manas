#!/usr/bin/env bash
# Database Snapshot & Backup Utility for MANAS

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

if docker ps --format '{{.Names}}' | grep -q "manas_db_prod"; then
    echo "Creating PostgreSQL backup from container manas_db_prod..."
    docker exec manas_db_prod pg_dump -U manas manas > "${BACKUP_DIR}/manas_backup_${TIMESTAMP}.sql"
    echo "✓ Saved: ${BACKUP_DIR}/manas_backup_${TIMESTAMP}.sql"
elif [ -f "data/manas.db" ]; then
    echo "Creating SQLite database backup..."
    cp "data/manas.db" "${BACKUP_DIR}/manas_sqlite_${TIMESTAMP}.db"
    echo "✓ Saved: ${BACKUP_DIR}/manas_sqlite_${TIMESTAMP}.db"
else
    echo "No active database found to backup."
fi
