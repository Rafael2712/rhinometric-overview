# Ì¥å RHINOMETRIC API CONNECTOR - GU√çA DE PRUEBAS

## Ì≥ç URL Base
**http://localhost:8000**

---

## ‚úÖ **1. POSTGRESQL** (INTERNO - YA DISPONIBLE)

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "postgresql",
  "host": "rhinometric-postgres",
  "port": 5432,
  "database": "rhinometric_licenses",
  "username": "rhinometric",
  "password": "rhinometric",
  "ssl": false
}
```

### Prueba desde localhost (fuera de Docker):
```json
{
  "datasource_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "rhinometric_licenses",
  "username": "rhinometric",
  "password": "rhinometric",
  "ssl": false
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "rhinometric_licenses",
    "username": "rhinometric",
    "password": "rhinometric",
    "ssl": false
  }'
```

**Resultado Esperado:** ‚úÖ Connection successful

---

## ‚úÖ **2. REDIS** (INTERNO - YA DISPONIBLE)

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "redis",
  "host": "rhinometric-redis",
  "port": 6379,
  "database": 0,
  "password": "rhinometric",
  "ssl": false
}
```

### Prueba desde localhost:
```json
{
  "datasource_type": "redis",
  "host": "localhost",
  "port": 6379,
  "database": 0,
  "password": "rhinometric",
  "ssl": false
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "redis",
    "host": "localhost",
    "port": 6379,
    "database": 0,
    "password": "rhinometric",
    "ssl": false
  }'
```

**Resultado Esperado:** ‚úÖ Connection successful

---

## ‚úÖ **3. PROMETHEUS** (INTERNO - YA DISPONIBLE)

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "prometheus",
  "url": "http://localhost:9090",
  "timeout": 30
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "prometheus",
    "url": "http://localhost:9090",
    "timeout": 30
  }'
```

**Resultado Esperado:** ‚úÖ Connection successful

---

## Ìºê **4. AWS CLOUDWATCH** (EXTERNO - REQUIERE CREDENCIALES)

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "aws-cloudwatch",
  "region": "us-east-1",
  "access_key": "YOUR_AWS_ACCESS_KEY",
  "secret_key": "YOUR_AWS_SECRET_KEY"
}
```

### Opciones de Regiones:
- `us-east-1` (Norte de Virginia)
- `eu-west-1` (Irlanda)
- `eu-central-1` (Frankfurt)

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "aws-cloudwatch",
    "region": "us-east-1",
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }'
```

**Nota:** Requiere credenciales AWS reales para prueba exitosa.

---

## Ìºê **5. AZURE MONITOR** (EXTERNO - REQUIERE CREDENCIALES)

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "azure-monitor",
  "subscription_id": "YOUR_SUBSCRIPTION_ID",
  "tenant_id": "YOUR_TENANT_ID",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "azure-monitor",
    "subscription_id": "12345678-1234-1234-1234-123456789012",
    "tenant_id": "87654321-4321-4321-4321-210987654321",
    "client_id": "abcdef12-3456-7890-abcd-ef1234567890",
    "client_secret": "your-client-secret-here"
  }'
```

**Nota:** Requiere Service Principal de Azure con permisos de Monitor.

---

## Ì≥® **6. RABBITMQ** (LOCAL - REQUIERE INSTALACI√ìN)

### Instalaci√≥n Docker (Opcional):
```bash
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "rabbitmq",
  "host": "localhost",
  "port": 15672,
  "username": "guest",
  "password": "guest",
  "vhost": "/",
  "use_ssl": false
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "rabbitmq",
    "host": "localhost",
    "port": 15672,
    "username": "guest",
    "password": "guest",
    "vhost": "/",
    "use_ssl": false
  }'
```

**Acceso Web:** http://localhost:15672 (guest/guest)

---

## Ì≥ä **7. APACHE KAFKA** (LOCAL - REQUIERE INSTALACI√ìN)

### Instalaci√≥n Docker (Opcional):
```bash
docker run -d --name kafka \
  -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  bitnami/kafka:latest
```

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "kafka",
  "bootstrap_servers": "localhost:9092",
  "security_protocol": "PLAINTEXT",
  "sasl_mechanism": "PLAIN",
  "sasl_username": "",
  "sasl_password": "",
  "ssl_check_hostname": true
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "kafka",
    "bootstrap_servers": "localhost:9092",
    "security_protocol": "PLAINTEXT"
  }'
```

---

## Ìºê **8. MQTT BROKER** (LOCAL - REQUIERE INSTALACI√ìN)

### Instalaci√≥n Docker (Mosquitto):
```bash
docker run -d --name mosquitto \
  -p 1883:1883 \
  -p 9001:9001 \
  eclipse-mosquitto
```

### Datos de Conexi√≥n:
```json
{
  "datasource_type": "mqtt",
  "host": "localhost",
  "port": 1883,
  "username": "",
  "password": "",
  "client_id": "rhinometric-connector",
  "use_tls": false,
  "keepalive": 60,
  "clean_session": true,
  "test_topic": "rhinometric/test"
}
```

### Comando cURL:
```bash
curl -X POST http://localhost:8000/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_type": "mqtt",
    "host": "localhost",
    "port": 1883,
    "client_id": "rhinometric-test",
    "use_tls": false
  }'
```

---

## Ì∑™ PRUEBAS RECOMENDADAS

### Prueba 1: Servicios Internos (Disponibles ahora)
```bash
# PostgreSQL
curl -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"postgresql","host":"localhost","port":5432,"database":"rhinometric_licenses","username":"rhinometric","password":"rhinometric","ssl":false}'

# Redis
curl -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"redis","host":"localhost","port":6379,"database":0,"password":"rhinometric","ssl":false}'

# Prometheus
curl -X POST http://localhost:8000/api/test-connection -H "Content-Type: application/json" -d '{"datasource_type":"prometheus","url":"http://localhost:9090","timeout":30}'
```

### Prueba 2: Servicios Cloud (Requieren credenciales)
- AWS CloudWatch: Obtener credenciales desde AWS Console > IAM
- Azure Monitor: Crear Service Principal en Azure Portal

### Prueba 3: Mensajer√≠a Local (Opcional - Instalar primero)
- RabbitMQ: `docker run -d -p 15672:15672 rabbitmq:3-management`
- Kafka: Usar bitnami/kafka
- MQTT: Usar eclipse-mosquitto

---

## Ì≥ä RESUMEN

| Servicio | Estado | Puerto | Usuario | Password |
|----------|--------|--------|---------|----------|
| PostgreSQL | ‚úÖ Disponible | 5432 | rhinometric | rhinometric |
| Redis | ‚úÖ Disponible | 6379 | - | rhinometric |
| Prometheus | ‚úÖ Disponible | 9090 | - | - |
| AWS CloudWatch | ‚ö†Ô∏è Requiere Creds | - | access_key | secret_key |
| Azure Monitor | ‚ö†Ô∏è Requiere Creds | - | client_id | client_secret |
| RabbitMQ | ‚è∏Ô∏è No instalado | 15672 | guest | guest |
| Kafka | ‚è∏Ô∏è No instalado | 9092 | - | - |
| MQTT | ‚è∏Ô∏è No instalado | 1883 | - | - |

