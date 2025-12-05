# ❓ FAQ Rhinometric

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025

---

## 📋 Preguntas Generales

### **1. ¿Qué es Rhinometric?**

Rhinometric es una plataforma de observabilidad on-premise que unifica monitoreo (Prometheus), logs (Loki), traces (Jaeger), y detección de anomalías con IA, todo accesible desde una única Console web.

---

### **2. ¿Qué diferencia tiene Rhinometric frente a usar solo Grafana + Prometheus + Loki + Jaeger?**

| **Aspecto** | **Rhinometric** | **Stack manual** |
|-------------|----------------|------------------|
| **Configuración inicial** | 5 minutos (1 comando) | 2-3 días |
| **Console unificada** | Sí (1 interfaz) | No (4 URLs distintas) |
| **Detección de anomalías con IA** | ✅ Incluida | ❌ Hay que programarla |
| **Dashboards pre-configurados** | ✅ 8 dashboards listos | ❌ Hay que crearlos |
| **Gestión de licencias** | ✅ Incluida | ❌ No existe |
| **Alertas inteligentes** | ✅ IA + reglas | Solo reglas manuales |
| **Soporte comercial** | ✅ Disponible | No existe |

**Resumen:** Rhinometric es "stack manual + Console + IA + configuración", listo para producción en minutos.

---

### **3. ¿Puedo usarlo en la nube o sólo on-premise?**

**Versión actual (v2.5.1):** Solo on-premise (instalación local con Docker).

**Próximas versiones:**
- Cloud (AWS, Azure, GCP) - Roadmap 2026
- SaaS multi-tenant - Roadmap 2026

---

### **4. ¿Necesito conocimientos de Prometheus/Grafana para usar Rhinometric?**

**NO es obligatorio**, pero sí recomendado:

- **Para uso básico:** NO (Console es auto-explicativa)
- **Para configuración avanzada:** SÍ
  - Crear nuevos dashboards en Grafana
  - Modificar reglas de alertas en Prometheus
  - Agregar nuevos exporters

**Recomendación:** Usuario básico puede operar la Console sin problemas. Admin necesita conocer stack.

---

### **5. ¿Qué idiomas soporta Rhinometric?**

- **Console UI:** Solo inglés (v2.5.1)
- **Documentación:** Español (docs/) + Inglés (README.md)
- **Próximas versiones:** Soporte multi-idioma en roadmap

---

## 🏗️ Instalación y Arquitectura

### **6. ¿Qué requisitos mínimos necesito?**

**Hardware:**
- CPU: 4 vCPU
- RAM: 8 GB
- Disco: 50 GB

**Software:**
- Ubuntu 22.04+ / Rocky Linux 8+
- Docker >= 24.0
- Docker Compose >= 2.20

**Red:**
- Puertos 3000-9999 disponibles (ver [ARQUITECTURA_TECNICA.md](./ARQUITECTURA_TECNICA.md))

---

### **7. ¿Funciona en Windows / macOS?**

**Sí**, pero con limitaciones:

- **Windows:**
  - Requiere WSL2 (Windows Subsystem for Linux)
  - Docker Desktop instalado
  - Rendimiento 10-15% menor que Linux nativo

- **macOS:**
  - Docker Desktop instalado
  - Arquitectura ARM (M1/M2/M3) soportada
  - Rendimiento comparable a Linux

**Recomendación:** Para producción, usa Linux (Ubuntu/Rocky).

---

### **8. ¿Puedo instalar Rhinometric en Kubernetes?**

**NO directamente** en versión actual (v2.5.1).

**Próximas versiones:**
- Helm Charts para K8s - Roadmap Q1 2026
- Operador Kubernetes - Roadmap Q2 2026

**Workaround actual:** Usar Docker Compose en nodo de K8s (no recomendado para producción).

---

### **9. ¿Cuánto espacio en disco consume Rhinometric?**

Depende de:
- **Número de hosts monitorizados**
- **Retención de logs (Loki):** Por defecto 7 días
- **Retención de métricas (Prometheus):** Por defecto 15 días
- **Retención de traces (Jaeger):** Por defecto 3 días

**Ejemplo:**
- **10 hosts, retención por defecto:** ~20 GB/semana
- **50 hosts, retención por defecto:** ~150 GB/semana
- **100 hosts, retención 30 días:** ~800 GB/mes

