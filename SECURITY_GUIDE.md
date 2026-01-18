# 🔐 RHINOMETRIC - GUÍA DE SEGURIDAD PARA PRODUCCIÓN

## ⚠️ CHECKLIST DE SEGURIDAD PRE-DESPLIEGUE

### 1️⃣ **Cambio de Contraseña Obligatorio** ✅
- [x] Implementado: Usuario `admin` DEBE cambiar contraseña en primer login
- [x] Validación de complejidad:
  - Mínimo 8 caracteres
  - Al menos 1 mayúscula
  - Al menos 1 minúscula
  - Al menos 1 número
- [x] Ruta: `/change-password` (obligatoria si `must_change_password=true`)

### 2️⃣ **Variables de Entorno Críticas**
**Archivo:** `infrastructure/mi-proyecto/rhinometric-console/backend/.env`

```bash
# Copiar template
cp .env.example .env

# Editar y establecer valores seguros
nano .env
```

**Variables que DEBES cambiar:**

| Variable | Default (INSEGURO) | Acción Requerida |
|----------|-------------------|------------------|
| `ADMIN_PASSWORD` | `CHANGE_ME_IN_PRODUCTION` | Establecer contraseña fuerte (8+ chars, mix) |
| `SECRET_KEY` | `CHANGE_ME_...` | Generar token aleatorio 32+ chars |
| `POSTGRES_PASSWORD` | `rhinometric` | Cambiar a contraseña compleja |

**Generar SECRET_KEY seguro:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Output ejemplo: K8sT3qW9mL2nR5jP7vH6xC4yF1bN0aD2uE8gS3w
```

### 3️⃣ **Configuración HTTPS/Reverse Proxy**
Rhinometric NO debe exponerse directamente. Usa siempre un reverse proxy:

#### Opción A: Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name rhinometric.tu-dominio.com;

    ssl_certificate /etc/ssl/certs/rhinometric.crt;
    ssl_certificate_key /etc/ssl/private/rhinometric.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://rhinometric-console-frontend:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://rhinometric-console-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Opción B: Cloudflare Tunnel (Recomendado)
```yaml
# tunnel.yml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/credentials.json

ingress:
  - hostname: rhinometric.tu-dominio.com
    service: http://rhinometric-console-frontend:3002
  - service: http_status:404
```

### 4️⃣ **Configuración de Base de Datos**
**Si usas PostgreSQL en producción:**

```yaml
# docker-compose.yml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # Nunca hardcodear
  - POSTGRES_USER=rhinometric_prod
  - POSTGRES_DB=rhinometric_db
```

**Archivo `.env`:**
```bash
POSTGRES_PASSWORD=YourVerySecurePassword123!
```

### 5️⃣ **Limitar Intentos de Login (Futuro)**
⚠️ **TODO:** Implementar rate limiting

**Recomendación:**
- Máximo 5 intentos cada 15 minutos
- Bloqueo temporal de IP tras fallos repetidos
- Alertas de intentos de fuerza bruta

### 6️⃣ **Auditoría y Logs**
- ✅ Logs de autenticación: `backend/logs/auth.log`
- ✅ Registro de cambios de contraseña
- ⚠️ **TODO:** Integrar con SIEM para monitoreo

### 7️⃣ **Certificados SSL**
**Generar certificado autofirmado (desarrollo):**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout rhinometric.key -out rhinometric.crt
```

**Producción:** Usar Let's Encrypt o certificado comercial.

### 8️⃣ **Firewall y Puertos**
**Puertos expuestos:**
- Frontend: 3002 → Solo accesible vía proxy
- Backend: 8000 → Solo accesible vía proxy
- Grafana: 3000 → Solo accesible vía proxy
- Prometheus: 9090 → **NO exponer directamente**

**Configuración iptables:**
```bash
# Bloquear acceso directo a servicios internos
iptables -A INPUT -p tcp --dport 9090 -j DROP  # Prometheus
iptables -A INPUT -p tcp --dport 8085 -j DROP  # AI Anomaly
iptables -A INPUT -p tcp --dport 9093 -j DROP  # Alertmanager
```

### 9️⃣ **Modo Demo vs Producción**
| Aspecto | Demo | Producción |
|---------|------|------------|
| Contraseña admin | `admin` | Cambiar obligatoriamente |
| SECRET_KEY | Placeholder | Token aleatorio 32+ chars |
| HTTPS | Opcional | **OBLIGATORIO** |
| Credenciales expuestas | En `/api/auth/config` | **ELIMINAR endpoint** |
| Auditoría | Deshabilitada | Habilitada |

### 🔟 **Verificación Final**
Antes de desplegar, ejecuta:

```bash
# 1. Verificar que no hay passwords hardcodeadas
grep -r "password.*=.*admin\|demo\|123" . --exclude-dir=node_modules

# 2. Verificar SECRET_KEY cambiado
grep "SECRET_KEY.*CHANGE_ME" .env

# 3. Verificar ADMIN_PASSWORD cambiado
grep "ADMIN_PASSWORD.*CHANGE_ME" .env

# 4. Verificar permisos de archivos
chmod 600 .env
```

**Si todos los checks pasan → ✅ Listo para producción**

---

## 📚 Referencias Adicionales
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Let's Encrypt SSL Certificates](https://letsencrypt.org/)
