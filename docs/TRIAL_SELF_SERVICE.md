# 📋 RHINOMETRIC TRIAL SELF-SERVICE SYSTEM

## 🎯 Objetivo

Sistema automatizado de generación de licencias de prueba para leads que solicitan evaluar Rhinometric, sin intervención manual del equipo comercial.

---

## 🏗️ Arquitectura del Sistema

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO                            │
└─────────────────────────────────────────────────────────────┘

1. Lead accede a formulario web público
   ↓
2. Completa datos (nombre, empresa, email corporativo, país)
   ↓
3. Valida frontend (email corporativo, campos requeridos)
   ↓
4. POST /api/public/trial-signup
   ↓
5. Backend valida:
   - Email corporativo (no Gmail/Hotmail/etc.)
   - Rate limit (3 solicitudes/día por email/IP)
   - Campos requeridos
   ↓
6. Crea 2 licencias automáticamente:
   ┌─────────────────────────────────────────┐
   │ DEMO_CLOUD                              │
   │ - Vigencia: 4 horas desde activación    │
   │ - max_hosts: 5                          │
   │ - Status: not_activated                 │
   │ - License Key: DEMO-XXXX-XXXX-XXXX-XXXX │
   └─────────────────────────────────────────┘
   
   ┌─────────────────────────────────────────┐
   │ TRIAL                                   │
   │ - Vigencia: 14 días desde activación    │
   │ - max_hosts: 5                          │
   │ - Status: not_activated                 │
   │ - License Key: TRIAL-XXXX-XXXX-XXXX-XXXX│
   └─────────────────────────────────────────┘
   ↓
7. Envía email automático con:
   - Ambas license keys
   - Link de descarga de OVA
   - Manuales de instalación y uso
   - Requisitos del sistema
   - Próximos pasos
   ↓
8. Lead descarga OVA e instala
   ↓
9. Al activar primera vez con license key:
   - Status: not_activated → active
   - activated_at: timestamp actual
   - expires_at se calcula desde activated_at
   ↓
10. Rhinometric Console valida periódicamente:
    - Si licencia expiró → bloquea acceso
    - Si hosts_used > max_hosts → over_limit
```

---

## 📊 Definición de Tiers

### 1. **demo_cloud**
```yaml
Nombre: Demo Cloud
Duración: 4 horas desde primera activación
max_hosts: 5
Uso recomendado: 
  - Demo rápida de capacidades
  - PoC corta
  - Presentación a stakeholders
Features:
  - Dashboards pre-configurados
  - Detección de anomalías IA
  - Prometheus + Grafana + Loki
Limitaciones:
  - Solo 4 horas de uso continuo
  - Máximo 5 hosts monitorizados
```

### 2. **trial**
```yaml
Nombre: Trial Completo
Duración: 14 días desde primera activación
max_hosts: 5
Uso recomendado:
  - Evaluación seria en entorno cliente
  - Prueba con datos reales
  - Validación de requisitos
Features:
  - Monitorización completa (Prometheus, node-exporter)
  - Logs centralizados (Loki)
  - Distributed tracing (Jaeger)
  - Alertas configurables (Alertmanager)
  - Detección de anomalías IA
  - Dashboards personalizables
Limitaciones:
  - 14 días de vigencia
  - Máximo 5 hosts monitorizados
