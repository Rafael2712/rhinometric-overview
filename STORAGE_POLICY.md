# RHINOMETRIC - POLÍTICA DE ALMACENAMIENTO Y RETENCIÓN

**Versión**: 1.0  
**Fecha**: 26 de Enero, 2026  
**Prioridad**: P0 (Crítico)  
**Razón**: Incidente crítico - Disco 100% lleno (288GB logs Docker) causó caída completa de plataforma

---

## 🎯 OBJETIVO

**Rhinometric NUNCA debe poder llenar el disco de un cliente al 100%.**

Esta política define:
- ✅ Requisitos mínimos de disco por tier de licencia
- ✅ Retenciones por tipo de dato (métricas, logs, trazas)
- ✅ Regla del 70% de uso máximo
- ✅ Alertas y protecciones automáticas

---

## 📊 TIERS DE LICENCIA Y REQUISITOS DE DISCO

### **Tier 1 – ESSENTIALS** (1–20 hosts monitorizados)

**Disco recomendado para VM Rhinometric**: ≥ **200 GB**

**Retención por defecto**:
| Tipo de Dato | Retención | Volumen Estimado |
|--------------|-----------|------------------|
| **Métricas** (Prometheus) | 30 días | ~1-2 GB |
| **Logs** (Loki) | 7 días | ~5-10 GB |
| **Trazas** (Jaeger) | 3 días | ~2-5 GB |
| **Logs Docker** | 150 MB/contenedor | ~3 GB (19 contenedores) |

**Uso total estimado**: 15-25 GB  
**Margen de seguridad**: 175 GB libres

---

### **Tier 2 – GROWTH** (21–70 hosts monitorizados)

**Disco recomendado para VM Rhinometric**: ≥ **500 GB**

**Retención por defecto**:
| Tipo de Dato | Retención | Volumen Estimado |
|--------------|-----------|------------------|
| **Métricas** (Prometheus) | 30 días | ~5-10 GB |
| **Logs** (Loki) | 5 días | ~15-30 GB |
| **Trazas** (Jaeger) | 2 días | ~5-10 GB |
| **Logs Docker** | 150 MB/contenedor | ~3 GB |

**Uso total estimado**: 30-60 GB  
**Margen de seguridad**: 440 GB libres

---

### **Tier 3 – ENTERPRISE** (71+ hosts, sin límite)

**Disco recomendado para VM Rhinometric**: ≥ **1 TB**

**Retención por defecto**:
| Tipo de Dato | Retención | Volumen Estimado |
|--------------|-----------|------------------|
| **Métricas** (Prometheus) | 15 días | ~20-50 GB |
| **Logs** (Loki) | 3 días | ~50-100 GB |
| **Trazas** (Jaeger) | 24-48h | ~10-20 GB |
| **Logs Docker** | 150 MB/contenedor | ~3 GB |

**Uso total estimado**: 100-200 GB  
**Margen de seguridad**: 800 GB libres

**⚠️ Nota**: En entornos con 200+ hosts, considerar reducir retención de logs a 2 días o implementar muestreo de trazas.

---

## 🛡️ REGLA DEL 70% (GLOBAL)

**Rhinometric no debe usar más del 70% del disco asignado a la VM.**

### **Niveles de alerta**:

| Uso de Disco | Estado | Acción Automática |
|--------------|--------|-------------------|
| **< 70%** | ✅ **NORMAL** | Ninguna |
| **70-80%** | ⚠️ **WARNING** | Alerta visual en dashboard |
| **80-85%** | ⚠️ **WARNING HIGH** | Alerta crítica + notificación |
| **85-90%** | 🚨 **CRITICAL** | **Disk Guardian** activa medidas de emergencia |
| **> 90%** | ☠️ **EMERGENCY** | Parar ingesta no crítica (promtail, traces) |

### **Disk Guardian** (Protección automática):
- Script `disk-guardian.sh` ejecutándose cada 5 minutos vía cron
- Si disco > 90%:
  1. Registra log crítico
  2. Detiene `promtail` (logs) y `otel-collector` (traces)
  3. **NO toca servicios del cliente** (PostgreSQL, Redis, Backend)
  4. Envía alerta a Alertmanager
  5. Espera intervención humana

---

## 📐 POLÍTICA DE RETENCIÓN POR COMPONENTE

### **1. Logs Docker** (CRÍTICO)

**Incidente**: 288 GB acumulados en 3 días sin rotación.

**Configuración obligatoria**:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
```

**Límite por contenedor**: 150 MB (50MB × 3 archivos)  
**Límite total (19 contenedores)**: ~3 GB

**Ubicación**: `/etc/docker/daemon.json`  
**Aplicación**: `systemctl restart docker` (requiere downtime ~1 minuto)

---

### **2. Prometheus (Métricas)**

**Datos almacenados**:
- Series temporales de métricas (CPU, RAM, latencia, etc.)
- ~2,000-5,000 series activas por 20 hosts

**Configuración**:
```yaml
command:
  - '--storage.tsdb.retention.time=30d'  # Tier 1/2
  - '--storage.tsdb.retention.size=50GB' # Límite seguridad
