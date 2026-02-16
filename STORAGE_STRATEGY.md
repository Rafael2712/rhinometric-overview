# RHINOMETRIC - ESTRATEGIA TÉCNICA DE ALMACENAMIENTO

**Versión**: 1.0  
**Fecha**: 26 de Enero, 2026  
**Audiencia**: Equipo técnico, DevOps, SRE

---

## 🎯 OBJETIVO

Este documento describe la **implementación técnica** de la política de almacenamiento de Rhinometric.

**Referencia**: Ver [STORAGE_POLICY.md](STORAGE_POLICY.md) para la visión ejecutiva y tiers.

---

## 📦 COMPONENTES Y MECANISMOS DE RETENCIÓN

### **1. DOCKER LOG ROTATION** (Prioridad P0)

#### **Problema identificado**:
- **Incidente**: 288 GB logs Docker acumulados en 3 días
- **Causa**: Sin rotación configurada + logs JSON verbose (Fase 2.1)
- **Impacto**: Disco 100% lleno → plataforma caída

#### **Solución implementada**:

**Archivo**: `/etc/docker/daemon.json`

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3",
    "compress": "true"
  }
}
```

**Parámetros**:
- `max-size`: Tamaño máximo de cada archivo de log (50 MB)
- `max-file`: Número de archivos rotados a mantener (3)
- `compress`: Comprimir archivos rotados (ahorra 70-80% espacio)

**Límite por contenedor**: 50MB + (50MB × 3 comprimidos) ≈ **150 MB**  
**Límite total (19 contenedores)**: ~**3 GB**

#### **Aplicación**:

**En VM actual (Hetzner)**:
```bash
# Ya aplicado manualmente el 26 Enero 2026
cat /etc/docker/daemon.json
systemctl restart docker  # Requiere downtime ~1 min
```

**En instalaciones nuevas**:
```bash
# Incluido en install-storage-policies.sh
./scripts/install-storage-policies.sh
```

#### **Validación**:
```bash
# Ver configuración activa
docker info | grep -A 5 "Log Driver"

