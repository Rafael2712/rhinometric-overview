# 🎯 RhinoMetric v2.5.0 - Demo Appliance (OVA)

**Appliance preconfigurado** listo para importar en VirtualBox, VMware, Proxmox o ESXi.

---

## ⚡ Quick Start (10 minutos)

### 1. Download OVA
```bash
wget https://releases.rhinometric.io/rhinometric-demo-v2.5.0.ova
# or download from GitHub releases
```

### 2. Import to VirtualBox
```bash
VBoxManage import rhinometric-demo-v2.5.0.ova \
  --vsys 0 --vmname "RhinoMetric-Demo" \
  --memory 8192 --cpus 4
```

**Or use GUI**: File → Import Appliance → Select OVA → Import

### 3. Start VM
```bash
VBoxManage startvm "RhinoMetric-Demo" --type headless
# Or start from VirtualBox GUI
```

### 4. Access Grafana
**Wait 3-5 minutes** for first boot to complete, then:

```
https://<VM-IP>
Username: admin
Password: rhinometric_demo
```

**✅ Anomaly data will appear automatically in 1-3 minutes!**

---

## 📊 What's Included

- ✅ **Grafana 10.4.0** with pre-configured dashboards
- ✅ **Prometheus 2.53.0** (3d retention, 5GB)
- ✅ **Loki 3.0.0** for logs
- ✅ **Tempo 2.6.0** for traces
- ✅ **AI Anomaly Detection** with auto-seeding
- ✅ **PostgreSQL 15** + **Redis 7**
- ✅ **Traefik** reverse proxy with TLS
- ✅ **Exporters**: node-exporter, cAdvisor, blackbox

### Pre-configured Dashboards
1. **AI Anomaly Detection** - Real-time ML detections
2. **System Overview** - CPU, RAM, Disk, Network
3. **App Performance** - API latency, throughput, errors

---

## 🖥️ VM Specifications

| Resource | Value |
|----------|-------|
| **OS** | Ubuntu 22.04 LTS (minimal) |
| **CPU** | 4 vCPU |
| **RAM** | 8 GB |
| **Disk** | 60 GB (thin provision) |
| **Network** | Bridged (recommended) or NAT |

### Network Ports
- **80/443** - Grafana (HTTPS with self-signed cert)
- **22** - SSH (optional, can disable)

---

## 🔐 Default Credentials

```
Grafana:        admin / rhinometric_demo
SSH:            rhinouser / rhinometric
PostgreSQL:     rhinometric / rhinometric_demo_db
Redis:          rhinometric_demo_redis
```

**⚠️ IMPORTANT**: Change passwords after first login for production use!

---

## 📝 Common Tasks

### Check Status
```bash
ssh rhinouser@<VM-IP>
docker ps
```

### View Logs
```bash
sudo journalctl -u rhinometric-firstboot -f
tail -f /var/log/rhinometric-firstboot.log
```

### Restart Services
```bash
cd /opt/rhinometric
docker compose -f docker-compose-demo.yml restart
```

### Update to Latest
```bash
cd /opt/rhinometric
sudo bash scripts/update.sh
```

### Create Backup
```bash
sudo bash /opt/rhinometric/scripts/backup.sh
# Backup saved to /var/backups/rhinometric/
```

### Generate Support Bundle
```bash
sudo bash /opt/rhinometric/scripts/support-bundle.sh
# Creates: rhinometric-support-<date>.tar.gz
```

---

## 🛠️ Troubleshooting

### Services not starting
```bash
# Check Docker status
sudo systemctl status docker

# View service logs
docker logs rhinometric-grafana
docker logs rhinometric-ai-anomaly

# Restart all
cd /opt/rhinometric
docker compose -f docker-compose-demo.yml down
docker compose -f docker-compose-demo.yml up -d
```

### No anomaly data showing
```bash
# Check AI service
curl http://localhost:8085/health
curl http://localhost:8085/metrics | grep rhinometric_anomaly

# Restart anomaly seeder
pkill -f anomaly-seed
cd /opt/rhinometric
bash scripts/anomaly-seed.sh &
```

### Can't access Grafana
```bash
# Get VM IP
hostname -I

# Check Traefik
docker logs rhinometric-traefik

# Check firewall
sudo ufw status
```

---

## 🚀 Next Steps

1. **Explore Dashboards**: Navigate to Dashboards → Demo folder
2. **Configure Alerts**: Go to Alerting → Alert rules
3. **Add Data Sources**: Settings → Data sources
4. **Customize**: All configs in `/opt/rhinometric/`

---

## 📖 Documentation

- **Full Operations Guide**: `/opt/rhinometric/docs/OPERATIONS.md`
- **API Documentation**: `https://<VM-IP>/docs` (if enabled)
- **GitHub**: https://github.com/yourorg/rhinometric

---

## 🔒 Security Notes

### For Demo/Testing
- Uses self-signed TLS certificate
- Default passwords (CHANGE THEM!)
- SSH enabled by default
- Docs endpoints accessible

### For Production
Convert to production mode:
```bash
cd /opt/rhinometric
sudo bash scripts/harden.sh
# Follow prompts to:
# - Change all passwords
# - Generate new JWT secrets
# - Disable SSH
# - Get Let's Encrypt certificate
# - Disable docs endpoints
```

---

## 💡 FAQ

**Q: How do I get my company's logo in Grafana?**  
A: Settings → Preferences → Change org logo

**Q: Can I add more users?**  
A: Yes! Configuration → Users → New user

**Q: How do I connect to my own Prometheus?**  
A: Settings → Data sources → Edit Prometheus → Change URL

**Q: Can I export this to production?**  
A: Yes! See `/opt/rhinometric/docs/EXPORT-TO-PROD.md`

---

## 📞 Support

- **Issues**: GitHub Issues
- **Email**: support@rhinometric.io
- **Docs**: https://docs.rhinometric.io
- **Version**: v2.5.0

---

## ⚖️ License

See LICENSE file in `/opt/rhinometric/`

---

**🎉 Ready to demo! Access `https://<your-vm-ip>` and explore.**