```

### 3. **annual_standard** (no auto-generado)
```yaml
Nombre: Annual Standard
Duración: 1 año
max_hosts: 20
Uso: Licencia comercial estándar
Creación: Manual por admin
```

---

## 🔒 Seguridad y Validaciones

### Rate Limiting

**Límites por defecto:**
- **3 solicitudes por email por día**
- **3 solicitudes por IP por día**

**Implementación:**
```python
# Redis keys:
trial_signup:email:{email}:{YYYY-MM-DD} → count (TTL 24h)
trial_signup:ip:{ip_address}:{YYYY-MM-DD} → count (TTL 24h)
```

**Respuesta cuando se excede:**
```http
HTTP 429 Too Many Requests
{
  "detail": "Has alcanzado el límite de 3 solicitudes por día"
}
```

### Validación de Email Corporativo

**Dominios bloqueados (emails gratuitos):**
```python
BLOCKED_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com",
    "live.com", "icloud.com", "aol.com", "protonmail.com",
    "mail.com", "zoho.com", "yandex.com", "gmx.com"
}
```

**Validación:**
- Frontend: aviso preventivo
- Backend: rechazo con error HTTP 422

### Logs de Seguridad

**Eventos registrados:**
```
✅ Trial signup completed: {email} | Company: {company} | Country: {country}
⚠️  Rate limit exceeded for {email} / {ip}
❌ Failed to create licenses for {email}: {error}
❌ Failed to send email to {email}: {error}
```

**Ubicación:**
- Logs en `/app/logs/license_mail.log`
- Stdout de contenedor Docker

---

## 📧 Email Automático

### Template

**Asunto:**
```
Tu acceso de prueba a Rhinometric – Demo 4h + Trial 14 días
```

**Estructura del email:**

1. **Encabezado de bienvenida**
   - Logo/branding
   - Presentación de Rhinometric

2. **Bloque 1: Licencia Demo 4 Horas**
   - License key (monospace, copiable)
   - Características: 4h, 5 hosts, dashboards, IA
   - Fecha de expiración

3. **Bloque 2: Licencia Trial 14 Días**
   - License key (monospace, copiable)
   - Características: 14d, 5 hosts, full stack
   - Fecha de expiración

4. **Descarga e instalación**
   - Botón: Descargar Rhinometric OVA
   - Botón: Guía de Instalación
   - Botón: Manual de Usuario

5. **Requisitos del sistema**
   - CPU: 4 vCPUs (mín 2)
   - RAM: 8 GB (mín 4 GB)
   - Disco: 80 GB
   - Hypervisors compatibles

6. **Compatibilidad por OS**
   - Windows (VMware/VirtualBox)
   - macOS Intel/Apple Silicon
   - Linux
   - VMware ESXi

7. **Inicio rápido (6 pasos)**
   - Descarga OVA
   - Importa en hypervisor
   - Inicia VM
   - Accede a console web
   - Introduce license key
   - Comienza a monitorizar

8. **Soporte**
   - Email de contacto
   - Links a documentación

9. **Footer**
   - Copyright
   - Aclaración on-premise (datos no salen del cliente)

### Configuración SMTP

**Variables de entorno requeridas:**
```bash
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465  # SSL
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=<app_password_zoho>
SMTP_FROM=rafael.canelon@rhinometric.com
```

**URLs configurables:**
```bash
OVA_DOWNLOAD_URL=https://rhinometric.com/downloads/rhinometric-trial.ova
MANUAL_INSTALL_URL=https://rhinometric.com/docs/installation
MANUAL_USER_URL=https://rhinometric.com/docs/user-guide
```

---

## 🗄️ Esquema de Base de Datos

### Tabla `licenses`

**Columnas requeridas para trial self-service:**

```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    license_key VARCHAR(100) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL,  -- 'demo_cloud', 'trial', 'annual_standard'
    max_hosts INT NOT NULL,
    
    -- Timestamps
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMP,  -- NULL hasta primera activación
    expires_at TIMESTAMP,    -- Se calcula desde activated_at
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'not_activated',
    -- Valores: 'not_activated', 'active', 'expired', 'revoked', 'over_limit'
    
    -- Organization info
    organization VARCHAR(255),
    organization_email VARCHAR(255),
    client_phone VARCHAR(50),
    client_country VARCHAR(100),
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_licenses_key ON licenses(license_key);
CREATE INDEX idx_licenses_email ON licenses(organization_email);
CREATE INDEX idx_licenses_status ON licenses(status);
CREATE INDEX idx_licenses_tier ON licenses(tier);
```

**Ejemplo de registro creado:**

```sql
-- Demo Cloud
INSERT INTO licenses VALUES (
    1,
    'Juan Pérez',
    'DEMO-A1B2-C3D4-E5F6-G7H8',
    'demo_cloud',
    5,  -- max_hosts
    '2025-12-11 10:00:00',  -- issued_at
    NULL,  -- activated_at (se setea al activar)
    '2025-12-11 14:00:00',  -- expires_at (issued_at + 4h)
    'not_activated',
    'Acme Corp',
    'juan.perez@acme.com',
    '+34600123456',
    'España',
    'Auto-generated via trial signup. Use: Testing monitoring',
    TRUE,
    '2025-12-11 10:00:00',
    '2025-12-11 10:00:00'
);