# Verificar tamaño logs actuales
du -sh /var/lib/docker/containers/*/*.log | sort -hr | head -5
```

#### **Alternativa Docker Compose** (por contenedor):
```yaml
services:
  my-service:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
```
**Nota**: Preferir `/etc/docker/daemon.json` para aplicar globalmente.

---

### **2. PROMETHEUS (Métricas)**

#### **Datos almacenados**:
- Series temporales (TSDB)
- ~2,000-5,000 series activas (20 hosts)
- Granularidad: 15s (scrape interval)

#### **Mecanismo de retención**:

**Flags de línea de comando**:
```yaml
command:
  - '--storage.tsdb.retention.time=30d'    # Retención por tiempo
  - '--storage.tsdb.retention.size=50GB'   # Límite de seguridad
  - '--storage.tsdb.path=/prometheus'
```

**Configuración actual**: ❌ SIN RETENCIÓN CONFIGURADA  
**Implementación**: Ver sección "Cambios en docker-compose-v2.5.0-core.yml"

#### **Ajustes por Tier**:

| Tier | Retención Tiempo | Límite Tamaño | Volumen Estimado |
|------|------------------|---------------|------------------|
| Tier 1 (1-20 hosts) | 30d | 10GB | 2-5 GB |
| Tier 2 (21-70 hosts) | 30d | 50GB | 5-10 GB |
| Tier 3 (71+ hosts) | 15d | 100GB | 20-50 GB |

**Recomendación**: Usar ambas flags para protección doble.

#### **Compactación automática**:
Prometheus compacta bloques antiguos automáticamente:
- Bloques 2h → 12h → 1d → 7d
- Libera espacio sin intervención manual

#### **Validación**:
```bash
# Ver configuración actual
docker inspect rhinometric-prometheus | grep -A 10 "Cmd"

# Ver métricas de TSDB
curl -s http://localhost:9090/api/v1/status/tsdb | jq
```

---

### **3. LOKI (Logs estructurados)**

#### **Datos almacenados**:
- Logs JSON del backend
- Logs de servicios del cliente
- **Mayor consumidor de espacio** (~70% del almacenamiento total)

**Volumen actual**: 3.3 GB (46 horas) → **~1.7 GB/día**

#### **Mecanismo de retención**:

**Archivo**: `config/loki-config.yml`

```yaml
limits_config:
  retention_period: 168h  # 7 días para Tier 1

chunk_store_config:
  max_look_back_period: 168h

table_manager:
  retention_deletes_enabled: true
  retention_period: 168h
```

**Ajustes por Tier**:

| Tier | Retención | Volumen Estimado |
|------|-----------|------------------|
| Tier 1 (1-20 hosts) | 7d (168h) | ~12 GB |
| Tier 2 (21-70 hosts) | 5d (120h) | ~8.5 GB |
| Tier 3 (71+ hosts) | 3d (72h) | ~5 GB |

**⚠️ Importante**: Loki no borra datos automáticamente sin `table_manager` configurado correctamente.

#### **Compactación**:
```yaml
compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

#### **Validación**:
```bash
# Ver configuración actual
docker exec rhinometric-loki cat /etc/loki/loki-config.yml | grep -A 5 retention

# Ver tamaño actual
du -sh ~/rhinometric_data_v2.2/loki

# API: Verificar retención activa
curl -s http://localhost:3100/config | jq '.limits_config.retention_period'
```

---

### **4. JAEGER (Trazas distribuidas)**

#### **Datos almacenados**:
- Spans de OpenTelemetry
- Traces completas (request → DB → response)

**Volumen proyectado**: 2-5 GB/semana con tráfico alto

#### **Mecanismo de retención**:

**Backend: Badger (file-based)**

```yaml
environment:
  SPAN_STORAGE_TYPE: badger
  BADGER_EPHEMERAL: false          # Persistir datos
  BADGER_DIRECTORY_VALUE: /badger/data
  BADGER_DIRECTORY_KEY: /badger/key
  BADGER_TTL: "72h"                # Retención 3 días (Tier 1)
```

**Ajustes por Tier**:

| Tier | TTL | Volumen Estimado |
|------|-----|------------------|
| Tier 1 (1-20 hosts) | 72h (3d) | 2-5 GB |
| Tier 2 (21-70 hosts) | 48h (2d) | 3-6 GB |
| Tier 3 (71+ hosts) | 24h (1d) | 5-10 GB |

**⚠️ Nota**: Badger con `BADGER_EPHEMERAL=false` + TTL elimina automáticamente spans antiguos.

#### **Alternativa: Elasticsearch/Cassandra** (para grandes volúmenes):
```yaml
# Solo si Tier 3 con 500+ hosts
SPAN_STORAGE_TYPE: elasticsearch
ES_SERVER_URLS: http://elasticsearch:9200
ES_INDEX_PREFIX: jaeger
```

#### **Validación**:
```bash
# Ver configuración actual
docker inspect rhinometric-jaeger | grep -A 5 "Env"

# Ver tamaño actual
du -sh ~/rhinometric_data_v2.2/jaeger

# API: Query traces
curl -s "http://localhost:16686/api/traces?service=console-backend&limit=1"
```

---

### **5. POSTGRESQL (Base de datos operacional)**

#### **Datos almacenados**:
- Usuarios, servicios, anomalías, configuración
- **No crece indefinidamente** (datos operacionales, no históricos)

**Volumen actual**: 47 MB  
**Proyección**: 100-500 MB (estable)

#### **Mantenimiento**:
```sql
-- Cleanup manual de anomalías antiguas (si fuera necesario)
DELETE FROM ai_anomalies WHERE detected_at < NOW() - INTERVAL '90 days';

-- VACUUM para recuperar espacio
VACUUM FULL ai_anomalies;
```

**Recomendación**: No implementar retención automática (datos críticos).

#### **Backup**:
```bash
# Backup automático (contenedor rhinometric-backup)
docker exec rhinometric-backup /backup-postgres.sh
```

---

## 🛡️ DISK GUARDIAN - PROTECCIÓN AUTOMÁTICA

### **Script**: `scripts/disk-guardian.sh`

#### **Función**:
Monitorea uso de disco cada 5 minutos y actúa si > 90%.

#### **Lógica**:
```bash
#!/bin/bash
THRESHOLD=90
CURRENT_USE=$(df / | grep / | awk '{print $5}' | sed 's/%//')

if [ "$CURRENT_USE" -ge "$THRESHOLD" ]; then
  echo "[CRITICAL] Disk usage: ${CURRENT_USE}% - Activating emergency measures"
  
  # Parar ingesta no crítica
  docker stop rhinometric-promtail || true
  docker stop rhinometric-otel-collector || true
  
  # Enviar alerta a Alertmanager
  curl -X POST http://localhost:9093/api/v1/alerts \
    -d '[{"labels":{"alertname":"DiskEmergency","severity":"critical"}}]'
  
  # Log evento
  logger -t disk-guardian "Emergency stop: promtail, otel-collector"
fi
```

#### **Instalación**:
```bash
# Añadir a crontab
crontab -e
*/5 * * * * /opt/rhinometric/infrastructure/mi-proyecto/scripts/disk-guardian.sh >> /var/log/disk-guardian.log 2>&1
```

#### **Validación**:
```bash
# Ver cron activo
crontab -l | grep disk-guardian

