# 🔐 Autenticación y Gestión de Usuarios – Rhinometric v2.5.3

**Autor:** Rhinometric.com  
**Versión:** 2.5.3  
**Fecha:** 09 de febrero de 2026  
**Estado:** Producción Ready

---

## 📋 Descripción General

El módulo de **Autenticación y Gestión de Usuarios** de Rhinometric v2.5.3 proporciona un sistema completo de autenticación empresarial con las siguientes capacidades:

- **Login Dual**: Los usuarios pueden iniciar sesión usando su email o username
- **Recuperación Self-Service de Contraseña**: Flujo completo de "Olvidé mi contraseña" con tokens seguros enviados por email
- **Seguridad Robusta**: Rate limiting, tokens de un solo uso, expiración de tokens, validación de contraseñas complejas
- **Audit Logging**: Registro completo de eventos de autenticación en Loki
- **Preparación para SSO**: Campos y hooks estructurales para futura integración SAML/LDAP
- **Interfaz en Español**: UI completamente localizada para el mercado hispanohablante

---

## 🎯 Características Principales

### ✅ Login Dual (Email o Username)

Los usuarios pueden autenticarse usando cualquiera de los dos identificadores:

```bash
# Login con email
curl -X POST http://console.rhinometric.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=rafael.canelon@rhinometric.com&password=MiPassword123!"

# Login con username (backward compatible)
curl -X POST http://console.rhinometric.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

**Beneficios:**
- Alineación con estándares enterprise
- Mejor experiencia de usuario (recordar email es más fácil que username)
- 100% backward compatible con logins existentes

---

### 🔄 Recuperación Self-Service de Contraseña

#### Flujo de Usuario

1. **Usuario olvida su contraseña**
   - Va a la página de login
   - Click en "¿Olvidó su contraseña?"
   - Ingresa su email en el modal

2. **Sistema envía email**
   - Backend genera token UUID único
   - Token se guarda en DB con expiración de 1 hora
   - Email se envía vía SMTP Zoho con enlace de reset

3. **Usuario recibe email**
   - Asunto: "Reset Your Rhinometric Password"
   - Email contiene enlace: `http://console.rhinometric.com/reset-password?token=UUID`

4. **Usuario resetea contraseña**
   - Click en enlace (o copia/pega en navegador)
   - Ingresa nueva contraseña (con validación)
   - Confirma contraseña
   - Click "Reset Password"

5. **Sistema actualiza contraseña**
   - Valida token (existe, no usado, no expirado)
   - Actualiza password con bcrypt
   - Marca token como usado
   - Invalida otros tokens del usuario
   - Registra evento en audit log

6. **Usuario hace login con nueva contraseña**
   - Redirigido automáticamente a login
   - Ingresa nueva contraseña
   - Acceso exitoso

#### Flujo Técnico

```mermaid
sequenceDiagram
    Usuario->>Frontend: Click "¿Olvidó su contraseña?"
    Frontend->>Backend: POST /api/auth/forgot-password {email}
    Backend->>DB: Buscar usuario por email
    Backend->>DB: Generar y guardar token (expires: 1h)
    Backend->>SMTP: Enviar email con enlace
    SMTP->>Usuario: Email "Reset Your Password"
    Usuario->>Frontend: Click enlace /reset-password?token=UUID
    Frontend->>Usuario: Formulario nueva contraseña
    Usuario->>Backend: POST /api/auth/reset-password {token, new_password}
    Backend->>DB: Validar token (exists, not used, not expired)
    Backend->>DB: UPDATE users SET password_hash = bcrypt(new_password)
    Backend->>DB: UPDATE password_reset_tokens SET used = TRUE
    Backend->>Loki: Audit log (PASSWORD_CHANGED)
    Backend->>Frontend: 200 OK {message: "Password reset successfully"}
    Frontend->>Usuario: Pantalla éxito + redirect /login
```

---

## 🛠️ Requisitos Técnicos

### Dependencias Backend

Agregadas en `backend/requirements.txt`:

```txt
fastapi-mail==1.4.1  # Envío asíncrono de emails
slowapi==0.1.9       # Rate limiting
alembic==1.13.1      # Migraciones DB (ya existente)
bcrypt               # Hashing de passwords (ya existente)
```

