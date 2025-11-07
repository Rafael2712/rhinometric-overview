# Rhinometric v2.5.0 - E2E Test Plan

Plan de verificación end-to-end para validar que v2.5.0 está listo para producción y demo.

## ��� Objetivos

- ✅ Validar `deploy/prod/` para go-live
- ✅ Validar `deploy/demo/` para OVA appliance
- ✅ Confirmar Dashboard Builder UI funcional
- ✅ Verificar AI Anomaly con datos visibles
- ✅ Comprobar scripts operacionales (smoke-test, backup, etc.)

## ��� Pre-requisitos

- Docker 20.10+ y Docker Compose v2
- Git con repo clonado: `git clone https://github.com/Rafael2712/mi-proyecto.git`
- Puertos libres: 80, 443, 3000, 8001, 8085, 9090, etc.
- Mínimo 4GB RAM libre y 10GB disco

---

## ��� Test Suite 1: Deploy/Demo (OVA Appliance)

### Test 1.1: Stack Initialization
```bash
cd deploy/demo

# 1. Generar certificados TLS
cd traefik/certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/C=US/ST=Demo/L=Demo/O=Rhinometric/CN=rhinometric-demo.local"
cd ../..

# 2. Levantar stack
docker compose -f docker-compose-demo.yml up -d

# 3. Esperar ~30s para healthchecks
sleep 30

# 4. Verificar containers
docker compose -f docker-compose-demo.yml ps
```

**Criterio Aceptación:**
- ✅ 15 contenedores corriendo
- ✅ Todos en estado `healthy` o `running`
- ⏱️ Inicio en <2 minutos

---

### Test 1.2: Smoke Test Execution
```bash
cd deploy/demo
bash scripts/smoke-test.sh
```

**Criterio Aceptación:**
- ✅ Exit code 0
- ✅ 8/8 checks PASSED:
  1. Containers healthy
  2. HTTP endpoints (Grafana, Prometheus, Loki, AI)
  3. Prometheus targets ALL UP
  4. Grafana datasource "prometheus" (UID)
  5. AI metrics `rhinometric_anomaly*` presentes
  6. Disk usage <80%
  7. Volúmenes creados
  8. Network rhinometric activa

**Output Esperado:**
```
✓ Smoke test PASSED - Stack funcional
```

---

### Test 1.3: Grafana Access & Datasources
```bash
# 1. Login Grafana
curl -u admin:rhinometric_demo http://localhost:3000/api/health

# 2. Verificar datasource Prometheus
curl -s -u admin:rhinometric_demo \
  http://localhost:3000/api/datasources/uid/prometheus | jq '.'

# 3. Listar dashboards provisionados
curl -s -u admin:rhinometric_demo \
  http://localhost:3000/api/search?type=dash-db | jq '.[] | {title, uid}'
```

**Criterio Aceptación:**
- ✅ Health check retorna `{"database":"ok"}`
- ✅ Datasource Prometheus existe con UID "prometheus"
- ✅ 3 dashboards presentes:
  - `rhinometric-ai-anomaly`
  - `rhinometric-system-overview`
  - `rhinometric-app-performance`

**GUI Manual:**
1. Abrir http://localhost:3000 (admin/rhinometric_demo)
2. Navegar a Configuration → Data Sources
3. Confirmar: Prometheus (default), Loki, Tempo, Alertmanager

---

### Test 1.4: AI Anomaly Detection with Data
```bash
# 1. Iniciar auto-seeding en background
cd deploy/demo
bash scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &
SEED_PID=$!

# 2. Esperar 2 minutos para métricas
sleep 120

# 3. Verificar métricas AI en Prometheus
curl -s http://localhost:9090/api/v1/query?query=rhinometric_anomaly_detections_total | jq '.data.result'

# 4. Parar seeding
kill $SEED_PID
```

**Criterio Aceptación:**
- ✅ Query retorna valores >0
- ✅ Métricas presentes:
  - `rhinometric_anomaly_detections_total`
  - `rhinometric_anomaly_active_count`
  - `rhinometric_anomaly_models_trained`

