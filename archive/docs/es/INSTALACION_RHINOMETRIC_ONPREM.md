# 🚀 Rhinometric - Guía de Instalación On-Premise

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025  
**Tiempo estimado:** 1-2 horas  
**Audiencia:** Administradores de sistemas, DevOps Engineers

---

## ✅ Prerrequisitos

### **1. Sistema Operativo**

Sistemas operativos soportados:
- ✅ **Ubuntu 22.04 LTS** (recomendado)
- ✅ Ubuntu 20.04 LTS
- ✅ Debian 11 / 12
- ✅ Rocky Linux 8 / 9
- ✅ CentOS 8 Stream
- ⚠️ Windows 10/11 con WSL2 (solo para desarrollo/testing)
- ⚠️ macOS (solo para desarrollo/testing)

---

### **2. Hardware Mínimo**

| **Componente** | **Mínimo** | **Recomendado** |
|----------------|-----------|----------------|
| **CPU** | 4 vCPUs | 8 vCPUs |
| **RAM** | 8 GB | 16 GB |
| **Disco** | 100 GB SSD | 500 GB SSD |
| **Red** | 100 Mbps | 1 Gbps |

**Nota:** Estos requisitos son para monitorizar 10-50 hosts. Ver [Arquitectura Técnica](./ARQUITECTURA_TECNICA.md) para configuraciones mayores.

---

### **3. Software Requerido**

#### **Docker Engine >= 24.0**

**Ubuntu/Debian:**
```bash
# Desinstalar versiones antiguas
sudo apt-get remove docker docker-engine docker.io containerd runc

# Instalar dependencias
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Agregar clave GPG de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar instalación
docker --version  # Debe mostrar >= 24.0
```

**Rocky Linux / CentOS:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
docker --version
```

#### **Docker Compose >= 2.20**

**Verificar si ya está instalado:**
```bash
docker compose version
```

**Si no está instalado (standalone):**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

### **4. Puertos Disponibles**

Verificar que estos puertos NO estén ocupados:

```bash
# Verificar puertos
sudo netstat -tulpn | grep -E ':(3000|3002|3100|8085|8090|8105|9090|9093|9100|9121|9187|14317|14318|16686)\s'
```

Si algún puerto está ocupado, deberás:
- Detener el servicio que lo usa, O
- Modificar `docker-compose.yml` para cambiar el puerto externo

**Puertos necesarios:**
- **3000:** Grafana
- **3002:** Rhinometric Console Frontend
- **8105:** Rhinometric Console Backend (API)
- **9090:** Prometheus
- **3100:** Loki
- **16686:** Jaeger UI
- **9093:** Alertmanager
- **8085:** AI Anomaly Engine
- **Otros:** Exporters (9100, 9121, 9187, 8090, etc.)

---

### **5. Permisos de Usuario**

El usuario que ejecuta Docker debe tener permisos:

```bash
# Agregar usuario actual al grupo docker
sudo usermod -aG docker $USER

# Aplicar cambios (logout/login o ejecutar)
newgrp docker

# Verificar
docker ps  # No debe pedir sudo
```

---

## 📦 Descarga del Bundle de Instalación

### **Opción 1: Descarga directa (Recomendado)**

```bash
# Crear directorio de instalación
mkdir -p ~/rhinometric-install
cd ~/rhinometric-install

# Descargar bundle (URL ficticia - actualizar cuando esté disponible)
wget https://releases.rhinometric.com/v2.5.1/rhinometric-v2.5.1-bundle.tar.gz

# Verificar checksum
sha256sum rhinometric-v2.5.1-bundle.tar.gz
# Debe coincidir con: <HASH_A_PUBLICAR>

# Extraer
tar -xzf rhinometric-v2.5.1-bundle.tar.gz
cd rhinometric-v2.5.1/
```

### **Opción 2: Clonar desde repositorio Git**

```bash
git clone https://github.com/rhinometric/rhinometric-platform.git
cd rhinometric-platform/infrastructure/mi-proyecto/
```

---

## 🔧 Configuración Inicial

### **1. Variables de Entorno (Opcional)**

Crear archivo `.env` para personalizar configuración:

```bash
cat > .env <<EOF
# Rhinometric Configuration

