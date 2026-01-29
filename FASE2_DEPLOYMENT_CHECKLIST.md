# FASE 2 - Deployment Checklist

**Ejecutar en:** VM 89.167.15.73 (rhinometric-restore)  
**Persona:** Rafael Canelón  
**Fecha programada:** _________  
**Commit a desplegar:** `af76e94`

---

## ✅ Pre-Deployment

- [ ] Snapshot disponible: `GOLD-CORE-V2.7.0-NOTIFICATIONS-OK`
- [ ] (Opcional) Crear snapshot pre-deployment: `GOLD-CORE-V2.8.0-PRE-NGINX`
- [ ] Acceso SSH funcionando: `ssh rhinometric-restore`
- [ ] No hay usuarios activos críticos en el sistema

---

## 📥 Sincronizar Código

```bash
cd /opt/rhinometric
git fetch origin
git checkout feature/use-direct-grafana-links
git pull origin feature/use-direct-grafana-links
```

**Verificar:**
- [ ] `git log -1` muestra: `af76e94 feat(security): FASE 2...`
- [ ] `grep -c "ports:" docker-compose-v2.5.0.yml` → resultado: **1**
- [ ] `grep -c "expose:" docker-compose-v2.5.0.yml` → resultado: **46+**
- [ ] `ls -lh nginx/nginx.conf` → existe (243 líneas aprox)
- [ ] `ls -lh nginx/.htpasswd` → existe

---

## 🚀 Deployment

```bash
cd /opt/rhinometric

# Ver estado actual
docker compose ps > /tmp/pre-deployment-state.txt

# Bajar stack
docker compose down

# Subir con nueva config
docker compose up -d

# Esperar healthchecks
sleep 60

# Ver nuevo estado
docker compose ps
```

**Estados esperados:**
- [ ] `rhinometric-nginx` → **healthy**
- [ ] `rhinometric-console-frontend` → **healthy**
- [ ] `rhinometric-console-backend` → **healthy**
- [ ] `rhinometric-grafana` → **healthy**
- [ ] Resto de servicios → **running** (mínimo)

---

## 🧪 Tests de Acceso

### Console
- [ ] `http://89.167.15.73/` → Carga UI de Rhinometric
- [ ] No hay errores 502 Bad Gateway

### API
- [ ] `curl http://89.167.15.73/api/health` → responde 200

### Grafana
- [ ] `http://89.167.15.73/grafana/` → pide Basic Auth
- [ ] Usuario: `proxy-admin` / Password: `aJtImXAwtoiGGGZan/CKfmalSl9wtNsQ`
- [ ] Después pide login Grafana (admin / password)
- [ ] Dashboards cargan correctamente
- [ ] URLs en navegador son `/grafana/...` (no `/...`)

### Kiosk Mode
- [ ] Abrir dashboard desde console
- [ ] URL debe ser: `http://89.167.15.73/grafana/d/XXXX?kiosk=tv`
- [ ] Dashboard se muestra en modo kiosk (sin chrome)

### Notificaciones
- [ ] Disparar alerta de prueba
- [ ] Slack recibe mensaje
- [ ] Email llega correctamente

---

## 🔒 Validación de Seguridad

### En la VM:
```bash
ss -tulpn | grep LISTEN | grep "0.0.0.0"
```

**Resultado esperado (SOLO estos):**
- [ ] `0.0.0.0:22` (SSH)
- [ ] `0.0.0.0:80` (Nginx)

**NO debe aparecer:**
- [ ] ❌ `0.0.0.0:3000` (Grafana)
- [ ] ❌ `0.0.0.0:3002` (Console Frontend)
- [ ] ❌ `0.0.0.0:5432` (PostgreSQL)
- [ ] ❌ `0.0.0.0:6379` (Redis)
- [ ] ❌ `0.0.0.0:8105` (Console Backend)
- [ ] ❌ `0.0.0.0:9090` (Prometheus)
- [ ] ❌ `0.0.0.0:9093` (Alertmanager)

### Desde PC externo:
```bash
nmap -p 1-1000 89.167.15.73
```

- [ ] Solo puertos abiertos: **22, 80**
- [ ] Resto: filtered o closed

---

## 📊 Post-Deployment (después de 24h estables)

- [ ] Sistema estable sin reinicios
- [ ] No hay errores en logs críticos
- [ ] Crear snapshot: `GOLD-CORE-V2.8.0-NGINX-PERIMETER-OK`
- [ ] Actualizar `SECURITY_PERIMETER_PHASE2.md` con:
  - Fecha/hora de deployment
  - Resultado de `ss -tulpn`
  - Tests pasados
  - Persona ejecutante

---

## 🚨 Rollback (si algo falla)

**Opción 1: Snapshot**
```bash
# En Hetzner Cloud Panel
1. Detener VM
2. Restore: GOLD-CORE-V2.7.0-NOTIFICATIONS-OK
3. Iniciar VM
```

**Opción 2: Git revert**
```bash
cd /opt/rhinometric
git checkout fa95594  # Commit anterior a FASE 2
docker compose down
docker compose up -d
```

---

## 📝 Troubleshooting Rápido

**Nginx no arranca:**
```bash
docker logs rhinometric-nginx --tail 100
docker exec rhinometric-nginx nginx -t
```

**Console 502 Bad Gateway:**
```bash
docker compose ps | grep console
docker logs rhinometric-console-backend --tail 50
docker logs rhinometric-console-frontend --tail 50
```

**Grafana redirect loop:**
```bash
docker exec rhinometric-grafana env | grep GF_SERVER
# Debe mostrar:
# GF_SERVER_ROOT_URL=http://...grafana/
# GF_SERVER_SERVE_FROM_SUB_PATH=true
```

**Basic Auth no funciona:**
```bash
docker exec rhinometric-nginx cat /etc/nginx/.htpasswd
# Debe existir y mostrar: proxy-admin:$apr1$...
```

---

**Completado por:** ___________________  
**Fecha real de deployment:** ___________________  
**Duración total:** ___________________  
**Incidencias:** ___________________

---

**✅ FASE 2 COMPLETADA** cuando todos los checkboxes estén marcados y el sistema lleve 24h estable.
