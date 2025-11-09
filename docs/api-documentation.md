# 📚 Rhinometric API Documentation

Esta documentación describe la API RESTful de Rhinometric, una plataforma SaaS multi-tenant.

## 📋 Información General

### URLs Base

| Ambiente | URL Base | Estado |
|----------|----------|---------|
| **Development** | `https://dev-api.rhinometric.com/api/v1` | 🟢 Activo |
| **Staging** | `https://staging-api.rhinometric.com/api/v1` | 🟡 Testing |
| **Production** | `https://api.rhinometric.com/api/v1` | 🔵 Producción |

### Versioning

- **Versión Actual**: `v1`
- **Formato**: `/api/v1/endpoint`
- **Header**: `Accept: application/json`

### Autenticación

```http
Authorization: Bearer <jwt_token>
```

## 🔐 Autenticación

### POST /auth/register

Registra un nuevo usuario en el sistema.

**Endpoint:** `POST /api/v1/auth/register`

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123",
  "firstName": "Juan",
  "lastName": "Pérez",
  "companyName": "Empresa SA"
}
```

**Response 201 (Created):**
```json
{
  "success": true,
  "message": "Usuario registrado exitosamente",
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "usuario@ejemplo.com",
      "firstName": "Juan",
      "lastName": "Pérez",
      "companyName": "Empresa SA",
      "createdAt": "2025-10-14T10:30:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response 400 (Validation Error):**
```json
{
  "success": false,
  "message": "Error de validación",
  "errors": [
    {
      "field": "email",
      "message": "Email inválido"
    },
    {
      "field": "password",
      "message": "La contraseña debe tener al menos 8 caracteres"
    }
  ]
}
```

### POST /auth/login

Autentica un usuario existente.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```

**Response 200 (Success):**
```json
{
  "success": true,
  "message": "Login exitoso",
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "usuario@ejemplo.com",
      "firstName": "Juan",
      "lastName": "Pérez"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": "24h"
  }
}
```

**Response 401 (Unauthorized):**
```json
{
  "success": false,
  "message": "Credenciales inválidas"
}
```

### POST /auth/refresh

Renueva un token JWT.

**Endpoint:** `POST /api/v1/auth/refresh`

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response 200 (Success):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": "24h"
  }
}
```

### POST /auth/logout

Cierra sesión y revoca el token.

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response 200 (Success):**
```json
{
  "success": true,
  "message": "Logout exitoso"
}
```

## 👤 Usuarios

### GET /users/profile

Obtiene el perfil del usuario autenticado.

**Endpoint:** `GET /api/v1/users/profile`

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response 200 (Success):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "usuario@ejemplo.com",
      "firstName": "Juan",
      "lastName": "Pérez",
      "companyName": "Empresa SA",
      "role": "user",
      "isActive": true,
      "createdAt": "2025-10-14T10:30:00Z",
      "updatedAt": "2025-10-14T10:30:00Z"
    }
  }
}
```

### PUT /users/profile

Actualiza el perfil del usuario autenticado.

**Endpoint:** `PUT /api/v1/users/profile`

**Headers:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "firstName": "Juan Carlos",
  "lastName": "Pérez García",
  "companyName": "Nueva Empresa SAS"
}
```

**Response 200 (Success):**
```json
{
  "success": true,
  "message": "Perfil actualizado exitosamente",
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "usuario@ejemplo.com",
      "firstName": "Juan Carlos",
      "lastName": "Pérez García",
      "companyName": "Nueva Empresa SAS",
      "updatedAt": "2025-10-14T11:00:00Z"
    }
  }
}
```

### PUT /users/password

Cambia la contraseña del usuario autenticado.

**Endpoint:** `PUT /api/v1/users/password`

**Headers:**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "currentPassword": "password123",
  "newPassword": "newpassword456"
}
```

**Response 200 (Success):**
```json
{
  "success": true,
  "message": "Contraseña actualizada exitosamente"
}
```

**Response 400 (Invalid Current Password):**
```json
{
  "success": false,
  "message": "La contraseña actual es incorrecta"
}
```

## 🔍 Health Check

### GET /health

Verifica el estado de la API y sus dependencias.

**Endpoint:** `GET /api/v1/health`

**Response 200 (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-14T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": {
      "status": "connected",
      "responseTime": "12ms"
    },
    "redis": {
      "status": "connected", 
      "responseTime": "3ms"
    }
  },
  "uptime": 86400
}
```

