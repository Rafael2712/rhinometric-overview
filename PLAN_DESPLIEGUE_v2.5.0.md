# 🚀 Plan de Despliegue Rhinometric v2.5.0

**IMPORTANTE:** Este plan es para CUANDO decidas migrar de v2.1.0 a v2.5.0.
**Estado actual:** v2.1.0 en producción, v2.5.0 preparado pero NO desplegado.

---

## FASE 1: Staging - Probar v2.5.0 sin afectar producción

### 1.1 Preparar entorno de staging

**Opción A: Nuevo servidor (RECOMENDADO)**
```bash
# Crear servidor staging en AWS Lightsail
# Especificaciones: 8 GB RAM, 4 vCPU, 160 GB SSD
# Costo: ~$40/mes

# Acceso SSH
ssh -i lightsail-staging.pem ubuntu@<IP_STAGING>
```

**Opción B: Mismo servidor, puertos diferentes (NO RECOMENDADO - poca RAM)**
```bash
# Modificar docker-compose-v2.5.0.yml para usar:
# Grafana: 3001 (en vez de 3000)
# Prometheus: 9091 (en vez de 9090)
# License Server: 5001 (en vez de 5000)
# etc.
```

### 1.2 Desplegar stack v2.5.0 en staging

```bash
# 1. Clonar repositorio
git clone https://github.com/Rafael2712/mi-proyecto.git
cd mi-proyecto/infrastructure/mi-proyecto

# 2. Configurar .env para staging
cp .env.example .env.staging
nano .env.staging

# Configurar:
# - ZOHO_PASSWORD
# - DATABASE_URL
# - REDIS_URL
# - Puertos si es mismo servidor

# 3. Desplegar v2.5.0
docker compose -f docker-compose-v2.5.0.yml --env-file .env.staging up -d

# 4. Verificar servicios
docker compose -f docker-compose-v2.5.0.yml ps
```

### 1.3 Checklist de validación staging

```bash
# Sistema básico
□ Todos los contenedores UP
  docker compose -f docker-compose-v2.5.0.yml ps

□ Grafana accesible
  curl -I http://<IP_STAGING>:3000

□ Prometheus scrapeando targets
  curl http://<IP_STAGING>:9090/api/v1/targets | jq '.data.activeTargets[].health'

□ Loki recibiendo logs
  curl http://<IP_STAGING>:3100/ready

# Jaeger (nuevo en v2.5.0)
□ Jaeger UI accesible
  curl -I http://<IP_STAGING>:16686

□ Jaeger recibiendo trazas
  # Generar traza de prueba
  curl http://<IP_STAGING>:14268/api/traces

# License Server v2
□ API docs accesibles
  curl http://<IP_STAGING>:5000/api/docs

□ Crear licencia de prueba
  curl -X POST http://<IP_STAGING>:5000/api/admin/licenses \
    -H "Content-Type: application/json" \
    -d '{
      "customer_name": "Test Staging",
      "client_email": "test@rhinometric.com",
      "client_company": "Test Corp",
      "license_type": "trial"
    }'

□ Email recibido correctamente

□ Enlaces de descarga funcionan
  # Clic en enlaces del email

# License UI (si existe en v2.5.0)
□ UI accesible
  curl -I http://<IP_STAGING>:8092

□ Crear licencia desde UI
□ Ver lista de licencias

# Console v3 (si existe en v2.5.0)
□ Console accesible
  curl -I http://<IP_STAGING>:8080

□ Login funciona
□ Dashboards cargan

# AI Anomaly Engine (si existe en v2.5.0)
□ Servicio arrancado
  docker compose -f docker-compose-v2.5.0.yml logs ai-anomaly-engine

□ Detecta anomalías de prueba
```

---

## FASE 2: Test End-to-End en Staging

### 2.1 Escenario completo de Trial

```bash
# PASO 1: Cliente solicita trial desde rhinometric.com
# (En staging, hacerlo manual vía API)

curl -X POST http://<IP_STAGING>:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Empresa Demo",
    "client_email": "tu-email-real@gmail.com",
    "client_company": "Demo SA",
    "license_type": "trial"
  }'

# PASO 2: Verificar email recibido
# - Asunto: "Licencia Rhinometric Trial"
# - Contiene: LICENSE_KEY
# - Enlaces: Instalador, Manual, Guía

# PASO 3: Descargar instalador desde enlace del email
wget <LINK_INSTALADOR_DEL_EMAIL>

# PASO 4: Instalar en máquina de prueba
chmod +x install-rhinometric.sh
./install-rhinometric.sh

# PASO 5: Configurar licencia descargada
# (El archivo .lic viene adjunto en el email)
cp RHINO-TRIAL-*.lic /ruta/rhinometric/

# PASO 6: Arrancar stack del cliente
cd /ruta/rhinometric
docker compose up -d

# PASO 7: Verificar que licencia se reporta como activa
# (En el License Server de staging)
curl http://<IP_STAGING>:5000/api/admin/licenses | jq '.[] | select(.status=="active")'

# PASO 8: Ver dashboards de Grafana del cliente
# Acceder a http://localhost:3000
# Usuario: admin / admin

# PASO 9: Verificar que métricas del host aparecen en staging
# (Si existe dashboard de "Hosts Monitoreados")
```

