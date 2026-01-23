# 🔐 RHINOMETRIC LICENSE SERVER - API DOCUMENTATION v2.1.0

## 📋 Overview

Sistema completo de gestión y control de licencias con auditoría de activaciones y métricas de seguridad.

**Nueva funcionalidad:**
- ✅ Validación de licencias antes de descarga
- ✅ Registro de todas las activaciones (IP, hardware, timestamp)
- ✅ Detección de uso sospechoso (múltiples IPs/hardware)
- ✅ Bloqueo de licencias expiradas/revocadas
- ✅ Métricas completas de uso y seguridad

---

## 🚀 Quick Start

### 1. Inicializar Base de Datos

```bash
# Ejecutar script de inicialización (solo primera vez)
cd /app
chmod +x init_database.sh
./init_database.sh
```

### 2. Iniciar License Server

```bash
docker compose up -d rhinometric-license-server-v2
```

### 3. Verificar Health

```bash
curl http://localhost:8090/api/health
```

---

## 📡 API ENDPOINTS

### 🟢 Health & Monitoring

#### `GET /api/health`
Health check del servidor.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "service": "Rhinometric License Server",
  "timestamp": "2025-10-29T10:30:00Z",
  "database": "connected",
  "redis": "connected"
}
```

#### `GET /api/metrics`
Métricas Prometheus del servidor.

---

### 🔑 License Validation & Activation Control

#### `POST /api/licenses/validate`
**⭐ ENDPOINT PRINCIPAL** - Valida licencia y registra activación.

**Request:**
```json
{
  "license_key": "RHINO-TRIAL-2025-ABC123",
  "hardware_id": "docker-server-001",
  "hostname": "prod-server.local",
  "ip_address": "192.168.1.100",
  "user_agent": "Rhinometric-Installer/2.1.0",
  "client_info": {
    "os": "Ubuntu 22.04",
    "docker_version": "24.0.5",
    "installation_id": "uuid-12345"
  }
}
```

**Response (Valid License):**
```json
{
  "valid": true,
  "license_id": 42,
  "customer_name": "Acme Corporation",
  "license_type": "trial",
  "expires_at": "2025-11-28T00:00:00Z",
  "days_remaining": 30,
  "download_allowed": true,
  "download_url": "https://github.com/Rafael2712/rhinometric-overview/releases/latest/download/rhinometric-v2.1.0-stable.tar.gz",
  "activation_id": 123,
  "message": "License valid. 30 days remaining."
}
```

**Response (Invalid/Expired):**
```json
{
  "valid": false,
  "download_allowed": false,
  "message": "License expired on 2025-09-15. Renew at rhinometric.com"
}
```

**Use Cases:**
- ✅ Instalador verifica licencia antes de download
- ✅ Script de instalación valida antes de `docker compose up`
- ✅ Auto-update valida licencia antes de actualizar
- ✅ Control de acceso a releases privados

---

#### `GET /api/licenses/{license_key}/activations`
Obtiene historial de activaciones de una licencia.

**Response:**
```json
[
  {
    "id": 123,
    "license_id": 42,
    "license_key": "RHINO-TRIAL-2025-ABC123",
    "activated_at": "2025-10-29T10:30:00Z",
    "ip_address": "192.168.1.100",
    "user_agent": "Rhinometric-Installer/2.1.0",
    "hardware_id": "docker-server-001",
    "hostname": "prod-server.local",
    "download_allowed": true,
    "download_completed": false,
    "validation_status": "success",
    "error_message": null
  }
]
```

**Use Cases:**
- 👤 Cliente consulta su historial de activaciones
- 🔍 Admin audita uso de licencia
- 🔒 Detecta activaciones no autorizadas

---

### 📊 License Management

#### `POST /api/admin/licenses`
Crear nueva licencia.

**Request:**
```json
{
  "customer_name": "Acme Corporation",
  "client_email": "admin@acme.com",
  "client_company": "Acme Inc",
  "license_type": "trial",
  "client_phone": "+1234567890",
  "client_country": "Spain",
  "notes": "Enterprise trial"
}
```

**Response:**
```json
{
  "id": 42,
  "customer_name": "Acme Corporation",
  "license_key": "RHINO-TRIAL-2025-XYZ789",
  "license_type": "trial",
  "client_email": "admin@acme.com",
  "status": "active",
  "created_at": "2025-10-29T10:00:00Z",
  "expires_at": "2025-11-28T10:00:00Z",
  "days_remaining": 30,
  "is_active": true,
  "email_sent": true
}
```

---

#### `GET /api/admin/licenses`
Listar todas las licencias.

**Response:**
```json
[
  {
    "id": 42,
    "customer_name": "Acme Corporation",
    "license_key": "RHINO-TRIAL-2025-XYZ789",
    "license_type": "trial",
    "status": "active",
    "created_at": "2025-10-29T10:00:00Z",
    "expires_at": "2025-11-28T10:00:00Z",
    "days_remaining": 30,
    "is_active": true
  }
]
```

---

#### `GET /api/admin/licenses/stats`
**⭐ NUEVO** - Estadísticas completas con métricas de activación.

**Response:**
```json
{
  "licenses": {
    "total": 150,
    "active": 120,
    "expired": 20,
    "revoked": 10,
    "expiring_soon": 5,
    "by_type": {
      "trial": 80,
      "annual": 50,
      "permanent": 20
    }
  },
  "activations": {
    "total": 450,
    "unique_ips": 180,
    "unique_hardware": 150,
    "today": 12,
    "avg_per_license": 3.0
  },
  "security": {
    "failed_attempts_today": 3,
    "failed_attempts_total": 45,
    "success_rate": 90.91
  },
  "top_licenses": [
    {
      "license_key": "RHINO-ANNUAL-2025-TOP001",
      "customer_name": "Big Corp",
      "activations": 25
    }
  ],
  "revenue_estimate": {
    "annual": "$99950 USD/year (estimate)",
    "note": "Based on $1999/license standard pricing"
  },
  "last_updated": "2025-10-29T10:30:00Z"
}
```

---

### 🔒 Security & Monitoring

#### `GET /api/admin/licenses/security`
**⭐ NUEVO** - Alertas de seguridad y patrones sospechosos.

**Response:**
```json
{
  "suspicious_activations": [
    {
      "license_key": "RHINO-TRIAL-2025-SUSP001",
      "distinct_ips": 8,
      "distinct_hardware": 6,
      "total_activations": 15,
      "last_activation": "2025-10-29T09:00:00Z"
    }
  ],
  "failed_attempts": [
    {
      "license_key": "RHINO-FAKE-2025-INVALID",
      "reason": "License key not found",
      "attempt_count": 12,
      "distinct_ips": 3,
      "last_attempt": "2025-10-29T10:00:00Z"
    }
  ],
  "alert_count": 2,
  "generated_at": "2025-10-29T10:30:00Z"
}
```

**Detecta:**
- 🚨 Licencia usada desde >5 IPs diferentes (compartida ilegalmente)
- 🚨 Licencia usada en >3 hardware IDs (uso no autorizado)
- 🚨 >10 activaciones en 7 días (excesivo)
- 🚨 Intentos fallidos repetidos (potencial ataque)

---

#### `POST /api/admin/licenses/{license_key}/revoke`
**⭐ NUEVO** - Revocar licencia (bloquear activaciones futuras).

**Request:**
```bash
curl -X POST http://localhost:8090/api/admin/licenses/RHINO-TRIAL-2025-ABC123/revoke \
  -H "Content-Type: application/json" \
  -d '{"reason": "Uso no autorizado detectado"}'
