# Rhinometric Demo Appliance - Operations Guide

Guía operativa completa para administradores del appliance OVA.

## ��� Tabla de Contenidos

1. [Acceso y Credenciales](#acceso-y-credenciales)
2. [Operaciones Diarias](#operaciones-diarias)
3. [Monitoreo y Salud](#monitoreo-y-salud)
4. [Backup y Restore](#backup-y-restore)
5. [Updates y Mantenimiento](#updates-y-mantenimiento)
6. [Troubleshooting](#troubleshooting)
7. [Seguridad](#seguridad)

---

## ��� Acceso y Credenciales

### SSH
```bash
ssh rhinouser@<VM_IP>
# Password: rhinometric
```

### Grafana Web UI
- **URL:** https://\<VM_IP\>:3000
- **Usuario:** admin
- **Password:** rhinometric_demo

### Dashboard Builder
- **URL:** http://\<VM_IP\>:3001

### Prometheus
- **URL:** http://\<VM_IP\>:9090

### Servicios Internos
```bash
# Ver todos los servicios
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs de servicio específico
docker logs rhinometric-ai-anomaly-demo -f
```

---

## ��� Operaciones Diarias

### Verificación de Salud (Smoke Test)

```bash
cd /opt/rhinometric/deploy/demo
sudo bash scripts/smoke-test.sh
```

**Output esperado:**
```
��� Rhinometric Demo - Smoke Test
==================================
[1/8] Verificando contenedores...
✓ Todos los contenedores healthy
[2/8] Verificando endpoints HTTP...
✓ Grafana :3000
✓ Prometheus :9090
✓ Loki :3100
✓ AI Anomaly :8085
[3/8] Verificando Prometheus targets...
✓ Todos los targets UP
[4/8] Verificando datasources Grafana...
✓ Datasource Prometheus (UID: prometheus)
[5/8] Verificando métricas AI...
✓ Métricas AI presentes
[6/8] Verificando espacio en disco...
✓ Disco <80% (actual: 45%)
[7/8] Verificando volúmenes...
✓ Volúmenes creados
[8/8] Verificando red...
✓ Red rhinometric activa
==================================
✓ Smoke test PASSED - Stack funcional
```

### Restart de Servicios

```bash
# Restart completo del stack
cd /opt/rhinometric/deploy/demo
docker compose down
docker compose up -d

# Restart de servicio individual
docker restart rhinometric-grafana-demo

# Ver logs durante restart
docker compose logs -f --tail=50
```

### Verificar Consumo de Recursos

```bash
# CPU y memoria por contenedor
docker stats --no-stream

# Espacio en disco
df -h

# Volúmenes Docker
docker system df
```

---

## ��� Monitoreo y Salud

### Dashboards Disponibles

1. **AI Anomaly Detection** - `/d/rhinometric-ai-anomaly`
   - Detecciones últimas 24h
   - Anomalías activas
   - Modelos entrenados
   - Gráfico tiempo real

2. **System Overview** - `/d/rhinometric-system-overview`
   - CPU, RAM, Disk, Network
   - Métricas de node-exporter

3. **App Performance** - `/d/rhinometric-app-performance`
   - Requests/sec
   - Error rate
   - Latency percentiles

### Verificar Targets Prometheus

```bash
# Via curl
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up") | .scrapePool'

# Via web
# Abrir http://<VM_IP>:9090/targets
```

**Todos deben estar UP (verde):**
- prometheus
- grafana
- node-exporter
- cadvisor
- blackbox-exporter
- rhinometric-ai-anomaly
- rhinometric-dashboard-builder

### Health Checks Manuales

```bash
# AI Anomaly Detection
curl http://localhost:8085/health
# Expected: {"status":"healthy"}

# Dashboard Builder
curl http://localhost:8001/health
# Expected: {"status":"healthy","service":"dashboard-builder"}

# Grafana
curl -u admin:rhinometric_demo http://localhost:3000/api/health
# Expected: {"database":"ok"}

# Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.
```

---

## ��� Backup y Restore

### Backup Manual

```bash
cd /opt/rhinometric/deploy/demo
sudo bash scripts/backup.sh
```

**Genera:**
- `/opt/rhinometric/deploy/demo/backups/grafana-data_YYYYMMDD_HHMMSS.tar.gz`
- `/opt/rhinometric/deploy/demo/backups/prometheus-data_YYYYMMDD_HHMMSS.tar.gz`
- `/opt/rhinometric/deploy/demo/backups/loki-data_YYYYMMDD_HHMMSS.tar.gz`
- `/opt/rhinometric/deploy/demo/backups/postgres-data_YYYYMMDD_HHMMSS.tar.gz`
- Checksums SHA256 (`.sha256`)

**Retención:** 7 días (automático)

### Verificar Backups

```bash
ls -lh /opt/rhinometric/deploy/demo/backups/

# Verificar integridad
cd /opt/rhinometric/deploy/demo/backups
sha256sum -c grafana-data_*.tar.gz.sha256
```

### Restore desde Backup

```bash
# 1. Parar servicios
cd /opt/rhinometric/deploy/demo
docker compose down

# 2. Listar backups disponibles
ls -lt backups/*.tar.gz | head -5

# 3. Restaurar volumen específico (ejemplo: Grafana)
BACKUP_FILE="backups/grafana-data_20241109_143022.tar.gz"

# Eliminar volumen actual
docker volume rm demo_grafana-data

# Restaurar desde backup
docker run --rm \
  -v demo_grafana-data:/data \
  -v "$PWD/backups:/backup" \
  alpine tar xzf "/backup/$(basename $BACKUP_FILE)" -C /data

# 4. Reiniciar servicios
docker compose up -d

# 5. Verificar
sudo bash scripts/smoke-test.sh
```

### Backup Automático (Cron)

```bash
# Editar crontab
sudo crontab -e

# Agregar backup diario a las 2 AM
0 2 * * * cd /opt/rhinometric/deploy/demo && bash scripts/backup.sh >> /var/log/rhinometric-backup.log 2>&1
```

---

## ��� Updates y Mantenimiento

### Update del Stack

```bash
cd /opt/rhinometric/deploy/demo
sudo bash scripts/update.sh
```

**Proceso:**
1. Ejecuta backup automático
2. Pull de imágenes actualizadas
3. Reinicia servicios
4. Espera healthchecks
5. Ejecuta smoke test

### Update Manual

```bash
cd /opt/rhinometric/deploy/demo

# 1. Backup
sudo bash scripts/backup.sh

# 2. Pull imágenes
docker compose pull

# 3. Recrear contenedores
docker compose up -d --force-recreate

# 4. Verificar
sudo bash scripts/smoke-test.sh
```

### Limpieza de Docker

```bash
# Eliminar imágenes no usadas
docker image prune -a -f

# Eliminar volúmenes huérfanos
docker volume prune -f

# Eliminar redes no usadas
docker network prune -f

# Limpieza completa
docker system prune -a --volumes -f
```

---

## ��� Troubleshooting

### Dashboard "No data"

**Síntoma:** Dashboards AI muestran "No data"

**Solución:**
```bash
# 1. Verificar que anomaly-seed está corriendo
ps aux | grep anomaly-seed

# 2. Si no está, reiniciarlo
cd /opt/rhinometric/deploy/demo
nohup bash scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &

# 3. Esperar 2 minutos y refrescar dashboard

# 4. Verificar métricas en Prometheus
curl -s http://localhost:9090/api/v1/query?query=rhinometric_anomaly_detections_total | jq '.data.result'
```

### Prometheus Targets DOWN

**Síntoma:** Targets aparecen en rojo en `/targets`

**Diagnóstico:**
```bash
# Ver qué target está DOWN
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up") | {job: .scrapePool, health: .health, error: .lastError}'

# Revisar logs del servicio
docker logs rhinometric-ai-anomaly-demo --tail 50
```

**Solución:**
```bash
# Restart del servicio afectado
docker restart rhinometric-<SERVICE>-demo

# Si persiste, recrear contenedor
docker compose up -d --force-recreate rhinometric-<SERVICE>
```

### Containers Unhealthy

**Síntoma:** `docker ps` muestra status "unhealthy"

**Diagnóstico:**
```bash
# Ver detalles del healthcheck
docker inspect rhinometric-grafana-demo | jq '.[0].State.Health'

# Logs del contenedor
docker logs rhinometric-grafana-demo --tail 100
```

**Solución:**
```bash
# 1. Restart
docker restart rhinometric-grafana-demo

# 2. Si falla, verificar configuración
docker compose config | grep -A 10 grafana

# 3. Recrear desde cero
docker compose up -d --force-recreate grafana
```

### Grafana Datasource Error

**Síntoma:** Error "Data source not found"

**Solución:**
```bash
# 1. Verificar UID del datasource
curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources/uid/prometheus | jq '.'

# Expected: {"id":1,"uid":"prometheus","name":"Prometheus",...}

# 2. Si no existe, re-provision
docker restart rhinometric-grafana-demo
sleep 15

# 3. Verificar de nuevo
curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources | jq '.[] | {name, uid, type}'
```

### Dashboard Builder CORS Error

**Síntoma:** Frontend no puede conectar con backend

**Solución:**
```bash
# 1. Verificar backend
curl http://localhost:8001/health

# 2. Verificar logs
docker logs rhinometric-dashboard-builder-demo --tail 50

# 3. Verificar CORS en navegador (DevTools > Console)

# 4. Si es problema de CORS, reiniciar backend
docker restart rhinometric-dashboard-builder-demo
```

### VM Lenta / Alto Consumo

**Diagnóstico:**
```bash
# CPU por contenedor
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Procesos del sistema
top -b -n 1 | head -20
```

**Solución:**
```bash
# 1. Identificar contenedor problemático
docker stats --no-stream

# 2. Restart del contenedor
docker restart <CONTAINER_NAME>

# 3. Si es anomaly-seed consumiendo mucho, ajustar intervalo
# Editar scripts/anomaly-seed.sh y cambiar INTERVAL de 90 a 180
```

### Support Bundle para Diagnóstico

```bash
cd /opt/rhinometric/deploy/demo
sudo bash scripts/support-bundle.sh

# Genera: support-bundle-YYYYMMDD_HHMMSS.tar.gz
# Contiene: logs, configs, docker info, health checks
```

---

## ��� Seguridad

### Cambiar Password de Grafana

```bash
# Via Docker exec
docker exec -it rhinometric-grafana-demo grafana-cli admin reset-admin-password NEW_PASSWORD

# O vía API
curl -X PUT http://admin:rhinometric_demo@localhost:3000/api/user/password \
  -H "Content-Type: application/json" \
  -d '{"oldPassword":"rhinometric_demo","newPassword":"NEW_PASSWORD","confirmNew":"NEW_PASSWORD"}'
```

### Cambiar Password SSH

```bash
# Login via SSH
ssh rhinouser@<VM_IP>

# Cambiar password
passwd
# Ingresa: rhinometric
# Nueva password: (tu elección)
```

### Firewall (UFW)

```bash
# Ver status
sudo ufw status verbose

# Permitir puerto adicional
sudo ufw allow 8080/tcp

# Denegar puerto
sudo ufw deny 8080/tcp

# Reload
sudo ufw reload
```

### Certificados TLS

**Default:** Self-signed certificates en `/opt/rhinometric/deploy/demo/traefik/certs/`

**Reemplazar con certs válidos:**
```bash
# 1. Copiar certificados
sudo cp your-cert.pem /opt/rhinometric/deploy/demo/traefik/certs/cert.pem
sudo cp your-key.pem /opt/rhinometric/deploy/demo/traefik/certs/key.pem

# 2. Restart Traefik
docker restart rhinometric-traefik-demo

# 3. Verificar
curl -vI https://localhost:443 2>&1 | grep "subject:"
```

### Logs de Auditoría

```bash
# Logs de acceso Traefik
docker logs rhinometric-traefik-demo --tail 100

# Logs de autenticación SSH
sudo tail -50 /var/log/auth.log

# Logs de Docker
sudo journalctl -u docker --since "1 hour ago"
```

---

## �� Soporte

### Información del Sistema

```bash
# Versión del appliance
cat /opt/rhinometric/VERSION

# Versión de Docker
docker --version
docker compose version

# Info del sistema
uname -a
lsb_release -a
```

### Generar Reporte de Estado

```bash
cd /opt/rhinometric/deploy/demo

# Ejecutar smoke test con output detallado
sudo bash scripts/smoke-test.sh > /tmp/health-report.txt 2>&1

# Generar support bundle
sudo bash scripts/support-bundle.sh

# Enviar ambos archivos a soporte
```

### Contacto

- **Issues:** https://github.com/Rafael2712/mi-proyecto/issues
- **Email:** [soporte@rhinometric.local]
- **Documentación:** `/opt/rhinometric/docs/`

---

## ��� Referencias

- **BUILD-OVA.md** - Proceso de construcción del appliance
- **OVA-README.md** - Guía de importación e instalación inicial
- **E2E-TEST-PLAN.md** - Plan de pruebas end-to-end
- **deploy/demo/README.md** - Documentación del stack demo

---

**Última Actualización:** 2024-11-09  
**Versión:** Rhinometric v2.5.0  
**Appliance:** rhinometric-demo.ova