Instalar:
```bash
docker exec rhinometric-console-backend pip install -r requirements.txt
```

### Variables de Entorno (`.env`)

Agregar en `backend/.env`:

```bash
# Email Configuration (Zoho Mail Europe)
MAIL_USERNAME=rafael.canelon@rhinometric.com
MAIL_PASSWORD=TuAppPasswordAqui123  # Ver sección "Configuración SMTP"
MAIL_FROM=rafael.canelon@rhinometric.com
MAIL_PORT=587
MAIL_SERVER=smtp.zoho.eu
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
MAIL_FROM_NAME=Rhinometric Platform

# Frontend URL (para enlaces de reset)
FRONTEND_URL=http://console.rhinometric.com

# Rate Limiting
RATE_LIMIT_FORGOT_PASSWORD=3/hour
```

### Base de Datos

Ejecutar migración Alembic:

```bash
# Dentro del contenedor backend
docker exec rhinometric-console-backend alembic upgrade head
```

Esto crea:
- Tabla `password_reset_tokens` (id, user_id, token, expires_at, used, created_at)
- Campo `email_verified` en tabla `users`

---

## 📧 Configuración SMTP (Zoho Mail)

### Paso 1: Habilitar IMAP/POP en Zoho

1. Inicia sesión en [Zoho Mail](https://mail.zoho.eu)
2. Ve a **Settings** → **Mail Accounts**
3. Selecciona tu cuenta
4. Habilita **POP/IMAP Access**

### Paso 2: Generar App Password (si tienes 2FA)

Si tienes Two-Factor Authentication habilitado:

1. Ve a **Zoho Account Settings** → **Security** → **App Passwords**
2. Click **Generate New Password**
3. Nombre: "Rhinometric Platform"
4. Copia el password de 12 caracteres (ej: `AbC123XyZ789`)
5. Úsalo en `MAIL_PASSWORD` en `.env`

### Paso 3: Probar Conexión SMTP

```bash
# Test desde backend container
docker exec rhinometric-console-backend python3 test_smtp.py
```

**Salida esperada:**
```
✅ SMTP CONNECTION SUCCESSFUL
   Message: SMTP connection successful
   Test email sent to: rafael.canelon@rhinometric.com
```

Si ves error 535 (Authentication Failed):
- Verifica que IMAP/POP esté habilitado
- Usa App Password si tienes 2FA
- Confirma que `MAIL_FROM` = `MAIL_USERNAME`
- Usa `smtp.zoho.eu` (no `.com`) para cuentas europeas

---

## 🔌 Endpoints API

### 1. Login (Dual)

**Endpoint:** `POST /api/auth/login`

**Método:** OAuth2 Password Flow

**Body (form-urlencoded):**
```
username=usuario_o_email
password=contraseña
```

**Ejemplos:**

```bash
# Con email
curl -X POST http://console.rhinometric.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=rafael.canelon@rhinometric.com&password=MiPassword123!"

# Con username
curl -X POST http://console.rhinometric.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

**Respuesta (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "must_change_password": false
}
```

**Errores:**
- `401 Unauthorized`: Credenciales incorrectas
- `403 Forbidden`: Usuario desactivado

---

### 2. Obtener Info del Usuario

**Endpoint:** `GET /api/auth/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Ejemplo:**

```bash
curl -X GET http://console.rhinometric.com/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "rafael.canelon@rhinometric.com",
  "full_name": "Rafael Cañelón",
  "roles": ["OWNER", "ADMIN"],
  "permissions": ["users:read", "users:write", "dashboards:read", "dashboards:write"],
  "highest_role": "OWNER",
  "must_change_password": false,
  "last_login": "2026-02-09T16:30:45.123Z",
  "created_at": "2026-01-15T10:00:00.000Z",
  "sso_provider": "local",
  "email_verified": true,
  "avatar_url": null,
  "phone": null,
  "timezone": "UTC",
  "language": "es"
}
```

---

### 3. Forgot Password

**Endpoint:** `POST /api/auth/forgot-password`

**Body (JSON):**
```json
{
  "email": "rafael.canelon@rhinometric.com"
}
```

**Ejemplo:**

```bash
curl -X POST http://console.rhinometric.com/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "rafael.canelon@rhinometric.com"}'
```

**Respuesta (200 OK):**
```json
{
  "message": "If your email is registered, you will receive a password reset link shortly.",
  "email": "rafael.canelon@rhinometric.com"
}
```

**Notas:**
- Respuesta genérica para prevenir email enumeration
- Rate limited: 3 intentos/hora por IP
- Si email no existe, responde igual (por seguridad)
- Token expira en 1 hora

**Errores:**
- `429 Too Many Requests`: Demasiados intentos

---

### 4. Reset Password

**Endpoint:** `POST /api/auth/reset-password`

**Body (JSON):**
```json
{
  "token": "c6e129c8-c001-451d-b147-5755e863a6f5",
  "new_password": "MiNuevaPassword123!"
}
```

**Ejemplo:**

```bash
curl -X POST http://console.rhinometric.com/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "c6e129c8-c001-451d-b147-5755e863a6f5",
    "new_password": "MiNuevaPassword123!"
  }'
