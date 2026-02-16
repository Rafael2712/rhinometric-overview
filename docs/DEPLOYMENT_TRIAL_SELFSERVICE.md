# 🚀 DEPLOYMENT GUIDE - Trial Self-Service

## ⚡ Quick Start (5 minutos)

### 1. Preparar archivos en el servidor

```bash
# En el servidor License Server (54.197.192.198)
cd /home/ubuntu/license-server

# Crear directorios necesarios
mkdir -p static logs docs

# Subir archivos desde tu máquina local
```

Desde tu máquina **Windows local**:

```powershell
# Subir módulo Python
scp c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\license-server-trial-selfservice.py ubuntu@54.197.192.198:/home/ubuntu/license-server/app/

# Subir formulario HTML
scp c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\static\trial-signup.html ubuntu@54.197.192.198:/home/ubuntu/license-server/static/

# Subir integración
scp c:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\INTEGRATION_TRIAL_SELFSERVICE.py ubuntu@54.197.192.198:/home/ubuntu/license-server/
```

### 2. Integrar en main.py

```bash
# En el servidor
cd /home/ubuntu/license-server

# Editar main.py (usa el archivo INTEGRATION_TRIAL_SELFSERVICE.py como referencia)
nano app/main.py
```

**Agregar al final de imports:**
```python
from fastapi.staticfiles import StaticFiles
from license_server_trial_selfservice import router as trial_router
from pathlib import Path
```

**Agregar después de SMTP config:**
```python
# Trial Self-Service URLs
OVA_DOWNLOAD_URL = os.getenv(
    "OVA_DOWNLOAD_URL",
    "https://rhinometric.com/downloads/rhinometric-v2.5.0.ova"
)
MANUAL_INSTALL_URL = os.getenv("MANUAL_INSTALL_URL", "https://docs.rhinometric.com/installation")
MANUAL_USER_URL = os.getenv("MANUAL_USER_URL", "https://docs.rhinometric.com/user-guide")
```

**Agregar en startup event:**
```python
@app.on_event("startup")
async def startup():
    # ... código existente ...
    
    # Trial self-service config
    app.state.smtp_host = SMTP_HOST
    app.state.smtp_port = SMTP_PORT
    app.state.smtp_user = SMTP_USER
    app.state.smtp_password = SMTP_PASSWORD
    app.state.smtp_from = SMTP_FROM
    app.state.ova_download_url = OVA_DOWNLOAD_URL
    app.state.manual_install_url = MANUAL_INSTALL_URL
    app.state.manual_user_url = MANUAL_USER_URL
```

**Agregar después de crear `app`:**
```python
# Include trial router
app.include_router(trial_router)

# Serve static files
STATIC_DIR = Path("/app/static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Trial page redirect
from fastapi.responses import HTMLResponse

@app.get("/trial", response_class=HTMLResponse)
async def trial_page():
    with open("/app/static/trial-signup.html") as f:
        return f.read()
```

### 3. Actualizar docker-compose.yml

```bash
nano docker-compose.yml
```

**Agregar en `license-api` service, sección `environment`:**

```yaml
      # Trial Self-Service URLs
      OVA_DOWNLOAD_URL: ${OVA_DOWNLOAD_URL:-https://rhinometric.com/downloads/rhinometric-v2.5.0.ova}
      MANUAL_INSTALL_URL: ${MANUAL_INSTALL_URL:-https://docs.rhinometric.com/installation}
      MANUAL_USER_URL: ${MANUAL_USER_URL:-https://docs.rhinometric.com/user-guide}
```

**Agregar en `license-api` service, sección `volumes`:**

```yaml
    volumes:
      - ./static:/app/static:ro
      - ./logs:/app/logs:rw
```

### 4. Verificar estructura de directorios

```bash
cd /home/ubuntu/license-server

# Debe verse así:
tree -L 2
```

**Resultado esperado:**
```
/home/ubuntu/license-server/
├── app/
│   ├── main.py  # Modificado
│   └── license_server_trial_selfservice.py  # Nuevo
├── static/
│   └── trial-signup.html  # Nuevo
├── logs/
│   └── license_mail.log  # Se crea automáticamente
├── docs/  # Opcional, para PDFs
├── docker-compose.yml  # Modificado
└── Dockerfile
```

### 5. Reiniciar servicio

```bash
cd /home/ubuntu/license-server

# Rebuild y restart
docker-compose down
docker-compose build license-api
docker-compose up -d

# Ver logs
docker-compose logs -f license-api
```

**Logs esperados:**
```
✅ Trial self-service configured with OVA URL: https://...
✅ Trial self-service endpoints registered
✅ Static files served from /app/static
```

### 6. Verificar que funciona

```bash
# Test 1: Health check
curl http://localhost:5000/health

# Test 2: Trial page existe
curl http://localhost:5000/trial

# Test 3: Endpoint público responde
curl http://localhost:5000/docs

# Buscar: POST /api/public/trial-signup
```

### 7. Prueba end-to-end

**Desde navegador:**
1. Ve a: `http://54.197.192.198:5000/trial`
2. Completa formulario con email real tuyo
3. Submit
4. Verifica en logs:
   ```bash
   docker-compose logs license-api | grep -i "trial signup"
   ```
5. Revisa tu correo (y carpeta SPAM)