**Response 503 (Unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2025-10-14T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": {
      "status": "disconnected",
      "error": "Connection timeout"
    },
    "redis": {
      "status": "connected",
      "responseTime": "3ms"
    }
  }
}
```

## 📊 Códigos de Estado HTTP

| Código | Significado | Descripción |
|--------|-------------|-------------|
| **200** | OK | Solicitud exitosa |
| **201** | Created | Recurso creado exitosamente |
| **204** | No Content | Solicitud exitosa sin contenido |
| **400** | Bad Request | Error en la solicitud del cliente |
| **401** | Unauthorized | Autenticación requerida |
| **403** | Forbidden | Acceso prohibido |
| **404** | Not Found | Recurso no encontrado |
| **409** | Conflict | Conflicto con el estado actual |
| **422** | Unprocessable Entity | Error de validación |
| **429** | Too Many Requests | Rate limit excedido |
| **500** | Internal Server Error | Error interno del servidor |
| **503** | Service Unavailable | Servicio temporalmente no disponible |

## 🛡️ Manejo de Errores

### Formato de Error Estándar

Todos los errores siguen el mismo formato:

```json
{
  "success": false,
  "message": "Descripción del error",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-14T12:00:00Z",
  "path": "/api/v1/endpoint",
  "errors": [
    {
      "field": "campo",
      "message": "Mensaje específico del campo"
    }
  ]
}
```

### Códigos de Error Personalizados

| Código | Descripción |
|--------|-------------|
| `AUTH_INVALID_CREDENTIALS` | Credenciales inválidas |
| `AUTH_TOKEN_EXPIRED` | Token JWT expirado |
| `AUTH_TOKEN_INVALID` | Token JWT inválido |
| `VALIDATION_ERROR` | Error de validación de datos |
| `USER_NOT_FOUND` | Usuario no encontrado |
| `USER_ALREADY_EXISTS` | Usuario ya existe |
| `RATE_LIMIT_EXCEEDED` | Límite de requests excedido |
| `INTERNAL_ERROR` | Error interno del servidor |

### Ejemplos de Errores

**Error de Validación:**
```json
{
  "success": false,
  "message": "Error de validación",
  "code": "VALIDATION_ERROR",
  "timestamp": "2025-10-14T12:00:00Z",
  "path": "/api/v1/auth/register",
  "errors": [
    {
      "field": "email",
      "message": "El email debe tener un formato válido"
    },
    {
      "field": "password",
      "message": "La contraseña debe tener al menos 8 caracteres"
    }
  ]
}
```

**Error de Autenticación:**
```json
{
  "success": false,
  "message": "Token JWT inválido",
  "code": "AUTH_TOKEN_INVALID",
  "timestamp": "2025-10-14T12:00:00Z",
  "path": "/api/v1/users/profile"
}
```

## 🔧 Rate Limiting

### Límites por Endpoint

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| `POST /auth/login` | 5 requests | 15 minutos |
| `POST /auth/register` | 3 requests | 1 hora |
| `GET /users/profile` | 100 requests | 15 minutos |
| `PUT /users/profile` | 10 requests | 15 minutos |
| `GET /health` | Sin límite | - |

### Headers de Rate Limit

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95  
X-RateLimit-Reset: 1634212800
```

### Error de Rate Limit

**Response 429:**
```json
{
  "success": false,
  "message": "Límite de requests excedido",
  "code": "RATE_LIMIT_EXCEEDED",
  "retryAfter": 300
}
```

## 🔒 Seguridad

### CORS

La API acepta requests desde los siguientes orígenes:

- `https://www.rhinometric.com`
- `https://app.rhinometric.com`
- `http://localhost:3000` (solo desarrollo)

### Headers de Seguridad

La API incluye los siguientes headers de seguridad:

```http
Strict-Transport-Security: max-age=63072000
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### Validación de Input

- Todos los inputs son validados y sanitizados
- Se usa validación tanto en frontend como backend
- Los errores de validación incluyen detalles específicos

## 📝 Ejemplos de Uso

### Registro y Login Completo

```javascript
// 1. Registro
const registerResponse = await fetch('https://api.rhinometric.com/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'usuario@ejemplo.com',
    password: 'password123',
    firstName: 'Juan',
    lastName: 'Pérez',
    companyName: 'Empresa SA'
  })
});

