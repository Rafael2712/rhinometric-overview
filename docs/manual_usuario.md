# 🦏 Rhinometric v2.1.0 - Manual de Usuario

**Plataforma de Observabilidad Empresarial**

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación Rápida](#instalación-rápida)
4. [Acceso a Servicios](#acceso-a-servicios)
5. [Dashboards de Grafana](#dashboards-de-grafana)
6. [Monitoreo de APIs Externas](#monitoreo-de-apis-externas)
7. [Gestión de Licencias](#gestión-de-licencias)
8. [Configuración Avanzada](#configuración-avanzada)
9. [Troubleshooting](#troubleshooting)
10. [Soporte](#soporte)

---

## 🎯 Introducción

Rhinometric es una plataforma completa de observabilidad empresarial que integra:

- **Métricas**: Prometheus + Node Exporter + Postgres Exporter
- **Logs**: Loki + Promtail
- **Trazas**: Tempo + OpenTelemetry Collector
- **Visualización**: Grafana con 8 dashboards pre-configurados
- **Alertas**: Alertmanager con reglas predefinidas
- **APIs**: Conector para monitoreo de servicios externos

### ✨ Características Principales

✅ **Instalación en 1 comando** - Scripts automatizados para Linux, macOS y Windows  
✅ **16 servicios integrados** - Stack completo pre-configurado  
✅ **8 dashboards listos** - Métricas, logs, trazas, APIs  
✅ **Alertas inteligentes** - CPU, RAM, disk, API downtime  
✅ **Multi-tenant** - Aislamiento de datos por cliente  
✅ **Alta disponibilidad** - Configuración HA opcional  

---

## 💻 Requisitos del Sistema

### Mínimos (Trial/Desarrollo)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 50 GB libres
- **SO**: Linux (Ubuntu 20.04+), macOS (11+), Windows 10/11
- **Software**: Docker 20.10+, Docker Compose 2.0+

### Recomendados (Producción)
- **CPU**: 8 cores
- **RAM**: 16 GB
- **Disco**: 200 GB SSD
- **Red**: 1 Gbps
- **SO**: Ubuntu 22.04 LTS o Rocky Linux 9

### Puertos Requeridos
```
3000  - Grafana (UI principal)
5000  - License Server API
5432  - PostgreSQL
6379  - Redis
8090  - API Proxy
8091  - API Connector UI
8092  - License Management UI
9090  - Prometheus
9093  - Alertmanager
9100  - Node Exporter
```

---

## 🚀 Instalación Rápida

### Linux / macOS

```bash
# 1. Descargar Rhinometric
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal

# 2. Configurar licencia (si ya la tienes)
cp .env.example .env
nano .env  # Agregar LICENSE_KEY

# 3. Ejecutar instalador
chmod +x install.sh
./install.sh

# 4. Verificar servicios
docker compose -f docker-compose-v2.1.0.yml ps
```

### Windows (PowerShell)

```powershell
# 1. Descargar Rhinometric
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto\infrastructure\mi-proyecto\rhinometric-trial-v2.1.0-universal

# 2. Configurar licencia
copy .env.example .env
notepad .env  # Agregar LICENSE_KEY

# 3. Ejecutar instalador
.\install.ps1

# 4. Verificar servicios
docker compose -f docker-compose-v2.1.0.yml ps
```

---

## 🌐 Acceso a Servicios

Después de la instalación, accede a:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Grafana** | http://localhost:3000 | Ver archivo `credentials.txt` |
| **Prometheus** | http://localhost:9090 | - |
| **License Server API** | http://localhost:5000/api/docs | - |
| **API Connector UI** | http://localhost:8091 | - |
| **License Management** | http://localhost:8092 | - |
| **Alertmanager** | http://localhost:9093 | - |

### 🔐 Primer Acceso a Grafana

1. Abrir http://localhost:3000
2. Usuario: `admin`
3. Contraseña: Ver `credentials.txt` generado por el instalador
4. **Cambiar contraseña** en el primer login (obligatorio)

---

## 📊 Dashboards de Grafana

Rhinometric incluye 8 dashboards pre-configurados:

### 1. 📈 **System Overview**
- **Descripción**: Métricas generales del sistema
- **Contenido**:
  - CPU usage por core
  - RAM disponible/usada
  - Disk I/O y espacio libre
  - Network traffic (ingress/egress)
- **Uso**: Monitoreo general de salud del servidor

### 2. 🗄️ **Database Health**
- **Descripción**: PostgreSQL performance
- **Contenido**:
  - Conexiones activas
  - Query time promedio
  - Cache hit ratio
  - Transacciones por segundo
  - Locks y deadlocks
- **Uso**: Optimización de queries y detección de cuellos de botella

### 3. 🐳 **Container Metrics**
- **Descripción**: Docker containers via cAdvisor
- **Contenido**:
  - CPU/RAM por contenedor
  - Network I/O
  - Restart count
  - Container health status
- **Uso**: Identificar contenedores problemáticos

### 4. 🌐 **API Monitoring**
- **Descripción**: Servicios externos monitoreados
- **Contenido**:
  - Response time (p50, p95, p99)
  - Status codes (2xx, 4xx, 5xx)
  - Availability %
  - Error rate
- **Uso**: SLA tracking de APIs externas

### 5. 📝 **Logs Explorer**
- **Descripción**: Búsqueda centralizada de logs
- **Contenido**:
  - Filtros por servicio, severity, timestamp
  - Log stream en tiempo real
  - Búsqueda full-text
  - Exportación de logs
- **Uso**: Debugging y auditoría

### 6. 🔍 **Distributed Tracing**
- **Descripción**: Service graph y latency
- **Contenido**:
  - Service dependency map
  - Trace timeline
  - Span duration heatmap
  - Error traces
- **Uso**: Identificar microservicios lentos

### 7. 📋 **License Management**
- **Descripción**: Estado de licencias
- **Contenido**:
  - Licencias activas/expiradas
  - Timeline de expiración
  - Uso por tipo (trial/annual/permanent)
- **Uso**: Gestión de clientes

### 8. 🚨 **Alerting Dashboard**
- **Descripción**: Alertas activas e históricas
- **Contenido**:
  - Alertas firing/pending
  - Alert history
  - MTTR (Mean Time To Resolve)
  - Silences configurados
- **Uso**: Incident management

---

## 🔌 Monitoreo de APIs Externas

### Agregar una API Externa

1. **Acceder al API Connector UI**:
   - URL: http://localhost:8091
   
2. **Configurar API**:
   ```json
   {
     "name": "GitHub API",
     "endpoint": "https://api.github.com/status",
     "auth_type": "none",
     "scrape_interval": 60
   }
   ```

3. **Verificar en Grafana**:
   - Dashboard: **API Monitoring**
   - Métricas aparecerán en ~2 minutos

### Tipos de Autenticación Soportados

- **None**: Sin autenticación
- **Bearer Token**: `Authorization: Bearer <token>`
- **API Key**: Header personalizado
- **Basic Auth**: Username + Password

### Ejemplo con Bearer Token

```bash
curl -X POST http://localhost:5000/api/external-apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Private API",
    "endpoint": "https://api.example.com/health",
    "auth_type": "bearer",
    "auth_token": "your_token_here",
    "scrape_interval": 120
  }'
```

---

## 🎫 Gestión de Licencias

### Crear Licencia (UI)

1. **Acceder**: http://localhost:8092
2. **Click** en "Crear Nueva Licencia"
3. **Completar formulario**:
   - Nombre del cliente
   - Email
   - Empresa
   - Tipo: Trial (30d) / Annual (365d) / Permanent
4. **Enviar**: La licencia se genera y envía por email automáticamente

### Crear Licencia (API)

```bash
curl -X POST http://localhost:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Acme Corp",
    "client_email": "admin@acme.com",
    "client_company": "Acme Corporation",
    "license_type": "annual"
  }'
```

### Listar Licencias

```bash
# Ver todas las licencias
curl http://localhost:5000/api/admin/licenses

# Estadísticas
curl http://localhost:5000/api/admin/licenses/stats
```

---

## ⚙️ Configuración Avanzada

### Personalizar Alertas

Editar `prometheus/rules/alerts.yml`:

```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RAM crítica en {{ $labels.instance }}"
```

Reiniciar Prometheus:
```bash
docker compose -f docker-compose-v2.1.0.yml restart prometheus
```

### Configurar Retención de Datos

Editar `docker-compose-v2.1.0.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=90d'  # 90 días de métricas
    - '--storage.tsdb.retention.size=50GB'

loki:
  command:
    - '-config.file=/etc/loki/local-config.yaml'
    - '-table-manager.retention-period=30d'  # 30 días de logs
```

### Habilitar HTTPS

1. **Generar certificados**:
   ```bash
   cd nginx
   ./generate-ssl-cert.sh
   ```

2. **Actualizar nginx.conf**:
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       ...
   }
   ```

3. **Reiniciar Nginx**:
   ```bash
   docker compose -f docker-compose-v2.1.0.yml restart nginx
   ```

---

## 🔧 Troubleshooting

### Problema: Servicios no inician

**Síntomas**: `docker compose ps` muestra servicios en estado "Restarting"

**Solución**:
```bash
# Ver logs del servicio problemático
docker compose -f docker-compose-v2.1.0.yml logs <service_name>

# Verificar puertos ocupados
netstat -tulpn | grep -E '3000|5432|9090'

# Liberar puertos y reiniciar
docker compose -f docker-compose-v2.1.0.yml down
docker compose -f docker-compose-v2.1.0.yml up -d
```

### Problema: Grafana no carga dashboards

**Síntomas**: Dashboards aparecen vacíos

**Solución**:
```bash
# Verificar Prometheus está scrapeando
curl http://localhost:9090/api/v1/targets

# Verificar Loki recibe logs
curl http://localhost:3100/ready

# Reimportar dashboards
docker compose -f docker-compose-v2.1.0.yml restart grafana
```

### Problema: Email de licencia no llega

**Síntomas**: Licencia creada pero email no se envía

**Solución**:
1. Verificar SMTP_PASSWORD en `.env`
2. Comprobar logs:
   ```bash
   docker compose -f docker-compose-v2.1.0.yml logs license-server-v2 | grep "Email"
   ```
3. Verificar app password de Zoho:
   - https://accounts.zoho.com/home#security/security
   - Crear nuevo "App Password"
   - Actualizar `.env` y reiniciar:
     ```bash
     docker compose -f docker-compose-v2.1.0.yml restart license-server-v2
     ```

### Problema: Disco lleno

**Síntomas**: Servicios lentos, errores de escritura

**Solución**:
```bash
# Verificar uso de disco
docker system df

# Limpiar imágenes y volúmenes no usados
docker system prune -a --volumes

# Reducir retención de datos (ver Configuración Avanzada)
```

---

## 📞 Soporte

### Canales de Soporte

- **Email**: soporte@rhinometric.com
- **Web**: https://rhinometric.com
- **GitHub Issues**: https://github.com/Rafael2712/mi-proyecto/issues
- **Documentación**: Este manual + README.md

### Información para Reportar Issues

Incluir siempre:
1. Versión de Rhinometric (`docker compose version`)
2. Sistema operativo y versión
3. Logs relevantes (`docker compose logs <service>`)
4. Pasos para reproducir el problema
5. Screenshot si aplica

### Horarios de Atención

- **Lunes a Viernes**: 9:00 - 18:00 (CET)
- **Email 24/7**: Respuesta en 24-48h
- **Emergencias**: contacto@rhinometric.com

---

## 📚 Recursos Adicionales

- **README.md**: Documentación completa del proyecto
- **CONFIGURAR_EMAIL_ZOHO.md**: Guía de configuración de emails
- **CHANGELOG.md**: Historial de versiones
- **Terraform**: `terraform/oracle-cloud/README.md` para deploy en cloud

---

**© 2025 Rhinometric. Todos los derechos reservados.**

Versión del documento: 2.1.0  
Última actualización: Octubre 2025

---

> **Nota**: Este documento debe convertirse a PDF usando:
> - Pandoc: `pandoc manual_usuario.md -o manual_usuario.pdf`
> - Markdown to PDF: https://www.markdowntopdf.com/
> - VSCode Extension: "Markdown PDF"