**Verificar en BD:**
```bash
docker-compose exec postgres psql -U license_admin -d licenses -c "SELECT customer_name, license_key, tier, status, organization_email FROM licenses ORDER BY id DESC LIMIT 4;"
```

**Debe mostrar:**
```
 customer_name    | license_key              | tier       | status        | organization_email
------------------+--------------------------+------------+---------------+-------------------
 Tu Nombre        | DEMO-...                 | demo_cloud | not_activated | tu@email.com
 Tu Nombre        | TRIAL-...                | trial      | not_activated | tu@email.com
```

---

## 🔧 Configuración de URLs

### Opción A: URLs temporales (testing)

Si aún no tienes OVA ni docs públicas:

```bash
# En .env o directamente en docker-compose.yml
OVA_DOWNLOAD_URL=https://rhinometric.com/downloads/rhinometric-v2.5.0.ova
MANUAL_INSTALL_URL=https://rhinometric.com/docs/installation
MANUAL_USER_URL=https://rhinometric.com/docs/user-guide
```

### Opción B: URLs reales (producción)

Sube la OVA a S3/CloudFront/CDN:

```bash
# AWS S3 example
aws s3 cp rhinometric-v2.5.0.ova s3://rhinometric-downloads/ova/
aws s3api put-object-acl --bucket rhinometric-downloads --key ova/rhinometric-v2.5.0.ova --acl public-read

# Get URL
echo "https://rhinometric-downloads.s3.amazonaws.com/ova/rhinometric-v2.5.0.ova"
```

Actualiza docker-compose.yml:
```yaml
OVA_DOWNLOAD_URL: https://rhinometric-downloads.s3.amazonaws.com/ova/rhinometric-v2.5.0.ova
```

---

## 📊 Monitoreo

### Ver signups recientes

```bash
# Últimos 7 días
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  "http://localhost:5000/api/admin/trial-signups?days=7"

# Solo demo_cloud
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  "http://localhost:5000/api/admin/trial-signups?tier=demo_cloud"
```

### Ver logs de email

```bash
tail -f /home/ubuntu/license-server/logs/license_mail.log
```

### Métricas Prometheus (si configurado)

```
rhinometric_trial_signups_total{tier="demo_cloud"}
rhinometric_trial_signups_total{tier="trial"}
```

---

## 🧪 Testing de Rate Limiting

```bash
# Script de prueba
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST http://localhost:5000/api/public/trial-signup \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test User",
      "company": "Test Corp",
      "email": "test@testcorp.com",
      "country": "España",
      "accept_terms": true
    }'
  echo -e "\n---"
  sleep 1
done
```

**Esperado:**
- Request 1, 2, 3: ✅ Success
- Request 4, 5: ❌ HTTP 429 (Rate limit exceeded)

---

## 🔐 Seguridad

### 1. Verificar CORS en producción

```python
# En main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rhinometric.com",
        "https://www.rhinometric.com",
        # NO uses "*" en producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 2. Rate limiting estricto

Si recibes spam, ajusta:

```python
# En license_server_trial_selfservice.py
MAX_TRIAL_REQUESTS_PER_DAY = 1  # Solo 1 por día
```

### 3. Habilitar HTTPS

```bash
# Con Nginx reverse proxy
sudo apt install nginx certbot python3-certbot-nginx

# Configurar nginx
sudo nano /etc/nginx/sites-available/rhinometric-license

# Contenido:
server {
    listen 80;
    server_name trial.rhinometric.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Habilitar y obtener cert
sudo ln -s /etc/nginx/sites-available/rhinometric-license /etc/nginx/sites-enabled/
sudo certbot --nginx -d trial.rhinometric.com
sudo systemctl reload nginx
```

---

## 🐛 Troubleshooting

### Email no llega

```bash
# Ver logs SMTP
docker-compose logs license-api | grep -i smtp

# Verificar variables
docker-compose exec license-api env | grep SMTP

# Test manual de conectividad
telnet smtp.zoho.eu 465
```

### Formulario da error 500

```bash
# Ver logs completos
docker-compose logs --tail=100 license-api

# Ver si Redis responde
docker-compose exec redis redis-cli ping

# Ver si PostgreSQL responde
docker-compose exec postgres pg_isready
```

### Rate limit no funciona

```bash
# Verificar Redis keys
docker-compose exec redis redis-cli
> KEYS trial_signup:*
> GET trial_signup:email:test@example.com:2025-12-11
```

---

## ✅ Checklist Final

- [ ] Archivos subidos al servidor
- [ ] main.py modificado con integración
- [ ] docker-compose.yml actualizado
- [ ] Directorios creados (static, logs)
- [ ] Servicio reiniciado
- [ ] Logs muestran "Trial self-service configured"
- [ ] Formulario accesible en http://IP:5000/trial
- [ ] Email de prueba enviado y recibido
- [ ] Licencias creadas en BD
- [ ] Rate limiting funciona (4ta request rechazada)
- [ ] SMTP configurado correctamente
- [ ] URLs de descarga configuradas

---

**¿Todo funciona?** Ahora puedes:

1. Configurar DNS: `trial.rhinometric.com` → IP servidor
2. Habilitar HTTPS con Let's Encrypt
3. Compartir URL con leads
4. Monitorear signups en `/api/admin/trial-signups`

**¿Necesitas ayuda?** rafael.canelon@rhinometric.com