```

**Response:**
```json
{
  "success": true,
  "license_key": "RHINO-TRIAL-2025-ABC123",
  "message": "License revoked successfully",
  "revoked_at": "2025-10-29T10:30:00Z"
}
```

---

## 🗄️ Database Schema

### Tablas Principales

#### `licenses`
Información de licencias emitidas.

```sql
id, customer_name, license_key, created_at, expires_at, is_active,
client_email, client_company, client_phone, client_country, 
client_city, industry, company_size, servers_count, services_count,
infrastructure_type, notes, last_check, updated_at
```

#### `license_activations` ⭐ NUEVO
Registro de todas las activaciones.

```sql
id, license_id, license_key, activated_at, ip_address, user_agent,
hardware_id, hostname, download_allowed, download_url,
download_completed, validation_status, error_message, client_info
```

#### `license_validation_failures` ⭐ NUEVO
Intentos fallidos (seguridad).

```sql
id, license_key, attempted_at, ip_address, user_agent, reason,
hardware_id, is_suspicious, blocked
```

---

## 📈 Use Cases

### 1️⃣ Instalador Automático

```bash
#!/bin/bash
# Script de instalación con validación de licencia

LICENSE_KEY="$1"

# Validar licencia antes de instalar
VALIDATION=$(curl -s -X POST http://license-server:8090/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d "{
    \"license_key\": \"$LICENSE_KEY\",
    \"hardware_id\": \"$(hostname)\",
    \"ip_address\": \"$(curl -s ifconfig.me)\"
  }")

IS_VALID=$(echo $VALIDATION | jq -r '.valid')

if [ "$IS_VALID" != "true" ]; then
  echo "❌ Licencia inválida o expirada"
  echo "   Mensaje: $(echo $VALIDATION | jq -r '.message')"
  exit 1
fi

# Obtener URL de descarga
DOWNLOAD_URL=$(echo $VALIDATION | jq -r '.download_url')