**Configurar retención en:** `.env` (variables `PROMETHEUS_RETENTION`, `LOKI_RETENTION`)

---

### **10. ¿Puedo monitorear servicios externos (no Docker)?**

**SÍ**, mediante exporters:

1. **Instalar exporter en host externo:**
   ```bash
   # Node Exporter (Linux)
   wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
   tar xvfz node_exporter-*.tar.gz
   cd node_exporter-*/
   ./node_exporter &
   ```

2. **Agregar target en Prometheus:**
   - Editar `config/prometheus.yml`
   - Agregar en `scrape_configs`:
     ```yaml
     - job_name: 'external_host'
       static_configs:
         - targets: ['192.168.1.100:9100']
     ```

3. **Reiniciar Prometheus:**
   ```bash
   docker restart rhinometric-prometheus
   ```

**Limitación:** No hay UI en Console para agregar targets (hay que editar YAML manualmente).

---

## 🤖 IA y Anomalías

### **11. ¿Cómo funciona el AI Anomaly Engine?**

**Modelos ML usados:**
- **Isolation Forest:** Detección de outliers
- **LSTM (Long Short-Term Memory):** Predicción de series temporales
- **Z-Score:** Detección estadística básica

**Pipeline:**
1. Prometheus exporta métricas
2. AI Engine las consume cada 5 minutos
3. Compara valor actual vs. baseline (histórico 7 días)
4. Si desviación > umbral → genera anomalía
5. Anomalía aparece en Console

---

### **12. ¿El AI Engine puede "inventar" anomalías que no existen?**

**NO inventa datos**, pero SÍ puede generar falsos positivos:

- **Falso positivo:** Detecta anomalía cuando comportamiento es normal (ej: deploy programado que aumenta CPU)
- **Falso negativo:** NO detecta anomalía cuando sí existe (ej: problema muy sutil)

**Cómo reducir falsos positivos:**
- Aumentar umbral de desviación (editar `config/ai-anomaly-config.yml`)
- Excluir métricas ruidosas (ej: `node_network_transmit_bytes`)

---

### **13. ¿Qué pasa si el AI Engine falla?**

**Impacto:**
- ❌ NO se detectan anomalías nuevas
- ✅ Alertas normales (Alertmanager) siguen funcionando
- ✅ Dashboards, logs, traces NO se afectan

**Cómo detectar fallo:**
- Home → "AI Anomaly Engine" = DOWN
- Logs: `docker logs rhinometric-ai-anomaly`

**Cómo reiniciar:**
```bash
docker restart rhinometric-ai-anomaly
```

---

### **14. ¿Puedo entrenar el AI Engine con mis propios datos?**

**NO directamente** en v2.5.1.

**Próximas versiones:**
- UI para ajustar umbral de desviación
- Opción "Feedback" para marcar falsos positivos
- Re-entrenamiento automático con feedback

**Workaround actual:** Editar `config/ai-anomaly-config.yml` manualmente.

---

## 🚨 Alertas y Notificaciones

### **15. ¿Las alertas envían notificaciones a Slack / Email / PagerDuty?**

**NO directamente** en v2.5.1.

**Estado actual:**
- Alertas se muestran solo en Console UI
- Alertmanager está instalado pero sin integración configurada

**Próximas versiones:**
- UI para configurar webhooks (Slack, Email, PagerDuty)
- Templates predefinidos
- Roadmap: Q1 2026

