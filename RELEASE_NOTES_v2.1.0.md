# ��� Rhinometric v2.1.0-stable - Production Ready Release

## ��� Instalación Rápida

### Linux/macOS
```bash
wget https://github.com/Rafael2712/rhinometric-overview/releases/download/v2.1.0-stable/rhinometric-v2.1.0-stable.tar.gz
tar -xzf rhinometric-v2.1.0-stable.tar.gz
cd rhinometric-overview
cp .env.example .env
nano .env  # Configurar credenciales
chmod +x scripts/install.sh
./scripts/install.sh
```

### Windows
```powershell
# Descargar rhinometric-v2.1.0-stable.zip desde Releases
Expand-Archive rhinometric-v2.1.0-stable.zip
cd rhinometric-overview
Copy-Item .env.example .env
notepad .env  # Configurar credenciales
.\scripts\install.ps1
```

## ✨ Novedades v2.1.0

### ��� Instalación Simplificada
- ✅ **Instalador bash** (Linux/macOS) - 1 comando, validación automática
- ✅ **Instalador PowerShell** (Windows) - Detección automática de requisitos
- ✅ **Template .env** - Sin passwords hard-coded, configuración segura
- ✅ **Validación prerequisites** - Verifica Docker 24.0+ y Compose v2

### ��� Seguridad Mejorada
- ✅ **Credenciales en .env** - No más passwords en código o README
- ✅ **Advertencia primer login** - Recordatorio cambiar password default
- ✅ **SMTP opcional** - Sistema de emails con PDFs profesionales
- ✅ **Licencias con hash** - Password inicial derivada del server hash

### ��� CI/CD Pipeline
- ✅ **GitHub Actions** - Validación automática en push/PR
- ✅ **Docker Compose config** - Valida sintaxis antes de merge
- ✅ **YAML linting** - Detecta errores de formato
- ✅ **Scripts validation** - Verifica sintaxis bash/PowerShell

### ��� Sistema de Licencias
- ✅ **License Server** - FastAPI con gestión completa
- ✅ **UI Vue.js** - Interfaz web para administración (puerto 8092)
- ✅ **Emails automáticos** - HTML profesional con PDFs adjuntos
- ✅ **Trial 15 días** - Activación automática post-instalación

### ��� Observabilidad Completa
- ✅ **15 Dashboards Grafana** - Pre-configurados para producción
- ✅ **Drilldown completo** - Prometheus → Loki → Tempo
- ✅ **8+ Exporters** - Node, PostgreSQL, Redis, Cadvisor, etc.
- ✅ **API Connector** - UI para gestión de APIs externas

## ���️ Stack Tecnológico

| Componente | Versión | Puerto | Descripción |
|------------|---------|--------|-------------|
| Grafana | 10.x | 3000 | Dashboards + Alertas |
| Prometheus | 2.x | 9090 | Métricas time-series |
| Loki | 2.x | 3100 | Agregación logs |
| Tempo | 2.x | 3200 | Distributed tracing |
| PostgreSQL | 15 | 5432 | Base datos principal |
| Redis | 7 | 6379 | Cache + sessions |
| License Server | FastAPI | 8090 | API licencias |
| License UI | Vue.js 3 | 8092 | Gestión web |

## ��� Requisitos

### Hardware Mínimo
- CPU: 4 cores
- RAM: 8 GB
- Disco: 50 GB SSD

### Software
- Docker: 24.0+
- Docker Compose: v2.20+
- SO: Linux, macOS, Windows 10/11

## ��� Acceso Post-Instalación

Después de ejecutar el instalador (3-5 minutos):

- **Grafana**: http://localhost:3000
  - Usuario: `admin`
  - Password: Definido en `.env` → `GF_SECURITY_ADMIN_PASSWORD`
  
- **License Management**: http://localhost:8092
  - Crear/gestionar licencias trial/comerciales

- **API Connector**: http://localhost:8091
  - Configurar integraciones externas

- **Prometheus**: http://localhost:9090
  - Queries directas de métricas

## ��� Troubleshooting

### Contenedores no inician
```bash
docker compose -f deploy/docker-compose.yml logs -f
```

### Verificar salud de servicios
```bash
curl http://localhost:3000/api/health  # Grafana
curl http://localhost:9090/-/healthy   # Prometheus
docker ps | grep rhinometric
```

### Reinstalar desde cero
```bash
docker compose -f deploy/docker-compose.yml down -v
rm -rf ~/rhinometric_data_v2.1
./scripts/install.sh
```

## ��� Documentación Completa

- [README Principal](README.md)
- [Guía Cloud Deployment](CLOUD_DEPLOYMENT_GUIDE.md)
- [Arquitectura Híbrida](HYBRID_ARCHITECTURE_GUIDE.md)
- [Sistema de Licencias](LICENSE_SERVER_CLARIFICATION.md)
- [Instalación Linux](INSTALACION_LINUX.md)
- [Instalación macOS](INSTALACION_MACOS.md)
- [Instalación Windows](INSTALACION_WINDOWS.md)

## ��� Soporte

- ��� **Email**: rafael.canelon@rhinometric.com
- ⏰ **Horario**: Lunes-Viernes, 9:00-18:00 CET
- ��� **Issues**: https://github.com/Rafael2712/rhinometric-overview/issues
- ��� **Licencias**: rafael.canelon@rhinometric.com

## �� Licencia

**Propietaria** - Rhinometric® es una marca registrada.

- Trial: 30 días uso completo
- Desarrollo: Permitido uso no comercial
- Comercial: Requiere licencia de pago

---

**Fecha Release**: 29 Octubre 2025  
**SHA Commit**: cec93dc  
**Autor**: Rafael Canel