echo "✅ Licencia válida. Descargando Rhinometric..."
wget $DOWNLOAD_URL -O rhinometric.tar.gz
```

### 2️⃣ Dashboard Admin

```javascript
// React component para mostrar estadísticas
const LicenseStats = () => {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch('http://localhost:8090/api/admin/licenses/stats')
      .then(res => res.json())
      .then(data => setStats(data));
  }, []);
  
  return (
    <div>
      <h2>Licencias Activas: {stats?.licenses.active}</h2>
      <h3>Activaciones hoy: {stats?.activations.today}</h3>
      <h3>Success Rate: {stats?.security.success_rate}%</h3>
    </div>
  );
};
```

### 3️⃣ Alertas de Seguridad

```python
# Script de monitoreo (ejecutar cada hora)
import requests
import smtplib

response = requests.get('http://localhost:8090/api/admin/licenses/security')
data = response.json()

if data['alert_count'] > 0:
    # Enviar alerta por email
    send_alert_email(
        subject=f"⚠️ {data['alert_count']} alertas de seguridad",
        body=f"Activaciones sospechosas: {len(data['suspicious_activations'])}\n"
             f"Intentos fallidos: {len(data['failed_attempts'])}"
    )
```

---

## 🧪 Testing

### Ejecutar Test Suite

```bash
# Instalar dependencias
pip install httpx rich

# Ejecutar tests
python test_license_api.py
```

**Tests incluidos:**
1. ✅ Health check
2. ✅ Crear licencia
3. ✅ Validar licencia válida
4. ✅ Validar licencia inválida (seguridad)
5. ✅ Consultar historial de activaciones
6. ✅ Estadísticas completas
7. ✅ Alertas de seguridad

---

## 🔧 Configuration

### Variables de Entorno

```env
# PostgreSQL
DATABASE_URL=postgresql://user:pass@postgres:5432/rhinometric_trial
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=rhinometric_trial
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=rhinometric

# Redis (opcional)
REDIS_URL=redis://redis:6379

# Email (para envío automático)
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=rafael.canelon@rhinometric.com

# Modo de operación
RHINOMETRIC_MODE=trial  # o "production"
```

---

## 📊 Monitoring & Analytics

### Prometheus Metrics

El servidor expone métricas en `/api/metrics`:

```
# Request count
http_requests_total{method="POST", handler="/api/licenses/validate"} 1250

# Request duration
http_request_duration_seconds_bucket{le="0.1"} 1200
http_request_duration_seconds_bucket{le="0.5"} 1245

# Database connections
db_pool_connections_active 5
db_pool_connections_idle 15
```

### Grafana Dashboard

Importar dashboard de Grafana para visualizar:
- Licencias activas/expiradas
- Activaciones por día
- Tasa de éxito de validaciones
- Alertas de seguridad
- Top clientes por activaciones

---

## 🚨 Security Best Practices

1. **Rate Limiting**: Limitar intentos de validación por IP (5 req/min)
2. **IP Whitelist**: Para endpoints admin (`/api/admin/*`)
3. **HTTPS**: Usar SSL en producción
4. **API Keys**: Autenticación Bearer token para endpoints sensibles
5. **Audit Logs**: Revisar `license_validation_failures` diariamente
6. **Alertas**: Configurar notificaciones para `alert_count > 0`

---

## 📞 Support

**Technical Support:**
- Email: rafael.canelon@rhinometric.com
- Docs: http://localhost:8090/api/docs (Swagger UI)
- Schedule: Mon-Fri, 9:00-18:00 CET

**API Documentation:**
- Swagger UI: http://localhost:8090/api/docs
- ReDoc: http://localhost:8090/api/redoc

---

## 🆕 Changelog v2.1.0

### Added ✨
- ✅ Endpoint `POST /api/licenses/validate` - Control de activaciones
- ✅ Tabla `license_activations` - Auditoría completa
- ✅ Tabla `license_validation_failures` - Seguridad
- ✅ Endpoint `GET /api/licenses/{key}/activations` - Historial
- ✅ Endpoint `GET /api/admin/licenses/security` - Alertas
- ✅ Endpoint `POST /api/admin/licenses/{key}/revoke` - Revocar
- ✅ Métricas extendidas en `/api/admin/licenses/stats`
- ✅ Views SQL para análisis (`v_licenses_summary`, `v_suspicious_activations`)
- ✅ Script de inicialización de BD (`init_db.sql`, `init_database.sh`)
- ✅ Test suite completo (`test_license_api.py`)

### Improved 🔧
- Estadísticas ahora incluyen activaciones, IPs únicas, hardware IDs
- Success rate de validaciones
- Top 5 licencias más activas
- Estimación de revenue anual

---

**Version**: 2.1.0  
**Last Updated**: October 29, 2025  
**Author**: Rafael Canel  
**License**: Proprietary - Rhinometric®