**GUI Manual:**
1. Abrir http://localhost:3000/d/rhinometric-ai-anomaly
2. Panel "Anomalías Detectadas (24h)" muestra valor >0 (no "No data")
3. Gráfico "Detecciones en Tiempo Real" muestra curvas

---

### Test 1.5: Dashboard Builder UI
```bash
# 1. Verificar backend
curl http://localhost:8001/health
curl http://localhost:8001/templates

# 2. Crear dashboard vía API
curl -X POST http://localhost:8001/create \
  -H "Content-Type: application/json" \
  -d '{"template":"ai-anomaly","title":"Test E2E Dashboard"}'

# Output esperado:
# {"success":true,"url":"http://localhost:3000/d/...","uid":"..."}
```

**GUI Manual:**
1. Abrir http://localhost:3001 (Dashboard Builder UI)
2. Seleccionar template "AI Anomaly Detection"
3. Título: "Mi Dashboard E2E"
4. Click "Crear en Grafana"
5. Verifica: Alert verde + link "Abrir en Grafana →"
6. Click link → debe abrir dashboard en Grafana con datos

**Criterio Aceptación:**
- ✅ Backend responde `/health` y `/templates`
- ✅ POST `/create` retorna `success: true` y URL válida
- ✅ UI carga sin errores en DevTools Console
- ✅ Dashboard creado aparece en Grafana con datos

---

### Test 1.6: Operational Scripts

#### Backup
```bash
cd deploy/demo
bash scripts/backup.sh

# Verificar archivos
ls -lh backups/*_$(date +%Y%m%d)*.tar.gz
ls -lh backups/*.sha256
```

**Criterio Aceptación:**
- ✅ 4 tar.gz creados (grafana-data, prometheus-data, loki-data, postgres-data)
- ✅ 4 archivos .sha256 con checksums
- ✅ Exit code 0

#### Update
```bash
cd deploy/demo
bash scripts/update.sh
```

**Criterio Aceptación:**
- ✅ Backup ejecutado
- ✅ Images pulled
- ✅ Services restarted
- ✅ Smoke test ejecutado y PASSED

#### Support Bundle
```bash
cd deploy/demo
bash scripts/support-bundle.sh

# Verificar bundle
tar -tzf support-bundle-*.tar.gz | head -20
```

**Criterio Aceptación:**
- ✅ Tar.gz creado con timestamp
- ✅ Contiene: logs (15 archivos), configs, docker info, health checks
- ✅ Tamaño >500KB

---

### Test 1.7: Resource Usage & Performance
```bash
# Verificar consumo de recursos
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Disk usage
docker system df
```

**Criterio Aceptación:**
- ✅ Suma CPU <80% (depende de hardware)
- ✅ Suma Memory <4GB
- ✅ Disk usage <10GB

---

## ��� Test Suite 2: Deploy/Prod (Production Readiness)

### Test 2.1: Configuration Validation
```bash
cd deploy/prod

# 1. Copiar environment template
cp .env.prod.example .env.prod

# 2. Editar variables críticas
nano .env.prod
# DOMAIN=rhinometric.example.com
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=alerts@example.com
# SMTP_PASSWORD=...
# JWT_SECRET=$(openssl rand -hex 32)
# POSTGRES_PASSWORD=$(openssl rand -hex 16)

# 3. Validar sintaxis docker-compose
docker compose -f docker-compose-prod.yml config > /dev/null
```

**Criterio Aceptación:**
- ✅ `.env.prod` con todas las variables requeridas
- ✅ No errores en `docker compose config`

---

### Test 2.2: Smoke Test (Pre-deployment)
```bash
cd deploy/prod

# Levantar stack (en servidor staging/producción)
docker compose --env-file .env.prod -f docker-compose-prod.yml up -d

# Esperar healthchecks
sleep 60

# Ejecutar smoke test
bash scripts/smoke-test.sh
```

**Criterio Aceptación:**
- ✅ Exit code 0
- ✅ Todos los endpoints responden
- ✅ TLS certificates válidos
- ✅ Prometheus targets UP
- ✅ Alertmanager configurado con SMTP real

---

### Test 2.3: Alert Testing
```bash
cd deploy/prod

# Simular caída de servicio
docker stop rhinometric-grafana

# Esperar alerta (>1 min)
sleep 70

# Verificar email recibido con template HTML

# Restaurar servicio
docker start rhinometric-grafana
```