-- Trial
INSERT INTO licenses VALUES (
    2,
    'Juan Pérez',
    'TRIAL-X9Y8-Z7W6-V5U4-T3S2',
    'trial',
    5,
    '2025-12-11 10:00:00',
    NULL,
    '2025-12-25 10:00:00',  -- issued_at + 14 days
    'not_activated',
    'Acme Corp',
    'juan.perez@acme.com',
    '+34600123456',
    'España',
    'Auto-generated via trial signup. Use: Testing monitoring',
    TRUE,
    '2025-12-11 10:00:00',
    '2025-12-11 10:00:00'
);
```

---

## 🚀 Instalación y Configuración

### 1. Actualizar `docker-compose.yml`

```yaml
services:
  license-api:
    build:
      context: ./app
      dockerfile: ../Dockerfile
    ports:
      - "8090:80"
    environment:
      # ... existing vars ...
      
      # SMTP Configuration
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      SMTP_FROM: ${SMTP_FROM}
      
      # Trial Self-Service URLs
      OVA_DOWNLOAD_URL: ${OVA_DOWNLOAD_URL}
      MANUAL_INSTALL_URL: ${MANUAL_INSTALL_URL}
      MANUAL_USER_URL: ${MANUAL_USER_URL}
    
    volumes:
      - ./static:/app/static:ro  # Serve static files
```

### 2. Configurar variables de entorno

**Archivo `.env`:**
```bash
# SMTP Configuration (Zoho Mail)
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=rafael.canelon@rhinometric.com
SMTP_PASSWORD=271211Rc$  # App password
SMTP_FROM=rafael.canelon@rhinometric.com

# Download URLs
OVA_DOWNLOAD_URL=https://rhinometric.com/downloads/rhinometric-v2.5.0.ova
MANUAL_INSTALL_URL=https://docs.rhinometric.com/installation
MANUAL_USER_URL=https://docs.rhinometric.com/user-guide
```

### 3. Integrar módulo en `main.py`

```python
# En license-server-v2-main.py

from license_server_trial_selfservice import router as trial_router

# ... existing code ...

# Add trial self-service router
app.include_router(trial_router)

# Store config in app state
app.state.smtp_host = SMTP_HOST
app.state.smtp_port = SMTP_PORT
app.state.smtp_user = SMTP_USER
app.state.smtp_password = SMTP_PASSWORD
app.state.smtp_from = SMTP_FROM
app.state.ova_download_url = os.getenv("OVA_DOWNLOAD_URL", "")
app.state.manual_install_url = os.getenv("MANUAL_INSTALL_URL", "")
app.state.manual_user_url = os.getenv("MANUAL_USER_URL", "")

# Serve static files (formulario HTML)
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect /trial to formulario
@app.get("/trial", response_class=HTMLResponse)
async def trial_page():
    with open("static/trial-signup.html") as f:
        return f.read()
```

### 4. Crear estructura de directorios

```bash
/app/
├── main.py  # license-server-v2-main.py
├── license_server_trial_selfservice.py  # Nuevo módulo
├── static/
│   └── trial-signup.html  # Formulario público
├── logs/
│   └── license_mail.log
└── docs/
    ├── manual_usuario.pdf
    ├── guia_instalacion.pdf
    └── politica_privacidad_GDPR.pdf
