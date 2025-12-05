# ==============================================================================
# INSTRUCCIONES DE DESPLIEGUE RHINOMETRIC TRIAL v2.0.0 EN UBUNTU WSL2
# ==============================================================================

## 📋 RESUMEN DE CAMBIOS

Este rebuild incluye las siguientes mejoras:

### ✅ Versiones Fijas (Sin `latest`)
- grafana: 10.4.0
- prometheus: v2.53.0
- loki: 3.0.0
- tempo: 2.6.0
- redis: 7.2-alpine
- postgres: 15.10-alpine
- nginx: 1.27-alpine
- alertmanager: v0.27.0
- node-exporter: v1.8.2
- cadvisor: v0.50.0
- blackbox-exporter: v0.25.0
- postgres-exporter: v0.15.0
- promtail: 3.0.0
- telemetrygen: v0.111.0

### ✅ Healthchecks Completos
Todos los 16 servicios tienen healthcheck configurado:
- license-server: curl http://localhost:5000/health
- postgres: pg_isready
- redis: redis-cli ping
- prometheus: wget http://localhost:9090/-/healthy
- loki: wget http://localhost:3100/ready
- tempo: wget http://localhost:3200/ready
- grafana: wget http://localhost:3000/api/health
- alertmanager: wget http://localhost:9093/-/healthy
- Y todos los exporters, nginx, promtail, telemetrygen

### ✅ Bind Mounts Persistentes
Todos los volúmenes usan bind mounts en `~/rhinometric_data/`:
- postgres → ~/rhinometric_data/postgres
- redis → ~/rhinometric_data/redis
- prometheus → ~/rhinometric_data/prometheus
- grafana → ~/rhinometric_data/grafana
- loki → ~/rhinometric_data/loki
- tempo → ~/rhinometric_data/tempo
- license → ~/rhinometric_data/license
- alertmanager → ~/rhinometric_data/alertmanager

### ✅ Modo Oscuro Grafana
Confirmado: `GF_USERS_DEFAULT_THEME: dark`

---

## 🚀 DESPLIEGUE EN UBUNTU WSL2

### Opción 1: Despliegue Automatizado (RECOMENDADO)

```bash
# 1. Acceder a WSL2
wsl -d Ubuntu

# 2. Navegar al directorio del proyecto
cd /mnt/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# 3. Dar permisos de ejecución al script
chmod +x rebuild-rhinometric.sh

# 4. Ejecutar script de rebuild
./rebuild-rhinometric.sh
```

El script ejecutará automáticamente:
- ✓ Verificación del sistema (Ubuntu, Docker, Docker Compose)
- ✓ Verificación de archivos requeridos
- ✓ Creación de directorios de datos en ~/rhinometric_data
- ✓ Validación del archivo .env
- ✓ Limpieza de contenedores anteriores
- ✓ Construcción de imágenes custom
- ✓ Despliegue de 16 servicios
- ✓ Espera de healthchecks (hasta 5 minutos)
- ✓ Validación funcional completa
- ✓ Generación de reporte de validación

**Tiempo estimado:** 5-10 minutos

---

### Opción 2: Despliegue Manual

Si prefieres control manual:

```bash
# 1. Acceder a WSL2
wsl -d Ubuntu

# 2. Navegar al proyecto
cd /mnt/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# 3. Crear directorios de datos
mkdir -p ~/rhinometric_data/{postgres,redis,prometheus,grafana,loki,tempo,license,alertmanager}

# 4. Ajustar permisos (crítico)
sudo chown 10001:10001 ~/rhinometric_data/loki
sudo chown 472:472 ~/rhinometric_data/grafana
sudo chown 65534:65534 ~/rhinometric_data/prometheus

# 5. Detener contenedores anteriores (si existen)
docker compose -f docker-compose-trial.yml down -v 2>/dev/null || true

# 6. Limpieza opcional (CUIDADO: borra todo Docker)
# docker system prune -a -f --volumes

# 7. Construir imágenes custom
docker compose -f docker-compose-rebuilt.yml build --no-cache

# 8. Desplegar servicios
docker compose -f docker-compose-rebuilt.yml up -d

# 9. Esperar a que servicios estén healthy (5 min aprox)
watch -n 5 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# 10. Validar estado
chmod +x validate-stack.sh
./validate-stack.sh
```

---

## 🔍 VALIDACIÓN POST-DESPLIEGUE

### Verificar contenedores

```bash
# Ver todos los contenedores
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Debe mostrar 16 contenedores con estado "healthy"
```

### Verificar healthchecks

```bash
# Ejecutar script de validación
./validate-stack.sh
```