```

**Respuesta (200 OK):**
```json
{
  "message": "Password reset successfully. You can now login with your new password.",
  "username": "admin"
}
```

**Validaciones:**
- Password mínimo 8 caracteres
- Debe contener: uppercase, lowercase, número, carácter especial
- Token debe existir, no estar usado, no estar expirado

**Errores:**
- `400 Bad Request`: Token inválido/expirado/usado, o password débil
- `404 Not Found`: Usuario no encontrado

---

## 🔒 Características de Seguridad

### 1. Rate Limiting

**Endpoint protegido:** `/api/auth/forgot-password`

- **Límite:** 3 intentos por hora por dirección IP
- **Implementación:** `slowapi` (compatible con FastAPI)
- **Respuesta excedida:** `429 Too Many Requests`

**Configuración:**
```python
# backend/.env
RATE_LIMIT_FORGOT_PASSWORD=3/hour
```

---

### 2. Single-Use Token

- Token se marca como `used=TRUE` después del primer reset exitoso
- Intentos subsecuentes con el mismo token son rechazados
- Previene reutilización maliciosa

**SQL:**
```sql
UPDATE password_reset_tokens 
SET used = TRUE 
WHERE token = 'uuid-token-here';
```

---

### 3. Expiración de Token

- **Vida útil:** 1 hora desde generación
- **Campo:** `expires_at` (timestamp)
- **Validación server-side:**
```python
if datetime.utcnow() > token.expires_at:
    raise HTTPException(400, "Token expired")
