#!/bin/bash
# ==============================================================================
# RHINOMETRIC TRIAL v2.0.0 - ZIP PACKAGE GENERATOR
# ==============================================================================
# Genera paquete distribuible listo para Ubuntu/Linux
# ==============================================================================

set -euo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
PACKAGE_NAME="rhinometric-trial-v2.0.0-linux-rebuilt"
TEMP_DIR="$BUILD_DIR/$PACKAGE_NAME"

echo -e "${BLUE}========================================"
echo "GENERANDO PAQUETE DISTRIBUIBLE"
echo -e "========================================${NC}"
echo ""

# Crear directorios
rm -rf "$TEMP_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$TEMP_DIR"

# Copiar archivos esenciales
echo -e "${BLUE}Copiando archivos...${NC}"

cp "$PROJECT_DIR/docker-compose-rebuilt.yml" "$TEMP_DIR/docker-compose.yml"
cp "$PROJECT_DIR/.env" "$TEMP_DIR/.env.example"
cp "$PROJECT_DIR/rebuild-rhinometric.sh" "$TEMP_DIR/start.sh"
cp "$PROJECT_DIR/validate-stack.sh" "$TEMP_DIR/validate.sh"

# Copiar directorios
cp -r "$PROJECT_DIR/config" "$TEMP_DIR/"
cp -r "$PROJECT_DIR/grafana" "$TEMP_DIR/"
cp -r "$PROJECT_DIR/licensing" "$TEMP_DIR/"
cp -r "$PROJECT_DIR/license-dashboard" "$TEMP_DIR/"
cp -r "$PROJECT_DIR/init-db" "$TEMP_DIR/"
cp -r "$PROJECT_DIR/licenses" "$TEMP_DIR/"

# Crear directorio vacío para certs
mkdir -p "$TEMP_DIR/certs"

# Crear README
cat > "$TEMP_DIR/README.md" << 'EOF'
# 🦏 Rhinometric Trial v2.0.0 - Rebuilt Edition

## 🚀 Inicio Rápido

### Requisitos
- Ubuntu 20.04+ o WSL2
- Docker Engine 20.10+
- Docker Compose v2+
- 6 CPU cores
- 12 GB RAM
- 20 GB disco libre

### Instalación Automática

```bash
# 1. Extraer paquete
unzip rhinometric-trial-v2.0.0-linux-rebuilt.zip
cd rhinometric-trial-v2.0.0-linux-rebuilt

# 2. Dar permisos
chmod +x start.sh validate.sh

# 3. Ejecutar instalación
./start.sh
```

El script automáticamente:
- ✓ Verifica requisitos del sistema
- ✓ Crea directorios de datos en ~/rhinometric_data
- ✓ Construye imágenes custom
- ✓ Despliega 16 servicios
- ✓ Espera a que todos estén healthy
- ✓ Genera reporte de validación

**Tiempo estimado:** 5-10 minutos

### Validación Post-Instalación

```bash
./validate.sh
```

Debe mostrar: `✅ TODOS LOS SERVICIOS OPERATIVOS (16/16)`

### Acceso a Servicios

- **Grafana:** http://localhost:3000
  - Usuario: `admin`
  - Contraseña: `admin_trial_2024`
  - Modo oscuro: **HABILITADO** ✓

- **Prometheus:** http://localhost:9090
- **Alertmanager:** http://localhost:9093
- **License Dashboard:** http://localhost:8080

### Servicios Incluidos (16 contenedores)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Grafana | 3000 | Dashboard principal (modo oscuro) |
| Prometheus | 9090 | Métricas (7d retención) |
| Loki | 3100 | Logs (1d retención) |
| Tempo | 3200 | Trazas distribuidas (1d retención) |
| Alertmanager | 9093 | Gestión de alertas |
| License Server | 5000 | Sistema de licencias (180d) |
| License Dashboard | 8080 | Dashboard de licencias |
| Postgres | 5432 | Base de datos |
| Redis | 6379 | Cache |
| Nginx | 80/443 | Reverse proxy |
| Promtail | - | Recolector de logs |
| Telemetrygen | - | Generador de trazas demo |
| Node Exporter | 9100 | Métricas del sistema |
| cAdvisor | 8080 | Métricas de contenedores |
| Blackbox Exporter | 9115 | Monitoreo de endpoints |
| Postgres Exporter | 9187 | Métricas de PostgreSQL |

