# 📊 RhinoMetric Report Generator v2.2.0 - Guía Completa

## 🎯 Descripción General

Sistema profesional de generación de reportes PDF/HTML con entrega por email y programación automática, integrado con Prometheus, AI Anomaly Detection y Grafana.

---

## 🚀 Inicio Rápido

### 1. Construir y Levantar el Servicio

```bash
cd /c/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# Build del servicio
docker-compose -f docker-compose-v2.2.0.yml build rhinometric-report-generator

# Levantar el servicio
docker-compose -f docker-compose-v2.2.0.yml up -d rhinometric-report-generator

# Verificar logs
docker logs -f rhinometric-report-generator
```

### 2. Verificar Salud del Servicio

```bash
# Health check
curl http://localhost:8086/health

# Documentación API (Swagger)
open http://localhost:8086/docs

# Métricas Prometheus
curl http://localhost:8086/metrics
```

---

## 📋 Casos de Uso

### Caso 1: Generar Reporte Ejecutivo PDF (On-Demand)

**Objetivo:** Generar un reporte ejecutivo de las últimas 24 horas en formato PDF.

```bash
curl -X POST http://localhost:8086/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "executive",
    "period_hours": 24,
    "formats": ["pdf"],
    "include_charts": true,
    "include_anomalies": true,
    "include_metrics": true
  }'
```

**Respuesta:**

```json
{
  "report_id": "executive_20240101_080000",
  "report_type": "executive",
  "status": "completed",
  "generated_at": "2024-01-01T08:00:00",
  "formats": ["pdf"],
  "files": {
    "pdf": "/app/reports/executive_20240101_080000.pdf"
  },
  "email_sent": false,
  "recipients": []
}
```

**Descargar el reporte:**

```bash
# Listar reportes disponibles
curl http://localhost:8086/api/v1/reports/list

# Descargar el PDF
curl -O http://localhost:8086/api/v1/reports/download/executive_20240101_080000.pdf
```

---

### Caso 2: Reporte con Envío Automático por Email

**Objetivo:** Generar reporte y enviarlo automáticamente a múltiples destinatarios.

```bash
curl -X POST http://localhost:8086/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "executive",
    "period_hours": 24,
    "formats": ["pdf", "html"],
    "recipients": [
      "ceo@rhinometric.com",
      "cto@rhinometric.com",
      "admin@rhinometric.com"
    ],
    "include_charts": true,
    "include_anomalies": true,
    "include_metrics": true
  }'
```

**Resultado:**
- PDF y HTML generados
- Email enviado a 3 destinatarios con ambos archivos adjuntos
- Email incluye resumen ejecutivo visual (HTML template)

---

### Caso 3: Reporte de Anomalías (48 horas)

**Objetivo:** Análisis profundo de anomalías detectadas por IA en las últimas 48 horas.

```bash
curl -X POST http://localhost:8086/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "anomaly",
    "period_hours": 48,
    "formats": ["pdf"],
    "recipients": ["ml-team@rhinometric.com"],
    "include_charts": true,
    "include_anomalies": true,
    "include_metrics": false
  }'
```

**Contenido del reporte:**
- Todas las anomalías detectadas (últimas 48h)
- Confidence scores por modelo (Isolation Forest, LOF, One-Class SVM, Statistical)
- Distribución de severidad (high, medium, low)
- Top 20 métricas con más anomalías
- Gráficas de detección en el tiempo

---

### Caso 4: Reporte Técnico Semanal

**Objetivo:** Reporte técnico detallado de 7 días para el equipo DevOps.

```bash
curl -X POST http://localhost:8086/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "technical",
    "period_hours": 168,
    "formats": ["pdf"],
    "recipients": [
      "devops@rhinometric.com",
      "sre@rhinometric.com"
    ],
    "include_charts": true,
    "include_anomalies": true,
    "include_metrics": true
  }'
```

**Contenido del reporte:**
- **System Metrics:**
  - CPU Usage (current, avg, min, max)
  - Memory Usage (current, avg, min, max)
  - Disk Usage (current, avg, min, max)
  - Network Traffic (RX/TX in MB/s)

- **Application Metrics:**
  - HTTP Request Rate (req/s)
  - HTTP Error Rate (%)
  - API Latency P95 (ms)
  - Database Connections (active)

- **Anomalies:** Tabla completa con timestamp, severidad, confidence
- **Alerts:** Alertas activas en el período

