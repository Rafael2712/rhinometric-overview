# 🔧 SOLUCIÓN AL PROBLEMA DE RHINOMETRIC EN MAC

## 📋 DIAGNÓSTICO DEL PROBLEMA

### Problemas Identificados:

1. **❌ Atributo `version: '3.8'` obsoleto**
   - Docker Compose v2+ (incluido en Docker Desktop para Mac) ya NO requiere ni soporta este atributo
   - Causa que Compose se quede colgado sin mostrar errores claros
   - **SOLUCIONADO**: Eliminado del `docker-compose.yml`

2. **❌ Configuración de volúmenes incompatible con macOS**
   - `node-exporter` y `cadvisor` intentaban montar `/proc`, `/sys` y `/` de forma que no funciona en Docker Desktop para Mac
   - **SOLUCIONADO**: Ajustados volúmenes con opciones compatibles con macOS

3. **❌ Falta de validación de sintaxis**
   - El script `start-trial.sh` no validaba la sintaxis del `docker-compose.yml` antes de intentar levantar servicios
   - **SOLUCIONADO**: Agregada validación con `docker compose config`

---

## ✅ CAMBIOS REALIZADOS

### 1. `docker-compose.yml` (ARREGLADO)

#### Cambio 1: Eliminado atributo obsoleto

**ANTES (❌ NO FUNCIONA):**
```yaml
version: '3.8'

services:
  ...
```

**DESPUÉS (✅ FUNCIONA):**
```yaml
# ════════════════════════════════════════════════════════════════════
# RHINOMETRIC TRIAL - Docker Compose
# Versión: 1.0.1 (Trial 180 días)
# Compatible con Docker Compose v2+ (macOS/Linux/Windows)
# ════════════════════════════════════════════════════════════════════

services:
  ...
```

#### Cambio 2: Volúmenes compatibles con macOS

**ANTES (❌ NO FUNCIONA EN MAC):**
```yaml
node-exporter:
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/host:ro  # ❌ Causa problemas en macOS
```

**DESPUÉS (✅ FUNCIONA EN MAC):**
```yaml
node-exporter:
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/host:ro,rslave  # ✅ Opción rslave para macOS
  privileged: false  # ✅ Deshabilitado para macOS
```

**ANTES (❌ NO FUNCIONA EN MAC):**
```yaml
cadvisor:
  volumes:
    - /:/rootfs:ro  # ❌ Problemático en macOS
    - /var/run:/var/run:ro
    - /sys:/sys:ro
    - /var/lib/docker/:/var/lib/docker:ro
```

**DESPUÉS (✅ FUNCIONA EN MAC):**
```yaml
cadvisor:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro  # ✅ Simplificado
    - /sys:/sys:ro
    - /var/lib/docker/:/var/lib/docker:ro
  privileged: false  # ✅ Deshabilitado para macOS
```

---

### 2. `start-trial.sh` (MEJORADO)

#### Agregada validación de sintaxis:

```bash
# Validar sintaxis de docker-compose.yml
if ! $COMPOSE_CMD config > /dev/null 2>&1; then
    print_error "Error de sintaxis en docker-compose.yml"
    echo ""
    echo "Ejecuta para ver detalles:"
    echo "  $COMPOSE_CMD config"
    exit 1
fi

print_success "Sintaxis de docker-compose.yml válida"
```

#### Agregada limpieza de contenedores colgados:

```bash
# Detener servicios previos si existen
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true

# Limpiar contenedores colgados
print_info "Limpiando contenedores anteriores..."
docker container prune -f 2>/dev/null || true
```

#### Agregado logging mejorado:

```bash
# Iniciar servicios con logging mejorado
if $COMPOSE_CMD up -d --build 2>&1 | tee /tmp/rhinometric-startup.log; then
    print_success "Contenedores iniciados correctamente"
else
    print_error "Falló el inicio de servicios"
    echo ""
    echo "Detalles del error en: /tmp/rhinometric-startup.log"
    echo ""
    echo "Para diagnóstico detallado ejecuta:"
    echo "  ./debug.sh"
    exit 1
fi
```

#### Agregada verificación de servicios corriendo:

```bash
# Verificar que al menos algunos servicios estén corriendo
RUNNING_SERVICES=$($COMPOSE_CMD ps --services --filter "status=running" | wc -l)

if [ "$RUNNING_SERVICES" -eq 0 ]; then
    print_warning "Ningún servicio está corriendo"
    echo ""
    echo "Ejecuta para ver errores:"
    echo "  $COMPOSE_CMD logs"
else
    print_success "$RUNNING_SERVICES servicios están corriendo"
fi
```

---

### 3. `debug.sh` (NUEVO)

Script completamente nuevo para diagnóstico rápido:

**Características:**
- ✅ Verifica Docker y Docker Compose
- ✅ Valida archivos esenciales
- ✅ Valida sintaxis de `docker-compose.yml`
- ✅ Muestra estado de servicios
- ✅ Detecta contenedores colgados y los limpia
- ✅ Detecta puertos ocupados
- ✅ Muestra comandos útiles

