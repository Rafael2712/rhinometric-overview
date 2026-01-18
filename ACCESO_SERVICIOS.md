# 🔐 RHINOMETRIC v2.2.0 - URLs y Credenciales de Acceso

**Fecha**: 4 de Noviembre de 2025  
**Estado**: ✅ 23/23 contenedores HEALTHY  
**Red**: WSL2 Ubuntu-22.04 (modo reflejada)

---

## 🎯 SERVICIOS PRINCIPALES (Interfaz Web)

### 1. 🌐 **Grafana** - Observabilidad y Dashboards
```
URL Principal: http://localhost:80
URL Alternativa: http://localhost:3000
Usuario: admin
Contraseña: rhinometric2024

Descripción: 
- Visualización de métricas (Prometheus)
- Exploración de logs (Loki)
- Análisis de traces (Tempo)
- Dashboards interactivos
```

### 2. 🎨 **Dashboard Builder** - Creación Visual de Dashboards
```
URL: http://localhost:8001
Endpoint Health: http://localhost:8001/health
Docs API: http://localhost:8001/docs

Autenticación: JWT Token (requiere licencia válida)

Descripción:
- API FastAPI para crear dashboards
- 4 templates predefinidos
- Integración con PostgreSQL
- Validación de licencias

Endpoints Principales:
- GET  /health          → Estado del servicio
- POST /dashboards      → Crear dashboard
- GET  /dashboards      → Listar dashboards
- GET  /dashboards/{id} → Obtener dashboard
- GET  /templates       → Listar templates disponibles
```

### 3. 🔐 **License Server** - Sistema de Licencias
```
URL: http://localhost:5000
Docs API: http://localhost:5000/docs
Endpoint Health: http://localhost:5000/health

Autenticación: API Key generada automáticamente

Descripción:
- FastAPI v2.0
- Licencias RSA-4096
- Validación automática
- Redis para caché
- PostgreSQL para persistencia

Endpoints Principales:
- POST /generate       → Generar nueva licencia
- POST /validate       → Validar licencia existente
- GET  /licenses       → Listar licencias
- GET  /health         → Estado del servicio
```

### 4. 🖼️ **License UI** - Interfaz de Gestión de Licencias
```
URL: http://localhost:8092

Autenticación: No requiere (frontend Vite)

Descripción:
- Interfaz web moderna (Vite + React)
- Gestión visual de licencias
- Integración con License Server
- Validación en tiempo real
```

### 5. 🔌 **API Proxy** - Conector Universal de APIs
```
URL: http://localhost:8081
Métricas: http://localhost:8081/api/metrics/prometheus
Health: http://localhost:8081/health

Autenticación: No requiere (uso interno)

Descripción:
- Proxy para APIs externas
- Caché Redis (5 min TTL)
- Métricas Prometheus
- 8 conectores preconfigurados
```

---

## 📊 MONITOREO Y OBSERVABILIDAD

### 6. 📈 **Prometheus** - Motor de Métricas
```
URL: http://localhost:9090
Graph: http://localhost:9090/graph
Targets: http://localhost:9090/targets
Alerts: http://localhost:9090/alerts

Autenticación: No requiere

Descripción:
- Time-series database
- Consultas PromQL
- Scraping de 10+ exporters
- Almacenamiento local
```

### 7. 📝 **Loki** - Agregación de Logs
```
URL: http://localhost:3100
Ready: http://localhost:3100/ready
Metrics: http://localhost:3100/metrics

Autenticación: No requiere (acceso desde Grafana)

Descripción:
- Sistema de logs distribuido
- Query language LogQL
- Integración con Promtail
- Almacenamiento eficiente
```

### 8. 🔍 **Tempo** - Distributed Tracing
```
URL: http://localhost:3200
Ready: http://localhost:3200/ready
Status: http://localhost:3200/status

Autenticación: No requiere (acceso desde Grafana)

Descripción:
- Traces distribuidos
- Integración OpenTelemetry
- Correlación con métricas y logs
- Almacenamiento local
```

### 9. 🚨 **AlertManager** - Gestión de Alertas
```
URL: http://localhost:9093
Status: http://localhost:9093/#/status
Alerts: http://localhost:9093/#/alerts

Autenticación: No requiere

Descripción:
- Gestión de alertas
- Routing y agrupación
- Integración con Prometheus
- Notificaciones (email, Slack, etc.)
```

### 10. 📦 **cAdvisor** - Métricas de Contenedores
```
URL: http://localhost:8080
Containers: http://localhost:8080/containers
Docker: http://localhost:8080/docker

Autenticación: No requiere

Descripción:
- Métricas de contenedores Docker
- CPU, memoria, red, disco
- Visualización en tiempo real
- Integración con Prometheus
```

---

## 🔍 EXPORTERS (Métricas Especializadas)

### 11. 💻 **Node Exporter** - Métricas del Sistema
```
URL: http://localhost:9100
Metrics: http://localhost:9100/metrics

Métricas:
- CPU, memoria, disco
- Red, procesos
- Filesystem, hardware
```

### 12. 🗄️ **PostgreSQL Exporter** - Métricas de Base de Datos
```
URL: http://localhost:9187
Metrics: http://localhost:9187/metrics

Métricas:
- Conexiones, queries
- Replicación, vacuum
- Bloqueos, transacciones
```

### 13. 🔎 **Blackbox Exporter** - Monitoreo de Endpoints
```
URL: http://localhost:9115
Config: http://localhost:9115/config
Metrics: http://localhost:9115/metrics

Descripción:
- Probing HTTP/HTTPS/TCP/ICMP
- SSL certificate validation
- DNS queries
```

