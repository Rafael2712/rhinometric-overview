# Quick Start Guide

## Opción 1: Desarrollo Local (Recomendado para pruebas)

```bash
cd dashboard-studio
npm install
npm run dev
```

Abre: http://localhost:3001

## Opción 2: Producción con Docker Compose

```bash
cd dashboard-studio
docker-compose up -d --build
```

Servicios:
- Dashboard Studio: http://localhost:3001
- Dashboard Builder API: http://localhost:8001

## Opción 3: Script de Setup Automático

```bash
cd dashboard-studio
chmod +x setup.sh
./setup.sh
```

## Autenticación JWT

Genera un token:

```bash
docker exec rhinometric-dashboard-builder python -c \
  "import jwt; from datetime import datetime, timedelta, timezone; \
   print(jwt.encode({'user_id': 'admin', 'username': 'admin', 'role': 'admin', \
   'iat': datetime.now(timezone.utc), 'exp': datetime.now(timezone.utc) + timedelta(days=365)}, \
   'your_jwt_secret_for_license_system_change_this', algorithm='HS256'))"
```

Copia el token y pégalo en la UI cuando se solicite.

## Smoke Test End-to-End

```bash
cd dashboard-studio
chmod +x smoke-test.sh
./smoke-test.sh
```

Esto probará:
✓ Conectividad API
✓ Datasource Prometheus
✓ Creación de dashboard
✓ Validación en Grafana

## Resolución de Problemas

### "Cannot connect to API"
```bash
docker ps | grep dashboard-builder
docker logs rhinometric-dashboard-builder
```

### "No datasource found"
Verifica en Grafana: http://localhost:3000/datasources

### Puerto 3001 ocupado
Cambia el puerto en `docker-compose.yml`:
```yaml
ports:
  - "3002:3001"  # Usa puerto 3002
```

## Documentación Completa

Ver: `README.md`