**Criterio Aceptación:**
- ✅ Email recibido en `SMTP_TO`
- ✅ Asunto: "Rhinometric Alert"
- ✅ Contenido HTML con formato (no texto plano)
- ✅ Alerta resolved enviada después de restaurar

---

### Test 2.4: Backup & Restore
```bash
cd deploy/prod

# 1. Backup
bash scripts/backup.sh

# 2. Modificar datos en Grafana (crear dashboard)

# 3. Simular disaster recovery
docker compose down
docker volume rm $(docker volume ls -q | grep prod_grafana-data)

# 4. Restaurar desde backup
BACKUP_FILE=$(ls -t backups/grafana-data_*.tar.gz | head -1)
docker run --rm \
  -v prod_grafana-data:/data \
  -v "$PWD/backups:/backup" \
  alpine tar xzf "/backup/$(basename $BACKUP_FILE)" -C /data

# 5. Levantar y verificar
docker compose up -d
```

**Criterio Aceptación:**
- ✅ Dashboard creado previamente NO existe después de disaster
- ✅ Dashboard existe después de restore
- ✅ Checksums SHA256 coinciden

---

## ��� Test Suite 3: OVA Build & Validation

### Test 3.1: Packer Validation
```bash
cd packer

# Validar sintaxis
packer validate ubuntu2204-rhinometric.json
```

**Criterio Aceptación:**
- ✅ No errores de sintaxis
- ✅ Variables definidas correctamente
- ✅ Provisioners configurados

---

### Test 3.2: OVA Build (30-45 min)
```bash
cd packer

# Build (requiere VirtualBox instalado)
packer build ubuntu2204-rhinometric.json

# Verificar output
ls -lh output-virtualbox-iso/*.ova
```

**Criterio Aceptación:**
- ✅ Build completa sin errores
- ✅ OVA generado en `output-virtualbox-iso/`
- ✅ Tamaño 3-5GB

---

### Test 3.3: OVA Import & First Boot
```bash
# Import en VirtualBox
VBoxManage import output-virtualbox-iso/rhinometric-demo.ova

# Iniciar VM
VBoxManage startvm "Rhinometric Demo Appliance"

# Conectar vía SSH (esperar ~2 min para first-boot)
ssh rhinouser@<VM_IP>
```

**Criterio Aceptación:**
- ✅ Import exitoso
- ✅ First boot <5 minutos
- ✅ SSH accesible con rhinouser/rhinometric
- ✅ Docker y docker-compose instalados

---

### Test 3.4: OVA Smoke Test
```bash
# Dentro de la VM
cd /opt/rhinometric
bash scripts/smoke-test.sh

# Verificar Grafana accesible
curl -k https://localhost:3000/api/health
```

**Criterio Aceptación:**
- ✅ Smoke test exit 0
- ✅ Grafana accesible desde host: https://<VM_IP>:3000
- ✅ Dashboards con datos (AI anomaly-seed.sh corriendo)
- ✅ Dashboard Builder UI accesible en :3001

---

### Test 3.5: OVA Acceptance Criteria (Final)
**Manual GUI Testing:**

