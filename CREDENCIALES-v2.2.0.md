# 🔐 CREDENCIALES RHINOMETRIC v2.2.0

## 📋 Acceso Rápido

### 1. Grafana (Principal)
```
URL:      http://localhost:3000
Usuario:  admin
Password: rhinometric_v22  ✅ CONFIGURADO
```

**Dashboards pre-cargados:**
- 📊 Executive Overview - Para directivos
- 🖥️  Infrastructure & Containers - Monitoreo técnico
- 🌐 Applications & APIs - Rendimiento de aplicaciones
- 🌱 VeriVerde Insights - Sostenibilidad (NUEVO v2.2.0)

---

### 2. Prometheus
```
URL: http://localhost:9090
```
No requiere autenticación.

**Consultas útiles:**
- `up` - Ver servicios activos
- `rhinometric_energy_kwh` - Consumo energético
- `rhinometric_co2_emissions_kg` - Emisiones CO₂
- `rate(http_requests_total[5m])` - Request rate

---

### 3. License Management UI
```
URL: http://localhost:8092
```
No requiere autenticación (UI interna).

**Funciones:**
- Activar licencias trial (30 días)
- Gestionar licencias permanentes
- Ver estadísticas de uso

---

### 4. VeriVerde (Sostenibilidad)
```
Métricas: http://localhost:9200/metrics
Health:   http://localhost:9200/health
```

**Métricas expuestas:**
- `rhinometric_energy_kwh` - Consumo energético
- `rhinometric_room_temperature_c` - Temperatura
- `rhinometric_renewable_percent` - % Renovables
- `rhinometric_co2_emissions_kg` - Emisiones CO₂
- `rhinometric_efficiency_score` - Score eficiencia (0-100)

---

### 5. AI Anomaly Detector
```
API:    http://localhost:8085/anomalies
Health: http://localhost:8085/health
```

**Ejemplo de uso:**
```bash
curl http://localhost:8085/anomalies | jq .
```

---

## 🚀 Instalación

### Opción 1: Script Automático (Recomendado)

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto
chmod +x install-v2.2.0.sh
./install-v2.2.0.sh
```

### Opción 2: Manual

```bash
cd ~/mi-proyecto/infrastructure/mi-proyecto

# Crear directorios
mkdir -p $HOME/rhinometric_data_v2.2/{prometheus,loki,tempo,grafana,postgres,redis,alertmanager,license-server/logs,nginx/logs}
mkdir -p $HOME/rhinometric_backups

# Construir imágenes
docker build -t rhinometric-veriverde:v2.2.0 ./rhinometric-veriverde
docker build -t rhinometric-ai-anomaly:v2.2.0 ./rhinometric-ai-anomaly
docker build -t rhinometric-backup:v2.2.0 ./rhinometric-backup
docker build -t rhinometric-report:v2.2.0 ./rhinometric-report

# Iniciar
docker compose -f docker-compose-v2.2.0.yml up -d
```

---

## 🔧 Configuración de Variables

Archivo: `.env.v2.2.0`

```bash
# Base de datos
POSTGRES_PASSWORD=rhinometric_v22_secure
REDIS_PASSWORD=redis_v22_secure

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=rhinometric_v22

# SMTP (para reportes automáticos)
SMTP_PASSWORD=271211Rc$
REPORT_RECIPIENTS=tu_email@ejemplo.com

# VeriVerde (Sostenibilidad)
RENEWABLE_PERCENT=35       # España: ~35% renovable
CO2_FACTOR=0.233           # EU promedio: 0.233 kg/kWh

