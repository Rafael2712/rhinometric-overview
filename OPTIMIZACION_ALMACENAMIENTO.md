# 🚀 OPTIMIZACIÓN DE ALMACENAMIENTO - RHINOMETRIC TRIAL

**Fecha:** 22 de Octubre 2025  
**Objetivo:** Reducir consumo de almacenamiento de **~15GB a ~3-5GB**  
**Retención:** Reducida de **7 días a 1-2 días**

---

## 📊 CAMBIOS APLICADOS

### 1. **PROMETHEUS** (Métricas)
- ✅ Retención: `7d` → **`1d`** (1 día)
- ✅ Límite almacenamiento: `10GB` → **`2GB`**
- ✅ Scrape interval: `15s` → **`30s`** (reduce carga en 50%)
- ✅ CPU: `1.0` → **`0.5`**
- ✅ RAM: `2G` → **`1G`**

**Ahorro estimado:** ~8GB → ~2GB

### 2. **LOKI** (Logs)
- ✅ Retención: `168h` (7d) → **`24h`** (1 día)
- ✅ Max query length: `721h` → **`48h`** (2 días)
- ✅ Max query lookback: `721h` → **`48h`**
- ✅ Cache: `100MB` → **`50MB`**
- ✅ Ingestion rate: `10MB/s` → **`5MB/s`**
- ✅ Ingestion burst: `20MB` → **`10MB`**
- ✅ CPU: `0.5` → **`0.3`**
- ✅ RAM: `1G` → **`512M`**

**Ahorro estimado:** ~5GB → ~1GB

### 3. **TEMPO** (Trazas Distribuidas)
- ✅ Block retention: `168h` (7d) → **`24h`** (1 día)
- ✅ Max duration: `168h` → **`48h`** (2 días)
- ✅ Default result limit: `20` → **`10`**
- ✅ Max concurrent queries: `20` → **`10`**
- ✅ CPU: `0.5` → **`0.3`**
- ✅ RAM: `512M` → **`256M`**

**Ahorro estimado:** ~2GB → ~500MB

### 4. **POSTGRESQL** (Base de datos)
- ✅ CPU: `1.0` → **`0.3`**
- ✅ RAM: `2G` → **`512M`**

**Ahorro estimado:** Datos transaccionales mínimos (~200MB)

### 5. **REDIS** (Cache)
- ✅ Max memory: `256MB` → **`128MB`**
- ✅ CPU: `0.2` → **`0.1`**
- ✅ RAM: `256M` → **`128M`**

**Ahorro estimado:** 256MB → 128MB

### 6. **GRAFANA** (Dashboards)
- ✅ CPU: `0.8` → **`0.4`**
- ✅ RAM: `1G` → **`512M`**

**Ahorro estimado:** Configuración ~100MB

### 7. **TELEMETRYGEN** (Generador de trazas)
- ✅ **DESHABILITADO** (comentado en docker-compose)
- ✅ Libera CPU y reduce tráfico de red innecesario

---

## 📈 RECURSOS TOTALES ANTES vs DESPUÉS

| Servicio | CPU ANTES | CPU DESPUÉS | RAM ANTES | RAM DESPUÉS |
|----------|-----------|-------------|-----------|-------------|
| Prometheus | 1.0 | **0.5** | 2G | **1G** |
| Loki | 0.5 | **0.3** | 1G | **512M** |
| Tempo | 0.5 | **0.3** | 512M | **256M** |
| Grafana | 0.8 | **0.4** | 1G | **512M** |
| PostgreSQL | 1.0 | **0.3** | 2G | **512M** |
| Redis | 0.2 | **0.1** | 256M | **128M** |
| Otros | ~1.5 | ~1.5 | ~2G | ~2G |
| **TOTAL** | **~5.5 vCPUs** | **~3.4 vCPUs** | **~9GB** | **~5GB** |

**Reducción total:**
- CPU: -38% (5.5 → 3.4 vCPUs)
- RAM: -44% (9GB → 5GB)
- Almacenamiento: -70% (~15GB → ~3-5GB estimado)

---

## ⚠️ LIMITACIONES DEL TRIAL OPTIMIZADO

### Retenciones:
- ✅ Prometheus: **1 día** de métricas
- ✅ Loki: **1 día** de logs
- ✅ Tempo: **1 día** de trazas

### Queries:
- ✅ Consultas máximas: **2 días hacia atrás**
- ✅ Resultados limitados
- ✅ Concurrent queries reducidas

### Capacidades:
- ⚠️ **NO** usar en producción
- ⚠️ Solo para **evaluación y testing**
- ⚠️ Datos más antiguos de 24h se **eliminan automáticamente**
- ⚠️ Consultas limitadas a últimas 48 horas

---

## 🎯 RECOMENDACIONES DE USO

### Para Testing:
1. ✅ Genera métricas/logs/traces diariamente
2. ✅ Revisa dashboards cada 12-24h
3. ✅ No esperes retener datos > 1 día
4. ✅ Exporta dashboards importantes como JSON

### Para Producción (Licencia Comercial):
- 📈 Retención: 30-90 días
- 📈 Almacenamiento: 100GB-1TB
- 📈 HA (Alta Disponibilidad)
- 📈 Backups automáticos
- 📈 Soporte 24/7

---

## 📝 CÓMO APLICAR LOS CAMBIOS

```bash
# 1. Detener servicios actuales
docker-compose -f docker-compose-trial.yml down

# 2. Limpiar volúmenes antiguos (OPCIONAL - BORRA DATOS)
docker volume prune -f

# 3. Iniciar con nueva configuración
docker-compose -f docker-compose-trial.yml up -d

# 4. Verificar estado
docker-compose -f docker-compose-trial.yml ps
```

---

## 🔍 MONITOREO DE ESPACIO

### Verificar uso de disco:
```bash
# Ver tamaño de volúmenes Docker
docker system df -v

# Ver espacio en contenedores específicos
docker exec rhinometric-prometheus du -sh /prometheus
docker exec rhinometric-loki du -sh /loki
docker exec rhinometric-tempo du -sh /tmp/tempo
```

### Limpiar espacio adicional:
```bash
# Limpiar imágenes no usadas
docker image prune -a -f

# Limpiar build cache
docker builder prune -a -f

# Limpiar todo (CUIDADO)
docker system prune -a --volumes -f
```

---

## 📞 SOPORTE

Si necesitas más retención o capacidad:

- 📧 Email: ventas@rhinometric.com
- 🌐 Web: https://rhinometric.com/pricing
- 💼 Licencia Comercial: Desde $999/mes

---

**© 2025 Rhinometric. Trial optimizado para evaluación.**
