# 🔌 DATOS DE CONEXIÓN - RHINOMETRIC PostgreSQL

## ✅ ESTADO: TODOS LOS SERVICIOS OPERACIONALES

**Fecha**: 2025-11-05  
**Verificación**: Completada exitosamente

---

## 📊 DATOS DE CONEXIÓN POSTGRESQL

### Conexión desde API Connector UI

**Abrir**: http://localhost:8000

**Datos del formulario**:
```
Tipo de Conector: PostgreSQL
Host: rhinometric-postgres
Puerto: 5432
Base de datos: rhinometric
Usuario: rhinometric
Password: rhinometric2024
```

### Conexión desde aplicaciones externas (fuera de Docker)

```
Host: localhost
Puerto: 5432
Base de datos: rhinometric
Usuario: rhinometric
Password: rhinometric2024
```

### String de conexión (formato estándar)

```
postgresql://rhinometric:rhinometric2024@localhost:5432/rhinometric
```

### String de conexión (desde contenedores Docker)

```
postgresql://rhinometric:rhinometric2024@rhinometric-postgres:5432/rhinometric
```

---

## 🧪 VERIFICACIÓN DE CONEXIÓN

### Desde línea de comandos (Windows)

```bash
# Usando psql desde WSL
wsl -d Ubuntu-22.04 -u rafael -- docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -c "SELECT version();"
```

### Desde Python

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="rhinometric",
    user="rhinometric",
    password="rhinometric2024"
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
conn.close()
```

### Desde Node.js

```javascript
const { Client } = require('pg');

const client = new Client({
  host: 'localhost',
  port: 5432,
  database: 'rhinometric',
  user: 'rhinometric',
  password: 'rhinometric2024'
});

client.connect();
client.query('SELECT version()', (err, res) => {
  console.log(res.rows[0]);
  client.end();
});
```

---

## 📊 INFORMACIÓN DE LA BASE DE DATOS

**Version**: PostgreSQL 15.10  
**Compilación**: x86_64-pc-linux-musl (Alpine Linux)  
**Contenedor**: rhinometric-postgres  
**Estado**: ✅ HEALTHY  
**Puerto interno**: 5432  
**Puerto expuesto**: 5432

---

## 🗄️ BASES DE DATOS DISPONIBLES

### Base de datos principal: `rhinometric`

**Propósito**: Almacenamiento de datos de la plataforma RHINOMETRIC

**Tablas disponibles** (verificar con `\dt`):
- Configuraciones de dashboards
- Metadatos de datasources
- Usuarios y licencias
- Logs y auditoría

---

## 🔧 COMANDOS ÚTILES

### Conectar al PostgreSQL desde Docker

```bash
# Acceso interactivo
docker exec -it rhinometric-postgres psql -U rhinometric -d rhinometric

# Ejecutar query directa
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -c "SELECT * FROM pg_database;"

# Ver tablas
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -c "\dt"

# Ver usuarios
docker exec rhinometric-postgres psql -U rhinometric -d rhinometric -c "\du"
```

### Backup de la base de datos

```bash
# Crear backup
docker exec rhinometric-postgres pg_dump -U rhinometric rhinometric > backup_$(date +%Y%m%d).sql

# Restaurar backup
cat backup_20251105.sql | docker exec -i rhinometric-postgres psql -U rhinometric -d rhinometric
```

---

## 🌐 TODOS LOS SERVICIOS - URLS Y CREDENCIALES

| Servicio | URL | Credenciales | Estado |
|----------|-----|--------------|--------|
| **Grafana** | http://localhost:80 | admin / admin | ✅ OK |
| **API Connector** | http://localhost:8000 | (no auth) | ✅ OK |
| **Dashboard Builder** | http://localhost:8001 | (no auth) | ✅ OK |
| **License UI** | http://localhost:8092 | (no auth) | ✅ OK |
| **Prometheus** | http://localhost:9090 | (no auth) | ✅ OK |
| **Loki** | http://localhost:3100 | (no auth) | ✅ OK |
| **Tempo** | http://localhost:3200 | (no auth) | ✅ OK |
| **PostgreSQL** | localhost:5432 | rhinometric / rhinometric2024 | ✅ OK |
| **Redis** | localhost:6379 | password: rhinometric | ✅ OK |

---

## 🧪 PROBAR API CONNECTOR CON POSTGRESQL

### Paso 1: Abrir API Connector

```
http://localhost:8000
```

### Paso 2: Seleccionar PostgreSQL

Click en el botón "PostgreSQL" o seleccionar del dropdown

### Paso 3: Completar formulario

```
Host: rhinometric-postgres
Puerto: 5432
Base de datos: rhinometric
Usuario: rhinometric
Password: rhinometric2024
```

### Paso 4: Probar Conexión

Click en el botón "Probar Conexión"

**Resultado esperado**: ✅ "Conexión exitosa"

### Paso 5: Crear Datasource en Grafana

Click en "🔗 Crear Datasource en Grafana"

**Resultado esperado**: ✅ "Datasource creado con UID: xxx"

**Nota**: Para este paso necesitas haber creado el Grafana API Token (ver HOW_TO_GET_GRAFANA_TOKEN.md)

---

## 🐛 TROUBLESHOOTING

### Error: Connection refused

**Problema**: No se puede conectar al PostgreSQL  
**Solución**:
```bash
# Verificar que el contenedor está corriendo
docker ps | grep postgres

# Verificar logs
docker logs rhinometric-postgres --tail 20

# Reiniciar si es necesario
docker restart rhinometric-postgres
```

### Error: Password authentication failed

**Problema**: Credenciales incorrectas  
**Solución**: Usar las credenciales correctas:
- Usuario: `rhinometric`
- Password: `rhinometric2024`

### Error: Database does not exist

**Problema**: Base de datos no existe  
**Solución**:
```bash
# Listar bases de datos disponibles
docker exec rhinometric-postgres psql -U rhinometric -c "\l"

# Crear base de datos si no existe
docker exec rhinometric-postgres psql -U rhinometric -c "CREATE DATABASE rhinometric;"
```

---

## 🔒 SEGURIDAD

⚠️ **IMPORTANTE**: Las credenciales mostradas son para desarrollo/demo

**En producción**:
1. Cambiar todas las passwords
2. Usar variables de entorno cifradas
3. Implementar SSL/TLS para conexiones
4. Restringir acceso por IP
5. Usar secrets management (Vault, K8s Secrets)

---

## 📝 NOTAS ADICIONALES

### Extensiones PostgreSQL disponibles

```sql
-- Ver extensiones instaladas
SELECT * FROM pg_extension;

-- Instalar extensión (ejemplo: pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

### Performance tuning

El PostgreSQL está configurado con límites de recursos:
- CPU: 0.5 cores
- Memory: 512 MB

Para ajustar, editar `docker-compose-v2.2.0.yml`:
```yaml
postgres:
  deploy:
    resources:
      limits:
        cpus: '1.0'      # Aumentar CPU
        memory: 1024M    # Aumentar memoria
```

---

**Documento generado**: 2025-11-05  
**Versión RHINOMETRIC**: v2.4.0  
**Estado**: ✅ TODOS LOS SERVICIOS OPERACIONALES