# Reportes
REPORT_SCHEDULE=weekly     # daily, weekly, monthly
```

---

## 🧪 Comandos de Testing

### Ver estado de servicios
```bash
docker compose -f docker-compose-v2.2.0.yml ps
```

### Ver logs en tiempo real
```bash
docker compose -f docker-compose-v2.2.0.yml logs -f
```

### Ver logs de un servicio específico
```bash
docker logs rhinometric-veriverde -f
docker logs rhinometric-ai-anomaly -f
docker logs rhinometric-report -f
```

### Verificar métricas de VeriVerde
```bash
curl http://localhost:9200/metrics
```

### Verificar anomalías detectadas
```bash
curl http://localhost:8085/anomalies | python3 -m json.tool
```

### Verificar salud de servicios
```bash
curl http://localhost:9200/health    # VeriVerde
curl http://localhost:8085/health    # AI Anomaly
curl http://localhost:9090/-/healthy # Prometheus
curl http://localhost:3000/api/health # Grafana
```

### Crear backup manual
```bash
./scripts/rmetricctl backup
```

### Listar backups
```bash
./scripts/rmetricctl list
```

---

## 📊 Primeros Pasos en Grafana

1. **Acceder a Grafana:**
   - Abrir http://localhost:3000
   - Login: `admin` / `rhinometric_v22`

2. **Ir a Dashboards:**
   - Menú lateral → Dashboards
   - Buscar carpeta "Rhinometric"
   - Verás 4 dashboards pre-cargados

3. **Probar VeriVerde Insights:**
   - Abrir "04 - VeriVerde Insights"
   - Ver métricas de sostenibilidad en tiempo real
   - Observar consumo energético, CO₂, temperatura

4. **Explorar Prometheus:**
   - Ir a http://localhost:9090
   - Escribir query: `rhinometric_energy_kwh`
   - Click en "Execute"

---

## 🛑 Detener Servicios

### Detener pero mantener datos
```bash
docker compose -f docker-compose-v2.2.0.yml stop
```

### Detener y eliminar contenedores (mantiene datos)
```bash
docker compose -f docker-compose-v2.2.0.yml down
```

### Detener y eliminar TODO (incluye datos)
```bash
docker compose -f docker-compose-v2.2.0.yml down -v
rm -rf $HOME/rhinometric_data_v2.2
```

---

## 🔄 Diferencias con v2.1.0

| Característica | v2.1.0 | v2.2.0 |
|----------------|--------|--------|
| **Dashboards** | Vacío (usuario debe crear) | 4 pre-cargados |
| **Sostenibilidad** | ❌ No | ✅ VeriVerde |
| **Backup** | Manual | ✅ Automático + CLI |
| **IA Anomalías** | ❌ No | ✅ Local ML |
| **Reportes PDF** | ❌ No | ✅ Email automático |
| **Servicios** | 16 | 20 |
| **Red Docker** | 172.21.0.0/16 | 172.22.0.0/16 |
| **Datos** | ~/rhinometric_data_v2.1 | ~/rhinometric_data_v2.2 |

---

## ⚠️  Notas Importantes

1. **Coexistencia con v2.1.0:**
   - v2.2.0 usa puertos diferentes en algunos casos
   - v2.2.0 usa red Docker diferente (172.22.x vs 172.21.x)
   - Los datos están separados (v2.1 vs v2.2)
   - **Pueden correr al mismo tiempo si hay recursos suficientes**

2. **Requisitos de recursos:**
   - CPU: ~4 vCPUs
   - RAM: ~7 GB
   - Disco: ~50 GB

3. **Puertos usados:**
   - 3000: Grafana
   - 5000: License Server
   - 8085: AI Anomaly (NUEVO)
   - 8092: License UI
   - 9090: Prometheus
   - 9200: VeriVerde (NUEVO)

---

## 🆘 Troubleshooting

### Problema: Puerto ya en uso
```bash
# Verificar qué está usando el puerto
lsof -i :3000   # o el puerto que falle

# Si es v2.1.0, detenerla primero:
cd ~/mi-proyecto/infrastructure/mi-proyecto/rhinometric-trial-v2.1.0-universal
docker compose down
```

### Problema: Grafana sin dashboards
```bash
# Verificar que los JSON existen
ls -lh grafana/provisioning/dashboards/json/0*.json

# Reiniciar Grafana
docker restart rhinometric-grafana
```

### Problema: VeriVerde no muestra métricas
```bash
# Ver logs
docker logs rhinometric-veriverde

# Verificar health
curl http://localhost:9200/health
```

### Problema: Backup falla
```bash
# Verificar permisos
ls -la $HOME/rhinometric_data_v2.2/

# Corregir ownership
sudo chown -R $(whoami):$(whoami) $HOME/rhinometric_data_v2.2/
```

---

## 📞 Soporte

- **Email:** rafael.canelon@rhinometric.com
- **GitHub:** https://github.com/Rafael2712/rhinometric-overview
- **Documentación:** Ver `README-v2.2.0.md`

---

## 🎯 Quick Test Checklist

Después de instalar, verifica:

- [ ] Grafana accesible en http://localhost:3000
- [ ] Login exitoso con `admin` / `rhinometric_v22`
- [ ] 4 dashboards visibles en carpeta "Rhinometric"
- [ ] VeriVerde métricas en http://localhost:9200/metrics
- [ ] Prometheus accesible en http://localhost:9090
- [ ] Query `up` muestra ~20 servicios
- [ ] AI Anomaly API responde en http://localhost:8085/health
- [ ] License UI accesible en http://localhost:8092

---

**RHINOMETRIC v2.2.0 Enterprise Edition**  
© 2025 Rafael Canelón  
100% On-Premise | GDPR Compliant | ENS Compatible
