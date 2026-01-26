# RHINOMETRIC - INVENTARIO DE ALMACENAMIENTO

**Fecha**: 26 de Enero, 2026  
**VM**: Hetzner CPX42 (89.167.6.43)  
**Disco total**: 301 GB  
**Estado**: Post-limpieza emergente (288 GB logs Docker eliminados)

---

## 📊 RESUMEN EJECUTIVO

| Componente | Uso Actual | Proyección 30d | Tier 1 Límite |
|------------|------------|----------------|---------------|
| **Loki** | 3.3 GB | ~12 GB | 12 GB (7d) |
| **Logs Docker** | 1.9 GB | 3 GB | 3 GB (rotación) |
| **Prometheus** | 144 MB | 2-5 GB | 5 GB (30d) |
| **PostgreSQL** | 47 MB | 100-500 MB | - |
| **Jaeger** | 60 KB | 2-5 GB | 5 GB (3d) |
| **Grafana** | 1.2 MB | 10-50 MB | - |
| **TOTAL** | ~5.4 GB | ~25-30 GB | **< 70 GB (Tier 1)** |

**Espacio disponible actual**: 275 GB (92%)  
**Margen de seguridad**: ✅ Excelente

---

## 🔍 DETALLE POR COMPONENTE

### **1. LOKI (Logs Estructurados)** 🔴 MAYOR CONSUMIDOR

**Ubicación**: `~/rhinometric_data_v2.2/loki/`  
**Uso actual**: **3.3 GB** (46 horas de logs)  
**Tasa de crecimiento**: ~**1.7 GB/día**

**Desglose**:
```bash
du -sh ~/rhinometric_data_v2.2/loki/*
3.1G    chunks/     # Datos de logs comprimidos
200M    wal/        # Write-Ahead Log (temporal)
8.0K    index/      # Índices de labels
```

**Proyección**:
| Retención | Tamaño Estimado |
|-----------|-----------------|
| 3 días | ~5 GB |
| 5 días | ~8.5 GB |
| **7 días (Tier 1)** | **~12 GB** |
| 30 días | ~50 GB |

**⚠️ Criticidad**: ALTA  
**Acción requerida**: Implementar `retention_period: 168h` (7d) en `config/loki-config.yml`

**Configuración actual**:
```bash
# ❌ SIN RETENCIÓN CONFIGURADA
grep -i retention config/loki-config.yml
# (vacío)
```

---

### **2. LOGS DOCKER** 🟠 SEGUNDO MAYOR CONSUMIDOR

**Ubicación**: `/var/lib/docker/containers/`  
**Uso actual**: **1.9 GB** (después de limpieza)

**Desglose por contenedor (top 5)**:
```bash
du -sh /var/lib/docker/containers/* | sort -hr | head -5

450M    rhinometric-loki
380M    rhinometric-console-backend
320M    rhinometric-prometheus
280M    rhinometric-otel-collector
190M    rhinometric-jaeger
```

**Histórico**:
- **Antes del incidente (24 enero)**: 288 GB ❌
- **Después de limpieza (26 enero)**: 1.9 GB ✅
- **Con rotación configurada**: máx 3 GB (19 contenedores × 150 MB)

**Configuración actual**:
```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3",
    "compress": "true"
  }
}
```
✅ **APLICADO** (26 enero 2026)

**Proyección con rotación**:
- Por contenedor: 50 MB + (50 MB × 3 comprimidos) ≈ 150 MB
- Total (19 contenedores): **~3 GB máximo**

---

### **3. PROMETHEUS (Métricas)**

**Ubicación**: `/var/lib/docker/volumes/rhinometric_prometheus-data/`  
**Uso actual**: **144 MB** (46 horas de métricas)

**Desglose**:
```bash
du -sh /var/lib/docker/volumes/rhinometric_prometheus-data/*
120M    01JKM8XZQRHN7WQVK3NAQXZC1P/  # Bloque TSDB actual
24M     wal/                        # Write-Ahead Log
```

**Métricas almacenadas**:
- Series activas: ~2,052 (visto en /metrics)
- Scrape interval: 15s
- Retention actual: ❌ **Sin límite** (por defecto 15 días)

**Proyección**:
| Retención | Tamaño Estimado |
|-----------|-----------------|
| 15 días (default) | ~2 GB |
| **30 días (Tier 1/2)** | **2-5 GB** |
| 60 días | ~8 GB |
| 90 días | ~12 GB |

**⚠️ Acción requerida**:
```yaml
# Añadir en docker-compose-v2.5.0-core.yml
command:
  - '--storage.tsdb.retention.time=30d'
  - '--storage.tsdb.retention.size=50GB'  # Safety limit
```