### Características

✅ **Versiones Fijas** (sin `latest`):
- Grafana: 10.4.0
- Prometheus: v2.53.0
- Loki: 3.0.0
- Tempo: 2.6.0
- Y todas las demás...

✅ **Healthchecks Completos:**
- 16/16 servicios con healthcheck
- Dependency ordering basado en health status

✅ **Persistencia de Datos:**
- Bind mounts en `~/rhinometric_data/`
- Datos sobreviven a reinicios de Docker
- Fácil backup/restore

✅ **Modo Oscuro de Grafana:**
- `GF_USERS_DEFAULT_THEME=dark`
- Configurado y verificado

### Comandos Útiles

```bash
# Ver logs
docker compose logs -f [servicio]

# Reiniciar servicio
docker compose restart [servicio]

# Detener todo
docker compose down

# Estado de servicios
docker compose ps
```

### Persistencia de Datos

Todos los datos se almacenan en:
```
~/rhinometric_data/
├── postgres/       # Base de datos
├── redis/          # Cache
├── prometheus/     # Métricas (7 días)
├── grafana/        # Dashboards y config
├── loki/           # Logs (1 día)
├── tempo/          # Trazas (1 día)
├── license/        # Licencias
└── alertmanager/   # Estado de alertas
```

### Backup de Datos

```bash
# Backup completo
tar -czf rhinometric_backup_$(date +%Y%m%d).tar.gz ~/rhinometric_data/

# Restore
tar -xzf rhinometric_backup_YYYYMMDD.tar.gz -C ~/
```

### Troubleshooting

#### Contenedor no inicia
```bash
# Ver logs del servicio
docker compose logs [servicio]

# Reiniciar servicio específico
docker compose restart [servicio]
```

#### Puerto ya en uso
```bash
# Ver qué usa el puerto
sudo lsof -i :[puerto]

# Cambiar puerto en docker-compose.yml si es necesario
```

#### Permisos en ~/rhinometric_data
```bash
# Ajustar ownership
sudo chown -R $(whoami):$(whoami) ~/rhinometric_data

# Permisos específicos
sudo chown 10001:10001 ~/rhinometric_data/loki
sudo chown 472:472 ~/rhinometric_data/grafana
sudo chown 65534:65534 ~/rhinometric_data/prometheus
```

### Soporte

Para más información, consulta:
- `DEPLOY_INSTRUCTIONS.md` - Instrucciones detalladas
- `validation_report.txt` - Reporte generado post-instalación
- Logs: `rebuild_*.log`

### Licencia

Trial de 180 días (6 meses)

---

**Versión:** 2.0.0-rebuilt  
**Fecha:** Octubre 2025  
**Sistema:** Ubuntu 20.04+ / WSL2
EOF

# Crear script de stop
cat > "$TEMP_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "Deteniendo Rhinometric Trial v2.0.0..."
docker compose down
echo "✓ Servicios detenidos (datos preservados en ~/rhinometric_data)"
EOF

chmod +x "$TEMP_DIR/start.sh"
chmod +x "$TEMP_DIR/validate.sh"
chmod +x "$TEMP_DIR/stop.sh"

# Crear CHANGELOG
cat > "$TEMP_DIR/CHANGELOG.md" << 'EOF'
# Changelog - Rhinometric Trial v2.0.0 Rebuilt

## [2.0.0-rebuilt] - 2025-10-24

### Added
- ✅ Healthchecks completos en 16/16 servicios
- ✅ Bind mounts persistentes en ~/rhinometric_data
- ✅ Script de instalación automatizado (start.sh)
- ✅ Script de validación post-deploy (validate.sh)
- ✅ Instrucciones detalladas de despliegue