# Console
CONSOLE_ADMIN_USER=admin
CONSOLE_ADMIN_PASSWORD=changeme123!

# Prometheus
PROMETHEUS_RETENTION=15d

# Loki
LOKI_RETENTION_PERIOD=720h

# PostgreSQL
POSTGRES_PASSWORD=rhinometric_db_pass

# Redis
REDIS_PASSWORD=rhinometric_redis_pass

# License (Coming Soon)
# LICENSE_KEY=RHINO-XXXX-XXXX-XXXX-XXXX
EOF
```

⚠️ **IMPORTANTE:** Cambiar contraseñas por defecto ANTES de poner en producción.

---

### **2. Ajustar Recursos (Opcional)**

Si tu hardware es limitado, editar `docker-compose.yml`:

```yaml
# Ejemplo: Reducir memoria de Prometheus
services:
  prometheus:
    deploy:
      resources:
        limits:
          memory: 1G  # Por defecto: 2G
```

---

## 🚀 Instalación

### **Paso 1: Levantar el Stack**

```bash
# Desde el directorio raíz de Rhinometric
docker compose up -d

# Verificar que todos los contenedores arranquen
docker compose ps
```

**Salida esperada:**
```
NAME                                                            STATUS
rhinometric-prometheus                                          Up 10 seconds (healthy)
rhinometric-grafana                                             Up 10 seconds (healthy)
rhinometric-console-backend                                     Up 10 seconds (healthy)
rhinometric-console-frontend                                    Up 10 seconds (healthy)
rhinometric-ai-anomaly                                          Up 10 seconds (healthy)
rhinometric-loki                                                Up 10 seconds (healthy)
rhinometric-jaeger                                              Up 10 seconds (healthy)
rhinometric-alertmanager                                        Up 10 seconds (healthy)
... (más servicios)
```

⏱️ **Tiempo de inicio:** 30-60 segundos hasta que todos los servicios estén `healthy`.

---

### **Paso 2: Verificar Logs**

Si algún servicio falla, revisar logs:

```bash
# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f prometheus
docker compose logs -f rhinometric-console-backend
```

**Errores comunes y soluciones:** Ver [Troubleshooting](#-troubleshooting).

---

### **Paso 3: Acceder a la Consola**

1. **Abrir navegador:** http://`<IP_DEL_HOST>`:3002

2. **Login inicial:**
   - Usuario: `admin`
   - Contraseña: `admin` (o la definida en `.env`)

3. **Cambiar contraseña:**
   - Sistema te pedirá cambiarla en el primer login
   - Usar contraseña fuerte (min 8 caracteres, mayúsculas, números, símbolos)

---

### **Paso 4: Verificar Componentes**

#### **4.1. Prometheus**

```bash
# Acceder a: http://<IP_DEL_HOST>:9090

# Verificar targets (Status → Targets)
# Deberías ver 11+ targets en estado "UP":
# - prometheus, grafana, loki, alertmanager
# - node-exporter, postgres-exporter, redis-exporter, cadvisor
# - console-backend, ai-anomaly, etc.
```

#### **4.2. Grafana**

```bash
# Acceder a: http://<IP_DEL_HOST>:3000

# Login inicial:
# Usuario: admin
# Contraseña: admin (cambiar obligatorio)

# Verificar dashboards:
# Home → Dashboards → Browse
# Deberías ver 8 dashboards:
# - 01-logs-explorer
# - 02-applications-apis
# - 03-github-webhooks
# - 04-rhinometric-overview
# - 05-docker-containers
# - 06-system-monitoring
# - 07-license-status
# - 08-stack-health
```

#### **4.3. Console - Home Page**

```bash
# http://<IP_DEL_HOST>:3002

# Verificar KPIs en tiempo real:
# - Service Status: "operational" (verde)
# - Monitored Services: 11+/11+ (o similar)
# - Active Anomalies: <número>
# - Alerts (24h): 0 (si todo está bien)

# Verificar gráficos históricos:
# - Deberían mostrar líneas con datos reales (no vacío)
# - Refrescar (F5) debe mostrar LOS MISMOS valores
```

#### **4.4. AI Anomaly Engine**

```bash
# Verificar endpoint:
curl http://localhost:8085/api/anomalies | jq

