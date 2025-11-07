# Rhinometric Demo Environment

Stack demo auto-contenido para demostraciones y desarrollo local.

## ��� Características

- **15 servicios** preconfigurados (Grafana, Prometheus, Loki, Tempo, AI Anomaly, etc.)
- **Credenciales de demostración** (admin/rhinometric_demo)
- **Auto-seeding de datos** para dashboards funcionales desde el inicio
- **Retención reducida** (3d Prometheus, 7d Loki, 3d Tempo) vs producción
- **TLS auto-firmado** con Traefik
- **Scripts operacionales** (smoke-test, backup, update, support-bundle)

## ��� Quick Start

```bash
# 1. Generar certificados (si no existen)
cd traefik/certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/C=US/ST=Demo/L=Demo/O=Rhinometric/CN=rhinometric-demo.local"
cd ../..

# 2. Levantar stack
docker compose -f docker-compose-demo.yml up -d

# 3. Esperar healthchecks (~30s)
docker compose -f docker-compose-demo.yml ps

# 4. Iniciar auto-seeding (opcional para datos inmediatos)
bash scripts/anomaly-seed.sh &

# 5. Verificar funcionamiento
bash scripts/smoke-test.sh
```

## ��� Acceso

- **Grafana**: http://localhost:3000 (admin/rhinometric_demo)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200
- **AI Anomaly**: http://localhost:8085
- **Dashboard Builder**: http://localhost:8001

## ��� Dashboards Incluidos

1. **AI Anomaly Detection** - Detección de anomalías en tiempo real
2. **System Overview** - Métricas de infraestructura (CPU, RAM, disco)
3. **App Performance** - Latencia, throughput, errores de API

## �� Operaciones

### Smoke Test
```bash
bash scripts/smoke-test.sh
# Verifica: containers, endpoints, targets, datasources, métricas AI, disco
```

### Backup
```bash
bash scripts/backup.sh
# Respalda volúmenes (grafana, prometheus, loki, postgres)
# Genera checksums SHA256
# Retención: 7 días
```

### Update
```bash
bash scripts/update.sh
# 1. Backup
# 2. Pull imágenes
# 3. Restart
# 4. Smoke test
```

### Support Bundle
```bash
bash scripts/support-bundle.sh
# Genera tar.gz con: logs, configs, docker info, health checks
```

### Auto-Seeding de Datos
```bash
bash scripts/anomaly-seed.sh
# POST continuo a AI Anomaly cada 90s
# Métricas: CPU, latency, memory, error_rate, disk_io_wait
# Mantener corriendo para dashboards con datos
```

## ��� Estructura

```
deploy/demo/
├── docker-compose-demo.yml     # 15 servicios
├── .env.demo                   # Credenciales demo
├── grafana/
│   └── provisioning/
│       ├── datasources/        # Prometheus, Loki, Tempo, Alertmanager
│       └── dashboards/         # Auto-import de JSONs
├── prometheus/
│   └── prometheus.yml          # 8 scrape jobs
├── alertmanager/
│   └── alertmanager.yml        # Email templates HTML
├── loki/
│   └── config.yml              # 7d retention
├── tempo/
│   └── tempo.yml               # OTLP receivers
├── traefik/
│   ├── traefik.yml             # TLS, redirects
│   └── certs/
│       ├── key.pem             # Auto-firmados
│       └── cert.pem
├── blackbox/
│   └── blackbox.yml            # HTTP/TCP/ICMP probes
└── scripts/
    ├── anomaly-seed.sh         # Auto-seeding
    ├── smoke-test.sh           # Validación
    ├── backup.sh               # Backup + SHA256
    ├── update.sh               # Update seguro
    └── support-bundle.sh       # Diagnóstico
```

## ��� Demo vs Producción

| Aspecto | Demo | Producción |
|---------|------|------------|
| **Retención Prometheus** | 3 días, 5GB | 15 días, 10GB |
| **Retención Loki** | 7 días | 30 días |
| **Retención Tempo** | 3 días | 7 días |
| **TLS** | Auto-firmado | Let's Encrypt/Cert válido |
| **Credenciales** | admin/rhinometric_demo | Variables de entorno seguras |
| **SMTP** | Simulado (no envía) | Configurado y validado |
| **Recursos** | Sin límites | CPU/Mem limits definidos |

## ⚠️ Notas Importantes

1. **No usar en producción** - Credenciales hardcodeadas, TLS auto-firmado
2. **Datos volátiles** - Retención reducida, sin backups automáticos
3. **Auto-seeding** - Ejecutar `anomaly-seed.sh` para tener datos en dashboards AI
4. **Smoke test** - Siempre ejecutar después de cambios: `bash scripts/smoke-test.sh`

## ��� Troubleshooting

### "No data" en dashboards
```bash
# Verificar que AI Anomaly está exponiendo métricas
curl http://localhost:8085/metrics | grep rhinometric_anomaly

# Iniciar auto-seeding
bash scripts/anomaly-seed.sh &
```

### Prometheus targets DOWN
```bash
# Ver targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up")'

# Logs del servicio
docker logs rhinometric-prometheus-demo
```

### Grafana datasource error
```bash
# Verificar UID de Prometheus
curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources/uid/prometheus | jq '.'

# Debe retornar: {"name":"Prometheus", "uid":"prometheus", ...}
```

## ��� Más Información

- **Producción**: Ver `../prod/README.md`
- **OVA Build**: Ver `../../docs/ova/BUILD-OVA.md`
- **Documentación Completa**: Ver `../../docs/`
