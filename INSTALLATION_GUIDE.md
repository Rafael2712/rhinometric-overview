# Rhinometric v2.5.0 - Guía de Instalación On-Premise

**Enterprise Observability Platform**  
Fecha: 2025-12-30  
Estado: Producción MVP

---

## 📋 Índice

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación Rápida](#instalación-rápida)
3. [Instalación Manual](#instalación-manual)
4. [Post-Instalación](#post-instalación)
5. [Verificación](#verificación)
6. [Troubleshooting](#troubleshooting)
7. [Mantenimiento](#mantenimiento)

---

## ⚙️ Requisitos del Sistema

### Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 4 cores | 8 cores |
| **RAM** | 8 GB | 16 GB |
| **Disco** | 150 GB SSD | 250 GB SSD |
| **Red** | 100 Mbps | 1 Gbps |

### Software Requerido

- **Sistema Operativo**: Ubuntu 22.04 LTS (recomendado) o compatible
- **Docker Engine**: 24.0.0 o superior
- **Docker Compose**: v2 (incluido en Docker Engine 20.10+)
- **Permisos**: Usuario con sudo o acceso root

### Puertos Requeridos

Los siguientes puertos deben estar disponibles:

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 3000 | Grafana | Dashboards y visualización |
| 3002 | Console Frontend | Interfaz principal |
| 5000 | License Server | Validador de licencias |
| 5432 | PostgreSQL | Base de datos |
| 6379 | Redis | Cache |
| 8085 | AI Anomaly | Detector de anomalías |
| 8105 | Console Backend | API Gateway |
| 9090 | Prometheus | Métricas |
| 9093 | Alertmanager | Gestión de alertas |
| 3100 | Loki | Agregación de logs |
| 16686 | Jaeger | Distributed tracing |

---

## 🚀 Instalación Rápida

### Opción 1: Script Automatizado (Recomendado)

```bash
# 1. Descargar paquete de instalación
wget https://releases.rhinometric.com/v2.5.0/rhinometric-v2.5.0.tar.gz
tar -xzf rhinometric-v2.5.0.tar.gz
cd rhinometric-v2.5.0

# 2. Ejecutar instalador
sudo bash install-rhinometric.sh

# 3. Seguir las instrucciones en pantalla
```

El instalador:
- ✅ Verifica requisitos del sistema
- ✅ Valida puertos disponibles
- ✅ Genera credenciales seguras automáticamente
- ✅ Configura y levanta el stack completo
- ✅ Realiza verificación post-instalación

**Tiempo estimado: 5-10 minutos**

---

## 🔧 Instalación Manual

### Paso 1: Preparar el Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker (si no está instalado)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Logout/login para aplicar cambios de grupo
```

### Paso 2: Descargar Rhinometric

```bash
# Crear directorio de instalación
sudo mkdir -p /opt/rhinometric
cd /opt/rhinometric

# Descargar y extraer
wget https://releases.rhinometric.com/v2.5.0/rhinometric-v2.5.0.tar.gz
tar -xzf rhinometric-v2.5.0.tar.gz
cd rhinometric-v2.5.0
```

### Paso 3: Configurar Credenciales

```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar credenciales
nano .env
```

Configurar las siguientes variables:

```bash
# Database
POSTGRES_PASSWORD=<password-seguro-generado>

# Cache
REDIS_PASSWORD=<password-seguro-generado>

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=<password-seguro-generado>

# License Validator
ADMIN_PASSWORD=<password-seguro-generado>
```

**💡 Tip**: Genera passwords seguros con:
```bash
openssl rand -base64 24 | tr -d "=+/" | cut -c1-20
```

### Paso 4: Iniciar Servicios

```bash
# Descargar imágenes Docker
docker compose pull

# Iniciar stack
docker compose up -d

# Verificar estado (esperar ~60 segundos)
docker compose ps
```

---

## ✅ Post-Instalación

### Acceso Inicial

Después de la instalación, accede a:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Console** | `http://<SERVER-IP>:3002` | Ver `/opt/rhinometric/CREDENCIALES.txt` |
| **Grafana** | `http://<SERVER-IP>:3000` | admin / (ver archivo credenciales) |
| **Prometheus** | `http://<SERVER-IP>:9090` | Sin autenticación |

### Dashboards Incluidos

Rhinometric incluye 7 dashboards pre-configurados:

1. **05 - Docker Containers**: Métricas de contenedores (CPU, RAM, red, disco)
2. **06 - System Monitoring**: Monitoreo del sistema host
3. **07 - License Status**: Estado de licencias activas
4. **08 - Stack Health**: Salud del stack de observabilidad
5. **10 - Platform Health & SLA**: SLA y disponibilidad
6. **11 - Infrastructure Performance**: Performance de infraestructura
7. **12 - Business Capacity**: Capacidad y planificación

### Configuración de Licencia

```bash
# Subir archivo de licencia
curl -X POST http://<SERVER-IP>:5000/api/admin/upload-license \
  -H "Authorization: Bearer <ADMIN_PASSWORD>" \
  -F "file=@/path/to/cliente.lic"
```

---

## 🔍 Verificación

### Verificar Contenedores

```bash
cd /opt/rhinometric
docker compose ps
```

**Salida esperada**: 17 contenedores en estado `healthy`

### Verificar Servicios

```bash
# Prometheus activo
curl -s http://localhost:9090/-/healthy
# Salida: Prometheus Server is Healthy.

# Grafana activo
curl -s http://localhost:3000/api/health | jq .
# Salida: {"database": "ok", ...}

# Console backend activo
curl -s http://localhost:8105/health | jq .
# Salida: {"status": "healthy", ...}
```

### Verificar Métricas

```bash
# Número de métricas en Prometheus
curl -s "http://localhost:9090/api/v1/label/__name__/values" | jq '.data | length'
# Salida esperada: >1000 métricas
```

### Verificar Logs

```bash
# Ver logs de un servicio específico
docker compose logs -f grafana

# Ver últimas 100 líneas de todos los servicios
docker compose logs --tail 100
```

---

## 🔧 Troubleshooting

### Problema: Contenedores no inician

**Causa común**: Puertos en uso

```bash
# Verificar puertos ocupados
sudo ss -tuln | grep -E ':(3000|5432|6379|9090)'

# Detener servicios conflictivos o cambiar puertos en docker-compose.yml
```

### Problema: Memoria insuficiente

**Síntoma**: Contenedores se reinician constantemente (OOMKilled)

```bash
# Verificar memoria disponible
free -h

# Ver consumo de memoria de contenedores
docker stats --no-stream

# Solución: Aumentar RAM o ajustar límites en docker-compose.yml
```

### Problema: Dashboard muestra "No data"

**Causa común**: Prometheus no está scrapeando métricas

```bash
# Verificar targets en Prometheus
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Si hay targets DOWN, verificar logs:
docker compose logs prometheus
```

### Problema: No puedo acceder desde navegador

**Causa común**: Firewall bloqueando puertos

```bash
# Ubuntu/Debian: Permitir puertos necesarios
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 3002/tcp  # Console
sudo ufw allow 9090/tcp  # Prometheus

# Verificar reglas activas
sudo ufw status
```

### Problema: Credenciales no funcionan

```bash
# Ver credenciales guardadas
sudo cat /opt/rhinometric/CREDENCIALES.txt

# Resetear password de Grafana:
docker compose exec grafana grafana-cli admin reset-admin-password <nueva-password>

# Verificar variables de entorno:
docker compose config | grep -E '(POSTGRES_PASSWORD|GRAFANA_PASSWORD)'
```

---

## 🛠️ Mantenimiento

### Comandos Básicos

```bash
# Ir al directorio de instalación
cd /opt/rhinometric

# Ver estado de servicios
docker compose ps

# Reiniciar un servicio específico
docker compose restart grafana

# Reiniciar todo el stack
docker compose restart

# Ver logs en tiempo real
docker compose logs -f

# Detener stack
docker compose down

# Iniciar stack
docker compose up -d
```

### Backup

```bash
# Backup de base de datos
docker compose exec -T postgres pg_dump -U rhinometric rhinometric_licenses > backup_$(date +%Y%m%d).sql

# Backup de configuración Grafana
docker compose cp grafana:/var/lib/grafana ./backup/grafana-$(date +%Y%m%d)

# Backup de datos Prometheus (últimos 7 días)
docker compose stop prometheus
tar -czf prometheus-backup-$(date +%Y%m%d).tar.gz ./data/prometheus
docker compose start prometheus
```

### Actualización

```bash
cd /opt/rhinometric

# Detener servicios
docker compose down

# Backup antes de actualizar
tar -czf rhinometric-backup-$(date +%Y%m%d).tar.gz .

# Descargar nueva versión
wget https://releases.rhinometric.com/v2.5.1/rhinometric-v2.5.1.tar.gz
tar -xzf rhinometric-v2.5.1.tar.gz

# Copiar configuración existente
cp ./rhinometric-v2.5.0/.env ./rhinometric-v2.5.1/

# Actualizar
cd rhinometric-v2.5.1
docker compose pull
docker compose up -d
```

### Logs y Rotación

```bash
# Ver tamaño de logs
docker compose logs | wc -l

# Limpiar logs antiguos
docker compose logs --since 24h > logs_recientes.txt
docker system prune -f

# Configurar rotación automática (editar /etc/docker/daemon.json)
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Monitoreo de Recursos

```bash
# Ver consumo en tiempo real
docker stats

# Ver uso de disco de volúmenes
docker system df -v

# Limpiar recursos no utilizados
docker system prune -a --volumes
```

---

## 📞 Soporte

### Documentación Adicional

- 📖 **Manual de Usuario**: `/opt/rhinometric/docs/USER_GUIDE.md`
- 🔍 **API Reference**: `http://<SERVER-IP>:8105/docs`
- 📊 **Dashboard Guide**: Ver dashboards pre-configurados en Grafana

### Contacto

- **Email**: soporte@rhinometric.com
- **Web**: https://rhinometric.com/support
- **Tickets**: https://support.rhinometric.com

### Logs para Soporte

Si necesitas ayuda, envía:

```bash
# Recopilar información del sistema
cd /opt/rhinometric
./collect-diagnostics.sh

# Genera: rhinometric-diagnostics-YYYYMMDD.tar.gz
# Enviar a soporte
```

---

## 📄 Licencia y Garantías

Este software requiere licencia comercial válida.  
Para información de licenciamiento, contacta: sales@rhinometric.com

**Versión**: 2.5.0  
**Fecha de Release**: 2025-12-30  
**Soporte**: 12 meses desde la fecha de compra