```

---

### 4. Invalidación Múltiple

Al reset exitoso, todos los otros tokens activos del usuario se invalidan:

```python
db.query(PasswordResetToken).filter(
    PasswordResetToken.user_id == user.id,
    PasswordResetToken.id != token_record.id,
    PasswordResetToken.used == False
).update({"used": True})
```

---

### 5. Validación de Contraseña

**Client-side (Frontend):**
```typescript
- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula
- Al menos 1 número
- Al menos 1 carácter especial (!@#$%^&*(),.?":{}|<>)
```

**Server-side (Backend):**
```python
if len(new_password) < 8:
    raise HTTPException(400, "Password must be at least 8 characters long")
# ... más validaciones
```

---

### 6. Anti-Enumeration

**Forgot Password** retorna mensaje genérico incluso si email no existe:

```json
{
  "message": "If your email is registered, you will receive a password reset link shortly."
}
```

Esto previene que atacantes descubran qué emails están registrados.

---

### 7. Audit Logging

Todos los eventos críticos se registran en Loki con estructura JSON:

**Eventos registrados:**
- Login exitoso (email/username, IP, timestamp)
- Login fallido (user not found, wrong password)
- Password reset solicitado (email, IP)
- Password reset completado (username, IP)
- Password reset fallido (token inválido/expirado, validation error)

**Consulta en Grafana/Loki:**
```logql
{service="console-backend"} |= "password_reset" | json
```

---

### 8. Session Invalidation

**Frontend:** localStorage se limpia automáticamente en:
- Entrada a página de reset (`useEffect`)
- Click en "Back to Login"
- Reset exitoso

Esto previene confusión si usuario tiene sesión JWT previa.

---

### 9. Headers de Seguridad (Cloudflare)

Nginx configurado para aceptar headers de Cloudflare:

```nginx
# Real IP del cliente
proxy_set_header X-Real-IP $http_cf_connecting_ip;
proxy_set_header X-Forwarded-For $http_cf_connecting_ip;

# SSL/HTTPS
proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
```

---

## 🧪 Testing del Flujo Completo

### Test Automatizado (Backend)

```bash
# Ejecutar script de test
/opt/rhinometric/test_password_reset_flow_v254.sh
```

**Tests incluidos:**
1. ✅ Forgot password request → Token generado
2. ✅ Reset con password débil → Rechazado (400)
3. ✅ Reset con password fuerte → Aceptado (200)
4. ✅ Token marcado como usado
5. ✅ Login con password vieja → Rechazado (401)
6. ✅ Login con password nueva → Aceptado (200)
7. ✅ Rate limiting → Enforced

---

### Test Manual (UI)

#### 1. Login Dual

**Test con Email:**
1. Ir a: `http://console.rhinometric.com/login`
2. Ingresar: `rafael.canelon@rhinometric.com`
3. Ingresar password
4. Click "Sign In"
5. ✅ Debe entrar al dashboard

**Test con Username:**
1. Ir a: `http://console.rhinometric.com/login`
2. Ingresar: `admin`
3. Ingresar password
4. Click "Sign In"
5. ✅ Debe entrar al dashboard

---

#### 2. Forgot Password

1. Ir a: `http://console.rhinometric.com/login`
2. Click "¿Olvidó su contraseña?"
3. **Verificar modal en español:**
   - Título: "Restablecer Contraseña"
   - Label: "Correo Electrónico"
   - Placeholder: "tucorreo@ejemplo.com"
   - Botones: "Cancelar" / "Enviar Enlace"
4. Ingresar email válido: `rafael.canelon@rhinometric.com`
5. Click "Enviar Enlace"
6. ✅ Debe mostrar mensaje de éxito: "¡Revisa tu correo!"

---

#### 3. Reset Password

1. **Revisar email** (puede tardar 1-5 minutos)
   - Bandeja de entrada o SPAM
   - Asunto: "Reset Your Rhinometric Password"
   - Remitente: rafael.canelon@rhinometric.com
2. **Click en enlace** del email
3. **O usar token directo:**
   ```
   http://console.rhinometric.com/reset-password?token={TOKEN}
   ```
4. **Ingresar nueva contraseña:**
   - Password: `MiNuevaPassword123!`
   - Confirmar: `MiNuevaPassword123!`
5. Click "Reset Password"
6. ✅ Debe mostrar pantalla de éxito
7. ✅ Redirigir a login automáticamente (2 segundos)

---

#### 4. Login con Nueva Contraseña

1. En login, ingresar email/username
2. Ingresar **nueva contraseña**: `MiNuevaPassword123!`
3. Click "Sign In"
4. ✅ Debe entrar al dashboard

---

#### 5. Verificar Password Vieja No Funciona

1. Logout del dashboard
2. Ir a login
3. Ingresar email/username
4. Ingresar **password vieja**
5. ✅ Debe mostrar error: "Incorrect username or password"

---

#### 6. Test de Validación de Password

**En página de reset:**

| Password | Resultado Esperado |
|----------|-------------------|
| `1234` | ❌ "Password must be at least 8 characters long" |
| `password` | ❌ "Password must contain at least one uppercase letter" |
| `PASSWORD` | ❌ "Password must contain at least one lowercase letter" |
| `Password` | ❌ "Password must contain at least one number" |
| `Password1` | ❌ "Password must contain at least one special character" |
| `Password1!` | ✅ Aceptado |

---

#### 7. Test de Token Expirado

1. Generar token de reset
2. **Esperar 1 hora + 1 minuto**
3. Intentar usar el enlace
4. ✅ Debe mostrar: "Reset token is expired"

---

#### 8. Test de Token Ya Usado

1. Completar reset exitosamente con token
2. Intentar usar el mismo enlace/token nuevamente
3. ✅ Debe mostrar: "Reset token is already used"

---

#### 9. Test de Rate Limiting

1. Ir a login → "¿Olvidó su contraseña?"
2. Enviar reset 3 veces seguidas (mismo email)
3. Intentar enviar 4ta vez
4. ✅ Debe mostrar error de rate limit

---

## 👥 Guía Rápida para Administradores

### Crear Usuarios Nuevos

**Opción 1: Desde UI**
1. Login como OWNER o ADMIN
2. Ir a: **Users** (sidebar)
3. Click **"+ Create User"**
4. Llenar formulario:
   - Username (único)
   - **Email** (importante para password reset)
   - Full Name
   - Password inicial
   - Roles (OWNER/ADMIN/OPERATOR/VIEWER)
5. Click **"Create User"**

**Opción 2: Desde API**
```bash
curl -X POST http://console.rhinometric.com/api/users \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo_usuario",
    "email": "usuario@empresa.com",
    "full_name": "Usuario Nuevo",
    "password": "PasswordTemporal123!",
    "roles": ["VIEWER"]
  }'
```

**Opción 3: Desde Base de Datos**
```sql
-- Conectar a PostgreSQL
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric

-- Insertar usuario
INSERT INTO users (username, email, password_hash, full_name, is_active, must_change_password)
VALUES (
  'nuevo_usuario',
  'usuario@empresa.com',
  '$2b$12$HashedPasswordAqui',  -- Usar bcrypt
  'Usuario Nuevo',
  TRUE,
  TRUE  -- Forzar cambio en primer login
);
```

---

### Forzar Reset de Contraseña

**Opción 1: Forzar Cambio en Próximo Login**

```sql
UPDATE users 
SET must_change_password = TRUE 
WHERE username = 'usuario_target';
```

Cuando el usuario haga login, será redirigido a `/change-password`.

**Opción 2: Resetear Password Manualmente (ADMIN)**

```bash
curl -X POST http://console.rhinometric.com/api/users/{user_id}/reset-password \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "PasswordTemporal123!"}'
```

Esto también activa `must_change_password=TRUE`.

**Opción 3: Usuario Usa Self-Service**

Instrucciones para el usuario:
1. Ir a login
2. Click "¿Olvidó su contraseña?"
3. Ingresar su email
4. Revisar email y seguir enlace
5. Crear nueva contraseña

---

### Ver Audit Logs en Grafana/Loki

#### Desde Grafana

1. **Login a Grafana:**
   ```
   http://console.rhinometric.com/grafana
   Usuario: admin
   Password: (ver docker-compose)
   ```

2. **Ir a Explore**
   - Sidebar → **Explore** (icono de brújula)

3. **Seleccionar Datasource: Loki**

4. **Query para eventos de autenticación:**
   ```logql
   {service="console-backend"} |= "AUTH" | json
   ```

5. **Query específica para password reset:**
   ```logql
   {service="console-backend"} 
     |= "password_reset" 
     | json 
     | category="auth" 
     | action=~"password_reset.*"
   ```

6. **Query para logins fallidos:**
   ```logql
   {service="console-backend"} 
     |= "login_failed" 
     | json
   ```

7. **Query para usuario específico:**
   ```logql
   {service="console-backend"} 
     |= "rafael.canelon@rhinometric.com" 
     | json
   ```

#### Desde Loki API (CLI)

```bash
# Ver últimos 100 eventos de auth
curl -G -s "http://rhinometric-loki:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="console-backend"} |= "AUTH" | json' \
  --data-urlencode 'limit=100' | jq .
```

#### Desde PostgreSQL (Tokens)

```sql
-- Ver tokens de reset recientes
SELECT 
  t.id,
  t.token,
  u.username,
  u.email,
  t.used,
  t.expires_at,
  t.created_at,
  CASE 
    WHEN t.used THEN 'Used'
    WHEN t.expires_at < NOW() THEN 'Expired'
    ELSE 'Valid'
  END as status
FROM password_reset_tokens t
JOIN users u ON t.user_id = u.id
ORDER BY t.created_at DESC
LIMIT 20;
```

---

### Troubleshooting Común

#### 1. Email no llega

**Verificar:**
```bash
# 1. Logs del backend
docker logs rhinometric-console-backend --tail 50 | grep -i email

# 2. Test SMTP
docker exec rhinometric-console-backend python3 test_smtp.py

# 3. Verificar token en DB
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT * FROM password_reset_tokens WHERE user_id=(SELECT id FROM users WHERE email='email@aqui.com') ORDER BY created_at DESC LIMIT 1;"
```

**Soluciones:**
- Revisar carpeta de SPAM
- Verificar que `MAIL_FROM` = `MAIL_USERNAME`
- Usar App Password de Zoho si tienes 2FA
- Confirmar servidor `smtp.zoho.eu` (no `.com`)

---

#### 2. Error 535 Authentication Failed (SMTP)

**Causas:**
- IMAP/POP deshabilitado en Zoho
- App Password incorrecto
- 2FA habilitado pero usando password normal (no App Password)

**Solución:**
1. Habilitar IMAP/POP en Zoho Settings
2. Generar nuevo App Password
3. Actualizar `MAIL_PASSWORD` en `.env`
4. Reiniciar backend: `docker restart rhinometric-console-backend`

---

#### 3. Modal "Forgot Password" en inglés o se ve mal

**Causa:** Cache del navegador

**Solución:**
1. Hard refresh: `Ctrl + Shift + R` (Windows/Linux) o `Cmd + Shift + R` (Mac)
2. O limpiar cache manualmente:
   - F12 → Application → Clear Storage → Clear site data

---

#### 4. Token expirado

**Causa:** Pasó más de 1 hora desde generación

**Solución:**
Usuario debe solicitar nuevo token:
1. Ir a login
2. Click "¿Olvidó su contraseña?" nuevamente
3. Ingresar email
4. Usar nuevo enlace

---

#### 5. Password vieja sigue funcionando

**Verificar:**
```bash
# 1. ¿Token se usó correctamente?
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT used FROM password_reset_tokens WHERE token='TOKEN_AQUI';"

# 2. ¿Password hash cambió?
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT username, LEFT(password_hash, 30) as hash_prefix FROM users WHERE username='admin';"
```

**Causa común:** Token era inválido y reset nunca se completó

**Solución:** Repetir flujo completo de reset

---

## 📊 Métricas y Monitoreo

### KPIs Recomendados

**Dashboards en Grafana:**

1. **Autenticación**
   - Logins exitosos/fallidos (rate/hora)
   - Ratio éxito/fallo
   - Top usuarios con más intentos fallidos
   - Distribución por método (email vs username)

2. **Password Reset**
   - Requests/día
   - Tasa de éxito (reset completado vs solicitado)
   - Tiempo promedio desde request hasta reset
   - Tokens expirados sin usar

3. **Seguridad**
   - Rate limit violations
   - Intentos de reutilización de tokens
   - Logins desde IPs nuevas
   - Usuarios con múltiples resets en 24h

### Queries Útiles (Loki)

```logql
# Login attempts por hora
rate({service="console-backend"} |= "LOGIN" | json [1h])

# Password resets exitosos
sum(rate({service="console-backend"} 
  | json 
  | action="password_reset" 
  | status="success" [1h]))

# Rate limit violations
{service="console-backend"} 
  |= "429" 
  |= "forgot-password" 
  | json
```

---

## 🔮 Roadmap Futuro

### v2.6.0 – SSO/SAML Integration
- Integración con proveedores SAML/OIDC
- Login con Google Workspace
- Login con Microsoft Azure AD
- Mapeo automático de roles desde SSO

### v2.7.0 – Multi-Factor Authentication (MFA)
- TOTP (Google Authenticator, Authy)
- SMS/Email OTP
- Backup codes
- Configuración por usuario

### v2.8.0 – Password Policies Configurables
- Configuración desde UI de admin
- Expiración de passwords (ej: cada 90 días)
- Historial de passwords (prevenir reutilización)
- Complejidad customizable

### v2.9.0 – Social Login
- Login con Google
- Login con Microsoft
- Login con GitHub
- Login con LinkedIn

---

## 📞 Soporte

**Documentación Oficial:** https://docs.rhinometric.com  
**Portal de Soporte:** https://support.rhinometric.com  
**Email:** support@rhinometric.com

---

## 📄 Licencia

**Rhinometric Platform** es software propietario.  
© 2026 Rhinometric.com. Todos los derechos reservados.

---

**Última actualización:** 09 de febrero de 2026  
**Versión del documento:** 1.0  
**Autor:** Rhinometric.com
