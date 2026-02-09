# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [2.5.3] - 2026-02-09

### 🎉 Auth Enhancement – Autenticación Empresarial

**Autor:** Rhinometric.com  
**Fecha:** 09 de febrero de 2026  
**Estado:** Producción Ready

### Añadido

#### Backend
- **Login Dual (Email o Username)**: Endpoint `/api/auth/login` ahora acepta tanto email como username como identificador, alineándose con estándares enterprise y mejorando la experiencia del usuario.
- **Recuperación Self-Service de Contraseña**: Sistema completo de "Olvidé mi contraseña" con dos endpoints:
  - `POST /api/auth/forgot-password`: Genera token UUID único y envía email con enlace de reset (expira en 1 hora).
  - `POST /api/auth/reset-password`: Valida token, actualiza contraseña con bcrypt, marca token como usado.
- **Servicio de Email (SMTP)**: Integración con Zoho Mail Europe (`smtp.zoho.eu:587`) usando `fastapi-mail` con templates HTML profesionales.
- **Modelo de Password Reset Tokens**: Tabla `password_reset_tokens` con campos: `id`, `user_id`, `token`, `expires_at`, `used`, `created_at`. Índices en `token` y `user_id` para performance.
- **Campo Email Verified**: Agregado `email_verified` (boolean) en tabla `users` para preparación de SSO futuro.
- **Rate Limiting**: Protección anti-brute-force en `/forgot-password` (3 intentos por hora por IP) usando `slowapi`.
- **Audit Logging Mejorado**: Logs estructurados en Loki para eventos críticos:
  - Login exitoso/fallido (con email/username)
  - Password reset solicitado
  - Password reset completado/fallido
  - Validación de token fallida
- **Script de Testing**: `test_smtp.py` para verificar conexión SMTP y `test_forgot_password.py` para flujo completo.
- **Migración Alembic**: `4a7b3c8d9e2f_password_reset_tokens.py` con lógica idempotente (IF NOT EXISTS).

#### Frontend
- **Login Dual en UI**: Campo "Email or Username" en página de login con placeholder adaptado.
- **Modal "Olvidé mi Contraseña"**: Modal en español con validación de email, feedback visual, y manejo de errores.
- **Página Reset Password**: Nueva ruta `/reset-password?token=...` con:
  - Validación de contraseña fuerte (min. 8 chars, uppercase, lowercase, número, carácter especial)
  - Confirmación de contraseña
  - Toggle de visibilidad de password
  - Pantalla de éxito con redirección automática a login
  - Manejo de tokens expirados/inválidos
- **Limpieza de Sesión**: localStorage se limpia automáticamente al entrar/salir de reset page para prevenir confusión por sesiones previas.
- **Interfaz 100% en Español**: Todos los textos del módulo de autenticación traducidos.

#### Seguridad
- **Single-Use Token**: Token se marca como `used=True` después del primer uso exitoso.
- **Expiración de Token**: 1 hora de vida útil.
- **Invalidación Múltiple**: Al reset exitoso, todos los otros tokens activos del usuario se invalidan.
- **Validación de Contraseña**: Requisitos robustos (min. 8 caracteres, complejidad).
- **Anti-Enumeration**: Mensajes genéricos en `/forgot-password` para prevenir descubrimiento de emails registrados.
- **Headers de Seguridad**: Integración correcta con Cloudflare (X-Forwarded-For, X-Forwarded-Proto).

#### Dependencias
- `fastapi-mail==1.4.1`: Envío asíncrono de emails
- `slowapi==0.1.9`: Rate limiting
- `alembic==1.13.1`: Migraciones de base de datos (ya existente)

### Mejorado

- **Endpoint `/api/auth/me`**: Ahora retorna datos completos del usuario incluyendo:
  - `id`, `username`, `email`, `full_name`
  - `roles` (lista de roles del usuario)
  - `permissions` (lista agregada de todos los permisos)
  - `highest_role` (rol con más privilegios)
  - `must_change_password`, `last_login`, `created_at`
  - `sso_provider`, `email_verified` (preparación SSO)
