# 🐧 MANUAL DE INSTALACIÓN - Linux

**Rhinometric v2.1.0 Trial**  
**Tiempo estimado**: 10-15 minutos  
**Nivel**: Principiante

---

## 📋 REQUISITOS PREVIOS

### **Hardware Mínimo**
- ✅ CPU: 2 cores (4 recomendado)
- ✅ RAM: 4 GB disponible (8 GB recomendado)
- ✅ Disco: 20 GB libres
- ✅ Red: Internet estable

### **Distribuciones Soportadas**

| Distro | Versión | Estado |
|--------|---------|--------|
| Ubuntu | 20.04 LTS+ | ✅ Recomendado |
| Debian | 11+ | ✅ Probado |
| CentOS | 8+ | ✅ Probado |
| Fedora | 36+ | ✅ Compatible |
| RHEL | 8+ | ✅ Compatible |
| Arch | Rolling | ⚠️ Experimental |

---

## 🔧 INSTALACIÓN RÁPIDA (Ubuntu/Debian)

### **Un Comando** (Recomendado)

```bash
curl -fsSL https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/install-rhinometric.sh | sudo bash
```

Este script hace TODO automáticamente:
- ✅ Instala Docker + Docker Compose
- ✅ Configura usuario en grupo `docker`
- ✅ Descarga Rhinometric v2.1.0
- ✅ Configura credenciales seguras
- ✅ Levanta los 17 contenedores
- ✅ Verifica funcionamiento

**Tiempo**: 10-15 minutos

---

## 🔧 INSTALACIÓN MANUAL

### **PASO 1: Instalar Docker**

#### **1.1 Ubuntu/Debian**

```bash
# Actualizar paquetes
sudo apt update
sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### **1.2 CentOS/RHEL/Fedora**

```bash
# Instalar dependencias
sudo yum install -y yum-utils

# Agregar repositorio Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### **1.3 Agregar usuario al grupo docker** (Evita usar sudo)

```bash
sudo usermod -aG docker $USER

# Aplicar cambios (sin logout)
newgrp docker

# O hacer logout/login
```

#### **1.4 Verificar instalación**

```bash
docker --version
# Docker version 24.0.0 o superior

docker compose version
# Docker Compose version v2.23.0 o superior

docker ps
# Tabla vacía (sin contenedores aún)
```

---

### **PASO 2: Descargar Rhinometric**

```bash
# Crear directorio
cd ~
mkdir -p rhinometric
cd rhinometric

# Descargar release
wget https://github.com/Rafael2712/mi-proyecto/releases/download/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz

# O con curl
# curl -LO https://github.com/Rafael2712/mi-proyecto/releases/download/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz

# Descomprimir
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
cd rhinometric-trial-v2.1.0-universal
ls -la
```

---

### **PASO 3: Configurar**

```bash
# Copiar ejemplo
cp .env.example .env

# Editar con nano (o vim, emacs)
nano .env
```

**Configurar**:

```env
# Credenciales Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=TuPasswordSeguro123!    # ← CAMBIAR

# Credenciales PostgreSQL
POSTGRES_USER=rhinometric
POSTGRES_PASSWORD=TuPasswordSeguro456!   # ← CAMBIAR
POSTGRES_DB=rhinometric

# Credenciales Redis
REDIS_PASSWORD=TuPasswordSeguro789!      # ← CAMBIAR

# Rutas Linux
HOME=/home/tuusuario                     # ← CAMBIAR
DATA_PATH=/var/lib/rhinometric           # Opcional

# Modo trial
RHINOMETRIC_MODE=trial
RHINOMETRIC_VERSION=2.1.0

# Networking
HOST_IP=0.0.0.0                          # Escucha en todas las interfaces
```

**Guardar**: `Ctrl + O` → Enter → `Ctrl + X`

---

### **PASO 4: Configurar Firewall** (Si aplica)

#### **UFW (Ubuntu/Debian)**

```bash
# Permitir puertos Rhinometric
sudo ufw allow 3000/tcp comment 'Grafana'
sudo ufw allow 9090/tcp comment 'Prometheus'
sudo ufw allow 8091/tcp comment 'API Connector'

# O permitir rangos
sudo ufw allow 3000:9200/tcp

# Ver reglas
sudo ufw status
```

#### **Firewalld (CentOS/RHEL/Fedora)**

