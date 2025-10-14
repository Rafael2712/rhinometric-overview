# GitHub Secrets Configuration

Esta documentación explica cómo configurar los secrets necesarios para el pipeline de CI/CD de Rhinometric.

## 📋 Tabla de Secrets Requeridos

### 🔐 Secrets de Oracle Cloud

| Secret Name | Description | Example Value | Environment |
|-------------|-------------|---------------|-------------|
| `ORACLE_SSH_PRIVATE_KEY` | Clave SSH privada para conectar a Oracle Cloud | `-----BEGIN OPENSSH PRIVATE KEY-----\n...` | All |
| `ORACLE_HOST` | IP pública del servidor Oracle Cloud | `198.51.100.123` | All |
| `ORACLE_USERNAME` | Usuario para SSH (generalmente 'opc') | `opc` | All |

### 🗄️ Secrets de Base de Datos

| Secret Name | Description | Example Value | Environment |
|-------------|-------------|---------------|-------------|
| `DB_HOST` | Host de la base de datos | `localhost` o IP del servidor | Per Environment |
| `DB_PORT` | Puerto de PostgreSQL | `5432` | Per Environment |
| `DB_NAME` | Nombre de la base de datos | `rhinometric_prod` | Per Environment |
| `DB_USER` | Usuario de PostgreSQL | `rhinometric_user` | Per Environment |
| `DB_PASSWORD` | Contraseña de PostgreSQL | `secure_password_123` | Per Environment |

### 🔑 Secrets de Aplicación

| Secret Name | Description | Example Value | Environment |
|-------------|-------------|---------------|-------------|
| `JWT_SECRET` | Clave secreta para JWT tokens | `your-super-secure-jwt-secret-key` | Per Environment |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379` | Per Environment |
| `API_ENCRYPTION_KEY` | Clave para encriptación de datos | `32-character-encryption-key` | Per Environment |

### 📢 Secrets de Notificaciones

| Secret Name | Description | Example Value | Environment |
|-------------|-------------|---------------|-------------|
| `SLACK_WEBHOOK` | Webhook URL para notificaciones Slack | `https://hooks.slack.com/services/...` | Repository |
| `EMAIL_USERNAME` | Usuario para notificaciones email | `notifications@rhinometric.com` | Repository |
| `EMAIL_PASSWORD` | Contraseña para email SMTP | `email_password_123` | Repository |
| `NOTIFICATION_EMAIL` | Email para recibir alertas | `admin@rhinometric.com` | Repository |

### 🔒 Secrets de Security Scanning

| Secret Name | Description | Example Value | Environment |
|-------------|-------------|---------------|-------------|
| `SNYK_TOKEN` | Token de Snyk para security scanning | `snyk-token-here` | Repository |
| `CODECOV_TOKEN` | Token para subir coverage reports | `codecov-token-here` | Repository |

## 🏗️ Configuración por Ambiente

### Development Environment
```bash
# Base de datos
DB_HOST=dev-db.rhinometric.com
DB_PORT=5432
DB_NAME=rhinometric_dev
DB_USER=rhinometric_dev_user
DB_PASSWORD=dev_password_secure

# Redis
REDIS_URL=redis://dev-redis.rhinometric.com:6379

# JWT
JWT_SECRET=development-jwt-secret-key-very-long-and-secure
```

### Staging Environment
```bash
# Base de datos
DB_HOST=staging-db.rhinometric.com
DB_PORT=5432
DB_NAME=rhinometric_staging
DB_USER=rhinometric_staging_user
DB_PASSWORD=staging_password_secure

# Redis
REDIS_URL=redis://staging-redis.rhinometric.com:6379

# JWT
JWT_SECRET=staging-jwt-secret-key-very-long-and-secure
```

### Production Environment
```bash
# Base de datos
DB_HOST=prod-db.rhinometric.com
DB_PORT=5432
DB_NAME=rhinometric_prod
DB_USER=rhinometric_prod_user
DB_PASSWORD=production_password_very_secure

# Redis
REDIS_URL=redis://prod-redis.rhinometric.com:6379

# JWT
JWT_SECRET=production-jwt-secret-key-extremely-long-and-secure
```

## 📝 Instrucciones de Configuración

### 1. Acceder a GitHub Secrets

1. Ve a tu repositorio en GitHub
2. Haz clic en **Settings** → **Secrets and variables** → **Actions**
3. Selecciona **Secrets** tab

### 2. Configurar Repository Secrets

Estos secrets se aplican a todo el repositorio:

```bash
# Notificaciones
SLACK_WEBHOOK=https://hooks.slack.com/services/your/slack/webhook
EMAIL_USERNAME=notifications@rhinometric.com
EMAIL_PASSWORD=your_email_password
NOTIFICATION_EMAIL=admin@rhinometric.com

# Security Scanning
SNYK_TOKEN=your_snyk_token
CODECOV_TOKEN=your_codecov_token

# Oracle Cloud
ORACLE_SSH_PRIVATE_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END OPENSSH PRIVATE KEY-----"
ORACLE_HOST=198.51.100.123
ORACLE_USERNAME=opc
```

### 3. Configurar Environment Secrets

Ve a **Settings** → **Environments** y configura cada ambiente:

#### Development Environment
- `DB_HOST`: `dev-db.rhinometric.com`
- `DB_PORT`: `5432`
- `DB_NAME`: `rhinometric_dev`
- `DB_USER`: `rhinometric_dev_user`
- `DB_PASSWORD`: `[secure_dev_password]`
- `REDIS_URL`: `redis://dev-redis.rhinometric.com:6379`
- `JWT_SECRET`: `[development_jwt_secret]`

#### Staging Environment
- `DB_HOST`: `staging-db.rhinometric.com`
- `DB_PORT`: `5432`
- `DB_NAME`: `rhinometric_staging`
- `DB_USER`: `rhinometric_staging_user`
- `DB_PASSWORD`: `[secure_staging_password]`
- `REDIS_URL`: `redis://staging-redis.rhinometric.com:6379`
- `JWT_SECRET`: `[staging_jwt_secret]`

#### Production Environment
- `DB_HOST`: `prod-db.rhinometric.com`
- `DB_PORT`: `5432`
- `DB_NAME`: `rhinometric_prod`
- `DB_USER`: `rhinometric_prod_user`
- `DB_PASSWORD`: `[secure_production_password]`
- `REDIS_URL`: `redis://prod-redis.rhinometric.com:6379`
- `JWT_SECRET`: `[production_jwt_secret]`

## 🔑 Generación de Claves Seguras

### JWT Secret
```bash
# Generar JWT secret de 64 caracteres
openssl rand -base64 48
```

### Encryption Key
```bash
# Generar clave de encriptación de 32 caracteres
openssl rand -hex 32
```

### Database Password
```bash
# Generar contraseña segura
openssl rand -base64 32
```

## 🚨 Buenas Prácticas de Seguridad

### ✅ DO (Hacer)

1. **Usar secretos diferentes por ambiente**
   - Nunca reutilices passwords entre dev/staging/production
   
2. **Rotar secretos regularmente**
   - Cambia JWT secrets cada 6 meses
   - Rota database passwords cada 3 meses
   
3. **Principio de menor privilegio**
   - Cada ambiente debe tener acceso solo a sus recursos
   
4. **Encriptar secretos en tránsito y reposo**
   - GitHub Secrets están encriptados automáticamente
   
5. **Auditar acceso a secretos**
   - Monitorea quién accede a qué secretos

### ❌ DON'T (No hacer)

1. **No hardcodear secretos en código**
   - Nunca pongas passwords en el código fuente
   
2. **No usar secretos débiles**
   - Evita passwords simples o predecibles
   
3. **No compartir secretos por email/chat**
   - Usa siempre canales seguros
   
4. **No logear secretos**
   - Asegúrate que no aparezcan en logs
   
5. **No usar secretos de producción en desarrollo**
   - Mantén ambientes completamente separados

## 📋 Checklist de Configuración

- [ ] ✅ Repository secrets configurados
- [ ] 🔧 Development environment secrets configurados
- [ ] 🎭 Staging environment secrets configurados
- [ ] 🌟 Production environment secrets configurados
- [ ] 🔑 Oracle Cloud SSH keys configurados
- [ ] 📢 Slack webhook configurado
- [ ] 📧 Email notifications configuradas
- [ ] 🔒 Snyk token configurado
- [ ] 📊 Codecov token configurado
- [ ] 🧪 Todos los secrets probados

## 🔧 Testing de Secrets

Para probar que todos los secrets están configurados correctamente:

```bash
# En tu repositorio local
gh workflow run ci-cd.yml --ref develop

# O crear un PR para triggear el pipeline
git checkout develop
git commit --allow-empty -m "test: trigger CI/CD pipeline"
git push origin develop
```

## 🆘 Troubleshooting

### Error: Secret not found
- Verifica que el nombre del secret coincida exactamente
- Asegúrate de estar en el ambiente correcto

### Error: SSH connection failed
- Verifica que `ORACLE_SSH_PRIVATE_KEY` esté en formato correcto
- Confirma que `ORACLE_HOST` sea la IP correcta
- Asegúrate que el firewall permita conexiones SSH

### Error: Database connection failed
- Verifica credenciales de base de datos
- Confirma que la base de datos esté accesible
- Revisa que los puertos estén abiertos

---

**📚 Documentación relacionada:**
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Oracle Cloud SSH Keys](../infrastructure/oracle-dns-helper.sh)