### 2.2 Escenario de Annual License

```bash
# Similar al Trial pero con license_type="annual"

curl -X POST http://<IP_STAGING>:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Cliente Premium",
    "client_email": "premium@empresa.com",
    "client_company": "Premium Corp",
    "license_type": "annual"
  }'

# Verificar:
# - Email recibido
# - Licencia válida por 365 días
# - Puede monitorear hasta 30 hosts (según plan)
```

### 2.3 Pruebas de carga

```bash
# Simular 10 hosts reportando métricas
for i in {1..10}; do
  docker run -d --name node-exporter-test-$i \
    -p 910$i:9100 \
    prom/node-exporter
done

# Configurar Prometheus para scrapear los 10 hosts de prueba

# Verificar:
# - CPU/RAM del servidor staging
# - Latencia de Grafana
# - Prometheus no se queda atrás en scraping
```

---

## FASE 3: Plan de Migración Producción v2.1.0 → v2.5.0

### 3.1 Pre-migración (1 día antes)

```bash
# 1. Backup completo de v2.1.0
ssh ubuntu@54.197.192.198

cd /home/ubuntu/license-server

# Backup base de datos
docker compose exec postgres pg_dump -U rhinometric rhinometric_trial > backup-v2.1.0-$(date +%Y%m%d).sql

# Backup volúmenes
tar -czf volumes-backup-v2.1.0-$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/

# Copiar backups a máquina local
scp ubuntu@54.197.192.198:/home/ubuntu/license-server/backup-*.sql ./
scp ubuntu@54.197.192.198:/home/ubuntu/license-server/volumes-backup-*.tar.gz ./

# 2. Documentar estado actual
docker compose ps > estado-pre-migracion.txt
curl http://54.197.192.198:5000/api/admin/licenses > licencias-pre-migracion.json

# 3. Notificar a clientes (si hay activos)
# Email: "Mantenimiento programado 19 de diciembre, 22:00-02:00 UTC"
```

### 3.2 Migración (ventana de 4 horas)

```bash
# HORA 00:00 - Detener v2.1.0

ssh ubuntu@54.197.192.198
cd /home/ubuntu/license-server

# Detener servicios
docker compose down

# HORA 00:15 - Desplegar v2.5.0

# Clonar repo actualizado (o git pull)
git pull origin main

# Copiar .env
cp .env .env.v2.1.0.backup
# Actualizar .env con variables nuevas de v2.5.0

# Migrar base de datos (si hay cambios de schema)
# (Ejecutar scripts de migración si existen)

# Arrancar v2.5.0
docker compose -f docker-compose-v2.5.0.yml up -d

# HORA 00:30 - Validación

# Verificar todos los servicios UP
docker compose -f docker-compose-v2.5.0.yml ps

# Prueba de humo
curl http://54.197.192.198:5000/api/health
curl http://54.197.192.198:3000/api/health

# Verificar licencias migradas
curl http://54.197.192.198:5000/api/admin/licenses

# Crear licencia de prueba
curl -X POST http://54.197.192.198:5000/api/admin/licenses \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Post-Migracion",
    "client_email": "test@rhinometric.com",
    "client_company": "Test",
    "license_type": "trial"
  }'

# HORA 01:00 - Pruebas completas

# Test de dashboards
# Test de alertas
# Test de Jaeger (nuevo)
# Test de License UI (si existe)

# HORA 02:00 - Go/No-Go

# ✅ TODO OK → Notificar clientes "Migración exitosa"
# ❌ PROBLEMAS → Rollback (ver Fase 3.3)
```

### 3.3 Plan de Rollback