```bash
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --permanent --add-port=8091/tcp
sudo firewall-cmd --reload
```

---

### **PASO 5: Levantar Rhinometric**

```bash
# Pull de imágenes (primera vez, 5-10 min)
docker compose -f docker-compose-v2.1.0.yml pull

# Iniciar todos los contenedores
docker compose -f docker-compose-v2.1.0.yml up -d

# Ver estado
docker ps | grep rhinometric
# Debe mostrar 17 contenedores "Up" o "Up (healthy)"

# Ver logs en tiempo real
docker compose -f docker-compose-v2.1.0.yml logs -f
```

---

### **PASO 6: Verificar**

```bash
# Verificación rápida
./validate-v2.1.sh

# O manual
curl -s http://localhost:3000/api/health | jq .
# Debe mostrar: {"database": "ok", "version": "..."}

# Verificar Prometheus
curl -s http://localhost:9090/-/healthy
# Prometheus is Healthy.

# Verificar Loki
curl -s http://localhost:3100/ready
# ready
```

**Acceder desde navegador**:
- **Grafana**: http://SERVER_IP:3000 (admin / tu_password)
- **API Connector**: http://SERVER_IP:8091
- **Prometheus**: http://SERVER_IP:9090

---

## 🐧 COMANDOS ÚTILES (Linux)

### **Systemd Service** (Autostart en boot)

```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/rhinometric.service
```

**Contenido**:

```ini
[Unit]
Description=Rhinometric Monitoring Stack v2.1.0
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/tuusuario/rhinometric/rhinometric-trial-v2.1.0-universal
ExecStart=/usr/bin/docker compose -f docker-compose-v2.1.0.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose-v2.1.0.yml down

[Install]
WantedBy=multi-user.target
```

**Habilitar**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable rhinometric.service
sudo systemctl start rhinometric.service

# Ver estado
sudo systemctl status rhinometric.service
```

---

### **Ver logs**

```bash
# Logs de Grafana
docker logs rhinometric-grafana --tail 100 -f

# Logs de todos los servicios
docker compose -f docker-compose-v2.1.0.yml logs -f

# Logs con timestamp
docker compose -f docker-compose-v2.1.0.yml logs -f --timestamps
```

---

### **Reiniciar servicios**

```bash
# Reiniciar todo
docker compose -f docker-compose-v2.1.0.yml restart

# Reiniciar solo Grafana
docker restart rhinometric-grafana

# Recrear contenedor (si hubo cambios)
docker compose -f docker-compose-v2.1.0.yml up -d --force-recreate grafana
```

---

### **Detener/Iniciar**

```bash
# Detener (datos se conservan)
docker compose -f docker-compose-v2.1.0.yml stop

# Iniciar después de detener
docker compose -f docker-compose-v2.1.0.yml start

# Detener y ELIMINAR todo (CUIDADO)
docker compose -f docker-compose-v2.1.0.yml down -v
```

---

### **Ver uso de recursos**

```bash
# CPU, RAM, Net por contenedor
docker stats --no-stream | grep rhinometric

# Uso de disco
docker system df

# Limpieza de recursos
docker system prune -a --volumes
```

---

## 🐛 TROUBLESHOOTING Linux

### **❌ "Cannot connect to Docker daemon"**

```bash
# Verificar estado Docker
sudo systemctl status docker

# Si está parado, iniciar
sudo systemctl start docker

# Verificar permisos
groups $USER | grep docker
# Si no aparece "docker", ejecuta:
sudo usermod -aG docker $USER
newgrp docker
```

---

### **❌ "Port already in use"**

```bash
# Ver qué proceso usa el puerto 3000
sudo lsof -i :3000
# O: sudo netstat -tulpn | grep 3000

# Matar proceso (reemplaza PID)
sudo kill -9 PID
```

---

### **❌ "Permission denied" en volúmenes**

```bash
# Cambiar ownership
sudo chown -R $USER:$USER data/

# O dar permisos amplios (menos seguro)
sudo chmod -R 777 data/
```

---

### **❌ "Out of disk space"**

```bash
# Ver uso de disco Docker
docker system df

# Limpiar imágenes no usadas
docker image prune -a

# Limpiar volúmenes huérfanos
docker volume prune

# Limpiar TODO (CUIDADO)
docker system prune -a --volumes
```

---

### **❌ "Network unreachable" al pull**

```bash
# Verificar DNS
cat /etc/resolv.conf

