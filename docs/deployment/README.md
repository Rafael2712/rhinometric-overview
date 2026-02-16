# Guía de Despliegue - RhinoMetric SaaS

## 🎯 Resumen de Entornos

| Entorno | Puerto | Branch | Dominio | Base de Datos |
|---------|--------|--------|---------|---------------|
| **Desarrollo** | 3001 | `develop` | `localhost:3001` | `rhinometric_dev` |
| **Staging** | 3002 | `staging` | `staging.rhinometric.com` | `rhinometric_staging` |
| **Producción** | 3000 | `main` | `rhinometric.com` | `rhinometric_prod` |

## 🚀 Configuración Inicial

### 1. Preparar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/mi-proyecto.git
cd mi-proyecto

# Crear las ramas necesarias
git checkout -b develop
git checkout -b staging
git checkout main
```

### 2. Configurar Entornos Locales

```bash
# Desarrollo
cd infrastructure/docker
cp .env.development .env
docker-compose -f docker-compose.dev.yml up -d

# Verificar servicios
docker-compose -f docker-compose.dev.yml ps
```

### 3. Inicializar Base de Datos

```bash
cd backend
npm install
npm run migrate
```

## 📋 Workflow de Desarrollo

### Flujo de Branches

```bash
# 1. Desarrollo de features
git checkout develop
git pull origin develop
git checkout -b feature/nueva-funcionalidad

# 2. Desarrollo y commit
# ... hacer cambios ...
git add .
git commit -m "feat: nueva funcionalidad"
git push origin feature/nueva-funcionalidad

# 3. Pull Request a develop
# Crear PR en GitHub: feature/nueva-funcionalidad → develop

# 4. Deploy a staging
git checkout staging
git merge develop
git push origin staging

# 5. Deploy a producción
git checkout main
git merge staging
git push origin main
```

### Comandos de Desarrollo

```bash
# Backend en desarrollo
cd backend
npm run dev                    # Servidor en modo desarrollo
npm run test                   # Ejecutar tests
npm run lint                   # Verificar código

# Docker para desarrollo
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up    # Levantar stack completo
docker-compose -f docker-compose.dev.yml logs  # Ver logs
docker-compose -f docker-compose.dev.yml down  # Parar servicios
```

## 🔧 Configuración por Entorno

### Desarrollo (Puerto 3001)

```bash
cd infrastructure/docker
cp .env.development .env
docker-compose -f docker-compose.dev.yml up -d
```

**URLs de acceso:**
- API: `http://localhost:3001`
- Health Check: `http://localhost:3001/api/v1/health`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Staging (Puerto 3002)

```bash
cd infrastructure/docker
cp .env.staging .env
# Editar .env con credenciales seguras
docker-compose -f docker-compose.yml up -d
```

**URLs de acceso:**
- API: `https://staging-api.rhinometric.com`
- Health Check: `https://staging-api.rhinometric.com/api/v1/health`

### Producción (Puerto 3000)

```bash
cd infrastructure/docker
cp .env.production .env
# Configurar credenciales de producción
docker-compose -f docker-compose.yml up -d
```

**URLs de acceso:**
- API: `https://api.rhinometric.com`
- Health Check: `https://api.rhinometric.com/api/v1/health`

## 🔒 Seguridad y Secretos

### Variables de Entorno Críticas

**⚠️ CAMBIAR EN PRODUCCIÓN:**

```bash
# Generar JWT Secret seguro
JWT_SECRET=$(openssl rand -base64 64)

# Generar password de BD seguro
DB_PASSWORD=$(openssl rand -base64 32)

# Generar password de Redis seguro
REDIS_PASSWORD=$(openssl rand -base64 32)
```

### GitHub Secrets

Configurar en GitHub Settings → Secrets:

```bash
# Producción
PROD_DB_PASSWORD
PROD_REDIS_PASSWORD
PROD_JWT_SECRET
PROD_GRAFANA_PASSWORD

# Staging
STAGING_DB_PASSWORD
STAGING_REDIS_PASSWORD
STAGING_JWT_SECRET
```

## 📊 Monitoreo

### Prometheus + Grafana

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (see `.env` for credentials)

### Health Checks

```bash
# API Health
curl http://localhost:3001/api/v1/health

# Detailed Health
curl http://localhost:3001/api/v1/health/detailed

# Database Health
docker-compose exec postgres pg_isready -U postgres
```

## 🚨 Troubleshooting

### Problemas Comunes

**1. Puerto ya en uso:**
```bash
# Verificar qué proceso usa el puerto
lsof -i :3001
# Cambiar puerto en .env
API_PORT=3005
```

**2. Base de datos no conecta:**
```bash
# Verificar contenedor PostgreSQL
docker-compose logs postgres
# Recrear contenedor
docker-compose down postgres && docker-compose up -d postgres
```

**3. Migraciones fallan:**
```bash
# Conectar a PostgreSQL directamente
docker-compose exec postgres psql -U postgres -d rhinometric_dev
# Verificar tablas existentes
\dt
```

### Logs y Debugging

```bash
# Logs de la API
docker-compose logs -f rhinometric-api

# Logs de todos los servicios
docker-compose logs -f

# Entrar al contenedor de la API
docker-compose exec rhinometric-api sh
```

## 📈 Escalamiento

### Horizontal Scaling

```bash
# Múltiples instancias de API
docker-compose up --scale rhinometric-api=3
```

### Configuración de Load Balancer

Ver configuración en `/infrastructure/nginx/` para balanceador de carga.

## 🔄 CI/CD Pipeline

### GitHub Actions

El pipeline automático ejecuta:

1. **Tests** en cada push/PR
2. **Build** de imagen Docker
3. **Deploy automático:**
   - `develop` → Entorno de desarrollo
   - `staging` → Entorno de staging  
   - `main` → Entorno de producción

### Deployment Manual

```bash
# Deploy manual a producción
git checkout main
git pull origin main
cd infrastructure/docker
docker-compose pull
docker-compose up -d
```