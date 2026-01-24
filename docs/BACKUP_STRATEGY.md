# Rhinometric Backup & Restore Strategy

## Backup Automático

### Qué se respalda

El script `scripts/backup-core.sh` realiza backups diarios de:

1. **PostgreSQL Database** (`postgres.dump.gz`)
   - Base de datos completa `rhinometric`
   - Formato custom compressed
   - ~5-50MB dependiendo de datos

2. **Grafana Data** (`grafana.tar.gz`)
   - Dashboards personalizados
   - Datasources
   - Usuarios y configuraciones
   - Alertas y notificaciones
   - ~10-20MB

3. **Configuraciones** (`docker-compose.yml`, `dashboards/`, `prometheus.yml`)
   - Docker Compose configuration
   - Dashboards provisionados
   - Prometheus rules

### Ubicación de Backups

```
/opt/rhinometric/backups/
├── 2026-01-24/
│   ├── postgres.dump.gz
│   ├── grafana.tar.gz
│   ├── docker-compose.yml
│   ├── dashboards/
│   └── prometheus.yml
├── 2026-01-25/
└── 2026-01-26/
```

**Retención**: Se mantienen los últimos 7 días automáticamente.

---

## Configuración del Cron

### 1. Hacer ejecutable el script

```bash
ssh root@89.167.6.43
chmod +x /opt/rhinometric/scripts/backup-core.sh
```

### 2. Añadir entrada al crontab

```bash
crontab -e
```

Añadir esta línea:

```cron
# Rhinometric daily backup at 3:00 AM
0 3 * * * /opt/rhinometric/scripts/backup-core.sh >> /var/log/rhinometric-backup.log 2>&1
```

### 3. Verificar que el cron está activo

```bash
crontab -l | grep rhinometric
systemctl status cron
```

### 4. Test manual del backup

```bash
/opt/rhinometric/scripts/backup-core.sh
ls -lh /opt/rhinometric/backups/$(date +%Y-%m-%d)/
```

---

## Restauración desde Backup

### Restaurar PostgreSQL

```bash
# 1. Detener servicios que usan la DB
docker stop rhinometric-console-backend rhinometric-license-server-v2

# 2. Restaurar el dump
BACKUP_DATE="2026-01-24"  # Cambiar a la fecha del backup
cd /opt/rhinometric/backups/$BACKUP_DATE

gunzip -c postgres.dump.gz > postgres.dump

docker exec -i rhinometric-postgres pg_restore \
  -U postgres \
  -d rhinometric \
  --clean \
  --if-exists \
  < postgres.dump

# 3. Reiniciar servicios
docker start rhinometric-console-backend rhinometric-license-server-v2
```

### Restaurar Grafana

```bash
# 1. Detener Grafana
docker stop rhinometric-grafana

# 2. Limpiar volumen actual (CUIDADO: esto borra todo)
docker volume rm rhinometric-grafana-data

# 3. Recrear volumen vacío
docker volume create rhinometric-grafana-data

# 4. Restaurar desde backup
BACKUP_DATE="2026-01-24"  # Cambiar a la fecha del backup
GRAFANA_VOLUME=$(docker volume inspect rhinometric-grafana-data --format '{{.Mountpoint}}')

cd /opt/rhinometric/backups/$BACKUP_DATE
tar -xzf grafana.tar.gz -C "$GRAFANA_VOLUME"

# 5. Reiniciar Grafana
docker start rhinometric-grafana
```

### Restaurar Configuraciones

```bash
BACKUP_DATE="2026-01-24"
cd /opt/rhinometric/backups/$BACKUP_DATE

# Dashboards
cp -r dashboards/* /opt/rhinometric/grafana/provisioning/dashboards/json/

# Prometheus config (revisar antes de sobrescribir)
cp prometheus.yml /opt/rhinometric/prometheus/prometheus.yml

# Docker Compose (revisar cambios)
diff docker-compose.yml /opt/rhinometric/docker-compose-trial.yml
```

---

## Disaster Recovery Completo

En caso de pérdida total del servidor:

### 1. Nueva VM en Hetzner
- Ubuntu 22.04
- Mismo tamaño o mayor (CPX42+)
- IP pública asignada

### 2. Instalar Docker
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

### 3. Clonar repositorio
```bash
cd /opt
git clone https://github.com/Rafael2712/mi-proyecto.git rhinometric
cd rhinometric
git checkout feature/use-direct-grafana-links  # o la rama en producción
```

### 4. Restaurar backup más reciente

Copiar desde backup externo (S3, otro servidor, etc.) a `/opt/rhinometric/backups/`

```bash
# Restaurar Postgres (antes de iniciar containers)
# Seguir pasos de "Restaurar PostgreSQL" arriba

# Restaurar Grafana
# Seguir pasos de "Restaurar Grafana" arriba
```

### 5. Iniciar stack
```bash
docker compose -f docker-compose-trial.yml up -d
```

### 6. Verificar servicios
```bash
docker ps
curl http://localhost:3000/api/health  # Grafana
curl http://localhost:9090/-/healthy    # Prometheus
```

---

## Backup Externo Recomendado

Para máxima seguridad, configura rsync o rclone para copiar backups a:

- **AWS S3** (rhinometric-backups bucket)
- **Hetzner Storage Box**
- **Otro servidor**

Ejemplo con rclone a S3:

```bash
# Instalar rclone
curl https://rclone.org/install.sh | sudo bash

# Configurar (una vez)
rclone config

# Añadir al cron (después del backup local)
0 4 * * * rclone sync /opt/rhinometric/backups/ s3-rhinometric:rhinometric-backups/hetzner/
```

---

## Monitorización de Backups

### Ver logs de backups
```bash
tail -f /var/log/rhinometric-backup.log
journalctl -t rhinometric-backup -f
```

### Verificar último backup
```bash
ls -lht /opt/rhinometric/backups/ | head -5
```

### Alerta si backup falla

Añadir a `prometheus/alerts.yml`:

```yaml
- alert: BackupMissing
  expr: time() - (node_filesystem_files{mountpoint="/opt/rhinometric/backups"} * 0 + time()) > 86400 * 2
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "Rhinometric backup parece no haberse ejecutado en 2 días"
```

---

## Notas Importantes

- **Passwords**: El script tiene hardcoded el password de Postgres. En producción, usar secrets.
- **Espacio en disco**: Backups ocupan ~100-200MB/día. Monitorizar `/opt/rhinometric/backups/`.
- **Testing**: Hacer restore tests cada mes para verificar que los backups funcionan.
- **Snapshots VM**: Además de backups de datos, hacer snapshots de la VM desde el panel de Hetzner cada semana.