# Salida esperada (JSON):
{
  "anomalies": [
    {
      "metric_name": "node_cpu_usage",
      "current_value": 45.2,
      "baseline": 38.5,
      "deviation": 17.4,
      "severity": "low",
      "timestamp": "2025-12-05T10:30:00Z"
    },
    ...
  ],
  "total_anomalies": 9,
  "last_update": "2025-12-05T10:35:12Z"
}
```

---

## ✅ Checklist Post-Instalación

Ejecutar este checklist para confirmar que todo funciona:

```bash
# 1. Verificar que todos los contenedores están "healthy"
docker compose ps | grep -i unhealthy
# Salida esperada: (vacío)

# 2. Verificar que Prometheus tiene targets UP
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health == "up") | .labels.job'
# Salida esperada: lista de jobs (prometheus, grafana, loki, etc.)

# 3. Verificar que Console API responde
curl -s http://localhost:8105/api/health | jq
# Salida esperada: {"status": "healthy"}

# 4. Verificar que Loki recibe logs
curl -s 'http://localhost:3100/loki/api/v1/query?query={container_name=~"rhinometric.*"}' | jq '.data.result | length'
# Salida esperada: >0

# 5. Verificar dashboards de Grafana
curl -s -u admin:admin http://localhost:3000/api/search?type=dash-db | jq '. | length'
# Salida esperada: 8

# 6. Verificar AI Anomaly Engine
curl -s http://localhost:8085/api/anomalies | jq '.total_anomalies'
# Salida esperada: número (puede ser 0 si no hay anomalías)
```

✅ **Si todos los checks pasan, la instalación es EXITOSA.**

---

## 🔒 Hardening de Seguridad (Recomendado para Producción)

### **1. Cambiar Contraseñas por Defecto**

```bash
# Console Admin Password
# - Cambiar vía UI en primer login

# Grafana Admin Password
# - Cambiar vía UI en primer login

# PostgreSQL Password
# - Editar .env → POSTGRES_PASSWORD
# - docker compose down && docker compose up -d

# Redis Password
# - Editar .env → REDIS_PASSWORD
# - Editar config/redis.conf → requirepass <nueva_password>
# - docker compose restart redis
```

---

### **2. Configurar Firewall**

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 3002/tcp     # Console
sudo ufw allow 3000/tcp     # Grafana (opcional, si se usa)
sudo ufw deny 9090/tcp      # Prometheus (solo acceso interno)
sudo ufw deny 3100/tcp      # Loki (solo acceso interno)
sudo ufw enable

# Rocky Linux / CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=3002/tcp  # Console
sudo firewall-cmd --permanent --add-port=3000/tcp  # Grafana
sudo firewall-cmd --reload
```

---

### **3. Habilitar HTTPS (Opcional pero recomendado)**

**Opción A: Reverse Proxy con Nginx**

```bash
# Instalar Nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Crear configuración
sudo nano /etc/nginx/sites-available/rhinometric

# Contenido:
server {
    listen 80;
    server_name rhinometric.tudominio.com;

    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/rhinometric /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtener certificado SSL
sudo certbot --nginx -d rhinometric.tudominio.com
```

**Opción B: Cloudflare Tunnel (Acceso remoto seguro)**

Ver documentación de Cloudflare Tunnel (archivo ya existe en proyecto).

---

## 🔄 Actualización a Versiones Nuevas

```bash
# 1. Backup de datos
cd ~/rhinometric-install/rhinometric-v2.5.1/
docker compose down
sudo tar -czf ~/rhinometric-backup-$(date +%Y%m%d).tar.gz data/

# 2. Descargar nueva versión
cd ~/rhinometric-install/
wget https://releases.rhinometric.com/v2.6.0/rhinometric-v2.6.0-bundle.tar.gz
tar -xzf rhinometric-v2.6.0-bundle.tar.gz
cd rhinometric-v2.6.0/

# 3. Copiar datos antiguos
cp -r ~/rhinometric-install/rhinometric-v2.5.1/data/ ./data/

# 4. Levantar nueva versión
docker compose pull
docker compose up -d

# 5. Verificar
docker compose logs -f
# Acceder a Console y verificar que funciona
```

---

## 🧹 Desinstalación Completa