# Simular ejecución
bash scripts/disk-guardian.sh

# Ver logs
tail -f /var/log/disk-guardian.log
```

---

## 🚨 ALERTAS DE DISCO (PROMETHEUS)

### **Archivo**: `config/rules/disk-alerts.yml`

```yaml
groups:
  - name: disk
    interval: 30s
    rules:
      - alert: DiskUsageWarning
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.30
        for: 10m
        labels:
          severity: warning
          component: infrastructure
        annotations:
          summary: "Disco en WARNING - Uso > 70% en {{ $labels.instance }}"
          description: "Espacio disponible: {{ $value | humanizePercentage }}\nRevise STORAGE_POLICY.md"

      - alert: DiskUsageCritical
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
        for: 5m
        labels:
          severity: critical
          component: infrastructure
        annotations:
          summary: "🚨 DISCO CRÍTICO - Uso > 85% en {{ $labels.instance }}"
          description: |
            Espacio disponible: {{ $value | humanizePercentage }}
            Disk Guardian activará medidas de emergencia si alcanza 90%.
            Acción inmediata requerida.

      - alert: DiskFillRate
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 4 * 3600) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disco se llenará en < 4 horas"
          description: "Proyección lineal indica disco lleno en 4h. Investigar crecimiento anormal."
```

### **Configuración Prometheus**:

**Archivo**: `config/prometheus.yml`

```yaml
rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - rhinometric-alertmanager:9093
```

### **Validación**:
```bash
# Ver reglas cargadas
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="disk")'

# Ver alertas activas
curl -s http://localhost:9090/api/v1/alerts | jq

# Verificar en Grafana
http://89.167.6.43:3000/alerting/list
```

---

## 📂 CAMBIOS EN DOCKER-COMPOSE

### **Archivo**: `docker-compose-v2.5.0-core.yml`

#### **1. Prometheus - Añadir retención**:
```yaml
prometheus:
  image: prom/prometheus:v3.2.1
  container_name: rhinometric-prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'    # NUEVO
    - '--storage.tsdb.retention.size=50GB'   # NUEVO
    - '--web.console.libraries=/usr/share/prometheus/console_libraries'
    - '--web.console.templates=/usr/share/prometheus/consoles'
```

#### **2. Loki - Verificar config mount**:
```yaml
loki:
  image: grafana/loki:3.0.0
  container_name: rhinometric-loki
  volumes:
    - ./config/loki-config.yml:/etc/loki/loki-config.yml:ro  # ✅ Verificar
    - ${HOME}/rhinometric_data_v2.2/loki:/loki