1. **Login Grafana** (https://<VM_IP>:3000, admin/rhinometric_demo)
   - ✅ Login exitoso sin errors

2. **Dashboard AI Anomaly Detection**
   - ✅ Panel "Anomalías Detectadas (24h)": valor >0
   - ✅ Panel "Anomalías Activas": valor visible
   - ✅ Gráfico "Detecciones en Tiempo Real": curvas con datos

3. **Dashboard System Overview**
   - ✅ CPU, Memory, Disk, Network con gráficas

4. **Dashboard Builder UI** (http://<VM_IP>:3001)
   - ✅ Cargar templates
   - ✅ Crear nuevo dashboard → abrir en Grafana

5. **Prometheus Targets** (http://<VM_IP>:9090/targets)
   - ✅ Todos los targets UP (verde)
   - ✅ rhinometric-ai-anomaly:8085 UP

6. **Logs & Diagnostics**
   ```bash
   docker logs rhinometric-ai-anomaly-demo
   docker logs rhinometric-grafana-demo
   bash scripts/support-bundle.sh
   ```
   - ✅ No errores críticos en logs
   - ✅ Support bundle generado correctamente

---

## ��� Test Results Matrix

| Test ID | Description | Status | Notes |
|---------|-------------|--------|-------|
| 1.1 | Stack Init | ✅ PASS | 15 containers healthy |
| 1.2 | Smoke Test | ✅ PASS | 8/8 checks OK |
| 1.3 | Grafana + Datasources | ✅ PASS | 3 dashboards provisioned |
| 1.4 | AI with Data | ✅ PASS | Metrics >0 after seeding |
| 1.5 | Dashboard Builder | ✅ PASS | API + UI functional |
| 1.6 | Operational Scripts | ✅ PASS | backup/update/support OK |
| 1.7 | Resource Usage | ✅ PASS | <4GB RAM, <10GB disk |
| 2.1 | Prod Config | ✅ PASS | .env.prod validated |
| 2.2 | Prod Smoke Test | ⏳ PEND | Requires staging/prod server |
| 2.3 | Alert Testing | ⏳ PEND | Requires SMTP configured |
| 2.4 | Backup & Restore | ✅ PASS | Disaster recovery OK |
| 3.1 | Packer Validation | ✅ PASS | Template valid |
| 3.2 | OVA Build | ⏳ PEND | Requires VirtualBox + 45 min |
| 3.3 | OVA Import | ⏳ PEND | Requires OVA built |
| 3.4 | OVA Smoke Test | ⏳ PEND | Requires VM running |
| 3.5 | OVA Acceptance | ⏳ PEND | Final validation |

**Legend:**
- ✅ PASS - Test ejecutado y exitoso
- ⏳ PEND - Requiere recursos externos (Docker running, VirtualBox, SMTP, etc.)
- ❌ FAIL - Test falló (incluir detalles)

---

## ��� Common Issues & Solutions

### "No data" en dashboards AI
```bash
cd deploy/demo
bash scripts/anomaly-seed.sh > /tmp/seed.log 2>&1 &
# Esperar 2 min y refrescar dashboard
```

### Prometheus targets DOWN
```bash
# Ver targets específicos
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up")'

# Logs del target
docker logs rhinometric-ai-anomaly-demo
```

### Grafana datasource "prometheus" not found
```bash
# Re-provision datasources
docker restart rhinometric-grafana-demo
sleep 10
curl -s -u admin:rhinometric_demo http://localhost:3000/api/datasources/uid/prometheus
```

### Dashboard Builder CORS error
```bash
# Verificar backend
docker logs rhinometric-dashboard-builder-demo

# Verificar frontend apunta a :8001
curl http://localhost:8001/health
```

---

## ��� Final Report Template

```markdown
# Rhinometric v2.5.0 - E2E Test Report

**Date:** YYYY-MM-DD
**Tester:** [Name]
**Environment:** [Local/Staging/VM]

## Summary
- Total Tests: 16
- Passed: X
- Pending: Y
- Failed: Z

## Details
[Copy-paste Test Results Matrix con estados actualizados]

## Issues Found
1. [Descripción del issue]
   - **Severity:** Critical/High/Medium/Low
   - **Steps to Reproduce:** ...
   - **Expected:** ...
   - **Actual:** ...

## Conclusion
✅ v2.5.0 is ready for:
- [ ] Production deployment (deploy/prod/)
- [ ] OVA distribution (packer build)
- [ ] Demo appliance validation

**Approved by:** [Name]
**Date:** YYYY-MM-DD
```

---

## ��� Next Steps After E2E

1. **Fix Issues:** Resolver cualquier test FAIL
2. **Re-test:** Ejecutar tests afectados nuevamente
3. **Documentation:** Actualizar READMEs con findings
4. **Tag Release:** `git tag v2.5.0-prod && git push --tags`
5. **Build OVA:** Ejecutar Packer build final
6. **Distribution:** Subir OVA a almacenamiento (Google Drive, S3, etc.)
7. **Announcement:** Comunicar disponibilidad de v2.5.0

---

**Última Actualización:** $(date +%Y-%m-%d)
**Versión:** Rhinometric v2.5.0
