# Rhinometric v2.5.0 - Release Package

**Enterprise Observability Platform**  
Fecha: 2025-12-30

## 📦 Contenido del Paquete

```
rhinometric-v2.5.0/
├── docker-compose-v2.5.0-core.yml    # Stack completo (17 servicios)
├── .env.example                       # Plantilla de configuración
├── scripts/
│   └── install-rhinometric.sh         # Instalador automatizado
├── docs/
│   ├── INSTALLATION_GUIDE.md          # Guía completa de instalación
│   └── AWS_AMI_BACKUP_INFO.txt        # Info de backup AWS (referencia)
├── grafana/
│   └── dashboards/                    # Dashboards pre-configurados (7)
└── config/                            # Configuraciones adicionales
```

## 🚀 Instalación Rápida

```bash
# Extraer paquete
tar -xzf rhinometric-v2.5.0.tar.gz
cd rhinometric-v2.5.0

# Ejecutar instalador
sudo bash scripts/install-rhinometric.sh
```

Consulta `docs/INSTALLATION_GUIDE.md` para instrucciones detalladas.

## ⚙️ Requisitos Mínimos

- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 150 GB SSD
- **Docker**: 24.0+ con Compose v2

## 📊 Servicios Incluidos

El stack incluye 17 contenedores:

**Core**:
- PostgreSQL 15 (Base de datos)
- Redis 7 (Cache)
- Prometheus 2.53 (Métricas)
- Grafana 10.4 (Dashboards)
- Loki 3.0 (Logs)
- Jaeger 1.57 (Tracing)

**Aplicación**:
- Console Frontend (React + Nginx)
- Console Backend (FastAPI)
- License Server v2
- AI Anomaly Detector

**Exporters**:
- Node Exporter
- cAdvisor
- Promtail
- OpenTelemetry Collector

## 🔗 Acceso Post-Instalación

| Servicio | Puerto | URL |
|----------|--------|-----|
| Console | 3002 | `http://<IP>:3002` |
| Grafana | 3000 | `http://<IP>:3000` |
| Prometheus | 9090 | `http://<IP>:9090` |

Credenciales en: `/opt/rhinometric/CREDENCIALES.txt`

## 📖 Documentación

- **Instalación**: `docs/INSTALLATION_GUIDE.md`
- **Troubleshooting**: Ver guía de instalación sección 6
- **API Docs**: `http://<IP>:8105/docs` (después de instalar)

## 🆘 Soporte

- Email: soporte@rhinometric.com
- Web: https://rhinometric.com/support

---

**Versión**: 2.5.0  
**Build Date**: 2025-12-30  
**License**: Comercial
