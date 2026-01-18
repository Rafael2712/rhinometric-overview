# Rhinometric v2.5.0 - Checklist de Testing Local

**Fecha**: 2025-12-30  
**Objetivo**: Validar instalación limpia desde cero  
**Entorno**: [VirtualBox / Hetzner / DigitalOcean / Otro]

---

## ✅ Pre-Requisitos

### Máquina de Testing
- [ ] Ubuntu 22.04 LTS instalado
- [ ] 4GB+ RAM disponible
- [ ] 2+ CPU cores
- [ ] 60GB+ disco libre
- [ ] Conexión a internet activa

### Archivos Necesarios
- [ ] `rhinometric-v2.5.0-release.tar.gz` copiado a la VM
- [ ] SSH key configurado (si es remoto)
- [ ] Acceso root/sudo disponible

---

## 🚀 FASE 1: Instalación Automatizada (30 min)

### 1.1 Preparación Inicial
```bash
# Conectar a la VM
ssh ubuntu@<IP-VM>

# Verificar sistema limpio
docker ps  # Debe fallar o mostrar vacío
```

**Resultado esperado**: ❌ Docker no instalado O contenedores vacíos  
**Resultado obtenido**: _________________________

### 1.2 Extraer Release Package
```bash
# Copiar archivo a VM (desde tu máquina local)
scp rhinometric-v2.5.0-release.tar.gz ubuntu@<IP-VM>:~

# En la VM:
tar -xzf rhinometric-v2.5.0-release.tar.gz
cd rhinometric-v2.5.0-release
ls -la
```

**Resultado esperado**: Carpeta con docker-compose, scripts/, docs/, etc.  
**Resultado obtenido**: _________________________

### 1.3 Revisar Documentación
```bash
cat README.md
cat docs/INSTALLATION_GUIDE.md | head -50
```

**Pregunta crítica**: ¿La guía es clara para alguien que NO conoce Rhinometric?  
**Respuesta**: _________________________

### 1.4 Ejecutar Instalador
```bash
# Dar permisos de ejecución
chmod +x scripts/install-rhinometric.sh

# Ejecutar con sudo
sudo bash scripts/install-rhinometric.sh
```

**Monitorear**:
- [ ] Banner ASCII se muestra correctamente
- [ ] Validaciones de sistema pasan (OS, CPU, RAM, disco)
- [ ] Docker se detecta (o pide instalarlo)
- [ ] Puertos se verifican como libres
- [ ] Confirmación antes de continuar
- [ ] Credenciales se generan automáticamente
- [ ] Docker Compose pull descarga imágenes
- [ ] Docker Compose up inicia servicios
- [ ] Espera 60s para healthchecks
- [ ] Mensaje de éxito con URLs

**Errores encontrados** (copiar texto exacto):
```
[Pegar errores aquí]
```

**Tiempo total de instalación**: _______ minutos

---

## 🔍 FASE 2: Verificación Básica (15 min)

### 2.1 Estado de Contenedores
```bash
cd /opt/rhinometric
docker compose ps
```

**Verificar**:
- [ ] 17 contenedores listados
- [ ] Todos en estado `healthy` (puede tomar 2-3 min)
- [ ] No hay `restarting` ni `exited`

**Resultado**:
```
[Pegar salida de docker compose ps]
```

### 2.2 Logs de Servicios Críticos
```bash
# Ver últimas 20 líneas de cada servicio
docker compose logs --tail 20 postgres
docker compose logs --tail 20 grafana
docker compose logs --tail 20 prometheus
```

**Errores en logs**: _________________________

### 2.3 Healthchecks Manuales
```bash
# Prometheus
curl -s http://localhost:9090/-/healthy
# Esperado: "Prometheus Server is Healthy."

# Grafana
curl -s http://localhost:3000/api/health | jq .
# Esperado: {"database": "ok", "version": "10.4.0"}

# Console Backend
curl -s http://localhost:8105/health | jq .
# Esperado: {"status": "healthy", "services": {...}}
```

**Resultados**:
- Prometheus: ✅ / ❌ → _________________________
- Grafana: ✅ / ❌ → _________________________
- Console: ✅ / ❌ → _________________________

### 2.4 Credenciales Guardadas
```bash
sudo cat /opt/rhinometric/CREDENCIALES.txt
```

**Verificar**:
- [ ] Archivo existe
- [ ] Contiene 4 passwords diferentes
- [ ] URLs muestran IP correcta de la VM
- [ ] Permisos 600 (solo root puede leer)

---

## 🌐 FASE 3: Acceso Web (15 min)

### 3.1 Console Frontend
**URL**: `http://<IP-VM>:3002`

**Verificar**:
- [ ] Página carga (no 404, no timeout)
- [ ] Muestra interfaz de Rhinometric
- [ ] Login funciona con credenciales de CREDENCIALES.txt
- [ ] Dashboards, Alerts, Anomalies son accesibles