```

**Ajustes por Tier**:
- **Tier 1/2**: 30 días
- **Tier 3**: 15 días (ajustable a 30d si hay espacio)

**Volumen actual**: 144 MB (46 horas de métricas)  
**Proyección 30 días**: ~2-5 GB

---

### **3. Loki (Logs estructurados)**

**Datos almacenados**:
- Logs JSON del backend (request_id, duration_ms, endpoint, etc.)
- Logs de servicios del cliente
- **Mayor consumidor de espacio** (~70% del total)

**Volumen actual**: 3.3 GB (46 horas)  
**Tasa acumulación**: ~1.7 GB/día

**Configuración** (`config/loki-config.yml`):
```yaml
limits_config:
  retention_period: 168h  # 7 días (Tier 1)

table_manager:
  retention_deletes_enabled: true
  retention_period: 168h
```

**Ajustes por Tier**:
- **Tier 1**: 7 días (168h) → ~12 GB
- **Tier 2**: 5 días (120h) → ~8.5 GB
- **Tier 3**: 3 días (72h) → ~5 GB

---

### **4. Jaeger (Trazas distribuidas)**

**Datos almacenados**:
- Spans de OpenTelemetry
- Traces de requests HTTP (inicio → DB → respuesta)

**Volumen actual**: 60 KB (contenedor nuevo)  
**Proyección**: 2-5 GB/semana en producción con tráfico alto

**Configuración**:
```yaml
environment:
  SPAN_STORAGE_TYPE: badger
  BADGER_EPHEMERAL: false
  BADGER_TTL: "72h"  # 3 días (Tier 1)
```

**Ajustes por Tier**:
- **Tier 1**: 3 días (72h)
- **Tier 2**: 2 días (48h)
- **Tier 3**: 24-48h

---

### **5. PostgreSQL (Base de datos)**

**Datos almacenados**:
- Usuarios, servicios, anomalías, configuración
- **No crece indefinidamente** (datos operacionales, no históricos)

**Volumen actual**: 47 MB  
**Proyección**: 100-500 MB (estable)

**Retención**:
- Sin límite (datos operacionales críticos)
- Cleanup manual de anomalías antiguas si fuera necesario

---

### **6. Grafana (Dashboards)**

**Datos almacenados**:
- Dashboards JSON
- Configuraciones de datasources
- Usuarios y permisos

**Volumen actual**: 1.2 MB  
**Proyección**: 10-50 MB (estable)

**Retención**: Sin límite (configuración crítica)

---

## 🚨 ALERTAS DE DISCO (PROMETHEUS)

**Archivo**: `config/rules/disk-alerts.yml`

### **Alerta 1: DiskUsageWarning**
```yaml
- alert: DiskUsageWarning
  expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.30
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Disco en WARNING - Uso > 70%"
    description: "Espacio disponible: {{ $value | humanizePercentage }}"
```

### **Alerta 2: DiskUsageCritical**
```yaml
- alert: DiskUsageCritical
  expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "🚨 DISCO CRÍTICO - Uso > 85%"
    description: "Disk Guardian activará medidas de emergencia en < 90%"
```

---

## 📋 REQUISITOS DE INSTALACIÓN

### **Para nuevas instalaciones**:

1. **Verificar disco disponible**:
   ```bash
   df -h /
   # Debe tener ≥ 200GB para Tier 1
   ```

2. **Aplicar políticas de almacenamiento**:
   ```bash
   cd /opt/rhinometric/infrastructure/mi-proyecto
   chmod +x scripts/install-storage-policies.sh
   ./scripts/install-storage-policies.sh
   ```

3. **Verificar alertas de disco**:
   ```bash
   # Prometheus Alerts
   curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="disk")'
   ```

4. **Activar Disk Guardian**:
   ```bash
   # Añadir a crontab
   */5 * * * * /opt/rhinometric/infrastructure/mi-proyecto/scripts/disk-guardian.sh >> /var/log/disk-guardian.log 2>&1
   ```

---

## 🔍 MONITOREO CONTINUO

### **Dashboard "System Health"**:
- Panel: Disk Usage (/)
- Threshold lines: 70%, 85%, 90%
- Proyección de llenado (linear regression)

### **Comandos de auditoría**:
```bash
# Uso total por componente
du -sh ~/rhinometric_data_v2.2/*

# Logs Docker
du -sh /var/lib/docker/containers

# Prometheus
du -sh /var/lib/docker/volumes/rhinometric_prometheus-data

# Ver qué contenedor genera más logs
du -sh /var/lib/docker/containers/* | sort -hr | head -5
```

---

## ✅ CUMPLIMIENTO

**Esta política debe cumplirse en**:
- ✅ Todas las instalaciones nuevas (automático vía `install-storage-policies.sh`)
- ✅ VM de producción Hetzner (89.167.6.43) - **APLICADO**
- ✅ Instalaciones de clientes (verificar en `verify-installation.sh`)

**Responsable**: Equipo de infraestructura  
**Revisión**: Trimestral o después de cada incidente de disco

---

## 📚 REFERENCIAS

- **STORAGE_STRATEGY.md**: Implementación técnica detallada
- **STORAGE_INVENTORY.md**: Inventario actual de volúmenes
- **STORAGE_IMPLEMENTATION_STATUS.md**: Checklist de implementación
- **Incidente crítico**: 26 Enero 2026 - Disco 100% lleno (288GB logs Docker)

---

**Última actualización**: 26 Enero 2026  
**Versión política**: 1.0