```bash
# 1. Detener todos los contenedores
docker compose down

# 2. Eliminar volúmenes (CUIDADO: esto borra TODOS los datos)
docker compose down -v

# 3. Eliminar imágenes
docker images | grep rhinometric | awk '{print $3}' | xargs docker rmi

# 4. Eliminar directorio de instalación
cd ~
rm -rf rhinometric-install/
```

---

## ⚠️ Troubleshooting

### **Problema 1: Puerto ocupado**

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:3002: bind: address already in use
```

**Solución:**
```bash
# Identificar proceso que usa el puerto
sudo lsof -i :3002
# O
sudo netstat -tulpn | grep :3002

# Matar proceso (si no es crítico)
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
# Editar:
#   - "3002:3002"  → "3005:3002" (ejemplo)
```

---

### **Problema 2: Contenedor no arranca (unhealthy)**

**Diagnóstico:**
```bash
# Ver logs del servicio problemático
docker compose logs -f <nombre_servicio>

# Ejemplos:
docker compose logs -f prometheus
docker compose logs -f rhinometric-console-backend
```

**Errores comunes:**

- **"Permission denied" en volúmenes:**
  ```bash
  sudo chown -R 65534:65534 data/prometheus/
  sudo chown -R 472:472 data/grafana/
  ```

- **"Out of memory":**
  ```bash
  # Verificar recursos disponibles
  free -h
  docker stats
  
  # Reducir límites de memoria en docker-compose.yml
  ```

---

### **Problema 3: Console muestra "Failed to fetch KPIs"**

**Causa:** Backend no puede conectar con Prometheus/AI/Alertmanager.

**Solución:**
```bash
# 1. Verificar que Prometheus está UP
curl http://localhost:9090/-/healthy
# Debe retornar: Prometheus is Healthy.

# 2. Verificar red Docker
docker network ls | grep rhinometric
docker network inspect rhinometric_network_v22

# 3. Reiniciar backend
docker compose restart rhinometric-console-backend

# 4. Ver logs
docker compose logs -f rhinometric-console-backend
# Debe mostrar: "[KPI] Fetching KPIs..."
```

---

### **Problema 4: Gráficos históricos vacíos**

**Causa:** Prometheus no tiene suficientes datos históricos (recién instalado).

**Solución:**
```bash
# Esperar 1-2 horas para que se acumulen datos

# Verificar que Prometheus tiene métricas:
curl 'http://localhost:9090/api/v1/query?query=up'

# Si retorna datos → esperar más tiempo
# Si retorna vacío → problema con scraping (ver logs de Prometheus)
```

---

### **Problema 5: AI Anomaly Engine no detecta anomalías**

**Causa:** Falta de datos históricos o métricas demasiado estables.

**Solución:**
```bash
# 1. Verificar logs del AI Engine
docker compose logs -f rhinometric-ai-anomaly

# Debe mostrar:
# "Isolation Forest trained with X samples"
# "BASELINE_DEBUG node_cpu_usage: mean=X, std=Y, samples=Z"

# 2. Si samples=0 → Prometheus no tiene datos
# Esperar 1 hora y verificar

# 3. Si no hay anomalías detectadas → sistema está estable
# Generar carga artificial para probar:
stress-ng --cpu 4 --timeout 60s
```

---

## 📚 Próximos Pasos

1. **Configurar monitorización de tus servicios:**
   - Agregar targets en `config/prometheus-v2.2.yml`
   - Reiniciar Prometheus: `docker compose restart prometheus`

2. **Leer guía de uso:**
   - [Guía de Uso de la Console](./GUÍA_USO_CONSOLE_RHINOMETRIC.md)

3. **Personalizar dashboards:**
   - Acceder a Grafana y editar dashboards según necesidades

4. **Configurar alertas a Slack/Email:**
   - (Próxima versión - por ahora manual vía Alertmanager config)

---

## 📞 Soporte

- **Documentación:** https://docs.rhinometric.com (actualizar)
- **FAQ:** [FAQ_RHINOMETRIC.md](./FAQ_RHINOMETRIC.md)
- **Email Soporte:** soporte@rhinometric.com (actualizar)
- **Comunidad:** (Discord/Slack - por definir)

---

**¡Felicidades! Rhinometric está instalado y funcionando** 🎉

---

**© 2025 Rhinometric - Instalación simplificada en <2 horas**