### 14. 🌍 **VeriVerde** - ESG Monitoring
```
URL: http://localhost:9200
Metrics: http://localhost:9200/metrics

Descripción:
- Monitoreo ESG (Environmental, Social, Governance)
- Métricas de sostenibilidad
- Integración con Prometheus
```

### 15. 🤖 **AI Anomaly Detector** - Detección de Anomalías
```
URL: http://localhost:8085
Health: http://localhost:8085/health

Descripción:
- Machine Learning para anomalías
- Análisis predictivo
- Python + scikit-learn
```

---

## 🗄️ BASES DE DATOS

### 16. 🐘 **PostgreSQL** - Base de Datos Principal
```
Host: localhost
Puerto: 5432
Base de datos: rhinometric
Usuario: rhinometric
Contraseña: rhinometric

Connection String:
postgresql://rhinometric:rhinometric@localhost:5432/rhinometric

Clientes recomendados:
- DBeaver
- pgAdmin
- psql (CLI)
- DataGrip
```

### 17. 🔴 **Redis** - Caché y Cola de Mensajes
```
Host: localhost
Puerto: 6379
Contraseña: rhinometric
Base de datos: 0

Connection String:
redis://:rhinometric@localhost:6379/0

Clientes recomendados:
- Redis Insight
- RedisInsight Desktop
- redis-cli
```

---

## 📡 TELEMETRÍA

### 18. 📊 **OpenTelemetry Collector**
```
Puerto OTLP gRPC: 4317
Puerto OTLP HTTP: 4318

Endpoint gRPC: http://localhost:4317
Endpoint HTTP: http://localhost:4318

Descripción:
- Recolección de traces, métricas y logs
- Procesamiento y exportación
- Integración con Tempo, Prometheus, Loki
```

### 19. 📋 **Promtail** - Recolector de Logs
```
Puerto interno: 9080

Descripción:
- Agente de logs para Loki
- Scraping de archivos de log
- Procesamiento y etiquetado
- Push a Loki
```

---

## 🛠️ SERVICIOS INTERNOS (Sin interfaz web)

### 20. 🔍 **License Monitor**
```
Descripción:
- Monitoreo continuo de licencias
- Validación automática
- Alertas de expiración
```

### 21. 💾 **Backup Service**
```
Descripción:
- Backup automático de PostgreSQL
- Snapshots de volúmenes
- Retención configurada
```

### 22. 📄 **Report Generator**
```
Descripción:
- Generación de reportes programados
- PDF, Excel, CSV
- Envío por email
```

---

## 🧪 VERIFICACIÓN DE SERVICIOS

### Comando para verificar estado de todos los contenedores:
```bash
wsl -d Ubuntu-22.04 -- docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

### Comando para verificar healthchecks:
```bash
wsl -d Ubuntu-22.04 -- bash -c "docker ps --format '{{.Status}}' | grep -c '(healthy)'"
```

### Verificar logs de un servicio específico:
```bash
wsl -d Ubuntu-22.04 -- docker logs rhinometric-<nombre-servicio> --tail=50
```

---

## 🔧 TROUBLESHOOTING

### Si un servicio no responde:

1. **Verificar estado del contenedor:**
   ```bash
   wsl -d Ubuntu-22.04 -- docker ps | grep <nombre-servicio>
   ```

2. **Ver logs:**
   ```bash
   wsl -d Ubuntu-22.04 -- docker logs <nombre-contenedor> --tail=100
   ```

3. **Verificar healthcheck:**
   ```bash
   wsl -d Ubuntu-22.04 -- docker inspect <nombre-contenedor> | grep -A 10 Health
   ```

4. **Reiniciar servicio:**
   ```bash
   wsl -d Ubuntu-22.04 -- bash -c "cd /mnt/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto && docker compose -f docker-compose-v2.2.0.yml restart <nombre-servicio>"
   ```

### Si no puedes acceder desde Windows:

1. **Verificar WSL2 networking:**
   ```bash
   wsl -d Ubuntu-22.04 -- ip addr show eth0
   ```

2. **Probar desde dentro de WSL:**
   ```bash
   wsl -d Ubuntu-22.04 -- curl http://localhost:<puerto>
   ```

3. **Verificar firewall de Windows:**
   - Windows Defender Firewall → Configuración avanzada
   - Reglas de entrada → Permitir puertos

---

## 📚 RECURSOS ADICIONALES

### Documentación:
- `IMPLEMENTATION_STATUS_v2.4.0.md` - Estado de implementación
- `VALIDATION_REPORT_v2.3.1.md` - Reporte de validación
- `DASHBOARD_BUILDER_GUIDE.md` - Guía Dashboard Builder
- `CREDENCIALES-v2.2.0.md` - Credenciales detalladas

### Scripts útiles:
- `check-health.sh` - Verificar salud de servicios
- `check_status.sh` - Estado general
- `check_logs.sh` - Ver logs agregados

---

## ✅ ESTADO ACTUAL (4 Nov 2025)

```
Total contenedores: 23
✅ HEALTHY: 23
❌ UNHEALTHY: 0
📊 Tasa de éxito: 100%
```

**Todos los servicios están operativos y responden correctamente.**

---

## 🎯 ACCESO RÁPIDO (URLs más usadas)

1. **Grafana**: http://localhost:80 (admin / rhinometric2024)
2. **Prometheus**: http://localhost:9090
3. **Dashboard Builder**: http://localhost:8001
4. **License Server**: http://localhost:5000/docs
5. **cAdvisor**: http://localhost:8080

---

*Generado automáticamente por GitHub Copilot*  
*RHINOMETRIC Platform v2.2.0*