Debe mostrar:
```
✓ rhinometric-license-server: HEALTHY
✓ rhinometric-postgres: HEALTHY
✓ rhinometric-redis: HEALTHY
✓ rhinometric-prometheus: HEALTHY
✓ rhinometric-loki: HEALTHY
✓ rhinometric-tempo: HEALTHY
✓ rhinometric-telemetrygen: HEALTHY
✓ rhinometric-grafana: HEALTHY
✓ rhinometric-alertmanager: HEALTHY
✓ rhinometric-node-exporter: HEALTHY
✓ rhinometric-cadvisor: HEALTHY
✓ rhinometric-blackbox-exporter: HEALTHY
✓ rhinometric-postgres-exporter: HEALTHY
✓ rhinometric-license-dashboard: HEALTHY
✓ rhinometric-nginx: HEALTHY
✓ rhinometric-promtail: HEALTHY

Resultado: 16/16 contenedores healthy
```

### Verificar acceso web

```bash
# Desde WSL2
curl -s http://localhost:3000/api/health | jq .
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3100/ready
curl -s http://localhost:3200/ready
curl -s http://localhost:5000/health | jq .
curl -s http://localhost:8080/health | jq .
```

Desde Windows:
- Grafana: http://localhost:3000 (admin / admin_trial_2024)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- License Dashboard: http://localhost:8080

### Verificar modo oscuro

```bash
docker exec rhinometric-grafana env | grep GF_USERS_DEFAULT_THEME
# Debe mostrar: GF_USERS_DEFAULT_THEME=dark
```

O acceder a http://localhost:3000 y verificar visualmente.

### Verificar persistencia

```bash
# Ver tamaño de datos
du -sh ~/rhinometric_data/*

# Debe mostrar directorios con datos:
# ~/rhinometric_data/postgres   (~50MB después de init)
# ~/rhinometric_data/grafana    (~10MB)
# ~/rhinometric_data/prometheus (~5MB creciente)
# etc.
```

---

## 🛠️ COMANDOS ÚTILES

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose -f docker-compose-rebuilt.yml logs -f

# Servicio específico
docker compose -f docker-compose-rebuilt.yml logs -f grafana
docker compose -f docker-compose-rebuilt.yml logs -f license-server
docker compose -f docker-compose-rebuilt.yml logs -f prometheus
```

### Reiniciar servicios

```bash
# Todos
docker compose -f docker-compose-rebuilt.yml restart

# Uno específico
docker compose -f docker-compose-rebuilt.yml restart grafana
```

### Detener servicios

```bash
# Detener sin borrar datos
docker compose -f docker-compose-rebuilt.yml stop

# Detener y borrar contenedores (datos persisten en ~/rhinometric_data)
docker compose -f docker-compose-rebuilt.yml down

# Detener, borrar contenedores Y volúmenes Docker (NO afecta bind mounts)
docker compose -f docker-compose-rebuilt.yml down -v
```

### Ver recursos usados

```bash
# CPU y RAM por contenedor
docker stats

# Solo servicios Rhinometric
docker stats $(docker ps --filter "name=rhinometric-" --format "{{.Names}}")
```

### Acceder a contenedores

```bash
# Postgres
docker exec -it rhinometric-postgres psql -U postgres -d rhinometric_trial

# Redis
docker exec -it rhinometric-redis redis-cli

# Grafana (inspeccionar configuración)
docker exec -it rhinometric-grafana cat /etc/grafana/grafana.ini

# License Server (ver logs en vivo)
docker exec -it rhinometric-license-server tail -f /app/logs/license_server.log
```

---

## 📦 GENERAR ZIP DISTRIBUIBLE

Una vez validado el sistema:

```bash
# Desde el directorio del proyecto
./create-trial-package.sh

# O crear manualmente:
cd /mnt/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# Crear estructura limpia
mkdir -p rhinometric-trial-v2.0.0-linux-rebuild
cp docker-compose-rebuilt.yml rhinometric-trial-v2.0.0-linux-rebuild/docker-compose.yml
cp -r config/ rhinometric-trial-v2.0.0-linux-rebuild/
cp -r grafana/ rhinometric-trial-v2.0.0-linux-rebuild/
cp -r licensing/ rhinometric-trial-v2.0.0-linux-rebuild/
cp -r license-dashboard/ rhinometric-trial-v2.0.0-linux-rebuild/
cp -r init-db/ rhinometric-trial-v2.0.0-linux-rebuild/
cp -r licenses/ rhinometric-trial-v2.0.0-linux-rebuild/
cp .env rhinometric-trial-v2.0.0-linux-rebuild/
cp rebuild-rhinometric.sh rhinometric-trial-v2.0.0-linux-rebuild/start.sh
cp validate-stack.sh rhinometric-trial-v2.0.0-linux-rebuild/

# Crear README
cat > rhinometric-trial-v2.0.0-linux-rebuild/README.md << 'EOF'
# Rhinometric Trial v2.0.0 - Rebuilt Edition