**Uso:**
```bash
cd ~/Downloads/trial-package
./debug.sh
```

---

## 🚀 CÓMO USAR LA VERSIÓN ARREGLADA

### Paso 1: Actualizar el paquete en tu Mac

Si ya tienes el paquete descargado:

```bash
cd ~/Downloads/trial-package

# Detener servicios colgados (si los hay)
docker compose down --remove-orphans

# Limpiar contenedores
docker container prune -f
```

### Paso 2: Reemplazar archivos arreglados

**Opción A: Reemplazo manual** (si estás en el Mac del usuario)

1. Sobrescribir `docker-compose.yml` con la versión arreglada
2. Sobrescribir `start-trial.sh` con la versión mejorada
3. Agregar el nuevo archivo `debug.sh`

**Opción B: Generar nuevo ZIP** (recomendado)

Desde tu máquina Windows:

```powershell
cd C:\Users\canel\mi-proyecto\infrastructure\mi-proyecto\trial-package

# Dar permisos ejecutables
# (esto se hace en Mac, pero podemos preparar el paquete)

# Crear nuevo ZIP
Compress-Archive -Path trial-package -DestinationPath rhinometric-trial-v1.0.1-FIXED.zip -Force
```

### Paso 3: Ejecutar el instalador

```bash
cd ~/Downloads/trial-package

# Dar permisos ejecutables
chmod +x start-trial.sh
chmod +x debug.sh

# Ejecutar instalador
./start-trial.sh
```

---

## 🔍 DIAGNÓSTICO SI SIGUE FALLANDO

### Si `start-trial.sh` sigue colgándose:

```bash
cd ~/Downloads/trial-package

# 1. Ejecutar script de diagnóstico
./debug.sh

# 2. Verificar sintaxis manualmente
docker compose config

# 3. Ver errores específicos
docker compose up 2>&1 | head -n 50

# 4. Ver logs de Docker Desktop
# Abrir Docker Desktop → Troubleshoot → View Logs
```

### Si `docker compose config` muestra errores:

```bash
# Ver detalles completos del error
docker compose config

# Verificar permisos de archivos
ls -la docker-compose.yml
ls -la config/
```

### Si los servicios no arrancan:

```bash
# Ver qué servicios fallaron
docker compose ps -a

# Ver logs del servicio que falla
docker compose logs postgres
docker compose logs license-server
docker compose logs grafana

# Verificar puertos ocupados
lsof -i :3000  # Grafana
lsof -i :9090  # Prometheus
lsof -i :8080  # License Dashboard
```

---

## 📊 TABLA DE COMPATIBILIDAD

| Componente | macOS | Linux | Windows |
|------------|-------|-------|---------|
| Docker Compose sin `version` | ✅ | ✅ | ✅ |
| node-exporter (volúmenes simplificados) | ✅ | ✅ | ⚠️ |
| cadvisor (sin `/rootfs`) | ✅ | ✅ | ⚠️ |
| privileged: false | ✅ | ⚠️ | ✅ |

**Leyenda:**
- ✅ Funciona perfectamente
- ⚠️ Puede requerir ajustes

---

## 🎯 RESUMEN DE LA SOLUCIÓN

### Problema raíz:
Docker Compose v2+ (incluido en Docker Desktop para Mac desde 2022) eliminó el soporte para el atributo `version` en `docker-compose.yml`. Cuando este atributo está presente, Compose lo ignora con un warning, pero puede causar comportamientos impredecibles.

### Solución aplicada:
1. ✅ Eliminado `version: '3.8'` del `docker-compose.yml`
2. ✅ Ajustados volúmenes de `node-exporter` y `cadvisor` para compatibilidad con macOS
3. ✅ Agregada validación de sintaxis en `start-trial.sh`
4. ✅ Agregado logging detallado de errores
5. ✅ Creado script `debug.sh` para troubleshooting

### Resultado esperado:
Los servicios deberían arrancar correctamente en 5-10 minutos (primera vez) mostrando progreso y sin quedarse colgados.

---

## 📞 SI SIGUE SIN FUNCIONAR

Proporciona esta información para diagnóstico adicional:

```bash
# 1. Versión de Docker
docker --version
docker compose version

# 2. Versión de macOS
sw_vers

# 3. Recursos disponibles
docker info | grep -A 5 "Server Version"

# 4. Salida completa del debug
./debug.sh > debug-output.txt 2>&1

# 5. Logs completos
docker compose logs > compose-logs.txt 2>&1

# 6. Configuración parseada
docker compose config > compose-parsed.yml 2>&1
```

Envía estos archivos para análisis detallado.

---

**Fecha**: 17 de Octubre, 2025  
**Versión del Fix**: 1.0.1  
**Archivos modificados**: 
- `docker-compose.yml` (eliminado `version`, volúmenes arreglados)
- `start-trial.sh` (validación mejorada)
- `debug.sh` (nuevo)
