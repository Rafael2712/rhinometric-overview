# 🍎 MANUAL DE INSTALACIÓN - macOS

**Rhinometric v2.1.0 Trial**  
**Tiempo estimado**: 10-15 minutos  
**Nivel**: Principiante

---

## 📋 REQUISITOS PREVIOS

### **Hardware Mínimo**
- ✅ Mac: 2018 o posterior (Intel o Apple Silicon M1/M2/M3)
- ✅ RAM: 4 GB disponible (8 GB recomendado)
- ✅ Disco: 20 GB libres
- ✅ macOS: 12 Monterey o superior

### **Software Requerido**

1. **Docker Desktop for Mac**
   - Versión: 4.25.0+
   - Descarga: https://www.docker.com/products/docker-desktop/

2. **Homebrew** (opcional pero recomendado)
   - Package manager para macOS
   - Instalación: https://brew.sh

---

## 🔧 INSTALACIÓN RÁPIDA (Homebrew)

### **Opción A: Un Comando** (Recomendado)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Rafael2712/mi-proyecto/main/install-mac-simple.sh)"
```

Este script hace TODO automáticamente:
- ✅ Instala Docker Desktop (si no está)
- ✅ Descarga Rhinometric v2.1.0
- ✅ Configura credenciales
- ✅ Levanta los 17 contenedores
- ✅ Verifica que todo funciona

**Tiempo**: 10 minutos (incluye descargas)

---

## 🔧 INSTALACIÓN MANUAL (Paso a Paso)

### **PASO 1: Instalar Docker Desktop**

#### **1.1 Usando Homebrew** (Recomendado)

```bash
# Instala Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instala Docker Desktop
brew install --cask docker

# Abre Docker Desktop
open -a Docker
```

#### **1.2 Instalación Manual**

1. Descarga: https://www.docker.com/products/docker-desktop/
2. Arrastra `Docker.app` a **Applications**
3. Abre **Docker** desde Applications
4. Acepta los permisos cuando se soliciten

#### **1.3 Verificar Instalación**

```bash
# Espera a que Docker inicie (icono ballena en menubar)
docker --version
# Docker version 4.25.0 o superior

docker ps
# Tabla vacía (sin contenedores aún)
```

---

### **PASO 2: Descargar Rhinometric**

#### **2.1 Crear directorio de trabajo**

```bash
cd ~
mkdir -p rhinometric
cd rhinometric
```

#### **2.2 Descargar release**

**Opción A: wget**
```bash
wget https://github.com/Rafael2712/mi-proyecto/releases/download/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz
```

**Opción B: curl**
```bash
curl -LO https://github.com/Rafael2712/mi-proyecto/releases/download/v2.1.0/rhinometric-trial-v2.1.0-universal.tar.gz
```

**Opción C: Git clone**
```bash
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto
```

#### **2.3 Descomprimir**

```bash
tar -xzf rhinometric-trial-v2.1.0-universal.tar.gz
cd rhinometric-trial-v2.1.0-universal
ls -la
# Debe mostrar docker-compose-v2.1.0.yml, .env.example, etc.
```

---

### **PASO 3: Configurar**

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar con tu editor favorito
nano .env
# O: code .env (si tienes VS Code)
# O: vim .env
```

**Cambiar estas líneas**:

```env
GRAFANA_USER=admin
GRAFANA_PASSWORD=TuPasswordSeguro123!    # ← CAMBIAR

POSTGRES_PASSWORD=TuPasswordSeguro456!   # ← CAMBIAR
REDIS_PASSWORD=TuPasswordSeguro789!      # ← CAMBIAR

# Path en macOS
HOME=/Users/tunombredeusuario            # ← CAMBIAR

RHINOMETRIC_MODE=trial
RHINOMETRIC_VERSION=2.1.0
```

**Guardar**:
- nano: `Ctrl + O` → Enter → `Ctrl + X`
- vim: `Esc` → `:wq` → Enter

---

### **PASO 4: Levantar Rhinometric**

```bash
# Pull de imágenes (primera vez, 5-10 min)
docker compose -f docker-compose-v2.1.0.yml pull

# Iniciar todos los contenedores
docker compose -f docker-compose-v2.1.0.yml up -d

# Ver estado
docker ps | grep rhinometric
# Debe mostrar 17 contenedores "Up" o "Up (healthy)"
```

---

### **PASO 5: Verificar y Acceder**

```bash
# Verificación rápida
./validate-v2.1.sh

# O manual
curl -s http://localhost:3000/api/health | jq .
# Debe mostrar: {"database": "ok", "version": "..."}
```

