# RHINOMETRIC - ESTADO DE IMPLEMENTACIÓN DE ALMACENAMIENTO

**Fecha**: 26 de Enero, 2026  
**VM Producción**: Hetzner CPX42 (89.167.6.43)  
**Versión**: v2.5.0-core

---

## 📊 RESUMEN EJECUTIVO

| Componente | Estado | Aplicado en VM | En Repo |
|------------|--------|----------------|---------|
| **Docker Log Rotation** | ✅ IMPLEMENTADO | ✅ Sí | ✅ Documentado |
| **Prometheus Retención** | ✅ IMPLEMENTADO | ⏸️ Pendiente aplicar | ✅ docker-compose |
| **Loki Retención** | ✅ IMPLEMENTADO | ✅ Sí | ✅ loki-config.yml |
| **Jaeger TTL** | ✅ IMPLEMENTADO | ⏸️ Pendiente aplicar | ✅ docker-compose |
| **Alertas Disco** | ✅ IMPLEMENTADO | ⏸️ Pendiente aplicar | ✅ disk-alerts.yml |
| **Disk Guardian** | ✅ IMPLEMENTADO | ⏸️ Pendiente aplicar | ✅ disk-guardian.sh |
| **Install Script** | ✅ IMPLEMENTADO | - | ✅ install-storage-policies.sh |

**Estado general**: ✅ **COMPLETO EN REPO** | ⏸️ **PENDIENTE APLICAR EN VM**

---

## 🔍 DETALLE POR COMPONENTE

### **1. DOCKER LOG ROTATION** ✅ ✅

**Archivo**: `/etc/docker/daemon.json`

**Configuración**:
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

**Estado**:
- ✅ **Aplicado en VM producción**: 26 Enero 2026 (post-incidente)
- ✅ **Documentado**: STORAGE_STRATEGY.md
- ✅ **Script instalación**: scripts/install-storage-policies.sh

**Efecto**:
- Límite por contenedor: 150 MB (50MB + 50MB×3 comprimidos)
- Total 19 contenedores: ~3 GB máximo
- **Antes del incidente**: 288 GB logs sin control ❌
- **Después**: 1.9 GB con rotación ✅

**Validación**:
```bash
# Verificar configuración
cat /etc/docker/daemon.json

# Verificar logs actuales
du -sh /var/lib/docker/containers
```

---

### **2. PROMETHEUS RETENCIÓN** ✅ ⏸️

**Archivo**: `docker-compose-v2.5.0-core.yml`

**Configuración implementada**:
```yaml
prometheus:
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'    # ✅ NUEVO
    - '--storage.tsdb.retention.size=50GB'   # ✅ NUEVO
    - '--web.console.libraries=/usr/share/prometheus/console_libraries'
    - '--web.console.templates=/usr/share/prometheus/consoles'
```

**Estado**:
- ✅ **Configurado en docker-compose**
- ⏸️ **Pendiente aplicar en VM** (requiere recreate del contenedor)
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Tier configurado**: Tier 1/2 (30 días)

**Proyección**:
- Volumen actual: 144 MB (46 horas)
- Con 30 días: 2-5 GB
- Límite seguridad: 50 GB

**Aplicación**:
```bash
cd /opt/rhinometric
git pull
docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate prometheus
```

**Validación**:
```bash
# Verificar flags activos
docker inspect rhinometric-prometheus | grep "storage.tsdb.retention"

# Ver configuración TSDB
curl -s http://localhost:9090/api/v1/status/tsdb | jq
```

---

### **3. LOKI RETENCIÓN** ✅ ✅

**Archivo**: `config/loki-config.yml`

**Configuración**:
```yaml
limits_config:
  retention_period: 168h  # 7 días (Tier 1)

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

**Estado**:
- ✅ **Configurado en loki-config.yml**
- ✅ **Aplicado en VM** (contenedor usa este config)
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Tier configurado**: Tier 1 (7 días / 168h)

**Proyección**:
- Volumen actual: 3.3 GB (46 horas)
- Tasa: ~1.7 GB/día
- Con 7 días: ~12 GB estable

**Validación**:
```bash
# Verificar configuración
docker exec rhinometric-loki cat /etc/loki/loki-config.yml | grep -A 5 retention

# Verificar tamaño actual
du -sh ~/rhinometric_data_v2.2/loki