**Workaround actual:**
- Configurar manualmente en `config/alertmanager.yml`
- Ver [Alertmanager docs](https://prometheus.io/docs/alerting/latest/configuration/)

---

### **16. ¿Cómo evito alert fatigue (demasiadas alertas)?**

**Causas comunes:**
1. Umbrales muy sensibles
2. Alertas sin periodo de "for" (se disparan instantáneamente)
3. Servicios ruidosos (ej: Redis con muchos restarts)

**Soluciones:**
1. **Ajustar umbrales:**
   - Editar `config/rules/alerts.yml`
   - Ejemplo: Cambiar `expr: up == 0` → `expr: up == 0 for 2m` (espera 2 minutos antes de alertar)

2. **Silenciar alertas temporales:**
   - Ir a Alertmanager (`http://<IP>:9093`)
   - Click en "Silence" → configurar duración

3. **Agrupar alertas:**
   - Configurar `group_by` en `alertmanager.yml`

---

### **17. ¿Qué diferencia hay entre Anomalías y Alertas?**

| **Criterio** | **Anomalías (AI)** | **Alertas (Rules)** |
|--------------|-------------------|---------------------|
| **Origen** | Machine Learning | Reglas YAML manuales |
| **Objetivo** | Detectar lo raro | Notificar lo crítico |
| **Sensibilidad** | Alta (muchos falsos +) | Baja (pocos falsos +) |
| **Uso** | Investigación proactiva | Respuesta reactiva |
| **Ejemplo** | CPU +20% sobre baseline | PostgreSQL caído |

**Recomendación:** Usar ambas. Anomalías para descubrir problemas nuevos, Alertas para problemas conocidos.

---

## 📊 Dashboards y Métricas

### **18. ¿Puedo crear mis propios dashboards?**

**SÍ**, pero fuera de Console:

1. Abrir Grafana nativo: `http://<IP>:3000`
2. Login: `admin / admin`
3. Click en "+" → "Create Dashboard"
4. Agregar paneles, queries, etc.
5. Guardar

**Limitación:** No se pueden crear desde Console UI (próxima versión).

---

### **19. ¿Puedo editar dashboards existentes?**

**SÍ**, en Grafana nativo:

1. Console → Dashboards → Click en dashboard
2. Click en "Open in Grafana" (botón superior derecho)
3. Editar en Grafana
4. Cambios se reflejan automáticamente en Console

---

### **20. ¿Qué métricas están disponibles por defecto?**

**Métricas de sistema (Node Exporter):**
- CPU: `node_cpu_seconds_total`, `node_load1`, `node_load5`
- RAM: `node_memory_MemAvailable_bytes`, `node_memory_MemTotal_bytes`
- Disco: `node_filesystem_avail_bytes`, `node_disk_io_time_seconds_total`
- Red: `node_network_receive_bytes_total`, `node_network_transmit_bytes_total`

**Métricas de Docker (cAdvisor):**
- CPU por contenedor: `container_cpu_usage_seconds_total`
- RAM por contenedor: `container_memory_usage_bytes`
- Red por contenedor: `container_network_receive_bytes_total`

**Métricas de PostgreSQL (Postgres Exporter):**
- Conexiones: `pg_stat_database_numbackends`
- Queries: `pg_stat_database_xact_commit`, `pg_stat_database_xact_rollback`

**Métricas custom:**
- Ver [Prometheus exporters](https://prometheus.io/docs/instrumenting/exporters/)

---

## 🔐 Licencias y Seguridad

### **21. ¿Qué limita mi licencia?**

**Versión actual (v2.5.1):** Sistema de licencias NO implementado (todo funciona sin restricciones).

**Próximas versiones (v2.6.0+):**
- **Trial (15 días):** Todas las funciones, máx. 10 hosts
- **Annual:** Renovación anual, máx. 50 hosts
- **Perpetual:** Sin renovación, máx. 100 hosts
- **Enterprise:** Sin límites, soporte 24/7

**¿Qué pasa al vencer licencia?**
- Console muestra banner "License expired"
- Funciones básicas siguen funcionando (read-only)
- AI Engine se desactiva
- No se pueden agregar nuevos hosts

---

### **22. ¿Rhinometric envía datos a la nube?**

**NO**. Rhinometric es 100% on-premise:

- ✅ Todas las métricas, logs, traces se quedan en tu servidor
- ✅ NO hay telemetría enviada a servidores externos
- ✅ NO hay "phone home"

**Única excepción:**
- Validación de licencia (próxima versión)
- Se envía SOLO: License Key + Timestamp
- NO se envían métricas, logs, ni datos sensibles

---

### **23. ¿Cómo cambio las contraseñas por defecto?**

**Console:**
1. Login con `admin / admin`
2. Home → Settings → "Change Password"

**Grafana:**
```bash
docker exec -it rhinometric-grafana grafana-cli admin reset-admin-password <NEW_PASSWORD>
```

**PostgreSQL:**
```bash
docker exec -it rhinometric-postgres psql -U rhinometric -c "ALTER USER rhinometric WITH PASSWORD 'NEW_PASSWORD';"
```

**Redis:**
- Editar `.env` → `REDIS_PASSWORD=nueva_contraseña`
- `docker-compose up -d --force-recreate rhinometric-redis`

---

### **24. ¿Puedo habilitar HTTPS en Console?**

**SÍ**, usando nginx reverse proxy:

1. **Instalar nginx:**
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   ```

2. **Configurar nginx:**
   ```nginx
   server {
       server_name rhinometric.tudominio.com;
       location / {
           proxy_pass http://localhost:3002;
           proxy_set_header Host $host;
       }
   }
   ```

3. **Obtener certificado SSL:**
   ```bash
   sudo certbot --nginx -d rhinometric.tudominio.com
   ```

4. **Acceder:** `https://rhinometric.tudominio.com`

---

## 🐛 Troubleshooting

### **25. ¿Qué hago si la Console muestra "API Error"?**

**Causas:**
1. Backend caído
2. Prometheus caído
3. Red entre containers rota

**Diagnóstico:**
```bash
# 1. Verificar containers
docker ps | grep rhinometric

# 2. Ver logs de backend
docker logs rhinometric-console-backend --tail 50

# 3. Verificar conexión a Prometheus
docker exec -it rhinometric-console-backend curl http://prometheus:9090/-/healthy
```

**Solución:**
```bash
# Reiniciar backend
docker restart rhinometric-console-backend

# Si persiste, reiniciar todo
docker-compose restart
```

---

### **26. ¿Por qué no veo logs en Console?**

**Causas:**
1. Loki caído
2. Promtail no está enviando logs
3. Filtro de tiempo incorrecto

**Diagnóstico:**
```bash
# 1. Verificar Loki
docker logs rhinometric-loki --tail 50

# 2. Verificar Promtail
docker logs rhinometric-promtail --tail 50

# 3. Query manual a Loki
curl -G http://localhost:3100/loki/api/v1/query --data-urlencode 'query={job="varlogs"}'
```

**Solución:**
```bash
docker restart rhinometric-loki rhinometric-promtail
```

---

### **27. ¿Por qué no veo traces en Jaeger?**

**Causas:**
1. Servicio NO instrumentado con OpenTelemetry
2. Jaeger caído
3. Firewall bloqueando puerto 14268

**Diagnóstico:**
```bash
# 1. Verificar Jaeger
curl http://localhost:16686

# 2. Ver logs
docker logs rhinometric-jaeger --tail 50
```

**Solución:**
- Si servicio no instrumentado: Ver [OpenTelemetry docs](https://opentelemetry.io/docs/)
- Si Jaeger caído: `docker restart rhinometric-jaeger`

---

### **28. ¿Cómo obtengo soporte técnico?**

**Recursos gratuitos:**
- **Documentación:** `docs/` en este repositorio
- **GitHub Issues:** https://github.com/rhinometric/rhinometric/issues (si proyecto es público)

**Soporte comercial (próximamente):**
- **Email:** soporte@rhinometric.com
- **SLA:** 4h (Critical), 24h (High), 48h (Medium)
- **Disponible con:** Licencias Annual, Perpetual, Enterprise

---

## 📈 Escalabilidad y Performance

### **29. ¿Cuántos hosts puedo monitorear con Rhinometric?**

**Límites técnicos (hardware estándar: 8vCPU, 16GB RAM):**
- **10-50 hosts:** Sin problemas
- **50-200 hosts:** Ajustar retención (reducir a 7 días métricas, 3 días logs)
- **200-500 hosts:** Requiere cluster (múltiples instancias Prometheus/Loki)
- **>500 hosts:** Contactar soporte para arquitectura enterprise

---

### **30. ¿Puedo hacer alta disponibilidad (HA)?**

**NO nativamente** en v2.5.1.

**Próximas versiones (Enterprise):**
- Prometheus HA (múltiples replicas)
- Loki HA (backend S3)
- Console HA (load balancer)

**Workaround actual:**
- Backup diario con `docker-compose` volumes
- Plan de recuperación ante desastres

---

**Para más preguntas, ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) o contactar soporte.**

---

**© 2025 Rhinometric - FAQ Completo**