**Acceder**:
- **Grafana**: http://localhost:3000 (admin / tu_password)
- **API Connector**: http://localhost:8091
- **Prometheus**: http://localhost:9090

---

## 🍺 COMANDOS ÚTILES (macOS)

### **Ver logs**

```bash
# Logs de Grafana
docker logs rhinometric-grafana --tail 50 -f

# Logs de todos los servicios
docker compose -f docker-compose-v2.1.0.yml logs -f
```

### **Reiniciar servicios**

```bash
# Reiniciar todo
docker compose -f docker-compose-v2.1.0.yml restart

# Reiniciar solo Grafana
docker restart rhinometric-grafana
```

### **Detener/Iniciar**

```bash
# Detener (datos se conservan)
docker compose -f docker-compose-v2.1.0.yml stop

# Iniciar después de detener
docker compose -f docker-compose-v2.1.0.yml start

# Detener y ELIMINAR todo (CUIDADO)
docker compose -f docker-compose-v2.1.0.yml down -v
```

### **Ver uso de recursos**

```bash
docker stats --no-stream | grep rhinometric
```

---

## 🐛 TROUBLESHOOTING macOS

### **❌ "Cannot connect to Docker daemon"**

```bash
# Verifica que Docker Desktop está corriendo
ps aux | grep -i docker

# Si no está, ábrelo
open -a Docker

# Espera 30 segundos y reintenta
docker ps
```

### **❌ "Port already allocated"**

```bash
# Ver qué proceso usa el puerto 3000
lsof -i :3000

# Matar el proceso (reemplaza PID con el número que viste)
kill -9 PID
```

### **❌ "Permission denied" al ejecutar scripts**

```bash
# Dar permisos de ejecución
chmod +x validate-v2.1.sh
chmod +x auto-update.sh
chmod +x *.sh
```

### **❌ M1/M2/M3 Mac - "exec format error"**

Algunas imágenes no son multi-arch. Solución:

```bash
# Usa Rosetta 2
softwareupdate --install-rosetta --agree-to-license

# O especifica plataforma en docker-compose
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose -f docker-compose-v2.1.0.yml up -d
```

---

## 🔄 AUTO-UPDATE

```bash
# Verificar si hay actualizaciones
./auto-update.sh --check-only

# Actualizar (con backup automático)
./auto-update.sh

# Actualizar a versión específica
./auto-update.sh --version=2.2.0
```

---

## 📊 VERIFICACIÓN POST-INSTALACIÓN

```bash
#!/bin/bash
echo "=== VERIFICACION RHINOMETRIC macOS ==="
docker ps | grep rhinometric | wc -l | xargs echo "Containers:"
curl -s http://localhost:3000/api/health | jq -r .database
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3100/ready
echo "✅ Verificación completa"
```

---

## 🍎 CARACTERÍSTICAS ESPECÍFICAS macOS

### **Integración con Spotlight**

Rhinometric logs son indexados automáticamente:

```bash
# Buscar en Spotlight
mdfind "rhinometric error"
```

### **Notificaciones nativas**

Configura alertas que se muestran en Notification Center:

```bash
# En Grafana: Contact Points → Add webhook
# URL: osascript://display-notification
```

### **Shortcuts / Automator**

Crea atajos para iniciar/detener Rhinometric:

```applescript
-- Shortcut: Iniciar Rhinometric
do shell script "cd ~/rhinometric/rhinometric-trial-v2.1.0-universal && docker compose -f docker-compose-v2.1.0.yml start"
display notification "Rhinometric iniciado" with title "Observabilidad"
```

---

## 📚 PRÓXIMOS PASOS

1. Lee: `docs/MANUAL_USUARIO_v2.1.0.md`
2. Explora dashboards en http://localhost:3000
3. Agrega APIs en http://localhost:8091
4. Configura alertas (Slack, email)

---

## 🆘 SOPORTE

- 📖 Docs: `docs/` directory
- 🐙 GitHub: https://github.com/Rafael2712/mi-proyecto/issues
- 📧 Email (comercial): rafael.canelon@rhinometric.com

---

**✅ INSTALACIÓN COMPLETADA EN macOS** 🎉

**Accede**: http://localhost:3000  
**Time**: ~10-15 minutos  
**Containers**: 17/17 running

---

**Versión**: 1.0.0 | **OS**: macOS 12+ | **Rhinometric**: v2.1.0 Trial
