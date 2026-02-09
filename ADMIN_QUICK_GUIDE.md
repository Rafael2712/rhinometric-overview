# 👨‍💼 Guía Rápida para Administradores – Rhinometric v2.5.3

**Autor:** Rhinometric.com  
**Versión:** 2.5.3  
**Fecha:** 09 de febrero de 2026

---

## 🎯 Índice Rápido

1. [Crear Usuarios](#crear-usuarios)
2. [Gestionar Roles](#gestionar-roles)
3. [Forzar Reset de Contraseña](#forzar-reset-de-contraseña)
4. [Ver Audit Logs](#ver-audit-logs)
5. [Troubleshooting Común](#troubleshooting-común)
6. [Comandos Útiles](#comandos-útiles)

---

## 👤 Crear Usuarios

### Desde la Interfaz Web (Recomendado)

1. **Login como OWNER o ADMIN**
   ```
   http://console.rhinometric.com/login
   ```

2. **Ir a Gestión de Usuarios**
   - Sidebar → **Users**
   - Click botón **"+ Create User"**

3. **Llenar Formulario**
   - **Username**: Identificador único (ej: `jperez`)
   - **Email**: **IMPORTANTE** – necesario para password reset (ej: `jperez@empresa.com`)
   - **Full Name**: Nombre completo (ej: `Juan Pérez`)
   - **Password**: Password inicial (será cambiado en primer login)
   - **Roles**: Seleccionar uno o más:
     - `OWNER`: Acceso total (límite: 1)
     - `ADMIN`: Gestión de usuarios y dashboards (límite: 2)
     - `OPERATOR`: Gestión de alertas y visualización de logs
     - `VIEWER`: Solo lectura

4. **Guardar**
   - Click **"Create User"**
   - Usuario recibirá credenciales y deberá cambiar password en primer login

### Desde API (Para Automatización)

```bash
# Obtener token de admin
ADMIN_TOKEN="tu_token_jwt_aqui"

# Crear usuario
curl -X POST http://console.rhinometric.com/api/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jperez",
    "email": "jperez@empresa.com",
    "full_name": "Juan Pérez",
    "password": "PasswordTemporal123!",
    "roles": ["VIEWER"]
  }'
```

### Desde Base de Datos (Avanzado)

```bash
# Conectar a PostgreSQL
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric

# Insertar usuario (usa bcrypt para password)
INSERT INTO users (username, email, password_hash, full_name, is_active, must_change_password)
VALUES (
  'jperez',
  'jperez@empresa.com',
  '$2b$12$TuHashBcryptAqui',
  'Juan Pérez',
  TRUE,
  TRUE
);

# Asignar rol
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'jperez' AND r.name = 'VIEWER';
```

---

## 🎭 Gestionar Roles

### Roles Disponibles

| Rol | Límite | Permisos |
|-----|--------|----------|
| **OWNER** | 1 | Acceso total, incluye gestión de licencia |
| **ADMIN** | 2 | Gestión de usuarios, dashboards, alertas |
| **OPERATOR** | ∞ | Gestión de alertas, logs, no puede borrar |
| **VIEWER** | ∞ | Solo lectura de métricas y dashboards |

### Asignar Rol a Usuario (UI)

1. **Ir a Users**
2. **Click en el usuario**
3. **Sección "Roles"**
4. **Click "+ Assign Role"**
5. **Seleccionar rol** del dropdown
6. **Guardar**

### Asignar Rol a Usuario (API)

```bash
curl -X POST http://console.rhinometric.com/api/users/{user_id}/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "OPERATOR"}'
```

### Remover Rol de Usuario

```bash
curl -X DELETE http://console.rhinometric.com/api/users/{user_id}/roles/{role_name} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🔐 Forzar Reset de Contraseña

### Opción 1: Forzar Cambio en Próximo Login

**Desde UI:**
1. Ir a **Users**
2. Click en usuario
3. Click **"Force Password Change"**
4. Confirmar

**Desde SQL:**
```sql
UPDATE users 
SET must_change_password = TRUE 
WHERE username = 'jperez';
```

Cuando el usuario haga login, será redirigido automáticamente a `/change-password`.

### Opción 2: Resetear Password Manualmente (ADMIN)

**Desde API:**
```bash
curl -X POST http://console.rhinometric.com/api/users/{user_id}/reset-password \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "PasswordTemporal123!"}'
```

Esto también activa `must_change_password=TRUE`.

### Opción 3: Usuario Usa Self-Service (Recomendado)

**Instrucciones para enviar al usuario:**

```
Hola [Usuario],

Para restablecer tu contraseña en Rhinometric:

1. Ve a: http://console.rhinometric.com/login
2. Click en "¿Olvidó su contraseña?"
3. Ingresa tu email: [email@empresa.com]
4. Revisa tu email (puede tardar 1-5 minutos, revisa spam)
5. Click en el enlace recibido
6. Crea tu nueva contraseña (mínimo 8 caracteres, con mayúscula, minúscula, número y carácter especial)
7. Haz login con tu nueva contraseña

Si tienes problemas, contáctanos.

Saludos,
Equipo Rhinometric
```

---

## 📊 Ver Audit Logs

### Desde Grafana (Recomendado)

1. **Login a Grafana**
   ```
   http://console.rhinometric.com/grafana
   Usuario: admin
   Password: [ver docker-compose]
   ```

2. **Ir a Explore**
   - Sidebar → Icono de brújula (Explore)

3. **Seleccionar Datasource: Loki**

4. **Queries Útiles:**

**Ver eventos de autenticación (últimas 24h):**
```logql
{service="console-backend"} 
  |= "AUTH" 
  | json 
  | __error__=""
```

**Password resets (últimas 24h):**
```logql
{service="console-backend"} 
  |= "password_reset" 
  | json 
  | category="auth"
```

**Logins fallidos (últimas 24h):**
```logql
{service="console-backend"} 
  |= "login_failed" 
  | json
```

**Eventos de usuario específico:**
```logql
{service="console-backend"} 
  |= "jperez@empresa.com" 
  | json
```

**Rate limit violations:**
```logql
{service="console-backend"} 
  |= "429" 
  | json
```

5. **Filtros Avanzados:**

```logql
# Logins por IP específica
{service="console-backend"} 
  | json 
  | action="login" 
  | ip_address="192.168.1.100"

# Password resets exitosos
{service="console-backend"} 
  | json 
  | action="password_reset" 
  | status="success"

# Eventos en rango de tiempo
{service="console-backend"} 
  | json 
  | timestamp >= "2026-02-09T00:00:00Z"
```

### Desde Loki API (CLI)

```bash
# Últimos 100 eventos de auth
curl -G -s "http://rhinometric-loki:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={service="console-backend"} |= "AUTH" | json' \
  --data-urlencode 'limit=100' \
  | jq '.data.result[].values[]'
```

### Desde PostgreSQL (Tokens)

```bash
# Conectar a DB
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric
```

**Ver tokens de reset recientes:**
```sql
SELECT 
  t.id,
  LEFT(t.token, 30) as token_prefix,
  u.username,
  u.email,
  t.used,
  t.expires_at,
  t.created_at,
  CASE 
    WHEN t.used THEN 'Usado'
    WHEN t.expires_at < NOW() THEN 'Expirado'
    ELSE 'Válido'
  END as estado
FROM password_reset_tokens t
JOIN users u ON t.user_id = u.id
ORDER BY t.created_at DESC
LIMIT 20;
```

**Ver historial de logins de usuario:**
```sql
SELECT 
  username,
  email,
  last_login,
  created_at,
  is_active
FROM users
WHERE username = 'jperez';
```

---

## 🔧 Troubleshooting Común

### 1. Usuario no recibe email de reset

**Diagnóstico:**
```bash
# 1. Verificar logs del backend
docker logs rhinometric-console-backend --tail 50 | grep -i email

# 2. Test SMTP
docker exec rhinometric-console-backend python3 test_smtp.py

# 3. Ver token en DB
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT * FROM password_reset_tokens WHERE user_id=(SELECT id FROM users WHERE email='usuario@empresa.com') ORDER BY created_at DESC LIMIT 1;"
```

**Soluciones:**
- ✅ Verificar email en carpeta de SPAM
- ✅ Confirmar que usuario tiene email válido en DB
- ✅ Test de conexión SMTP exitoso
- ✅ Usar enlace directo con token desde DB (workaround)

**Dar enlace directo al usuario:**
```
http://console.rhinometric.com/reset-password?token=[TOKEN_DE_DB]
```

---

### 2. Error "Token inválido o expirado"

**Causas:**
- Token ya fue usado (`used=TRUE`)
- Token expiró (más de 1 hora desde generación)
- Token no existe en DB

**Solución:**
Usuario debe solicitar nuevo token:
1. Ir a login
2. Click "¿Olvidó su contraseña?" nuevamente
3. Ingresar email
4. Usar nuevo enlace

---

### 3. Usuario no puede crear contraseña (validación falla)

**Requisitos de password:**
- Mínimo 8 caracteres
- Al menos 1 mayúscula (A-Z)
- Al menos 1 minúscula (a-z)
- Al menos 1 número (0-9)
- Al menos 1 carácter especial (!@#$%^&*(),.?":{}|<>)

**Ejemplo de password válido:**
```
MiPassword123!
Empresa2026#
Seguro456$
```

---

### 4. Error "Too Many Requests" en forgot password

**Causa:** Rate limiting activado (3 intentos/hora por IP)

**Solución:**
- Esperar 1 hora
- O como admin, generar token manualmente:

```sql
-- Generar token manual
INSERT INTO password_reset_tokens (user_id, token, expires_at, used)
VALUES (
  (SELECT id FROM users WHERE email='usuario@empresa.com'),
  'token-manual-uuid-aqui',
  NOW() + INTERVAL '1 hour',
  FALSE
);

-- Dar enlace al usuario
-- http://console.rhinometric.com/reset-password?token=token-manual-uuid-aqui
```

---

### 5. Login funciona pero no entra al dashboard

**Causa común:** Usuario tiene `must_change_password=TRUE`

**Verificar:**
```sql
SELECT username, must_change_password FROM users WHERE username='jperez';
```

**Solución:**
- Usuario será redirigido a `/change-password` automáticamente
- Debe cambiar password ahí
- Luego podrá acceder al dashboard

---

### 6. SMTP Error 535 (Authentication Failed)

**Diagnóstico:**
```bash
docker exec rhinometric-console-backend python3 test_smtp.py
```

**Causas:**
- IMAP/POP deshabilitado en Zoho
- App Password incorrecto (si 2FA habilitado)
- Servidor SMTP incorrecto

**Solución:**
1. **Habilitar IMAP/POP en Zoho:**
   - Login a Zoho Mail
   - Settings → Mail Accounts → [Tu cuenta]
   - Enable "POP/IMAP Access"

2. **Generar App Password (si 2FA):**
   - Zoho Account Settings → Security → App Passwords
   - Generate New Password
   - Copiar password de 12 caracteres

3. **Actualizar `.env`:**
```bash
MAIL_PASSWORD=NuevoAppPasswordAqui
```

4. **Reiniciar backend:**
```bash
docker restart rhinometric-console-backend
```

5. **Re-test:**
```bash
docker exec rhinometric-console-backend python3 test_smtp.py
```

---

## 🛠️ Comandos Útiles

### Gestión de Usuarios

```bash
# Ver todos los usuarios
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT id, username, email, is_active FROM users ORDER BY id;"

# Activar usuario
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "UPDATE users SET is_active=TRUE WHERE username='jperez';"

# Desactivar usuario
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "UPDATE users SET is_active=FALSE WHERE username='jperez';"

# Ver roles de usuario
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT u.username, r.name as role FROM users u JOIN user_roles ur ON u.id=ur.user_id JOIN roles r ON ur.role_id=r.id WHERE u.username='jperez';"
```

### Gestión de Tokens

```bash
# Ver tokens activos
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "SELECT COUNT(*) as activos FROM password_reset_tokens WHERE used=FALSE AND expires_at > NOW();"

# Invalidar todos los tokens de un usuario
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "UPDATE password_reset_tokens SET used=TRUE WHERE user_id=(SELECT id FROM users WHERE email='usuario@empresa.com');"

# Limpiar tokens antiguos (más de 7 días)
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric \
  -c "DELETE FROM password_reset_tokens WHERE created_at < NOW() - INTERVAL '7 days';"
```

### Logs y Monitoreo

```bash
# Ver logs del backend (últimas 100 líneas)
docker logs rhinometric-console-backend --tail 100

# Seguir logs en tiempo real
docker logs rhinometric-console-backend -f

# Buscar errores
docker logs rhinometric-console-backend --tail 500 | grep -i error

# Ver métricas
curl http://console.rhinometric.com/metrics
```

### Mantenimiento

```bash
# Reiniciar servicios
docker restart rhinometric-console-backend
docker restart rhinometric-console-frontend

# Ver estado de contenedores
docker ps | grep rhinometric

# Ejecutar migraciones
docker exec rhinometric-console-backend alembic upgrade head

# Backup de base de datos
docker exec rhinometric-postgres pg_dump -U rhinometric rhinometric > backup_$(date +%Y%m%d).sql
```

---

## 📞 Contacto Soporte

**Email:** support@rhinometric.com  
**Portal:** https://support.rhinometric.com  
**Documentación:** https://docs.rhinometric.com

---

**Última actualización:** 09 de febrero de 2026  
**Autor:** Rhinometric.com
