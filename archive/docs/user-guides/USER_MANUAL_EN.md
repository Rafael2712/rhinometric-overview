# Ì≥ñ User Manual - Rhinometric Enterprise v2.5.0

**Date**: November 2024  
**Version**: 2.5.0  
**Language**: English

---

## Ì≥ã Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface](#user-interface)
4. [Dashboards and Visualization](#dashboards-and-visualization)
5. [Alerts and Notifications](#alerts-and-notifications)
6. [AI Anomaly Detection](#ai-anomaly-detection)
7. [Dashboard Builder](#dashboard-builder)
8. [License Management](#license-management)
9. [Enterprise Branding](#enterprise-branding)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## ÌæØ Introduction

### What is Rhinometric?

**Rhinometric Enterprise** is a comprehensive enterprise observability platform that combines infrastructure monitoring, logs, distributed tracing, and AI-powered anomaly detection.

### Key Features

- **Unified Monitoring**: Metrics, logs, and traces in one platform
- **Integrated AI**: Automatic anomaly detection with Machine Learning
- **Visual Builder**: Create dashboards without code
- **Custom Branding**: Adapt the interface to your brand
- **Intelligent Alerts**: Multi-channel notifications
- **Scalability**: From 1 host to thousands of servers

---

## Ì∫Ä Getting Started

### System Requirements

#### Minimum Hardware
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- Network: 100 Mbps

#### Recommended Hardware
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 200+ GB SSD
- Network: 1 Gbps

### Installation with Docker Compose

```bash
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview/examples
docker compose up -d
```

### First Access

URL: http://localhost:3000
Username: admin
Password: rhinometric_v22

---

## Ì∂•Ô∏è User Interface

### Main Navigation

- **Home**: Main page
- **Explore**: Ad-hoc queries
- **Dashboards**: Dashboard list
- **Alerting**: Alert management
- **Configuration**: Settings

---

## Ì≥ä Dashboards and Visualization

### Pre-configured Dashboards

1. **System Metrics**: CPU, RAM, disk, network
2. **Application Metrics**: Request rate, latency, errors
3. **AI Anomaly Detection**: Anomaly detection

### PromQL Queries

```promql
# Total CPU
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Available memory
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024
```

---

## Ì¥î Alerts and Notifications

### Supported Channels

- Email (SMTP)
- Slack
- PagerDuty
- Webhooks

### Create Alert

1. Go to Alerting ‚Üí Alert rules
2. New alert rule
3. Configure query and conditions
4. Select notification channel

---

## Ì¥ñ AI Anomaly Detection

### How It Works

The AI engine:
1. Learns normal patterns (7 days)
2. Detects real-time deviations
3. Generates anomaly score (0-100)
4. Alerts when threshold exceeded

### Algorithms

- Isolation Forest
- ARIMA
- Z-Score

---

## Ìæ® Dashboard Builder

### Create Dashboard

1. Access Dashboard Builder
2. Select template
3. Add panels
4. Configure queries
5. Save

---

## Ì¥ê License Management

### License Types

- Trial: 30 days free
- Starter: 1-5 hosts
- Professional: 6-50 hosts
- Enterprise: Unlimited

### Activate License

```bash
docker cp license.lic rhinometric-license-server:/app/licenses/
docker exec rhinometric-license-server python /app/activate.py
```

---

## Ìæ® Enterprise Branding

### Customize Logo

```bash
cp logo.png infrastructure/nginx/landing/assets/
docker compose restart nginx
```

---

## Ì¥ß Troubleshooting

### Services Won't Start

```bash
docker compose ps
docker compose logs [service]
```

### Dashboards Not Loading Data

Check datasource at Grafana ‚Üí Configuration ‚Üí Data sources

---

## ‚ùì FAQ

**Q: Can I use in production?**
A: Yes, v2.5.0 is production-ready.

**Q: How many hosts can I monitor?**
A: Depends on your license (1-5, 6-50, unlimited).

---

## Ì≥û Support

- Email: info@rhinometric.com
- Phone: +1 800 123 4567
- GitHub: https://github.com/Rafael2712/rhinometric-overview

---

**Version**: 2.5.0  
**Updated**: November 2024