# API: Verificar retención activa
curl -s http://localhost:3100/config | jq '.limits_config.retention_period'
```

**Ajustes por Tier**:
- **Tier 1**: 168h (7d) - Actual ✅
- **Tier 2**: 120h (5d) - Cambiar si necesario
- **Tier 3**: 72h (3d) - Para grandes volúmenes

---

### **4. JAEGER TTL** ✅ ⏸️

**Archivo**: `docker-compose-v2.5.0-core.yml`

**Configuración implementada**:
```yaml
jaeger:
  environment:
    SPAN_STORAGE_TYPE: badger
    BADGER_EPHEMERAL: "false"    # ✅ CAMBIO: true → false
    BADGER_TTL: "72h"              # ✅ NUEVO: 3 días
    BADGER_DIRECTORY_VALUE: /badger/data
    BADGER_DIRECTORY_KEY: /badger/key
```

**Estado**:
- ✅ **Configurado en docker-compose**
- ⏸️ **Pendiente aplicar en VM** (requiere recreate del contenedor)
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Tier configurado**: Tier 1 (72h / 3 días)

**Proyección**:
- Volumen actual: 60 KB (recién iniciado)
- Con tráfico alto: 2-5 GB (3 días)

**Aplicación**:
```bash
cd /opt/rhinometric
git pull
docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate jaeger
```

**Validación**:
```bash
# Verificar TTL configurado
docker inspect rhinometric-jaeger | grep BADGER_TTL

# Verificar tamaño actual
du -sh ~/rhinometric_data_v2.2/jaeger

# API: Query traces
curl -s "http://localhost:16686/api/services" | jq
```

**Ajustes por Tier**:
- **Tier 1**: 72h (3d) - Actual ✅
- **Tier 2**: 48h (2d)
- **Tier 3**: 24h (1d)

---

### **5. ALERTAS DISCO** ✅ ⏸️

**Archivo**: `config/rules/disk-alerts.yml`

**Alertas implementadas**:
1. **DiskUsageWarning**: Uso > 70% durante 10 min
2. **DiskUsageCritical**: Uso > 85% durante 5 min
3. **DiskFillRate**: Proyección llenado < 4 horas
4. **DockerLogsExcessive**: Logs Docker > 5 GB
5. **LokiStorageGrowthHigh**: Ingestion rate muy alta

**Estado**:
- ✅ **Creado**: config/rules/disk-alerts.yml
- ⏸️ **Pendiente aplicar en VM**
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Aplicación**:
```bash
cd /opt/rhinometric
git pull

# Recargar reglas Prometheus
curl -X POST http://localhost:9090/-/reload

# O reiniciar Prometheus
docker restart rhinometric-prometheus
```

**Validación**:
```bash
# Ver reglas cargadas
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="disk")'

# Ver alertas activas
curl -s http://localhost:9090/api/v1/alerts | jq

# Grafana Alerting
http://89.167.6.43:3000/alerting/list
```

---

### **6. DISK GUARDIAN** ✅ ⏸️

**Archivo**: `scripts/disk-guardian.sh`

**Función**:
- Monitorea disco cada 5 minutos (cron)
- Si uso > 90%: para promtail + otel-collector
- NO toca servicios del cliente
- Envía alerta a Alertmanager

**Estado**:
- ✅ **Creado**: scripts/disk-guardian.sh
- ⏸️ **Pendiente instalar en VM**
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Instalación**:
```bash
cd /opt/rhinometric/infrastructure/mi-proyecto

# Método 1: Script automático
chmod +x scripts/install-storage-policies.sh
sudo ./scripts/install-storage-policies.sh

# Método 2: Manual
sudo cp scripts/disk-guardian.sh /usr/local/bin/disk-guardian
sudo chmod +x /usr/local/bin/disk-guardian
(crontab -l; echo "*/5 * * * * /usr/local/bin/disk-guardian >> /var/log/disk-guardian.log 2>&1") | crontab -
```

**Validación**:
```bash
# Verificar instalación
ls -lh /usr/local/bin/disk-guardian

# Verificar cron
crontab -l | grep disk-guardian

# Ver logs
tail -f /var/log/disk-guardian.log

