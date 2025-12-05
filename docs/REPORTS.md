# 📊 REPORTES AUTOMÁTICOS - RHINOMETRIC v2.2.0

## Índice
1. [Visión General](#visión-general)
2. [Tipos de Reportes](#tipos-de-reportes)
3. [Configuración](#configuración)
4. [Contenido del Reporte](#contenido-del-reporte)
5. [Personalización](#personalización)
6. [Entrega de Reportes](#entrega-de-reportes)
7. [Casos de Uso](#casos-de-uso)
8. [Troubleshooting](#troubleshooting)

---

## Visión General

RHINOMETRIC v2.2.0 incluye un sistema de generación automática de reportes ejecutivos que proporciona:

- **Informes PDF/HTML profesionales** con métricas clave
- **Entrega automática por email** a stakeholders
- **Análisis de anomalías mediante IA** integrado
- **Recomendaciones automáticas** basadas en el estado de la plataforma
- **Diseño corporativo y sobrio** adecuado para presentaciones ejecutivas

### ¿Para quién son estos reportes?

- **CTO/CIO:** Visión estratégica de la infraestructura
- **Directores de Operaciones:** Estado de salud y disponibilidad
- **Gerentes de TI:** Métricas de rendimiento y alertas
- **Comités de Auditoría:** Evidencia de monitoreo y compliance
- **Clientes finales:** Transparencia en SLAs

---

## Tipos de Reportes

### Reporte Diario

- **Frecuencia:** Cada día a las 08:00 AM
- **Contenido:** Métricas de las últimas 24 horas
- **Objetivo:** Monitoreo operacional
- **Destinatarios:** Equipo técnico

### Reporte Semanal (Recomendado)

- **Frecuencia:** Lunes a las 08:00 AM
- **Contenido:** Resumen de la última semana
- **Objetivo:** Visión ejecutiva y toma de decisiones
- **Destinatarios:** Management y stakeholders

### Reporte Mensual

- **Frecuencia:** Primer lunes del mes a las 08:00 AM
- **Contenido:** Tendencias del mes anterior
- **Objetivo:** Reportes de gestión y auditoría
- **Destinatarios:** C-level y board

---

## Configuración

### Variables de Entorno

El servicio de reportes se configura en `docker-compose-v2.2.0.yml`:

```yaml
rhinometric-report:
  environment:
    # URLs de servicios
    PROMETHEUS_URL: "http://prometheus:9090"
    ANOMALY_SERVICE_URL: "http://rhinometric-ai-anomaly:8085"
    
    # Frecuencia de reportes
    REPORT_SCHEDULE: "weekly"  # daily, weekly, monthly
    
    # Configuración SMTP
    SMTP_HOST: "smtp.zoho.eu"
    SMTP_PORT: "587"
    SMTP_USER: "rafael.canelon@rhinometric.com"
    SMTP_PASSWORD: "${SMTP_PASSWORD}"
    
    # Destinatarios (separados por coma)
    REPORT_RECIPIENTS: "cto@empresa.com,ops@empresa.com"
    
    # Test: enviar reporte inmediatamente
    RUN_IMMEDIATE: "false"
```

### Cambiar Frecuencia de Reportes

**Opción 1: Editar docker-compose.yml**

```yaml
REPORT_SCHEDULE: "daily"   # Para reportes diarios
REPORT_SCHEDULE: "weekly"  # Para reportes semanales (predeterminado)
REPORT_SCHEDULE: "monthly" # Para reportes mensuales
```

Aplicar cambios:
```bash
docker compose up -d rhinometric-report
```

**Opción 2: Usar .env**

Crear archivo `.env`:
```bash
REPORT_SCHEDULE=weekly
REPORT_RECIPIENTS=rafael.canelon@rhinometric.com,ops@ejemplo.com
SMTP_PASSWORD=tu_password_aqui
```

### Añadir/Quitar Destinatarios

```yaml
# Un solo destinatario
REPORT_RECIPIENTS: "cto@empresa.com"

# Múltiples destinatarios (separados por coma, sin espacios)
REPORT_RECIPIENTS: "cto@empresa.com,ops@empresa.com,audit@empresa.com"
```

### Configurar SMTP Personalizado

Si no usas Zoho, puedes configurar otro proveedor:

**Gmail:**
```yaml
SMTP_HOST: "smtp.gmail.com"
SMTP_PORT: "587"
SMTP_USER: "tu_email@gmail.com"
SMTP_PASSWORD: "tu_app_password"  # Requiere App Password
```

**Microsoft 365:**
```yaml
SMTP_HOST: "smtp.office365.com"
SMTP_PORT: "587"
SMTP_USER: "tu_email@empresa.com"
SMTP_PASSWORD: "tu_password"
```

**SendGrid:**
```yaml
SMTP_HOST: "smtp.sendgrid.net"
SMTP_PORT: "587"
SMTP_USER: "apikey"
SMTP_PASSWORD: "SG.tu_api_key"
```

---

## Contenido del Reporte

### Estructura del Reporte PDF

#### 1. Header
- Logo/Nombre: **RHINOMETRIC**
- Título: **Informe Ejecutivo de Observabilidad**
- Fecha de generación
- Período cubierto

#### 2. Resumen Ejecutivo

Párrafo narrativo con:
- Estado general de la plataforma
- Número de servicios activos
- Disponibilidad alcanzada
- Alertas críticas (si las hay)
- Anomalías detectadas por IA

**Ejemplo:**
```
La plataforma RHINOMETRIC opera con normalidad. 20 servicios activos 
con disponibilidad del 99.87%. No se detectaron incidentes críticos 
durante el período reportado.
```

#### 3. Métricas Clave (Dashboard Visual)

Tres tarjetas con indicadores:

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Servicios Activos** | 20/20 | ✅ Verde |
| **Alertas Activas** | 0 | ✅ Verde |
| **Disponibilidad** | 99.87% | ✅ Verde |

Colores:
- Verde: Todo normal
- Amarillo: Atención requerida
- Rojo: Crítico

#### 4. Estado de Servicios (Tabla)

| Servicio | Estado | CPU | Memoria |
|----------|--------|-----|---------|
| License Server | ✅ Healthy | 15.2% | 45.6% |
| Prometheus | ✅ Healthy | 22.8% | 68.3% |
| Grafana | ✅ Healthy | 8.5% | 32.1% |
| VeriVerde | ✅ Healthy | 3.2% | 12.4% |
| AI Anomaly | ✅ Healthy | 18.7% | 38.9% |

#### 5. Anomalías Detectadas (IA)

Si el sistema de IA detectó patrones anómalos:

```
⚠️ Anomalía Detectada:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Métrica: CPU Usage
Severidad: Alta
Mensaje: Anomalía detectada en CPU Usage: 8/10 puntos recientes
Timestamp: 2025-01-30T14:23:45
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 6. Recomendaciones Automáticas

Basadas en el análisis del sistema:

- ✅ "Todos los sistemas operan dentro de parámetros normales"
- ✅ "Continuar con monitoreo rutinario"

O en caso de problemas:

- ⚠️ "Se detectaron 2 alertas activas que requieren atención"
- ⚠️ "El sistema de IA detectó 3 anomalías en las últimas horas"
- ⚠️ "La disponibilidad está por debajo del objetivo del 99.9%"

#### 7. Footer

- Versión: RHINOMETRIC v2.2.0 Enterprise Edition
- Disclaimer: "Plataforma de Observabilidad On-Premise | Cumplimiento RGPD/ENS"
- Nota: "Este informe ha sido generado automáticamente"

### Ejemplo de Email

**Asunto:**
```
RHINOMETRIC - Informe Semanal - 30/01/2025
```

**Cuerpo:**
```
Estimado/a,

Adjunto encontrará el informe de observabilidad de RHINOMETRIC 
correspondiente al período reportado.

Este informe incluye:
- Resumen ejecutivo del estado de la plataforma
- Métricas clave de rendimiento y disponibilidad
- Anomalías detectadas por IA (si las hay)
- Recomendaciones de acción

Para cualquier consulta, por favor contactar con el equipo de soporte.

Saludos,
RHINOMETRIC Automated Reporting System
```

**Adjunto:** `report_20250130_080000.pdf` (500-800 KB)

---

## Personalización

### Modificar Template HTML

El template está en: `rhinometric-report/template.html`

**Cambiar colores corporativos:**

```html
<style>
    .header h1 {
        color: #2c3e50;  /* Azul oscuro predeterminado */
    }
    .metric-card.good {
        border-color: #27ae60;  /* Verde */
    }
</style>
```

Ejemplo con colores de tu empresa:

```html
.header h1 {
    color: #003d7a;  /* Azul corporativo */
}
.metric-card.good {
    border-color: #00a86b;  /* Verde marca */
}
```

### Añadir Logo Corporativo

Editar `template.html`:

```html
<div class="header">
    <!-- ANTES -->
    <div class="logo">RHINOMETRIC</div>
    
    <!-- DESPUÉS -->
    <img src="data:image/png;base64,..." alt="Logo" style="height: 60px;">
    <div class="logo">TU EMPRESA - RHINOMETRIC</div>
</div>
```

### Modificar Texto del Email

Editar `rhinometric-report/reporter.py`:

```python
body = """
Estimado/a Cliente,

Adjuntamos el informe semanal de su plataforma RHINOMETRIC.

Contenido:
- Estado general de servicios
- Métricas de rendimiento
- Alertas y anomalías (si las hay)
- Recomendaciones del sistema

Atentamente,
Equipo de Monitoreo
"""
```

### Añadir Métricas Personalizadas

Editar `reporter.py`, sección `collect_data()`:

```python
def collect_data(self):
    data = {}
    
    # ... código existente ...
    
    # NUEVA MÉTRICA: Tasa de errores
    error_rate = self.fetch_prometheus_query(
        'sum(rate(http_requests_total{status=~"5.."}[1h]))'
    )
    data["error_rate"] = float(error_rate[0]["value"][1]) if error_rate else 0
    
    return data
```

Luego añadir al template HTML:

```html
<div class="metric-card {{ error_status }}">
    <div class="label">Tasa de Errores</div>
    <div class="value">{{ error_rate }}</div>
</div>
```

---

## Entrega de Reportes

### Generación Manual

Forzar generación inmediata de reporte:

```bash
docker exec rhinometric-report python reporter.py
```

O configurar `RUN_IMMEDIATE=true` al iniciar:

```yaml
environment:
  RUN_IMMEDIATE: "true"
```

```bash
docker compose up -d rhinometric-report
```

Esto generará un reporte de prueba inmediatamente.

### Verificar Envío

Ver logs del servicio:

```bash
docker logs -f rhinometric-report
```

**Salida esperada:**
```
2025-01-30 08:00:00 [INFO] Starting weekly report generation
2025-01-30 08:00:05 [INFO] Generating report...
2025-01-30 08:00:12 [INFO] Report generated: /tmp/report_20250130_080000.pdf
2025-01-30 08:00:15 [INFO] Sending report to 2 recipients...
2025-01-30 08:00:18 [INFO] ✅ Report sent successfully
2025-01-30 08:00:18 [INFO] Report cycle complete
```

### Almacenamiento Local

Los reportes se guardan temporalmente en:
```
/tmp/report_YYYYMMDD_HHMMSS.pdf
```

Para guardar permanentemente, modificar `docker-compose-v2.2.0.yml`:

```yaml
rhinometric-report:
  volumes:
    - ${HOME}/rhinometric_reports:/reports  # Añadir esta línea
```

Luego modificar `reporter.py`:

```python
# Cambiar ruta de guardado
pdf_path = Path(f"/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
```

---

## Casos de Uso

### Caso 1: Reporte Mensual para Dirección

**Objetivo:** Demostrar cumplimiento de SLA 99.9% ante el comité directivo

**Configuración:**
```yaml
REPORT_SCHEDULE: "monthly"
REPORT_RECIPIENTS: "cto@empresa.com,ceo@empresa.com,board@empresa.com"
```

**Personalización:**
- Añadir gráficos de tendencia mensual
- Incluir comparativa con mes anterior
- Añadir análisis de costos (si aplica)

### Caso 2: Reporte Diario para Operaciones

**Objetivo:** Monitoreo operacional para equipo técnico

**Configuración:**
```yaml
REPORT_SCHEDULE: "daily"
REPORT_RECIPIENTS: "ops@empresa.com,devops@empresa.com"
```

**Personalización:**
- Enfoque en alertas activas
- Lista detallada de incidentes
- Recomendaciones técnicas específicas

### Caso 3: Reporte para Cliente Final (MSP)

**Objetivo:** Transparencia de servicio gestionado

**Configuración:**
```yaml
REPORT_SCHEDULE: "weekly"
REPORT_RECIPIENTS: "cliente@ejemplo.com"
```

**Personalización:**
- Lenguaje no técnico en resumen ejecutivo
- Énfasis en disponibilidad y SLA
- Incluir disclaimer de confidencialidad
- Branding del cliente

### Caso 4: Reporte para Auditoría/Compliance

**Objetivo:** Evidencia de monitoreo continuo (GDPR/ENS/ISO27001)

**Configuración:**
```yaml
REPORT_SCHEDULE: "monthly"
REPORT_RECIPIENTS: "audit@empresa.com,compliance@empresa.com"
```

**Personalización:**
- Añadir sección de compliance checks
- Incluir métricas de seguridad
- Detallar incidentes de seguridad (si los hay)
- Firmar digitalmente el PDF

---

## Troubleshooting

### Problema: No llegan emails

**Síntoma:** El reporte se genera pero no se envía

**Diagnóstico:**
```bash
docker logs rhinometric-report | grep -i error
```

**Posibles causas y soluciones:**

1. **Credenciales SMTP incorrectas:**
   ```bash
   # Verificar variables
   docker inspect rhinometric-report | grep SMTP
   ```
   
   Solución: Corregir `SMTP_USER` y `SMTP_PASSWORD`

2. **Puerto bloqueado:**
   ```bash
   # Test de conectividad
   telnet smtp.zoho.eu 587
   ```
   
   Solución: Abrir puerto 587 en firewall

3. **Email marcado como spam:**
   - Revisar carpeta de spam del destinatario
   - Configurar SPF/DKIM en el dominio
   - Usar email corporativo verificado

### Problema: PDF no se genera

**Síntoma:**
```
[ERROR] PDF generation failed: wkhtmltopdf not found
```

**Solución:**
```bash
# Reconstruir imagen con dependencias
docker compose build rhinometric-report
docker compose up -d rhinometric-report
```

### Problema: Reporte vacío o con errores

**Síntoma:** El PDF se genera pero no tiene datos

**Diagnóstico:**
```bash
# Verificar conectividad con Prometheus
docker exec rhinometric-report curl http://prometheus:9090/api/v1/query?query=up
```

**Solución:**
- Verificar que Prometheus está accesible
- Revisar queries en `reporter.py`
- Verificar red Docker (`rhinometric_network_v22`)

### Problema: Horario incorrecto

**Síntoma:** Los reportes llegan a hora incorrecta

**Causa:** Zona horaria del contenedor

**Solución:**

Añadir timezone al `docker-compose-v2.2.0.yml`:

```yaml
rhinometric-report:
  environment:
    TZ: "Europe/Madrid"  # O tu zona horaria
```

Reiniciar:
```bash
docker compose up -d rhinometric-report
```

### Problema: Reportes muy grandes

**Síntoma:** PDFs de >10MB, emails rechazados

**Causa:** Muchos datos o gráficos embebidos

**Solución:**

1. Reducir período de datos:
   ```python
   # En reporter.py
   LOOKBACK_HOURS = 24  # En lugar de 168
   ```

2. Limitar gráficos embebidos

3. Enviar link de descarga en lugar de adjunto

---

## Comandos Rápidos

```bash
# Ver logs del servicio
docker logs -f rhinometric-report

# Generar reporte manual
docker exec rhinometric-report python reporter.py

# Reiniciar servicio (aplicar cambios)
docker compose restart rhinometric-report

# Verificar configuración SMTP
docker exec rhinometric-report python -c "import os; print(os.getenv('SMTP_HOST'))"

# Test de envío de email
docker exec rhinometric-report python -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test')
msg['Subject'] = 'Test RHINOMETRIC'
msg['From'] = 'rafael.canelon@rhinometric.com'
msg['To'] = 'tu_email@ejemplo.com'
with smtplib.SMTP('smtp.zoho.eu', 587) as server:
    server.starttls()
    server.login('rafael.canelon@rhinometric.com', 'password')
    server.send_message(msg)
print('Email enviado')
"
```

---

## Roadmap de Mejoras Futuras

Características planificadas para próximas versiones:

- [ ] Gráficos embebidos en PDF (matplotlib/plotly)
- [ ] Comparativas históricas (mes vs mes)
- [ ] Reportes multi-idioma (ES/EN)
- [ ] Dashboard web para ver reportes históricos
- [ ] Integración con Slack/Teams (notificaciones)
- [ ] Firma digital de PDFs para compliance
- [ ] Reportes personalizados por rol (CTO vs SysAdmin)
- [ ] Export a Excel para análisis adicional

---

## Contacto y Soporte

Para consultas sobre reportes:
- **Email:** rafael.canelon@rhinometric.com
- **Documentación:** `README.md`
- **Logs:** `docker logs rhinometric-report`

---

**RHINOMETRIC v2.2.0 Enterprise Edition**  
Sistema de Reportes Ejecutivos Automáticos  
Cumplimiento RGPD/ENS | 100% On-Premise
