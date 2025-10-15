# 🔐 Keycloak Enterprise Security Integration

## Sistema de Seguridad Implementado

**Keycloak v23.0.1** - Plataforma de seguridad enterprise open source
- ✅ **Identity & Access Management (IAM)**
- ✅ **Single Sign-On (SSO)**  
- ✅ **Multi-Factor Authentication (MFA)**
- ✅ **OAuth 2.0 / OpenID Connect**
- ✅ **Role-Based Access Control (RBAC)**
- ✅ **API Protection con JWT**
- ✅ **User Federation**
- ✅ **Admin Console Web**

## Arquitectura de Seguridad

```
[Frontend] ←→ [Keycloak] ←→ [Rhinometric API] ←→ [PostgreSQL]
                   ↓
             [Auth Database]
```

## Configuración Implementada

### 🏗️ Infrastructure
- **Keycloak Server**: `http://localhost:8080`
- **Admin Console**: `http://localhost:8080/admin`
- **Database**: PostgreSQL dedicada para Keycloak
- **Health Checks**: Endpoint `/health/ready`

### 🔑 Credenciales Iniciales
```
Admin Console:
- Usuario: admin
- Password: keycloak_admin_secure_2024
- URL: http://localhost:8080/admin
```

### 🎯 Realm Configuration
- **Realm Name**: `rhinometric`
- **Client ID**: `rhinometric-api`
- **Protocol**: OpenID Connect
- **Access Type**: Confidential

## Integración con API

### JWT Token Validation
- Validación automática de tokens JWT
- Verificación de firma con clave pública de Keycloak
- Claims validation (iss, aud, exp)

### Protected Endpoints
```javascript
// Endpoints que requieren autenticación:
POST /api/v1/auth/login    // Via Keycloak
GET  /api/v1/tenants       // Requiere token válido
POST /api/v1/tenants       // Requiere rol 'admin'
```

### Roles y Permisos
- **admin**: Acceso completo al sistema
- **tenant_manager**: Gestión de tenants
- **user**: Acceso básico
- **viewer**: Solo lectura

## Comandos de Inicio

```bash
# Iniciar con Keycloak
docker-compose -f docker-compose.security.yml up -d

# Ver logs de Keycloak
docker logs rhinometric-keycloak -f

# Acceder a Admin Console
open http://localhost:8080/admin
```

## Configuración Inicial

### 1. Crear Realm 'rhinometric'
1. Acceder a Admin Console: `http://localhost:8080/admin`
2. Login con admin/keycloak_admin_secure_2024
3. Crear nuevo realm: `rhinometric`

### 2. Configurar Client 'rhinometric-api'
```json
{
  "clientId": "rhinometric-api",
  "protocol": "openid-connect",
  "clientAuthenticatorType": "client-secret",
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": true,
  "serviceAccountsEnabled": true,
  "rootUrl": "http://localhost:3001",
  "validRedirectUris": ["http://localhost:3001/*"]
}
```

### 3. Crear Roles
- `admin` - Administrador del sistema
- `tenant_manager` - Gestor de tenants  
- `user` - Usuario estándar
- `viewer` - Solo lectura

### 4. Configurar Users
- Crear usuarios de prueba
- Asignar roles apropiados
- Configurar MFA (opcional)

## API Integration Code

Se implementan middlewares para:
- Validación de tokens JWT
- Extracción de roles y permisos
- Autorización basada en roles
- Refresh token handling

## Security Features Enabled

### 🛡️ Protecciones Implementadas
- **JWT Token Validation**
- **Role-Based Authorization**
- **CORS Protection**
- **Rate Limiting**
- **Security Headers**
- **SQL Injection Prevention**
- **XSS Protection**

### 📊 Monitoring & Auditing
- **Authentication Events Logging**
- **Failed Login Attempts Tracking**
- **Session Management**
- **Security Metrics**

## Production Considerations

### 🔐 Security Hardening
- Cambiar passwords por defecto
- Configurar HTTPS en producción
- Habilitar MFA obligatorio
- Configurar session timeouts
- Implementar password policies

### 🏭 Production Deployment
- Usar base de datos externa (no dev mode)
- Configurar clustering para HA
- SSL/TLS certificates
- Reverse proxy con Nginx
- Backup de configuración

## Testing

```bash
# Test de autenticación
curl -X POST http://localhost:8080/realms/rhinometric/protocol/openid-connect/token \
  -d "client_id=rhinometric-api" \
  -d "client_secret=your-secret" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testpass"

# Test de API protegida
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:3001/api/v1/tenants
```

---

**🎯 Estado**: Sistema de seguridad enterprise implementado  
**🔒 Nivel**: Máxima seguridad con Keycloak  
**📈 Mejora**: De seguridad básica a enterprise-grade