### Changed
- 🔄 Todas las imágenes Docker usan versiones fijas (eliminado `latest`)
- 🔄 Postgres: 15.10-alpine (antes: 15)
- 🔄 Redis: 7.2-alpine (antes: alpine)
- 🔄 Nginx: 1.27-alpine (antes: alpine)
- 🔄 Grafana: 10.4.0 (antes: latest)
- 🔄 Prometheus: v2.53.0 (antes: latest)
- 🔄 Loki: 3.0.0 (antes: latest)
- 🔄 Tempo: 2.6.0 (antes: latest)
- 🔄 Alertmanager: v0.27.0 (antes: latest)
- 🔄 Node Exporter: v1.8.2 (antes: latest)
- 🔄 cAdvisor: v0.50.0 (antes: latest)
- 🔄 Blackbox Exporter: v0.25.0 (antes: latest)
- 🔄 Postgres Exporter: v0.15.0 (antes: latest)
- 🔄 Promtail: 3.0.0 (antes: latest)
- 🔄 Telemetrygen: v0.111.0 (antes: latest)

### Fixed
- 🐛 Persistencia de datos en WSL2 (bind mounts en lugar de volumes)
- 🐛 Dependency ordering basado en healthchecks
- 🐛 Permisos de directorios de datos (loki:10001, grafana:472, prometheus:65534)
- 🐛 Healthcheck de postgres-exporter requiere postgres healthy primero

### Security
- 🔒 Versiones fijas previenen actualizaciones no controladas
- 🔒 Modo oscuro de Grafana confirmado y documentado

## [2.0.0] - 2025-10-23

### Initial Release
- Stack completo de observabilidad
- 16 servicios integrados
- Licenciamiento de 180 días
- Modo oscuro de Grafana
EOF

# Empaquetar
echo -e "${BLUE}Empaquetando...${NC}"
cd "$BUILD_DIR"

# TAR.GZ
tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME/"
TAR_SIZE=$(du -sh "${PACKAGE_NAME}.tar.gz" | cut -f1)

# ZIP
zip -r -q "${PACKAGE_NAME}.zip" "$PACKAGE_NAME/"
ZIP_SIZE=$(du -sh "${PACKAGE_NAME}.zip" | cut -f1)

# Calcular checksums
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}_checksums.txt"
sha256sum "${PACKAGE_NAME}.zip" >> "${PACKAGE_NAME}_checksums.txt"

# Limpiar directorio temporal
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ PAQUETE GENERADO EXITOSAMENTE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Archivos generados:${NC}"
echo "  • ${PACKAGE_NAME}.tar.gz ($TAR_SIZE)"
echo "  • ${PACKAGE_NAME}.zip ($ZIP_SIZE)"
echo "  • ${PACKAGE_NAME}_checksums.txt"
echo ""
echo -e "${BLUE}Ubicación:${NC}"
echo "  $BUILD_DIR"
echo ""
echo -e "${BLUE}Checksums:${NC}"
cat "${BUILD_DIR}/${PACKAGE_NAME}_checksums.txt"
echo ""
echo -e "${BLUE}Contenido del paquete:${NC}"
echo "  • docker-compose.yml (con versiones fijas + healthchecks)"
echo "  • start.sh (instalación automatizada)"
echo "  • validate.sh (validación post-deploy)"
echo "  • stop.sh (detener servicios)"
echo "  • README.md (guía de inicio rápido)"
echo "  • CHANGELOG.md (historial de cambios)"
echo "  • .env.example (plantilla de variables)"
echo "  • config/ (prometheus, loki, tempo, alertmanager, nginx, etc.)"
echo "  • grafana/ (provisioning: datasources + dashboards)"
echo "  • licensing/ (Dockerfile + license_server.py)"
echo "  • license-dashboard/ (Dockerfile + app.py + templates)"
echo "  • init-db/ (scripts SQL iniciales)"
echo "  • licenses/ (archivos de licencias)"
echo ""

exit 0