- **Manejo de Errores Frontend**: Errores del backend ahora se muestran claramente al usuario con `data.detail`, más `console.error()` para debugging.
- **Build Frontend**: Optimización de bundle size y performance (730KB minificado).

### Corregido

- **v2.5.4 Bug Fix**: Limpieza automática de sesiones en localStorage para prevenir confusión cuando usuario tiene sesión previa y usa password reset.
- **SMTP Region**: Corrección de servidor SMTP de `smtp.zoho.com` a `smtp.zoho.eu` (Europa) para entrega confiable.
- **Emails de Usuarios**: Actualización de emails en base de datos para usuarios existentes.

### Deprecated

- *Ninguno*

### Removido

- *Ninguno*

### Seguridad

- **Rate Limiting**: 3 intentos/hora en forgot-password por IP.
- **Token Single-Use**: Prevención de reutilización de tokens.
- **Session Invalidation**: Limpieza de localStorage en reset page.
- **Audit Logging**: Registro completo de eventos de autenticación en Loki.
- **Password Strength**: Validación robusta client-side y server-side.

### Notas Técnicas

- **Base de Datos**: PostgreSQL con Alembic para migraciones.
- **Email Provider**: Zoho Mail Europe (requiere App Password si 2FA habilitado).
- **Frontend**: React + TypeScript + Vite, reconstruido y desplegado.
- **Backend**: FastAPI + SQLAlchemy + bcrypt.
- **Testing**: End-to-end tests completados (automated + manual UI).

### Testing Realizado

- ✅ Login con email: `rafael.canelon@rhinometric.com`
- ✅ Login con username: `admin`
- ✅ Forgot password → Email enviado
- ✅ Reset password con token válido → Contraseña actualizada
- ✅ Token single-use enforcement
- ✅ Token expiration (1 hora)
- ✅ Password validation (weak rejected, strong accepted)
- ✅ Login con nueva contraseña → Exitoso
- ✅ Login con password vieja → Rechazado
- ✅ Audit logs en Loki → Registrados correctamente
- ✅ Rate limiting → Enforced
- ✅ Frontend en español → Desplegado

### Breaking Changes

**Ninguno.** Todos los cambios son backward compatible. El sistema sigue aceptando username como antes, y ahora también acepta email.

### Migración Requerida

**Base de Datos**: Ejecutar migración Alembic:
```bash
docker exec rhinometric-console-backend alembic upgrade head
```

### Archivos Modificados/Creados

**Backend:**
- `backend/.env` (configuración SMTP)
- `backend/config.py` (nuevas env vars)
- `backend/requirements.txt` (nuevas dependencias)
- `backend/routers/auth.py` (login dual, forgot/reset endpoints)
- `backend/services/email_service.py` (NUEVO)
- `backend/models/password_reset.py` (NUEVO)
- `backend/models/user.py` (campo email_verified)
- `backend/alembic/versions/4a7b3c8d9e2f_password_reset_tokens.py` (NUEVO)
- `backend/test_smtp.py` (NUEVO)
- `backend/test_forgot_password.py` (NUEVO)

**Frontend:**
- `frontend/src/pages/Login.tsx` (modal forgot password en español)
- `frontend/src/pages/ResetPassword.tsx` (NUEVO)
- `frontend/src/App.tsx` (ruta /reset-password)

**Documentación:**
- `CHANGELOG.md` (esta sección)
- `README_AUTH.md` (NUEVO)
- `BUG_FIX_REPORT_V254.md` (NUEVO)

### Próximos Pasos (Roadmap)

- [ ] SSO/SAML Integration (v2.6.0)
- [ ] Multi-Factor Authentication (v2.7.0)
- [ ] Password Policies Configurables (v2.8.0)
- [ ] Social Login (Google, Microsoft) (v2.9.0)

---

**Versión:** v2.5.3  
**Autor:** Rhinometric.com  
**Licencia:** Proprietary  
**Documentación Completa:** Ver `README_AUTH.md`

---

## [2.5.2] - 2026-02-08

### RBAC Enterprise

*(Contenido previo del CHANGELOG...)*

---

## [2.5.1] - 2026-02-07

### Rescue & Stabilization

*(Contenido previo del CHANGELOG...)*
