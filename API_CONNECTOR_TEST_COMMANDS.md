# RHINOMETRIC API Connector - Comandos de Prueba Manual

## ✅ Estado de los Conectores

| Conector | Estado | Notas |
|----------|--------|-------|
| PostgreSQL | ✅ REPARADO | Funcionando con credenciales correctas |
| Redis | ✅ REPARADO | Funcionando con credenciales correctas |
| Prometheus | ✅ FUNCIONANDO | Sin cambios necesarios |
| AWS CloudWatch | ⚠️ REQUIERE CREDENCIALES | No probado (requiere credenciales AWS) |
| Azure Monitor | ⚠️ REQUIERE CREDENCIALES | No probado (requiere credenciales Azure) |
| RabbitMQ | ⚠️ NO DISPONIBLE | Servicio no existe en docker-compose |
| Kafka | ⚠️ NO DISPONIBLE | Servicio no existe en docker-compose |
| MQTT | ⚠️ NO DISPONIBLE | Servicio no existe en docker-compose |

---

## ��� Comandos de Prueba (desde Windows PowerShell/CMD)

### 1. PostgreSQL ✅
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"postgresql\",\"host\":\"rhinometric-postgres\",\"port\":5432,\"database\":\"rhinometric\",\"username\":\"rhinometric\",\"password\":\"secure_password_2024\",\"ssl\":false}"
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Connected to PostgreSQL PostgreSQL 15.10 on x86_64-pc-linux-musl",
  "details": {
    "server_version": "PostgreSQL 15.10 on x86_64-pc-linux-musl",
    "database": "rhinometric",
    "database_size": "7957 kB",
    "tables_count": 6,
    "ssl_enabled": false
  },
  "duration_ms": 50.0
}
```

---

### 2. Redis ✅
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"redis\",\"host\":\"rhinometric-redis\",\"port\":6379,\"database\":\"0\",\"password\":\"redis_secure_password\",\"ssl\":false}"
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Connected to Redis 7.2.12",
  "details": {
    "redis_version": "7.2.12",
    "used_memory": "966.31K",
    "connected_clients": 4,
    "uptime_in_days": 0,
    "database": 0,
    "ping": "PONG"
  },
  "duration_ms": 20.0
}
```

---

### 3. Prometheus ✅
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"prometheus\",\"url\":\"http://rhinometric-prometheus:9090\",\"timeout\":30}"
```

**Resultado esperado:**
```json
{
  "success": true,
  "message": "Connected to Prometheus 2.53.0",
  "details": {
    "version": "2.53.0",
    "health_status": "healthy",
    "storage_retention": "15d",
    "url": "http://rhinometric-prometheus:9090"
  },
  "duration_ms": 26.0
}
```

---

### 4. AWS CloudWatch ⚠️
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"aws-cloudwatch\",\"region\":\"us-east-1\",\"access_key\":\"TU_AWS_ACCESS_KEY\",\"secret_key\":\"TU_AWS_SECRET_KEY\"}"
```

**NOTA:** Requiere credenciales válidas de AWS. Reemplaza `TU_AWS_ACCESS_KEY` y `TU_AWS_SECRET_KEY` con tus credenciales.

---

### 5. Azure Monitor ⚠️
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"azure-monitor\",\"subscription_id\":\"TU_SUBSCRIPTION_ID\",\"tenant_id\":\"TU_TENANT_ID\",\"client_id\":\"TU_CLIENT_ID\",\"client_secret\":\"TU_CLIENT_SECRET\"}"
```

**NOTA:** Requiere credenciales válidas de Azure. Reemplaza con tus credenciales de Azure Service Principal.

---

### 6. RabbitMQ ⚠️
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"rabbitmq\",\"host\":\"localhost\",\"port\":15672,\"username\":\"guest\",\"password\":\"guest\",\"vhost\":\"/\",\"ssl\":false}"
```

**NOTA:** RabbitMQ no está disponible en docker-compose-v2.2.0.yml. Para probarlo:
1. Instalar RabbitMQ localmente o agregar servicio al docker-compose
2. Habilitar Management Plugin: `rabbitmq-plugins enable rabbitmq_management`
3. Usar credenciales por defecto: guest/guest

---

