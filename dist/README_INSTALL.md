# Rhinometric Platform — Installation Guide

## Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 20.04 | Ubuntu 22.04+ |
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 150 GB | 250 GB+ SSD |
| Docker | 24.x+ | Latest stable |
| Docker Compose | v2 | Latest stable |
| Ports | 3000, 3002, 5432, 6379, 8105, 9090, 9093, 3100, 16686 | — |

## Distribution Package Contents

```
dist/
├── install-rhinometric.sh      # Main installer (run this)
├── uninstall-rhinometric.sh    # Uninstaller
├── rhino-lic                   # License validator binary
├── docker-compose.yml          # Docker stack definition
├── .env.template               # Environment template
└── README_INSTALL.md           # This file
```

## Installation

### Quick Start

```bash
# 1. Extract the distribution package
tar xzf rhinometric-v3.0.0.tar.gz
cd rhinometric-v3.0.0/

# 2. Run the installer as root
sudo bash install-rhinometric.sh
```

### Installation Flow

The installer performs these steps automatically:

1. **System Validation** — Checks OS, CPU, RAM, disk, Docker, ports
2. **Fingerprint Detection** — Displays your machine's unique fingerprint
3. **License Validation** — Optionally validates your license file
4. **Directory Setup** — Creates `/opt/rhinometric/` structure
5. **Docker Stack** — Pulls images and starts all containers
6. **Health Check** — Verifies the platform is responding
7. **Credentials** — Generates and saves access credentials

### Licensed Installation

To install with a valid license:

```bash
# Step 1: Run the installer — it will display your machine fingerprint
sudo bash install-rhinometric.sh

# The installer shows:
#   Machine Fingerprint Detected
#   sha256:abcdef1234567890...
#
# Step 2: Send this fingerprint to Rhinometric
# Step 3: Receive your signed license.key file
# Step 4: When prompted, enter the path to your license.key
```

Alternatively, place `license.key` in the same directory as the installer
and it will be detected automatically.

### Unlicensed Installation

Press ENTER when prompted for a license file. The platform will start
in unlicensed mode with limited features. You can add a license later
by placing `license.key` in `/opt/rhinometric/`.

## Post-Installation

### Access URLs

| Service | URL | Auth |
|---|---|---|
| Console | `http://<SERVER_IP>:3002` | admin / (see install-info.txt) |
| Grafana | `http://<SERVER_IP>:3000` | admin / (see install-info.txt) |
| Prometheus | `http://<SERVER_IP>:9090` | No auth |
| Alertmanager | `http://<SERVER_IP>:9093` | No auth |
| Jaeger | `http://<SERVER_IP>:16686` | No auth |

### Credentials

All credentials are saved to:
```
/opt/rhinometric/install-info.txt
```

**Important:** Save these credentials in a password manager and delete the file.

### Useful Commands

```bash
# Check status
cd /opt/rhinometric && docker compose ps

# View logs
cd /opt/rhinometric && docker compose logs -f

# View specific service logs
cd /opt/rhinometric && docker compose logs -f console-backend

# Restart all services
cd /opt/rhinometric && docker compose restart

# Stop platform
cd /opt/rhinometric && docker compose down

# Start platform
cd /opt/rhinometric && docker compose up -d
```

## License Management

### Check Machine Fingerprint

```bash
rhino-lic fingerprint
```

### Validate License

```bash
rhino-lic validate /opt/rhinometric/license.key
```

### License Status Codes

| Exit Code | Meaning |
|---|---|
| 0 | Valid license |
| 1 | Invalid signature |
| 2 | License expired |
| 3 | Fingerprint mismatch |
| 4 | Parse error |

## Uninstallation

```bash
sudo bash /opt/rhinometric/uninstall-rhinometric.sh
```

The uninstaller will:
- Stop all containers
- Optionally remove Docker volumes (database data)
- Optionally remove the installation directory
- Back up credentials before removal

## Troubleshooting

### Containers not starting
```bash
cd /opt/rhinometric && docker compose ps
cd /opt/rhinometric && docker compose logs --tail 50
```

### Backend not responding
```bash
curl -v http://localhost:8105/health
docker logs rhinometric-console-backend --tail 100
```

### License validation failing
```bash
# Check fingerprint
rhino-lic fingerprint

# Validate with verbose output
rhino-lic validate /opt/rhinometric/license.key
```

### Port conflicts
```bash
ss -tuln | grep -E ':(3000|3002|5432|6379|8105|9090|9093|3100|16686)\b'
```

## Support

- Email: soporte@rhinometric.com
- Documentation: https://docs.rhinometric.com