## Inicio Rápido

1. Asegurar que Docker esté corriendo
2. Ejecutar: `./start.sh`
3. Esperar 5 minutos
4. Acceder a http://localhost:3000

Usuario: admin
Contraseña: admin_trial_2024

EOF

# Empaquetar
tar -czf rhinometric-trial-v2.0.0-linux-rebuild.tar.gz rhinometric-trial-v2.0.0-linux-rebuild/

# O ZIP
zip -r rhinometric-trial-v2.0.0-linux-rebuild.zip rhinometric-trial-v2.0.0-linux-rebuild/

# Calcular checksums
sha256sum rhinometric-trial-v2.0.0-linux-rebuild.tar.gz > checksums.txt
sha256sum rhinometric-trial-v2.0.0-linux-rebuild.zip >> checksums.txt
```

---

## ⚠️ TROUBLESHOOTING

### Problema: "Cannot connect to Docker daemon"

```bash
# Verificar si Docker está corriendo
sudo systemctl status docker

# Si no está corriendo
sudo systemctl start docker

# O reiniciar
sudo systemctl restart docker
```

### Problema: "Permission denied" en ~/rhinometric_data

```bash
# Ajustar ownership
sudo chown -R $(whoami):$(whoami) ~/rhinometric_data

# Permisos específicos
sudo chown 10001:10001 ~/rhinometric_data/loki
sudo chown 472:472 ~/rhinometric_data/grafana
sudo chown 65534:65534 ~/rhinometric_data/prometheus
```

### Problema: Contenedores no llegan a "healthy"

```bash
# Ver logs del servicio problemático
docker compose -f docker-compose-rebuilt.yml logs [servicio]

# Ejemplo: ver logs de license-server
docker compose -f docker-compose-rebuilt.yml logs license-server

# Ver healthcheck detallado
docker inspect rhinometric-license-server | jq '.[0].State.Health'
```

### Problema: Puerto ya en uso

```bash
# Ver qué está usando el puerto
sudo lsof -i :3000  # Grafana
sudo lsof -i :9090  # Prometheus
sudo lsof -i :5000  # License Server

# Detener proceso o cambiar puerto en docker-compose-rebuilt.yml
```

### Problema: Construcción de imagen falla

```bash
# Limpiar build cache
docker builder prune -a -f

# Reconstruir desde cero
docker compose -f docker-compose-rebuilt.yml build --no-cache --progress=plain
```

---

## 📊 RECURSOS DEL SISTEMA

### Recursos mínimos requeridos
- CPU: 6 cores
- RAM: 12 GB
- Disco: 20 GB libres

### Recursos configurados en .wslconfig
```ini
[wsl2]
memory=4GB    # ⚠️ INSUFICIENTE - Aumentar a 12GB
processors=4  # ⚠️ INSUFICIENTE - Aumentar a 6
swap=2GB
localhostForwarding=true
```

### Ajuste recomendado para .wslconfig
Ubicación: `C:\Users\canel\.wslconfig`

```ini
[wsl2]
memory=12GB
processors=6
swap=4GB
localhostForwarding=true
nestedVirtualization=true
```

Después de cambiar, reiniciar WSL:
```powershell
wsl --shutdown
wsl -d Ubuntu
```

---

## 📞 SOPORTE

### Archivos generados por el script
- `rebuild_YYYYMMDD_HHMMSS.log` - Log completo de la ejecución
- `validation_report.txt` - Reporte de validación con estado de servicios

### Comandos de diagnóstico

```bash
# Estado general
docker compose -f docker-compose-rebuilt.yml ps

# Inspeccionar red
docker network inspect mi-proyecto_rhinometric_network

# Ver uso de recursos
docker stats --no-stream

# Exportar logs de todos los servicios
for service in $(docker ps --filter "name=rhinometric-" --format "{{.Names}}"); do
    docker logs $service > ${service}_$(date +%Y%m%d).log 2>&1
done
```

---

## ✅ CHECKLIST FINAL

Antes de dar por completado:

- [ ] 16/16 contenedores muestran status "healthy"
- [ ] Grafana accesible en http://localhost:3000
- [ ] Modo oscuro de Grafana activo
- [ ] Prometheus accesible en http://localhost:9090
- [ ] License Server responde en http://localhost:5000/health
- [ ] License Dashboard accesible en http://localhost:8080
- [ ] Directorios en ~/rhinometric_data tienen datos
- [ ] No hay errores en logs de servicios críticos
- [ ] `validation_report.txt` generado sin errores
- [ ] ZIP distribuible creado (opcional)

---

**Fecha de creación:** 24 de Octubre, 2025  
**Versión:** 2.0.0-rebuilt  
**Sistema objetivo:** Ubuntu 24.04 (WSL2)