```

### 5. Reiniciar servicio

```bash
cd /home/ubuntu/license-server
docker-compose down
docker-compose up -d
docker-compose logs -f license-api
```

---

## 🧪 Testing del Sistema

### Test Manual End-to-End

**1. Acceder al formulario:**
```
http://54.197.192.198:5000/trial
```

**2. Completar formulario:**
- Nombre: `Juan Pérez Test`
- Empresa: `Acme Corp`
- Email: `juan.perez@acmecorp.com` (corporativo)
- País: `España`
- Uso previsto: `Testing monitoring solution`
- ✅ Aceptar términos

**3. Enviar formulario**

**4. Verificar respuesta:**
```json
{
  "success": true,
  "message": "¡Licencias creadas exitosamente! Revisa tu correo.",
  "email_sent": true,
  "licenses_created": {
    "demo_cloud": "DEMO-A1B2-C3D4-E5F6-G7H8",
    "trial": "TRIAL-X9Y8-Z7W6-V5U4-T3S2"
  },
  "next_steps": [
    "1. Revisa tu correo electrónico (también carpeta SPAM)",
    "2. Descarga la OVA de Rhinometric",
    "3. Importa la OVA en VMware/VirtualBox",
    "4. Activa con una de las dos license keys recibidas",
    "5. Comienza a monitorizar (Demo: 4h | Trial: 14d)"
  ]
}
```

**5. Verificar en base de datos:**
```sql
SELECT id, customer_name, license_key, tier, status, organization_email
FROM licenses
WHERE organization_email = 'juan.perez@acmecorp.com'
ORDER BY id DESC
LIMIT 2;
```

**Resultado esperado:**
```
id | customer_name    | license_key              | tier       | status         | organization_email
---+------------------+--------------------------+------------+----------------+---------------------
 1 | Juan Pérez Test  | DEMO-A1B2-C3D4-E5F6-G7H8 | demo_cloud | not_activated  | juan.perez@acmecorp.com
 2 | Juan Pérez Test  | TRIAL-X9Y8-Z7W6-V5U4-T3S2| trial      | not_activated  | juan.perez@acmecorp.com
```

**6. Verificar email recibido:**
- Asunto: "Tu acceso de prueba a Rhinometric – Demo 4h + Trial 14 días"
- Contiene 2 license keys
- Contiene botones de descarga
- Contiene requisitos del sistema

**7. Probar rate limiting:**
- Enviar 4 formularios con mismo email
- El 4to debe rechazarse con HTTP 429

**8. Probar validación de email:**
- Enviar formulario con `test@gmail.com`
- Debe rechazarse con error de validación

### Test de Activación

**1. Descargar OVA y arrancar VM**

**2. En Rhinometric Console, al pedir license key:**
```
Introduce: DEMO-A1B2-C3D4-E5F6-G7H8
```

**3. Rhinometric llama a License Server:**
```http
POST /api/licenses/validate/v2
{
  "license_key": "DEMO-A1B2-C3D4-E5F6-G7H8",
  "hardware_id": "...",
  "hostname": "rhino-demo"
}
```

**4. License Server actualiza:**
```sql
UPDATE licenses
SET status = 'active',
    activated_at = NOW(),
    expires_at = NOW() + INTERVAL '4 hours'  -- Para demo_cloud
WHERE license_key = 'DEMO-A1B2-C3D4-E5F6-G7H8';
```

**5. Verificar validación periódica:**
- Rhinometric Console valida cada 5 minutos
- Después de 4 horas → status = 'expired'
- Console muestra: "Licencia expirada. Contacta con soporte."

---

## 📈 Monitorización

### Métricas a trackear

```python
# Prometheus metrics
trial_signups_total{tier="demo_cloud"}
trial_signups_total{tier="trial"}
trial_signups_by_country{country="España"}
trial_activations_total{tier="demo_cloud"}
trial_activations_total{tier="trial"}
trial_conversions_to_paid  # Future
rate_limit_rejections_total
email_send_failures_total
```

### Dashboard recomendado

**Panel 1: Signups por día**
- Gráfico de líneas: signups/día
- Filtro por tier

**Panel 2: Conversión**
```
Signups totales: 150
Activaciones demo: 80 (53%)
Activaciones trial: 95 (63%)
Conversiones a paid: 12 (8%)
```

**Panel 3: Top países**
```
España: 45
México: 30
Colombia: 20
Argentina: 15
...
```

**Panel 4: Rate limiting**
```
Requests totales: 180
Rechazados por rate limit: 15 (8%)
Rechazados por email inválido: 8 (4%)
```

---

## 🔧 Troubleshooting

### Problema: Email no llega

**Diagnóstico:**
```bash
# Ver logs
docker-compose logs license-api | grep -i "email\|smtp"