**Screenshots sugeridos**: Homepage, Dashboard list

**Problemas encontrados**: _________________________

### 3.2 Grafana
**URL**: `http://<IP-VM>:3000`  
**Login**: `admin` / (ver CREDENCIALES.txt)

**Verificar**:
- [ ] Login exitoso
- [ ] 4 dashboards aparecen en lista:
  - [ ] 05 - Docker Containers
  - [ ] 06 - System Monitoring
  - [ ] 07 - License Status
  - [ ] 08 - Stack Health
- [ ] Dashboard 05 muestra datos de contenedores
- [ ] Dashboard 06 muestra CPU/RAM del host
- [ ] No hay paneles con "No data" (excepto si no hay licencias)

**Problemas con dashboards**: _________________________

### 3.3 Prometheus (opcional)
**URL**: `http://<IP-VM>:9090`

**Verificar**:
- [ ] Interfaz carga
- [ ] Status → Targets muestra ~11 targets UP
- [ ] Graph: query `up` devuelve resultados

---

## 🐛 FASE 4: Troubleshooting Simulado (20 min)

### 4.1 Reiniciar Stack Completo
```bash
cd /opt/rhinometric
docker compose down
sleep 5
docker compose up -d
sleep 60
docker compose ps
```

**Verificar**:
- [ ] Todos los contenedores vuelven a `healthy`
- [ ] URLs siguen funcionando
- [ ] Grafana mantiene dashboards
- [ ] Credenciales siguen siendo las mismas

**Tiempo de recuperación**: _______ segundos

### 4.2 Simular Fallo de Servicio
```bash
# Detener Grafana
docker compose stop grafana

# Verificar que otros servicios siguen operativos
curl -s http://localhost:9090/-/healthy  # Debe funcionar
curl -s http://localhost:3000/api/health  # Debe fallar

# Reiniciar solo Grafana
docker compose start grafana
sleep 10
docker compose ps grafana
```

**Resultado**: _________________________

### 4.3 Uso de Recursos
```bash
# Memoria
free -h

# Uso por contenedor
docker stats --no-stream

# Disco
df -h /opt/rhinometric
du -sh /opt/rhinometric/data/*
```

**Métricas**:
- RAM total usada: _______ GB / _______ GB
- Contenedor que más consume: _________________________
- Espacio en disco usado: _______ GB

---

## 📚 FASE 5: Documentación (10 min)

### 5.1 Calidad de la Guía
**Pregunta**: ¿Un sysadmin sin conocimiento de Rhinometric podría instalar siguiendo solo `INSTALLATION_GUIDE.md`?

**Respuesta**: ✅ Sí / ❌ No  
**Razón**: _________________________

### 5.2 Errores/Mejoras Sugeridas

**Sección de Requisitos**:
- [ ] Clara y completa
- [ ] Falta mencionar: _________________________

**Sección de Instalación Rápida**:
- [ ] Funciona tal cual está escrita
- [ ] Falta paso: _________________________

**Sección de Troubleshooting**:
- [ ] Cubre los problemas que encontré
- [ ] Debería agregar: _________________________

### 5.3 Usabilidad del Script
**install-rhinometric.sh**:
- [ ] Mensajes claros y entendibles
- [ ] Errores bien explicados
- [ ] Genera credenciales correctamente
- [ ] Tiempo de ejecución razonable

**Mejoras sugeridas**: _________________________

---

## 📊 FASE 6: Resultado Final

### Checklist de Éxito
- [ ] ✅ Instalación completada sin intervención manual
- [ ] ✅ 17 contenedores operativos
- [ ] ✅ Console accesible y funcional
- [ ] ✅ Grafana con 4 dashboards mostrando datos
- [ ] ✅ Stack resiliente a reinicio
- [ ] ✅ Documentación suficiente para instalar solo

### Problemas Críticos Encontrados
1. _________________________
2. _________________________
3. _________________________

### Problemas Menores
1. _________________________
2. _________________________

### Tiempo Total de Testing
- Instalación: _______ min
- Verificación: _______ min
- Troubleshooting: _______ min
- **TOTAL**: _______ min

### Decisión Final
- [ ] ✅ **Release v2.5.0 APROBADO** - Puede entregarse a clientes
- [ ] ⚠️ **Requiere ajustes menores** - (listar)
- [ ] ❌ **No apto para release** - Problemas graves a resolver

---

## 📝 Notas Adicionales

### Experiencia General
_________________________

### Sorpresas Positivas
_________________________

### Frustraciones
_________________________

### Siguiente Paso Recomendado
_________________________

---

**Testeado por**: _________________________  
**Fecha**: _________________________  
**Entorno**: _________________________  
**Aprobado para release**: ✅ / ❌
