#!/bin/bash
#
# Rhinometric Core Backup Script
# Ejecuta backup diario de Postgres y Grafana
#

set -e

BACKUP_ROOT="/opt/rhinometric/backups"
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="$BACKUP_ROOT/$DATE"
COMPOSE_FILE="/opt/rhinometric/docker-compose-trial.yml"

# Configuración de DB (ajustar según docker-compose)
DB_CONTAINER="rhinometric-postgres"
DB_NAME="rhinometric"
DB_USER="rhinometric"
DB_PASSWORD="WSDyl7435nuXyvNsmfECyVS68aE5k6Gk"

# Crear directorio de backup
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

echo "[$(date)] === Rhinometric Backup Started ==="

# 1. Backup de PostgreSQL
echo "[$(date)] Backing up PostgreSQL database..."
docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -f /tmp/postgres_backup.dump

docker cp "$DB_CONTAINER:/tmp/postgres_backup.dump" "$BACKUP_DIR/postgres.dump"
docker exec "$DB_CONTAINER" rm /tmp/postgres_backup.dump

gzip "$BACKUP_DIR/postgres.dump"
echo "[$(date)] ✅ PostgreSQL backup completed: postgres.dump.gz"

# 2. Backup de Grafana data
echo "[$(date)] Backing up Grafana data..."
GRAFANA_VOLUME=$(docker volume inspect rhinometric-grafana-data --format '{{.Mountpoint}}' 2>/dev/null || echo "/var/lib/docker/volumes/rhinometric-grafana-data/_data")

if [ -d "$GRAFANA_VOLUME" ]; then
  tar -czf "$BACKUP_DIR/grafana.tar.gz" -C "$GRAFANA_VOLUME" .
  echo "[$(date)] ✅ Grafana backup completed: grafana.tar.gz"
else
  echo "[$(date)] ⚠️  Grafana volume not found at $GRAFANA_VOLUME"
fi

# 3. Backup de configuraciones
echo "[$(date)] Backing up configuration files..."
cp "$COMPOSE_FILE" "$BACKUP_DIR/docker-compose.yml"
cp -r /opt/rhinometric/grafana/provisioning/dashboards/json "$BACKUP_DIR/dashboards/"
cp /opt/rhinometric/prometheus/prometheus.yml "$BACKUP_DIR/" 2>/dev/null || true
echo "[$(date)] ✅ Configuration files backed up"

# 4. Resumen del backup
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[$(date)] === Backup Summary ==="
echo "  Location: $BACKUP_DIR"
echo "  Size: $BACKUP_SIZE"
echo "  Files:"
ls -lh "$BACKUP_DIR"

# 5. Limpieza de backups antiguos (mantener últimos 7 días)
echo "[$(date)] Cleaning old backups (keeping last 7 days)..."
find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +7 -name "20*" -exec rm -rf {} \;

echo "[$(date)] === Backup Completed Successfully ==="

# Log en syslog
logger -t rhinometric-backup "Backup completed: $BACKUP_DIR ($BACKUP_SIZE)"