# Verificar config SMTP
docker-compose exec license-api env | grep SMTP
```

**Soluciones:**
1. Verificar password de aplicación Zoho
2. Verificar conectividad a smtp.zoho.eu:465
3. Revisar carpeta SPAM del destinatario
4. Probar con email alternativo

### Problema: Rate limit no funciona

**Diagnóstico:**
```bash
# Verificar Redis
docker-compose exec redis redis-cli

# Ver keys de rate limit
KEYS trial_signup:*

# Ver valor
GET trial_signup:email:test@example.com:2025-12-11
```

**Solución:**
- Verificar que Redis está corriendo
- Verificar conexión a Redis desde license-api

### Problema: Licencias no se crean

**Diagnóstico:**
```bash
# Ver logs de BD
docker-compose logs postgres

# Verificar esquema
docker-compose exec postgres psql -U license_admin -d licenses -c "\d licenses"
```

**Solución:**
- Ejecutar migration si falta columna
- Verificar permisos de BD

### Problema: Formulario da error CORS

**Solución:**
```python
# En main.py, verificar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎯 Checklist de Despliegue

### Pre-deploy

- [ ] Variables de entorno configuradas en `.env`
- [ ] SMTP_PASSWORD es app password de Zoho (no password normal)
- [ ] URLs de descarga configuradas (OVA, manuales)
- [ ] Redis está corriendo
- [ ] PostgreSQL tiene esquema actualizado
- [ ] Logs directory existe: `/app/logs`
- [ ] Static files directory: `/app/static`

### Deploy

- [ ] Código subido al servidor
- [ ] `docker-compose.yml` actualizado
- [ ] `docker-compose down && docker-compose up -d`
- [ ] Verificar logs: `docker-compose logs -f license-api`
- [ ] Verificar health: `curl http://localhost:5000/health`
- [ ] Verificar formulario: `curl http://localhost:5000/trial`

### Post-deploy Testing

- [ ] Acceder a formulario desde navegador
- [ ] Enviar solicitud de prueba
- [ ] Verificar licencias creadas en BD
- [ ] Verificar email recibido
- [ ] Probar rate limiting (4 requests)
- [ ] Probar validación de email corporativo
- [ ] Probar activación con license key en OVA

### Producción

- [ ] Configurar DNS: `trial.rhinometric.com` → servidor
- [ ] Configurar HTTPS con Let's Encrypt
- [ ] Rate limit ajustado según tráfico esperado
- [ ] Monitoring de métricas configurado
- [ ] Alertas configuradas (email send failures, etc.)
- [ ] Backup de BD configurado
- [ ] Legal review de términos y privacidad

---

## 📝 Notas Adicionales

### ¿Por qué 2 licencias?

**Razón estratégica:**
- **demo_cloud (4h):** Baja barrera de entrada, quick win para leads indecisos
- **trial (14d):** Evaluación seria para leads comprometidos

**Ventajas:**
- Lead decide qué usar según su urgencia
- Mayor conversión vs. solo trial largo
- Datos para entender comportamiento (¿prefieren demo corta o trial largo?)

### Futuras mejoras

1. **Self-service form avanzado:**
   - Selección de tier (solo demo, solo trial, o ambos)
   - Campos custom según industria
   - Integración con CRM (HubSpot/Salesforce)

2. **Nurturing automático:**
   - Email day 3: "¿Cómo va tu prueba?"
   - Email day 7: "Casos de éxito similares"
   - Email day 13: "Tu trial expira mañana, ¿hablamos?"

3. **Analytics avanzado:**
   - Heatmap de usage durante trial
   - Features más usadas
   - Correlación país/industria con conversión

4. **Onboarding mejorado:**
   - Video tutorial en email
   - Asistente in-app para configuración
   - Dashboards pre-configurados según industria

---

**Versión:** 1.0  
**Última actualización:** 11 de diciembre de 2025  
**Autor:** Rhinometric Development Team  
**Contacto:** rafael.canelon@rhinometric.com