const registerData = await registerResponse.json();
const token = registerData.data.token;

// 2. Obtener perfil
const profileResponse = await fetch('https://api.rhinometric.com/api/v1/users/profile', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const profileData = await profileResponse.json();
console.log(profileData.data.user);

// 3. Actualizar perfil
const updateResponse = await fetch('https://api.rhinometric.com/api/v1/users/profile', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    firstName: 'Juan Carlos',
    companyName: 'Nueva Empresa'
  })
});
```

### cURL Examples

**Registro:**
```bash
curl -X POST https://api.rhinometric.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123",
    "firstName": "Juan",
    "lastName": "Pérez",
    "companyName": "Empresa SA"
  }'
```

**Login:**
```bash
curl -X POST https://api.rhinometric.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123"
  }'
```

**Perfil:**
```bash
curl -X GET https://api.rhinometric.com/api/v1/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Health Check:**
```bash
curl -X GET https://api.rhinometric.com/api/v1/health
```

## 🧪 Testing

### Postman Collection

Importa la colección de Postman para testing:

```bash
# Descargar collection
curl -o Rhinometric-API.postman_collection.json \
  https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/docs/Rhinometric-API.postman_collection.json

# Importar en Postman
# File -> Import -> Rhinometric-API.postman_collection.json
```

### Variables de Ambiente Postman

```json
{
  "dev_base_url": "https://dev-api.rhinometric.com/api/v1",
  "staging_base_url": "https://staging-api.rhinometric.com/api/v1", 
  "prod_base_url": "https://api.rhinometric.com/api/v1",
  "jwt_token": "{{jwt_token}}"
}
```

### Scripts de Test

```javascript
// Test para Login exitoso
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    
    const responseJson = pm.response.json();
    pm.expect(responseJson.success).to.be.true;
    pm.expect(responseJson.data.token).to.be.a('string');
    
    // Guardar token para siguientes requests
    pm.environment.set("jwt_token", responseJson.data.token);
});

// Test para error de validación
pm.test("Validation error", function () {
    pm.response.to.have.status(400);
    
    const responseJson = pm.response.json();
    pm.expect(responseJson.success).to.be.false;
    pm.expect(responseJson.errors).to.be.an('array');
});
```

## 📈 Métricas y Monitoreo

### Logs

Todos los requests son loggeados con el siguiente formato:

```json
{
  "timestamp": "2025-10-14T12:00:00Z",
  "level": "info",
  "message": "HTTP Request",
  "method": "POST",
  "url": "/api/v1/auth/login",
  "status": 200,
  "responseTime": 120,
  "userAgent": "Mozilla/5.0...",
  "ip": "192.168.1.1",
  "userId": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Health Monitoring

El endpoint `/health` se usa para monitoreo automatizado:

```bash
# Configurar health check cada 30 segundos
*/30 * * * * curl -f https://api.rhinometric.com/api/v1/health || echo "API Down"
```

## 🔄 Versionado

### Política de Versionado

- **v1**: Versión actual estable
- **v2**: Próxima versión mayor (en desarrollo)

### Compatibilidad

- Las versiones se mantienen por **12 meses** mínimo
- Los breaking changes solo se introducen en versiones mayores
- La versión anterior se marca como deprecated 6 meses antes del sunset

### Migration Guide

Al migrar a una nueva versión de API:

1. Revisar el changelog
2. Actualizar endpoints en tu aplicación
3. Probar en ambiente de staging
4. Desplegar gradualmente en producción

## 📞 Soporte

### Contacto

- 📧 **API Support**: rafael.canelon@rhinometric.com
- 📚 **Documentation**: GitHub Wiki
- 🐛 **Bug Reports**: GitHub Issues
- 💬 **Community**: Slack #api-help

### SLA

| Ambiente | Uptime | Response Time |
|----------|--------|---------------|
| **Production** | 99.9% | < 200ms |
| **Staging** | 99.5% | < 500ms |
| **Development** | Best Effort | < 1s |

---

**📅 Última actualización:** Octubre 2025  
**📝 Versión de API:** v1.0.0  
**👨‍💻 Mantenido por:** Rhinometric Development Team