---

## 📅 Configuración de Reportes Programados

### Editar config.yaml

El archivo `rhinometric-report-generator/config.yaml` contiene reportes pre-configurados:

```yaml
reports:
  # Reporte Diario Ejecutivo (8 AM)
  - name: executive_daily
    display_name: "Executive Daily Report"
    enabled: true
    type: executive
    format: [pdf, html]
    recipients:
      - admin@rhinometric.com
    schedule:
      enabled: true
      cron: "0 8 * * *"  # Daily at 8 AM UTC
      timezone: UTC
    lookback_hours: 24

  # Reporte Técnico Diario (9 AM)
  - name: technical_daily
    display_name: "Technical Daily Report"
    enabled: true
    type: technical
    format: [pdf]
    recipients:
      - devops@rhinometric.com
      - sre@rhinometric.com
    schedule:
      enabled: true
      cron: "0 9 * * *"  # Daily at 9 AM UTC
    lookback_hours: 24

  # Reporte Semanal (Lunes 8 AM)
  - name: executive_weekly
    display_name: "Executive Weekly Summary"
    enabled: true
    type: executive
    format: [pdf, html]
    recipients:
      - ceo@rhinometric.com
      - cto@rhinometric.com
    schedule:
      enabled: true
      cron: "0 8 * * 1"  # Every Monday at 8 AM UTC
    lookback_hours: 168  # 7 days

  # Reporte Mensual (1er día del mes, 8 AM)
  - name: executive_monthly
    display_name: "Executive Monthly Report"
    enabled: true
    type: executive
    format: [pdf]
    recipients:
      - executive-team@rhinometric.com
    schedule:
      enabled: true
      cron: "0 8 1 * *"  # First day of month at 8 AM UTC
    lookback_hours: 720  # 30 days
```

### Recargar Configuración sin Reiniciar

```bash
# Recargar config.yaml en caliente
curl -X POST http://localhost:8086/api/v1/config/reload

# Verificar configuración actual
curl http://localhost:8086/api/v1/config | jq
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno

El servicio usa variables de entorno para configuración sensible:

```bash
# En docker-compose-v2.2.0.yml
environment:
  # Servicio
  HOST: 0.0.0.0
  PORT: 8086
  LOG_LEVEL: INFO  # DEBUG, INFO, WARNING, ERROR
  
  # Data sources
  PROMETHEUS_URL: http://prometheus:9090
  GRAFANA_URL: http://grafana:3000
  GRAFANA_USER: admin
  GRAFANA_PASSWORD: ${GRAFANA_PASSWORD:-admin}
  
  # SMTP
  SMTP_ENABLED: "true"
  SMTP_HOST: smtp.zoho.eu
  SMTP_PORT: 587
  SMTP_USERNAME: rafael.canelon@rhinometric.com
  SMTP_PASSWORD: ${SMTP_PASSWORD}
  SMTP_USE_TLS: "true"
  SMTP_FROM: rafael.canelon@rhinometric.com
  SMTP_FROM_NAME: "RhinoMetric Reports"
  
  # Storage
  REPORTS_DIR: /app/reports
  MAX_AGE_DAYS: 30  # Retención de reportes
  MAX_SIZE_MB: 1000  # Límite de espacio
```

### Configurar Gmail como SMTP

```bash
# 1. Habilitar 2FA en tu cuenta Gmail
# 2. Generar App Password: https://myaccount.google.com/apppasswords
# 3. Configurar en docker-compose:

environment:
  SMTP_HOST: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USERNAME: tu-email@gmail.com
  SMTP_PASSWORD: "xxxx xxxx xxxx xxxx"  # App Password
  SMTP_USE_TLS: "true"
```

### Configurar SendGrid

```bash
environment:
  SMTP_HOST: smtp.sendgrid.net
  SMTP_PORT: 587
  SMTP_USERNAME: apikey
  SMTP_PASSWORD: "SG.xxxxxxxxxxxxxxxxxx"
  SMTP_USE_TLS: "true"