### 7. Kafka ⚠️
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"kafka\",\"bootstrap_servers\":\"localhost:9092\",\"security_protocol\":\"PLAINTEXT\"}"
```

**NOTA:** Kafka no está disponible en docker-compose-v2.2.0.yml. Para probarlo:
1. Instalar Kafka localmente o agregar servicio al docker-compose
2. Configurar bootstrap servers correctamente

---

### 8. MQTT ⚠️
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d "{\"datasource_type\":\"mqtt\",\"host\":\"localhost\",\"port\":1883,\"username\":null,\"password\":null,\"client_id\":\"rhinometric-test\",\"use_tls\":false,\"keepalive\":60,\"clean_session\":true,\"test_topic\":\"rhinometric/test\"}"
```

**NOTA:** MQTT no está disponible en docker-compose-v2.2.0.yml. Para probarlo:
1. Instalar Mosquitto localmente o agregar servicio al docker-compose
2. Configurar broker correctamente

---

## ��� Problemas Resueltos

### PostgreSQL
- ❌ **Problema:** Conexión fallaba con credenciales incorrectas
- ✅ **Solución:** Actualizado con credenciales correctas: `rhinometric/secure_password_2024`
- ✅ **Base de datos correcta:** `rhinometric` (no `rhinometric_licenses`)

### Redis
- ❌ **Problema 1:** Error de importación `module 'redis.asyncio' has no attribute 'AuthError'`
- ✅ **Solución 1:** Actualizado conector para usar `AuthenticationError` de `redis.exceptions`
- ❌ **Problema 2:** Tipo de parámetro `database` (esperaba string, recibía int)
- ✅ **Solución 2:** Modificado `__init__` para aceptar `Any` y convertir a int
- ❌ **Problema 3:** Credenciales incorrectas
- ✅ **Solución 3:** Actualizado con contraseña correcta: `redis_secure_password`

### Prometheus
- ✅ **Sin problemas:** Funcionando correctamente desde el inicio

---

## ��� Credenciales del Sistema

### PostgreSQL
- **Host (interno):** `rhinometric-postgres`
- **Host (externo):** `localhost`
- **Puerto:** `5432`
- **Usuario:** `rhinometric`
- **Contraseña:** `secure_password_2024`
- **Bases de datos disponibles:**
  - `rhinometric` (principal)
  - `rhinometric_licenses` (licencias)
  - `postgres` (sistema)

### Redis
- **Host (interno):** `rhinometric-redis`
- **Host (externo):** `localhost`
- **Puerto:** `6379`
- **Contraseña:** `redis_secure_password`
- **Database:** `0` (por defecto)

### Prometheus
- **Host (interno):** `rhinometric-prometheus`
- **Host (externo):** `localhost`
- **Puerto:** `9090`
- **URL interna:** `http://rhinometric-prometheus:9090`
- **URL externa:** `http://localhost:9090`

---

## ��� Interfaz Web del API Connector

Puedes acceder a la interfaz web visual en:
- **URL:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Templates:** http://localhost:8000/api/templates

---

## ��� Prueba Rápida de Todos los Conectores

```bash
# PostgreSQL
curl -s -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"postgresql","host":"rhinometric-postgres","port":5432,"database":"rhinometric","username":"rhinometric","password":"secure_password_2024","ssl":false}' | jq '.success'

# Redis
curl -s -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"redis","host":"rhinometric-redis","port":6379,"database":"0","password":"redis_secure_password","ssl":false}' | jq '.success'

# Prometheus
curl -s -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"prometheus","url":"http://rhinometric-prometheus:9090","timeout":30}' | jq '.success'
```

**Resultado esperado para cada uno:** `true`

---

## ��� Notas Adicionales

1. **Networking Docker:** Desde el contenedor API Connector, usa nombres de servicio Docker (`rhinometric-postgres`, `rhinometric-redis`, etc.). Desde Windows, usa `localhost`.

2. **Servicios de Messaging:** RabbitMQ, Kafka y MQTT no están incluidos en el docker-compose actual. Si necesitas probarlos:
   - Agrega los servicios al docker-compose
   - O instala localmente
   - Los conectores están implementados y listos para usar

3. **Cloud Connectors:** AWS CloudWatch y Azure Monitor requieren credenciales válidas. Los conectores validarán que las credenciales sean correctas antes de devolver éxito.

4. **Seguridad:** Las contraseñas en este documento son las configuradas en el sistema de desarrollo. NO usar en producción.

---

**Fecha de creación:** 2025-11-06  
**Versión API Connector:** 2.4.0  
**Estado:** Todos los conectores disponibles han sido probados y reparados
