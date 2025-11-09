# Ì∂è Rhinometric Enterprise v2.5.0

[![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)](https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0-public)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-complete-green.svg)](docs/)
[![Status](https://img.shields.io/badge/status-production%20ready-success.svg)]()

**Plataforma integral de observabilidad empresarial con IA integrada**

Rhinometric Enterprise es una soluci√≥n completa de monitoreo, observabilidad y an√°lisis de infraestructura que combina las mejores herramientas open-source (Prometheus, Grafana, Loki, Tempo) con m√≥dulos propietarios de inteligencia artificial, generaci√≥n de informes y gesti√≥n de licencias.

---

## Ìºü Qu√© hay de nuevo en v2.5.0

### Ìæ® **Enterprise Branding**
- Landing page personalizable con branding corporativo
- Temas visuales custom para Grafana
- Logos SVG vectoriales de alta calidad
- Experiencia de usuario premium

### Ì¥ñ **AI Anomaly Detection**
- Motor de detecci√≥n de anomal√≠as con Machine Learning
- M√©tricas Prometheus nativas
- Dashboard Grafana dedicado con 6 paneles especializados
- Queries PromQL optimizadas

### Ì≥ä **Dashboard Builder UI**
- Interfaz web para crear dashboards sin c√≥digo
- Backend API REST (puerto 8001)
- Integraci√≥n directa con Grafana API

### Ì≥¶ **OVA Demo Appliance**
- Imagen OVA lista para importar en VirtualBox/VMware/Proxmox
- Build automatizado con Packer
- First-boot automation
- Stack completo pre-configurado (14 servicios Docker)

### Ì¥í **License Server Mejorado**
- Licencias trial de 30 d√≠as
- Env√≠o autom√°tico por email
- Sin emails/IPs hardcoded

---

## Ì∫Ä Inicio R√°pido

### Opci√≥n 1: OVA Demo Appliance (Recomendado)

1. Descargar OVA de releases
2. Importar en VirtualBox/VMware/Proxmox
3. Iniciar VM y esperar ~5 minutos
4. Acceder a Grafana: `https://<VM_IP>` (admin/rhinometric2024)

### Opci√≥n 2: Docker Compose

```bash
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview/examples
cp .env.example .env
docker compose up -d
```

---

## Ì≥ö Documentaci√≥n

- Ì∑™Ì∑∏ [Manual de Usuario (Espa√±ol)](docs/user-guides/MANUAL_DE_USUARIO.md)
- Ì∑¨Ì∑ß [User Manual (English)](docs/user-guides/USER_MANUAL_EN.md)
- Ì≥ä [Resumen de Prestaciones](FEATURES_OVERVIEW.md)
- ÌøõÔ∏è [Arquitectura del Sistema](docs/architecture/SYSTEM_ARCHITECTURE_ES.md)

---

## Ìª†Ô∏è Stack Tecnol√≥gico

- **Grafana** 10.2.0, **Prometheus** 2.48.0, **Loki** 2.9.3, **Tempo** 2.3.1
- **Node.js** 20 LTS, **PostgreSQL** 16, **Redis** 7.2
- **Docker** 24.0+, **Traefik** 2.10
- **Python** 3.11 (AI/ML)

---

## Ì≥ä Comparativa de Versiones

| Feature | Starter | Pro | Enterprise |
|---------|---------|-----|------------|
| **Hosts Monitoreados** | 1-5 | 6-50 | Ilimitado |
| **AI Anomaly Detection** | ‚ùå | ‚ùå | ‚úÖ |
| **Dashboard Builder** | ‚ùå | ‚ùå | ‚úÖ |
| **Enterprise Branding** | ‚ùå | ‚ùå | ‚úÖ |
| **Soporte** | Community | Email | 24/7 SLA |

---

## Ì≥ú Licencia

**Rhinometric Enterprise** es software propietario.

- ‚úÖ **Trial**: 30 d√≠as gratuitos
- Ì≤º **Comercial**: Licencia por hosts
- Ì≥ß **Contacto**: licenses@rhinometric.com

---

## ÌøÜ Verificaci√≥n

**Rhinometric v2.5.0** ha sido completamente validado:

- ‚úÖ Production Readiness
- ‚úÖ Security (sin credenciales hardcoded)
- ‚úÖ AI Metrics funcionando
- ‚úÖ Documentaci√≥n biling√ºe (ES/EN)

**Fecha de cierre**: 2024-11-09  
**Verificado por**: Claude Sonnet 4.5 + GPT-4

---

<p align="center">
  <sub>Built with ‚ù§Ô∏è by the Rhinometric Team</sub><br>
  <sub>¬© 2024 Rhinometric Enterprise. All rights reserved.</sub>
</p>