```

---

## 📊 API Endpoints Completos

### POST /api/v1/reports/generate
**Genera un reporte nuevo**

**Request Body:**
```json
{
  "report_type": "executive | technical | anomaly",
  "period_hours": 24,
  "formats": ["pdf", "html"],
  "recipients": ["email1@example.com", "email2@example.com"],
  "include_charts": true,
  "include_anomalies": true,
  "include_metrics": true
}
```

**Response:**
```json
{
  "report_id": "executive_20240101_080000",
  "report_type": "executive",
  "status": "completed",
  "generated_at": "2024-01-01T08:00:00",
  "formats": ["pdf", "html"],
  "files": {
    "pdf": "/app/reports/executive_20240101_080000.pdf",
    "html": "/app/reports/executive_20240101_080000.html"
  },
  "email_sent": true,
  "recipients": ["email1@example.com"]
}
```

---

### GET /api/v1/reports/list
**Lista todos los reportes generados**

**Query Parameters:**
- `limit` (int, default: 50): Máximo de reportes a retornar
- `report_type` (string, optional): Filtrar por tipo (executive, technical, anomaly)

**Response:**
```json
{
  "reports": [
    {
      "filename": "executive_20240101_080000.pdf",
      "report_type": "executive",
      "size_bytes": 2458624,
      "created_at": "2024-01-01T08:00:00",
      "download_url": "/api/v1/reports/download/executive_20240101_080000.pdf"
    }
  ],
  "count": 1,
  "total": 1
}
```

---

### GET /api/v1/reports/download/{filename}
**Descarga un reporte específico**

**Example:**
```bash
curl -O http://localhost:8086/api/v1/reports/download/executive_20240101_080000.pdf
```

---

### DELETE /api/v1/reports/{filename}
**Elimina un reporte**

**Response:**
```json
{
  "status": "deleted",
  "filename": "executive_20240101_080000.pdf"
}
```

---

### GET /health
**Health check del servicio**

**Response:**
```json
{
  "status": "healthy",
  "version": "2.2.0",
  "uptime_seconds": 3600.5,
  "reports_generated": 42,
  "last_report_at": "2024-01-01T08:00:00"
}
```

---

### GET /metrics
**Métricas Prometheus**

Expone métricas para monitoreo:
- `rhinometric_reports_generated_total{report_type, format}` - Total de reportes generados
- `rhinometric_reports_sent_total{report_type, success}` - Total de reportes enviados
- `rhinometric_report_generation_seconds{report_type}` - Tiempo de generación
- `rhinometric_active_reports` - Reportes siendo generados actualmente

---

## 🛠️ Troubleshooting

### Problema: El servicio no inicia

**Diagnóstico:**
```bash
# Ver logs
docker logs rhinometric-report-generator

# Ver errores específicos
docker logs rhinometric-report-generator 2>&1 | grep ERROR
```

**Causas comunes:**
1. **Puertos ocupados:** Verificar que 8086 esté libre
2. **Volúmenes no existen:** Crear `~/rhinometric_data_v2.2/reports`
3. **Dependencias no saludables:** Verificar Prometheus, Grafana, AI Anomaly

---

### Problema: PDF no se genera

**Diagnóstico:**
```bash
# Verificar dependencias de sistema
docker exec rhinometric-report-generator dpkg -l | grep pango

# Test manual de PDF
docker exec -it rhinometric-report-generator python -c "from reportlab.pdfgen import canvas; print('OK')"
```

**Solución:**
```bash
# Rebuild con --no-cache
docker-compose -f docker-compose-v2.2.0.yml build --no-cache rhinometric-report-generator
```

---

### Problema: Email no se envía

**Diagnóstico:**
```bash
# Ver logs de email
docker logs rhinometric-report-generator | grep "email"

# Test manual de SMTP
docker exec -it rhinometric-report-generator python -c "
import aiosmtplib
import asyncio
async def test():
    smtp = aiosmtplib.SMTP(hostname='smtp.zoho.eu', port=587, use_tls=True)
    await smtp.connect()
    print('SMTP OK')
asyncio.run(test())
"
```

**Causas comunes:**
1. **Credenciales incorrectas:** Verificar `SMTP_USERNAME` y `SMTP_PASSWORD`
2. **Firewall:** Verificar que puerto 587 esté abierto
3. **SMTP deshabilitado:** Verificar `SMTP_ENABLED=true`

---

### Problema: Data aggregation falla

**Diagnóstico:**
```bash
# Test Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Test AI Anomaly API
curl http://localhost:8085/api/v1/anomalies?hours=24