```bash
# Si v2.5.0 falla, volver a v2.1.0

# 1. Detener v2.5.0
docker compose -f docker-compose-v2.5.0.yml down

# 2. Restaurar backup de base de datos
docker compose up -d postgres
docker compose exec postgres psql -U rhinometric -d rhinometric_trial < backup-v2.1.0-YYYYMMDD.sql

# 3. Restaurar volúmenes (si es necesario)
tar -xzf volumes-backup-v2.1.0-YYYYMMDD.tar.gz -C /

# 4. Arrancar v2.1.0
docker compose up -d

# 5. Verificar
docker compose ps
curl http://54.197.192.198:5000/api/health

# 6. Notificar clientes
# "Migración pospuesta, servicio restaurado"
```

---

## FASE 4: Post-Migración

### 4.1 Monitoreo primeras 48 horas

```bash
# Logs en tiempo real
docker compose -f docker-compose-v2.5.0.yml logs -f

# Métricas de recursos
docker stats

# Verificar alertas
curl http://54.197.192.198:9093/api/v1/alerts

# Dashboard de salud del sistema
# http://54.197.192.198:3000/d/system-overview
```

### 4.2 Actualizar documentación

```markdown
# Tareas post-migración:

- [ ] Actualizar rhinometric.com con "Versión 2.5.0"
- [ ] Actualizar Manual de Usuario a v2.5.0
- [ ] Actualizar Release Notes
- [ ] Crear anuncio de nuevas características
- [ ] Actualizar enlaces de descarga
- [ ] Enviar newsletter a usuarios existentes
```

### 4.3 Limpiar v2.1.0

```bash
# Después de 1 semana sin problemas:

# Eliminar backups antiguos de v2.1.0
rm backup-v2.1.0-*.sql
rm volumes-backup-v2.1.0-*.tar.gz

# Archivar docker-compose v2.1.0
mv docker-compose.yml docker-compose-v2.1.0.yml.archived

# Actualizar .env a versión final de v2.5.0
```

---

## FASE 5: Documentación Sincronizada

### 5.1 Documentos a crear para v2.5.0

```markdown
1. **Manual de Usuario v2.5.0**
   - Instalación con OVA
   - Instalación Linux avanzada
   - Acceso a Console v3
   - Uso de Jaeger (no Tempo)
   - License UI (si existe)
   - AI Anomaly Engine (si existe)

2. **Manual Técnico v2.5.0**
   - Arquitectura completa
   - docker-compose-v2.5.0.yml explicado
   - Requisitos de hardware REALES
   - Troubleshooting avanzado
   - Backup y restore
   - Escalado horizontal

3. **Release Notes v2.5.0**
   - Novedades vs v2.1.0
   - Breaking changes
   - Guía de migración
   - Deprecaciones

4. **Resumen Ejecutivo v2.5.0**
   - Características REALES de v2.5.0
   - Comparación v2.1.0 vs v2.5.0
   - ROI y casos de uso
   - Pricing actualizado
```

### 5.2 Archivos a marcar como legacy

```bash
# Renombrar documentos v2.1.0 para que no confundan:

mv docs/manual_usuario.md docs/manual_usuario_v2.1.0_legacy.md
mv docs/resumen_ejecutivo.md docs/resumen_ejecutivo_v2.1.0_legacy.md

# Agregar header en cada uno:
# "⚠️ Este documento aplica a Rhinometric v2.1.0 (versión legacy).
#  Para la versión actual v2.5.0, ver: [enlace]"
```

---

## 🎯 Resumen del Plan

### Estado Actual:
- ✅ v2.1.0 en producción (54.197.192.198)
- 🚧 v2.5.0 preparado pero NO desplegado

### Roadmap:

**Semana 1-2:** Staging de v2.5.0
- Montar servidor staging o usar puertos alternativos
- Desplegar docker-compose-v2.5.0.yml
- Tests E2E completos

**Semana 3:** Preparación migración
- Backups v2.1.0
- Runbook de migración
- Plan de rollback
- Notificar clientes

**Semana 4:** Migración v2.1.0 → v2.5.0
- Ventana de mantenimiento (4 horas)
- Despliegue v2.5.0
- Validación completa
- Monitoreo 48h

**Semana 5:** Documentación v2.5.0
- Manual de usuario actualizado
- Manual técnico completo
- Release notes publicadas
- Anuncio comercial

### Criterios de Éxito:
- ✅ Cero pérdida de datos (licencias migradas)
- ✅ Downtime < 4 horas
- ✅ Sin degradación de performance
- ✅ Todas las funcionalidades v2.1.0 + nuevas de v2.5.0 operativas
- ✅ Documentación completa y honesta

### Go/No-Go:
- **GO:** Si staging funciona 100% durante 1 semana
- **NO-GO:** Si hay cualquier funcionalidad rota en staging
