# 🏗️ RhinoMetric OVA - Build Instructions

Complete guide to build the RhinoMetric v2.5.0 Demo Appliance OVA.

---

## ✅ Prerequisites

### Required Software
- **Packer** v1.9+ ([download](https://www.packer.io/downloads))
- **VirtualBox** 7.0+ (for VirtualBox OVA)
- **VMware Workstation/Fusion** (for VMware OVA) - optional
- **Git** for cloning the repo

### System Requirements (build machine)
- **RAM**: 16GB minimum
- **Disk**: 100GB free space
- **OS**: Linux, macOS, or Windows with WSL2
- **Network**: Internet connection for downloading ISO and Docker images

---

## 🚀 Quick Build (5 commands)

```bash
# 1. Clone repository
git clone https://github.com/yourorg/rhinometric.git
cd rhinometric

# 2. Validate Packer template
cd packer
packer validate ubuntu2204-rhinometric.json

# 3. Build OVA (VirtualBox)
packer build ubuntu2204-rhinometric.json

# 4. Find output OVA
ls -lh output-virtualbox-iso/

# 5. Import and test
VBoxManage import output-virtualbox-iso/rhinometric-demo.ova
```

**Build time**: 30-45 minutes (depending on internet speed)

---

## 📋 Detailed Build Process

### Step 1: Prepare Build Environment

```bash
# Install Packer (Ubuntu/Debian)
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install packer

# Verify
packer version
# Packer v1.10.0

# Install VirtualBox
sudo apt-get install virtualbox virtualbox-ext-pack
```

### Step 2: Validate All Files

```bash
cd rhinometric

# Check directory structure
tree -L 3 deploy/demo packer

# Expected structure:
# deploy/demo/
# ├── docker-compose-demo.yml
# ├── scripts/
# │   ├── first-boot.sh
# │   ├── anomaly-seed.sh
# │   ├── smoke-test.sh
# │   ├── update.sh
# │   ├── backup.sh
# │   └── support-bundle.sh
# ├── grafana/provisioning/
# ├── prometheus/prometheus.yml
# ├── alertmanager/alertmanager.yml
# └── traefik/traefik.yml
#
# packer/
# ├── ubuntu2204-rhinometric.json
# ├── http/
# │   ├── user-data
# │   └── meta-data
# └── files/
#     └── rhinometric-firstboot.service

# Validate Packer template
cd packer
packer validate ubuntu2204-rhinometric.json
```

### Step 3: Build OVA

```bash
cd packer

# Option A: VirtualBox OVA (recommended for demos)
packer build ubuntu2204-rhinometric.json

# Option B: VMware OVA (for enterprise environments)
packer build -only=vmware-iso ubuntu2204-rhinometric.json

# Option C: Both formats
packer build ubuntu2204-rhinometric.json
```

**What happens during build:**
1. Downloads Ubuntu 22.04 ISO (~2.5GB) - **10 min**
2. Creates VM and installs Ubuntu - **5 min**
3. Installs Docker, UFW, utilities - **5 min**
4. Copies RhinoMetric files to /opt/rhinometric - **2 min**
5. Configures systemd firstboot service - **1 min**
6. Cleans up and exports to OVA - **5 min**

**Total**: ~30-45 minutes

### Step 4: Verify Build Output

```bash
ls -lh output-virtualbox-iso/

# Expected output:
# rhinometric-demo.ova    (~3.2 GB)
# rhinometric-demo.ovf
# rhinometric-demo-disk001.vmdk

# Check OVA integrity
tar -tzf output-virtualbox-iso/rhinometric-demo.ova | head
```

---

## 🧪 Testing the OVA

### Test 1: Import to VirtualBox

```bash
# Import OVA
VBoxManage import output-virtualbox-iso/rhinometric-demo.ova \
  --vsys 0 \
  --vmname "RhinoMetric-Demo-Test" \
  --memory 8192 \
  --cpus 4

# Configure network (bridged for easy access)
VBoxManage modifyvm "RhinoMetric-Demo-Test" \
  --nic1 bridged \
  --bridgeadapter1 eth0  # Change to your network adapter

# Start VM
VBoxManage startvm "RhinoMetric-Demo-Test" --type headless

# Wait for first boot (3-5 minutes)
sleep 180

# Get VM IP
VBoxManage guestproperty get "RhinoMetric-Demo-Test" "/VirtualBox/GuestInfo/Net/0/V4/IP"
```

### Test 2: Verify Services

```bash
# SSH into VM
ssh rhinouser@<VM-IP>
# Password: rhinometric

# Check first-boot log
tail -50 /var/log/rhinometric-firstboot.log

# Verify all containers running
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# rhinometric-traefik        Up 2 minutes
# rhinometric-grafana        Up 2 minutes (healthy)
# rhinometric-prometheus     Up 2 minutes (healthy)
# rhinometric-ai-anomaly     Up 2 minutes (healthy)
# ... (15 total containers)
```

### Test 3: Access Grafana

```bash
# From your browser
https://<VM-IP>

# Login:
# Username: admin
# Password: rhinometric_demo

# Verify:
# 1. Dashboards → Demo folder shows 3 dashboards
# 2. Dashboard "AI Anomaly Detection" shows data
# 3. Configuration → Data sources shows 3 sources (all green)
```

### Test 4: Verify AI Metrics

```bash
# From VM or external
curl -k https://<VM-IP>/api/datasources/proxy/1/api/v1/query?query=rhinometric_anomaly_detections_total

# Should return JSON with values > 0
```

### Test 5: Smoke Tests

```bash
# SSH to VM
ssh rhinouser@<VM-IP>

# Run smoke tests
cd /opt/rhinometric
bash scripts/smoke-test.sh

# Expected output:
# ✓ AI Anomaly: health OK
# ✓ AI Anomaly: metrics present
# ✓ Prometheus: targets UP
# ✓ Grafana: accessible
# ✓ Dashboards: present
# ✅ DEMO READY (exit 0)
```

---

## 📦 Distribution

### Create Release Package

```bash
cd output-virtualbox-iso

# Create checksums
sha256sum rhinometric-demo.ova > rhinometric-demo-v2.5.0.sha256

# Create zip with docs
mkdir rhinometric-demo-v2.5.0
cp rhinometric-demo.ova rhinometric-demo-v2.5.0/
cp ../docs/ova/OVA-README.md rhinometric-demo-v2.5.0/README.md
cp ../LICENSE rhinometric-demo-v2.5.0/
zip -r rhinometric-demo-v2.5.0.zip rhinometric-demo-v2.5.0/

ls -lh rhinometric-demo-v2.5.0.*
```

### Upload to Release Server

```bash
# GitHub Releases
gh release create v2.5.0-demo \
  --title "RhinoMetric v2.5.0 Demo Appliance" \
  --notes "Complete demo OVA with AI anomaly detection" \
  rhinometric-demo-v2.5.0.zip \
  rhinometric-demo-v2.5.0.sha256

# Or S3
aws s3 cp rhinometric-demo-v2.5.0.zip \
  s3://releases.rhinometric.io/v2.5.0/
```

---

## 🔧 Customization

### Change VM Resources

Edit `packer/ubuntu2204-rhinometric.json`:

```json
{
  "variables": {
    "cpus": "8",      // was 4
    "memory": "16384", // was 8192
    "disk_size": "122880"  // was 61440 (120GB instead of 60GB)
  }
}
```

### Add Custom Dashboards

```bash
# Place dashboard JSON files in:
deploy/demo/grafana/provisioning/dashboards/json/

# Rebuild OVA
cd packer
packer build ubuntu2204-rhinometric.json
```

### Change Default Credentials

Edit `deploy/demo/scripts/first-boot.sh`:

```bash
# Change these lines:
GF_SECURITY_ADMIN_PASSWORD=your_custom_password
POSTGRES_PASSWORD=your_custom_db_password
```

### Enable Production Mode by Default

Edit `deploy/demo/docker-compose-demo.yml`:

```yaml
services:
  ai-anomaly:
    environment:
      - ENVIRONMENT=production  # was demo
      - ENABLE_DOCS=false       # disable Swagger
```

---

## 🐛 Troubleshooting Build Issues

### Packer fails to download ISO

```bash
# Pre-download ISO manually
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso \
  -O ~/ubuntu-22.04.3-live-server-amd64.iso

# Update packer template to use local ISO
# Change "iso_url" to "file:///home/user/ubuntu-22.04.3-live-server-amd64.iso"
```

### VM won't boot after import

```bash
# Check VirtualBox settings
VBoxManage showvminfo "RhinoMetric-Demo-Test"

# Reset to safe defaults
VBoxManage modifyvm "RhinoMetric-Demo-Test" \
  --firmware bios \
  --graphicscontroller vmsvga \
  --vram 16
```

### Services fail to start

```bash
# SSH to VM
ssh rhinouser@<VM-IP>

# Check Docker
sudo systemctl status docker
sudo journalctl -u docker -f

# Check first-boot service
sudo journalctl -u rhinometric-firstboot -f

# Manually run first-boot
cd /opt/rhinometric
sudo bash scripts/first-boot.sh
```

### OVA too large (>4.5GB)

```bash
# Reduce disk size
# Edit packer template: "disk_size": "40960" (40GB instead of 60GB)

# Reduce retention
# Edit deploy/demo/prometheus/prometheus.yml:
#   - '--storage.tsdb.retention.time=1d'  # was 3d
#   - '--storage.tsdb.retention.size=2GB'  # was 5GB
```

---

## 📊 Build Statistics

### Expected Sizes
- **ISO Download**: 2.5 GB
- **Intermediate VM**: 8 GB
- **Final OVA**: 3.2 GB
- **Compressed ZIP**: 2.8 GB

### Expected Times (on modern hardware)
- **ISO Download**: 5-15 min (depends on connection)
- **VM Creation**: 5 min
- **Provisioning**: 10 min
- **Export to OVA**: 5 min
- **Total**: 30-45 min

---

## ✅ Acceptance Criteria Checklist

Before releasing OVA:

- [ ] OVA builds successfully without errors
- [ ] OVA size < 4.5 GB
- [ ] Imports to VirtualBox without errors
- [ ] VM boots and reaches login prompt in < 2 min
- [ ] First-boot service completes successfully
- [ ] All 15 containers start and become healthy
- [ ] Grafana accessible at `https://<IP>` with self-signed cert
- [ ] Dashboard "AI Anomaly Detection" shows data > 0
- [ ] Smoke tests pass (exit 0)
- [ ] Anomaly seeder runs in background
- [ ] VM survives reboot (systemd restart:always works)
- [ ] Backup script creates valid tar.gz
- [ ] Support bundle script generates diagnostics

---

## 🚀 Next Steps

After successful build:

1. **Test on multiple platforms**:
   - VirtualBox 7.0
   - VMware Workstation 17
   - VMware ESXi 7.0+
   - Proxmox VE 8.0+

2. **Create video demo**: Screen recording of import → access → explore

3. **Update marketing materials**: Screenshots from running OVA

4. **Create customer onboarding guide**: Quick start for sales demos

5. **Setup CI/CD**: Automate OVA builds on release tags

---

## 📞 Support

If you encounter build issues:

1. Check logs: `packer_log.txt` (enable with `PACKER_LOG=1`)
2. GitHub Issues: https://github.com/yourorg/rhinometric/issues
3. Email: support@rhinometric.io

---

**🎉 Ready to build! Run `packer build ubuntu2204-rhinometric.json`**