# Test manual
sudo /usr/local/bin/disk-guardian
```

---

### **7. SCRIPT INSTALACIÓN** ✅

**Archivo**: `scripts/install-storage-policies.sh`

**Función**:
- Aplica Docker log rotation
- Instala Disk Guardian
- Verifica alertas Prometheus
- Verifica retenciones configuradas

**Estado**:
- ✅ **Creado**: scripts/install-storage-policies.sh
- ✅ **Documentado**: STORAGE_STRATEGY.md

**Uso**:
```bash
cd /opt/rhinometric/infrastructure/mi-proyecto
chmod +x scripts/install-storage-policies.sh
sudo ./scripts/install-storage-policies.sh
```

**Output esperado**:
- Configura /etc/docker/daemon.json
- Instala /usr/local/bin/disk-guardian
- Configura cron job
- Verifica retenciones (Prometheus, Loki, Jaeger)
- Muestra checklist de acciones pendientes

---

## 📋 CHECKLIST DE APLICACIÓN EN VM

### **VM Producción (89.167.6.43)**:

#### **Ya Aplicado** ✅:
- [x] Docker log rotation (/etc/docker/daemon.json)
- [x] Loki retención (config/loki-config.yml activo)

#### **Pendiente Aplicar** ⏸️:
- [ ] Prometheus retención (recreate contenedor)
- [ ] Jaeger TTL (recreate contenedor)
- [ ] Alertas disco (reload Prometheus)
- [ ] Disk Guardian (instalar script + cron)

#### **Comandos para aplicar**:

```bash
# 1. Actualizar repo
cd /opt/rhinometric
git pull

# 2. Instalar Disk Guardian
cd infrastructure/mi-proyecto
chmod +x scripts/install-storage-policies.sh
sudo ./scripts/install-storage-policies.sh

# 3. Recrear Prometheus y Jaeger con nuevas configuraciones
docker compose -f docker-compose-v2.5.0-core.yml up -d --force-recreate prometheus jaeger

# 4. Recargar reglas Prometheus
curl -X POST http://localhost:9090/-/reload

# 5. Verificar todo
./scripts/verify-storage-policies.sh  # (crear este script)
```

---

### **Instalaciones Nuevas** (clientes):

```bash
# Ejecutar script de instalación completo
cd /opt/rhinometric/infrastructure/mi-proyecto
chmod +x scripts/install-storage-policies.sh
sudo ./scripts/install-storage-policies.sh

# Levantar stack con configuraciones
docker compose -f docker-compose-v2.5.0-core.yml up -d

# Verificar
docker ps
curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="disk")'
crontab -l | grep disk-guardian
```

---

## 🎯 PRÓXIMOS PASOS

### **Prioridad Inmediata**:
1. ✅ Aplicar cambios en VM producción
2. ✅ Verificar alertas apareciendo en Grafana
3. ✅ Monitorear logs disk-guardian durante 24h
4. ✅ Documentar en verify-installation.sh

### **Semana 1 (Post-implementación)**:
- Monitorear crecimiento diario de Loki
- Verificar que retención Prometheus funciona
- Confirmar Jaeger elimina traces antiguas
- Validar alertas NO se disparan con uso normal

### **Mes 1 (Auditoría)**:
- Ejecutar `STORAGE_INVENTORY.md` audit script
- Comparar volúmenes proyectados vs reales
- Ajustar retenciones si necesario
- Documentar lecciones aprendidas

---

## ✅ CRITERIOS DE ÉXITO

**Implementación exitosa si**:
1. ✅ Docker log rotation limitando a 3 GB total
2. ✅ Prometheus estable en ~5 GB (30 días)
3. ✅ Loki estable en ~12 GB (7 días)
4. ✅ Jaeger estable en ~5 GB (3 días)
5. ✅ Disk Guardian ejecutando cada 5 min sin errores
6. ✅ Alertas de disco aparecen en Grafana/Prometheus
7. ✅ Uso total Rhinometric < 30 GB (Tier 1)
8. ✅ Disco VM nunca supera 70% uso

---

## 📚 REFERENCIAS

- **STORAGE_POLICY.md**: Política ejecutiva y tiers
- **STORAGE_STRATEGY.md**: Implementación técnica detallada
- **STORAGE_INVENTORY.md**: Inventario actual de volúmenes
- **Incidente crítico**: 26 Enero 2026 - Disco 100% lleno (288GB logs)

---

**Última actualización**: 26 Enero 2026  
**Estado**: ✅ Implementación completa en repo, ⏸️ Pendiente aplicar en VM  
**Próxima acción**: Aplicar cambios en VM producción con comandos listados arriba