# Cambiar a DNS público (temporal)
sudo nano /etc/resolv.conf
# Agregar: nameserver 8.8.8.8

# O configurar en Docker daemon
sudo nano /etc/docker/daemon.json
```

```json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

```bash
sudo systemctl restart docker
```

---

### **❌ SELinux bloquea contenedores** (CentOS/RHEL/Fedora)

```bash
# Verificar si SELinux está activo
getenforce

# Opción A: Desactivar (menos seguro)
sudo setenforce 0

# Opción B: Agregar regla (recomendado)
sudo setsebool -P container_manage_cgroup on
sudo chcon -Rt svirt_sandbox_file_t /path/to/rhinometric/
```

---

## 🔄 AUTO-UPDATE

```bash
# Verificar actualizaciones
./auto-update.sh --check-only

# Actualizar (con backup automático)
./auto-update.sh

# Actualizar a versión específica
./auto-update.sh --version=2.2.0

# Rollback si algo falla
./auto-update.sh --rollback
```

---

## 📊 VERIFICACIÓN POST-INSTALACIÓN

```bash
#!/bin/bash
echo "=== VERIFICACION RHINOMETRIC Linux ==="
echo "Containers: $(docker ps | grep rhinometric | wc -l)/17"
echo "Grafana: $(curl -s http://localhost:3000/api/health | jq -r .database)"
echo "Prometheus: $(curl -s http://localhost:9090/-/healthy)"
echo "Loki: $(curl -s http://localhost:3100/ready)"
echo "API Proxy: $(curl -s http://localhost:8090/health)"
echo "✅ Verificación completa"
```

---

## 🚀 OPTIMIZACIONES LINUX

### **1. Limitar recursos Docker**

```bash
# Editar daemon.json
sudo nano /etc/docker/daemon.json
```

```json
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

---

### **2. Monitorear con systemd**

```bash
# Ver logs systemd
journalctl -u rhinometric.service -f

# Ver últimas 100 líneas
journalctl -u rhinometric.service -n 100
```

---

### **3. Backups automáticos con cron**

```bash
# Editar crontab
crontab -e
```

**Agregar**:

```cron
# Backup diario a las 2 AM
0 2 * * * cd /home/tuusuario/rhinometric/rhinometric-trial-v2.1.0-universal && ./backup.sh
```

---

## 🌐 ACCESO REMOTO SEGURO

### **Reverse Proxy con Nginx**

```bash
# Instalar Nginx
sudo apt install nginx -y

# Crear configuración
sudo nano /etc/nginx/sites-available/rhinometric
```

**Contenido**:

```nginx
server {
    listen 80;
    server_name monitoring.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/rhinometric /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### **HTTPS con Let's Encrypt**

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado
sudo certbot --nginx -d monitoring.example.com

# Renovación automática (ya incluida en cron)
sudo certbot renew --dry-run
```

---

## 📚 PRÓXIMOS PASOS

1. Lee: `docs/MANUAL_USUARIO_v2.1.0.md`
2. Explora dashboards: http://SERVER_IP:3000
3. Configura reverse proxy + HTTPS
4. Configura alertas (Slack, email, PagerDuty)
5. Revisa logs: `docker compose logs -f`

---

## 🆘 SOPORTE

- 📖 Docs: `docs/` directory
- 🐙 GitHub: https://github.com/Rafael2712/mi-proyecto/issues
- 📧 Email: info@rhinometric.com
- 💬 Discord: https://discord.gg/rhinometric

---

## 📦 DISTRIBUCIONES ESPECÍFICAS

### **Arch Linux**

```bash
sudo pacman -S docker docker-compose
sudo systemctl start docker.service
sudo systemctl enable docker.service
```

### **openSUSE**

```bash
sudo zypper install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### **Alpine Linux**

```bash
apk add docker docker-compose
rc-update add docker boot
service docker start
```

---

**✅ INSTALACIÓN COMPLETADA EN LINUX** 🐧🎉

**Accede**: http://SERVER_IP:3000  
**Time**: ~10-15 minutos  
**Containers**: 17/17 running  
**Systemd**: Configurado para autostart

---

**Versión**: 1.0.0 | **OS**: Linux (Ubuntu/Debian/CentOS/Fedora) | **Rhinometric**: v2.1.0 Trial