# Test Grafana
curl -u admin:admin http://localhost:3000/api/health
```

**Solución:**
Verificar que todos los servicios estén healthy:
```bash
docker ps --filter "name=prometheus|grafana|rhinometric-ai-anomaly"
```

---

## 📈 Monitoreo del Servicio

### Dashboard Grafana para Report Generator

Crear dashboard en Grafana con queries:

```promql
# Total de reportes generados
sum(rhinometric_reports_generated_total)

# Rate de generación (por minuto)
rate(rhinometric_reports_generated_total[5m]) * 60

# Tasa de éxito de envío de emails
sum(rhinometric_reports_sent_total{success="true"}) / sum(rhinometric_reports_sent_total)

# Tiempo promedio de generación
rate(rhinometric_report_generation_seconds_sum[5m]) / rate(rhinometric_report_generation_seconds_count[5m])

# Reportes activos
rhinometric_active_reports
```

---

## 🎨 Personalización de Templates

### Modificar Template de Email

Editar `rhinometric-report-generator/templates/email_report.html`:

```html
<!-- Cambiar colores de marca -->
<style>
  .header {
    background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
  }
  .cta-button {
    background: #YOUR_PRIMARY_COLOR;
  }
</style>

<!-- Añadir logo de empresa -->
<div class="header">
  <img src="https://your-company.com/logo.png" alt="Logo" style="height: 60px;">
  <h1>🎯 Your Company Reports</h1>
</div>
```

### Agregar Sección Personalizada al PDF

Editar `rhinometric-report-generator/app/pdf_generator.py`:

```python
def _build_custom_section(self, data: Dict[str, Any]) -> list:
    """Build custom section"""
    story = []
    
    story.append(Paragraph("Custom Metrics", self.styles['CustomTitle']))
    
    # Tu lógica personalizada aquí
    custom_data = [
        ["Metric", "Value"],
        ["Custom Metric 1", "123"],
        ["Custom Metric 2", "456"]
    ]
    
    table = Table(custom_data)
    # ... styling
    
    story.append(table)
    return story

# En generate_report(), agregar:
# story.extend(self._build_custom_section(data))
```

---

## 🔐 Seguridad

### Variables Sensibles

**NUNCA** comitear credenciales al repositorio. Usar `.env`:

```bash
# .env
SMTP_PASSWORD=tu_password_secreto
GRAFANA_PASSWORD=admin_password
```

```bash
# docker-compose-v2.2.0.yml
environment:
  SMTP_PASSWORD: ${SMTP_PASSWORD}
  GRAFANA_PASSWORD: ${GRAFANA_PASSWORD}
```

### Acceso a la API

**Recomendación:** Implementar autenticación en producción:

```python
# En app/main.py
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.post("/api/v1/reports/generate")
async def generate_report(
    request: ReportRequest,
    credentials: HTTPBasicCredentials = Depends(security)
):
    # Verificar credenciales
    if not verify_credentials(credentials):
        raise HTTPException(status_code=401)
    # ... resto del código
```

---

## 📦 Backup y Restauración

### Backup de Reportes

```bash
# Backup manual
tar -czf reports_backup_$(date +%Y%m%d).tar.gz \
  ~/rhinometric_data_v2.2/reports/

# Backup automático (cron)
0 3 * * * tar -czf ~/backups/reports_$(date +\%Y\%m\%d).tar.gz ~/rhinometric_data_v2.2/reports/
```

### Restauración

```bash
# Restaurar reportes
tar -xzf reports_backup_20240101.tar.gz -C ~/rhinometric_data_v2.2/

# Reiniciar servicio
docker-compose -f docker-compose-v2.2.0.yml restart rhinometric-report-generator
```

---

## 📞 Soporte

- **Documentación API:** http://localhost:8086/docs
- **Health Check:** http://localhost:8086/health
- **Logs:** `docker logs -f rhinometric-report-generator`
- **Métricas:** http://localhost:8086/metrics

---

## ✅ Checklist de Implementación

- [ ] Build del servicio exitoso
- [ ] Health check retorna `healthy`
- [ ] Prometheus, Grafana, AI Anomaly están healthy
- [ ] Generar reporte de prueba (sin email)
- [ ] Configurar credenciales SMTP
- [ ] Generar reporte con email de prueba
- [ ] Verificar PDF se descarga correctamente
- [ ] Configurar reportes programados en `config.yaml`
- [ ] Agregar monitoreo en Grafana
- [ ] Configurar backup automático de reportes
- [ ] Documentar usuarios finales

---

**© 2024 RhinoMetric v2.2.0 Enterprise Edition**