```

#### **3. Jaeger - Añadir TTL**:
```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  container_name: rhinometric-jaeger
  environment:
    SPAN_STORAGE_TYPE: badger
    BADGER_EPHEMERAL: false
    BADGER_TTL: "72h"  # NUEVO - 3 días
    BADGER_DIRECTORY_VALUE: /badger/data
    BADGER_DIRECTORY_KEY: /badger/key
```

---

## 🚀 SCRIPT DE INSTALACIÓN AUTOMÁTICA

### **Archivo**: `scripts/install-storage-policies.sh`

```bash
#!/bin/bash
set -euo pipefail

echo "=== Rhinometric Storage Policies Installation ==="

# 1. Configurar Docker log rotation
echo "Configurando Docker log rotation..."
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3",
    "compress": "true"
  }
}
EOF

# 2. Reiniciar Docker (requiere confirmación)
read -p "¿Reiniciar Docker daemon? (requiere ~1min downtime) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  systemctl restart docker
  echo "✅ Docker reiniciado"
else
  echo "⚠️  Aplicar manualmente: systemctl restart docker"
fi

# 3. Instalar Disk Guardian
echo "Instalando Disk Guardian..."
cp scripts/disk-guardian.sh /usr/local/bin/disk-guardian
chmod +x /usr/local/bin/disk-guardian

# 4. Configurar cron
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/disk-guardian >> /var/log/disk-guardian.log 2>&1") | crontab -
echo "✅ Disk Guardian instalado (cron cada 5 min)"

# 5. Verificar alertas Prometheus
if [ -f config/rules/disk-alerts.yml ]; then
  echo "✅ Alertas de disco configuradas"
else
  echo "⚠️  Crear config/rules/disk-alerts.yml (ver STORAGE_STRATEGY.md)"
fi

echo ""
echo "=== Instalación completada ==="
echo "Ejecutar: docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate"
```

---

## ✅ CHECKLIST DE VALIDACIÓN

Después de aplicar las políticas:

### **1. Docker Log Rotation**:
```bash
☐ Archivo /etc/docker/daemon.json existe
☐ Docker daemon reiniciado
☐ Logs nuevos no exceden 50MB: ls -lh /var/lib/docker/containers/*/*.log
```

### **2. Prometheus Retención**:
```bash
☐ Flags de retención en docker inspect rhinometric-prometheus
☐ TSDB muestra retención: curl http://localhost:9090/api/v1/status/tsdb
```

### **3. Loki Retención**:
```bash
☐ Archivo config/loki-config.yml tiene retention_period
☐ API Loki responde config: curl http://localhost:3100/config
```

### **4. Jaeger TTL**:
```bash
☐ Variable BADGER_TTL en docker inspect rhinometric-jaeger
☐ Jaeger UI muestra traces: http://localhost:16686
```

### **5. Alertas Disco**:
```bash
☐ Reglas cargadas: curl http://localhost:9090/api/v1/rules
☐ Alertas aparecen en Grafana: http://localhost:3000/alerting/list
```

### **6. Disk Guardian**:
```bash
☐ Script ejecutable: /usr/local/bin/disk-guardian
☐ Cron configurado: crontab -l | grep disk-guardian
☐ Log creado: tail /var/log/disk-guardian.log
```

---

## 📚 REFERENCIAS

- **STORAGE_POLICY.md**: Política ejecutiva y tiers
- **STORAGE_INVENTORY.md**: Inventario actual de volúmenes
- **STORAGE_IMPLEMENTATION_STATUS.md**: Estado de implementación
- **Prometheus TSDB**: https://prometheus.io/docs/prometheus/latest/storage/
- **Loki Retention**: https://grafana.com/docs/loki/latest/operations/storage/retention/
- **Jaeger Storage**: https://www.jaegertracing.io/docs/latest/deployment/#badger

---

**Última actualización**: 26 Enero 2026  
**Versión**: 1.0