---

### **4. POSTGRESQL (Base de Datos)**

**Ubicación**: `~/rhinometric_data_v2.2/postgres/`  
**Uso actual**: **47 MB**

**Desglose**:
```bash
du -sh ~/rhinometric_data_v2.2/postgres/*
28M     data/base/      # Databases
12M     data/pg_wal/    # Write-Ahead Log
4M      data/global/    # System catalogs
3M      data/pg_logical/ # Logical replication
```

**Tablas principales**:
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ai_anomalies: ~15 MB
-- services: ~8 MB
-- users: ~2 MB
-- client_services: ~5 MB
```

**Proyección**: 100-500 MB (estable)

**Crecimiento esperado**:
- Datos operacionales (no históricos)
- Anomalías: ~1 MB/día (con cleanup manual si necesario)
- Sin retención automática (datos críticos)

---

### **5. JAEGER (Trazas)**

**Ubicación**: `~/rhinometric_data_v2.2/jaeger/`  
**Uso actual**: **60 KB** (contenedor nuevo, sin tráfico)

**Desglose**:
```bash
du -sh ~/rhinometric_data_v2.2/jaeger/*
32K     data/   # Badger value log
28K     key/    # Badger key dir
```

**Proyección con tráfico**:
| Retención | Tráfico | Tamaño Estimado |
|-----------|---------|-----------------|
| 24h | Bajo | 500 MB - 1 GB |
| 48h | Medio | 1-3 GB |
| **72h (Tier 1)** | **Alto** | **2-5 GB** |
| 7d | Alto | 10-15 GB |

**Configuración actual**:
```yaml
# ❌ SIN TTL CONFIGURADO
environment:
  SPAN_STORAGE_TYPE: badger
  BADGER_EPHEMERAL: false
  # BADGER_TTL: "72h"  # FALTA AÑADIR
```

**⚠️ Acción requerida**: Añadir `BADGER_TTL: "72h"` en docker-compose

---

### **6. GRAFANA (Dashboards)**

**Ubicación**: `/var/lib/docker/volumes/rhinometric_grafana-data/`  
**Uso actual**: **1.2 MB**

**Desglose**:
```bash
du -sh /var/lib/docker/volumes/rhinometric_grafana-data/*
800K    dashboards/
200K    grafana.db       # SQLite database
100K    plugins/
100K    provisioning/
```

**Proyección**: 10-50 MB (estable)

**Contenido**:
- 6 dashboards JSON
- Datasources (Prometheus, Loki, Jaeger)
- Usuarios y permisos

---

### **7. REDIS (Cache)**

**Ubicación**: `~/rhinometric_data_v2.2/redis/`  
**Uso actual**: **8 KB** (casi vacío, solo metadata)

**Proyección**: 10-50 MB (volátil)

**Nota**: Redis es cache en memoria, dump.rdb es snapshot mínimo.

---

### **8. AI ANOMALY (Modelos ML)**

**Ubicación**: `~/rhinometric_data_v2.2/ai-anomaly/`  
**Uso actual**: **4.2 MB**

**Contenido**:
- Modelos entrenados (ARIMA, aislamiento)
- Cache de predicciones

**Proyección**: 10-50 MB (estable)

---

### **9. LICENSE SERVER**

**Ubicación**: `~/rhinometric_data_v2.2/license-server/`  
**Uso actual**: **8 KB**

**Proyección**: < 10 MB (configuración estática)

---

### **10. ALERTMANAGER**

**Ubicación**: `~/rhinometric_data_v2.2/alertmanager/`  
**Uso actual**: **4 KB**

**Proyección**: < 10 MB (configuración + silences)

---

### **11. BACKUP**

**Ubicación**: `~/rhinometric_data_v2.2/backup/`  
**Uso actual**: **4 KB** (sin backups activos)

**Proyección**: Depende de política de backup

**Recomendación**: Backups externos (S3, rclone) para no saturar disco local.

---

## 📈 TENDENCIAS Y PROYECCIONES

### **Crecimiento diario estimado**:

| Componente | Crecimiento/día | Acción |
|------------|----------------|--------|
| **Loki** | **+1.7 GB** | Retención 7d → estable en ~12 GB |
| **Logs Docker** | +200 MB | Rotación → estable en 3 GB |
| **Prometheus** | +100 MB | Retención 30d → estable en 5 GB |
| **Jaeger** | +500 MB | TTL 72h → estable en 5 GB |
| **PostgreSQL** | +1 MB | Crecimiento lineal lento |

**Total sin retención**: **+2.5 GB/día** → **75 GB/mes** 🔴  
**Total con retención**: **Estable en ~25 GB** ✅

---

## 🎯 CAPACIDAD POR TIER

### **Tier 1 (1-20 hosts) - 200 GB recomendados**:

| Componente | Límite | % del disco |
|------------|--------|-------------|
| Loki (7d) | 12 GB | 6% |
| Logs Docker | 3 GB | 1.5% |
| Prometheus (30d) | 5 GB | 2.5% |
| Jaeger (3d) | 5 GB | 2.5% |
| PostgreSQL | 1 GB | 0.5% |
| Otros | 2 GB | 1% |
| **TOTAL RHINOMETRIC** | **28 GB** | **14%** |
| **Espacio libre** | **172 GB** | **86%** ✅ |

**Regla 70%**: 200 GB × 70% = 140 GB máximo uso  
**Margen**: 140 - 28 = **112 GB** de buffer ✅

---

### **Tier 2 (21-70 hosts) - 500 GB recomendados**:

| Componente | Límite | % del disco |
|------------|--------|-------------|
| Loki (5d) | 8.5 GB | 1.7% |
| Logs Docker | 3 GB | 0.6% |
| Prometheus (30d) | 10 GB | 2% |
| Jaeger (2d) | 6 GB | 1.2% |
| PostgreSQL | 2 GB | 0.4% |
| Otros | 2 GB | 0.4% |
| **TOTAL RHINOMETRIC** | **31.5 GB** | **6.3%** |
| **Espacio libre** | **468.5 GB** | **93.7%** ✅ |

**Regla 70%**: 500 GB × 70% = 350 GB máximo uso  
**Margen**: 350 - 31.5 = **318.5 GB** de buffer ✅

---

### **Tier 3 (71+ hosts) - 1 TB recomendado**:

| Componente | Límite | % del disco |
|------------|--------|-------------|
| Loki (3d) | 5 GB | 0.5% |
| Logs Docker | 3 GB | 0.3% |
| Prometheus (15d) | 50 GB | 5% |
| Jaeger (24h) | 10 GB | 1% |
| PostgreSQL | 5 GB | 0.5% |
| Otros | 5 GB | 0.5% |
| **TOTAL RHINOMETRIC** | **78 GB** | **7.8%** |
| **Espacio libre** | **946 GB** | **92.2%** ✅ |

**Regla 70%**: 1000 GB × 70% = 700 GB máximo uso  
**Margen**: 700 - 78 = **622 GB** de buffer ✅

---

## 🛠️ COMANDOS DE AUDITORÍA

### **Uso total por componente**:
```bash
du -sh ~/rhinometric_data_v2.2/* | sort -hr
```

### **Logs Docker por contenedor**:
```bash
du -sh /var/lib/docker/containers/* | sort -hr | head -10
```

### **Volúmenes Docker**:
```bash
docker system df -v
```

### **Prometheus TSDB**:
```bash
curl -s http://localhost:9090/api/v1/status/tsdb | jq
```

### **Loki chunks**:
```bash
ls -lh ~/rhinometric_data_v2.2/loki/chunks/
```

### **Jaeger traces count**:
```bash
curl -s "http://localhost:16686/api/services" | jq
```

---

## ✅ VALIDACIÓN POST-RETENCIÓN

Después de implementar las políticas, esperar 7 días y verificar:

```bash
# Script de auditoría
#!/bin/bash
echo "=== RHINOMETRIC STORAGE AUDIT ==="
echo "Fecha: $(date)"
echo ""

echo "Disco total:"
df -h / | grep /

echo ""
echo "Loki:"
du -sh ~/rhinometric_data_v2.2/loki

echo ""
echo "Prometheus:"
du -sh /var/lib/docker/volumes/rhinometric_prometheus-data

echo ""
echo "Logs Docker:"
du -sh /var/lib/docker/containers

echo ""
echo "Jaeger:"
du -sh ~/rhinometric_data_v2.2/jaeger

echo ""
echo "PostgreSQL:"
du -sh ~/rhinometric_data_v2.2/postgres

echo ""
echo "=== TOTAL RHINOMETRIC ==="
du -sh ~/rhinometric_data_v2.2
du -sh /var/lib/docker/volumes/rhinometric*
du -sh /var/lib/docker/containers
```

**Ejecutar semanalmente** y comparar con proyecciones.

---

## 📚 REFERENCIAS

- **STORAGE_POLICY.md**: Política ejecutiva
- **STORAGE_STRATEGY.md**: Implementación técnica
- **STORAGE_IMPLEMENTATION_STATUS.md**: Estado de implementación

---

**Última actualización**: 26 Enero 2026  
**Próxima auditoría**: 2 Febrero 2026 (7 días post-retención)
