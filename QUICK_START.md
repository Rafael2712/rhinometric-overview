# 🚀 QUICK START - Rhinometric Trial v2.0.0 Rebuilt

## Para ejecutar AHORA en WSL2:

```bash
# 1. Abrir terminal WSL2 Ubuntu
wsl -d Ubuntu

# 2. Navegar al proyecto (desde WSL2)
cd /mnt/c/Users/canel/mi-proyecto/infrastructure/mi-proyecto

# 3. Dar permisos (solo primera vez)
chmod +x rebuild-rhinometric.sh validate-stack.sh create-rebuild-package.sh

# 4. EJECUTAR REBUILD COMPLETO
./rebuild-rhinometric.sh
```

## Resultado esperado:

```
✅ RHINOMETRIC TRIAL v2.0.0 RECONSTRUIDO

Servicios Desplegados:
  • rhinometric-license-server (healthy)
  • rhinometric-postgres (healthy)
  • rhinometric-redis (healthy)
  • rhinometric-prometheus (healthy)
  • rhinometric-loki (healthy)
  • rhinometric-tempo (healthy)
  • rhinometric-telemetrygen (healthy)
  • rhinometric-grafana (healthy)
  • rhinometric-alertmanager (healthy)
  • rhinometric-node-exporter (healthy)
  • rhinometric-cadvisor (healthy)
  • rhinometric-blackbox-exporter (healthy)
  • rhinometric-postgres-exporter (healthy)
  • rhinometric-license-dashboard (healthy)
  • rhinometric-nginx (healthy)
  • rhinometric-promtail (healthy)

Acceso a Servicios:
  • Grafana:         http://localhost:3000 (admin / admin_trial_2024)
  • Prometheus:      http://localhost:9090
  • Loki:            http://localhost:3100
  • Tempo:           http://localhost:3200
  • Alertmanager:    http://localhost:9093
  • License Dashboard: http://localhost:8080
  • Nginx:           http://localhost:80

Datos Persistentes:
  • Ubicación:       ~/rhinometric_data
  • Tamaño total:    ~500MB (después de init)

Reconstrucción completada exitosamente ✓
```

## Validación post-deploy:

```bash
./validate-stack.sh
```

## Generar ZIP distribuible:

```bash
./create-rebuild-package.sh
```

Genera:
- `build/rhinometric-trial-v2.0.0-linux-rebuilt.tar.gz`
- `build/rhinometric-trial-v2.0.0-linux-rebuilt.zip`
- Checksums SHA256

---

## 📋 CHECKLIST RÁPIDO

- [ ] WSL2 Ubuntu ejecutándose
- [ ] Docker Engine activo en WSL2
- [ ] Ejecutado `./rebuild-rhinometric.sh`
- [ ] 16/16 contenedores healthy
- [ ] Grafana accesible con modo oscuro
- [ ] `validation_report.txt` generado

---

## ⚙️ Si Docker no está corriendo en WSL2:

```bash
# Desde WSL2 Ubuntu:
sudo systemctl start docker

# O reiniciar servicio:
sudo systemctl restart docker

# Verificar estado:
sudo systemctl status docker
```

---

## 🔧 Troubleshooting rápido:

**Error: "Permission denied"**
```bash
chmod +x *.sh
```

**Error: "Cannot connect to Docker daemon"**
```bash
sudo systemctl start docker
```

**Contenedor no healthy:**
```bash
docker compose -f docker-compose-rebuilt.yml logs [nombre-servicio]
```

**Reiniciar todo:**
```bash
docker compose -f docker-compose-rebuilt.yml restart
```

---

**Tiempo total estimado:** 5-10 minutos

**Documentación completa:** Ver `DEPLOY_INSTRUCTIONS.md`
