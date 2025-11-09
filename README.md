# Ì∂è Rhinometric Enterprise v2.5.0

[![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)](https://github.com/Rafael2712/rhinometric-overview/releases/tag/v2.5.0-public)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-complete-green.svg)](docs/)
[![Status](https://img.shields.io/badge/status-production%20ready-success.svg)]()

**Plataforma integral de observabilidad empresarial con IA integrada**

Rhinometric Enterprise es una soluci√≥n completa de monitoreo, observabilidad y an√°lisis de infraestructura que combina las mejores herramientas open-source (Prometheus, Grafana, Loki, Tempo) con m√≥dulos propietarios de inteligencia artificial, generaci√≥n de informes y gesti√≥n de licencias.

---

## Ìæâ Qu√© hay de nuevo en v2.5.0

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

### Ì¥ê **License Server Mejorado**
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

- Ì≥ñ [Manual de Usuario (Espa√±ol)](docs/user-guides/MANUAL_DE_USUARIO.md)
- Ì≥ñ [User Manual (English)](docs/user-guides/USER_MANUAL_EN.md)
- Ì∫Ä [Resumen de Caracter√≠sticas](FEATURES_OVERVIEW.md)
- ÌøóÔ∏è [Arquitectura del Sistema](docs/architecture/SYSTEM_ARCHITECTURE_ES.md)

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
- Ì≤º **Comercial**: Licencias por n√∫mero de hosts
- Ì≥ß **Contacto**: licenses@rhinometric.com

---

## Ìºü Caracter√≠sticas Destacadas

### Monitoreo Unificado
- **M√©tricas**: Prometheus (scraping cada 15s)
- **Logs**: Loki (agregaci√≥n centralizada)
- **Trazas**: Tempo (distributed tracing)
- **Dashboards**: 20+ pre-configurados

### Inteligencia Artificial
- **Detecci√≥n de anomal√≠as**: Isolation Forest + ARIMA
- **Predicciones**: Forecasting de capacidad
- **Auto-tuning**: Ajuste autom√°tico de umbrales
- **Modelos custom**: Entrenamiento con tus datos

### Alertas Avanzadas
- **Multi-canal**: Email, Slack, PagerDuty, Webhooks
- **Silences**: Mantenimiento programado
- **Templates**: Reutiliza reglas de alerta
- **Routing**: Enrutamiento inteligente por severidad/equipo

### Seguridad Empresarial
- **RBAC**: Control de acceso basado en roles
- **LDAP/AD**: Integraci√≥n con directorio corporativo
- **SSO**: SAML, OAuth 2.0
- **TLS**: Cifrado end-to-end
- **Audit Logs**: Trazabilidad completa

---

## Ì≥û Soporte y Contacto

### Canales de Soporte

| Canal | Disponibilidad | SLA |
|-------|----------------|-----|
| **Email** | support@rhinometric.com | <4h |
| **GitHub Issues** | 24/7 | Community |
| **Tel√©fono** (Enterprise) | +34 900 123 456 | <15min |

### Recursos Adicionales

- **Documentaci√≥n**: https://docs.rhinometric.com
- **Blog**: https://blog.rhinometric.com
- **Community**: https://community.rhinometric.com
- **GitHub**: https://github.com/Rafael2712/rhinometric-overview

---

## Ì¥ß Instalaci√≥n y Configuraci√≥n

### Requisitos del Sistema

| Entorno | CPU | RAM | Disco | Red |
|---------|-----|-----|-------|-----|
| **Demo/POC** | 4 cores | 8 GB | 50 GB SSD | 100 Mbps |
| **Producci√≥n** | 8 cores | 16 GB | 200 GB SSD | 1 Gbps |
| **Enterprise HA** | 16 cores | 32 GB | 500 GB NVMe | 10 Gbps |

### Instalaci√≥n Detallada

Ver documentaci√≥n completa en:
- [Manual de Usuario (ES)](docs/user-guides/MANUAL_DE_USUARIO.md)
- [User Manual (EN)](docs/user-guides/USER_MANUAL_EN.md)

---

## Ì∑∫Ô∏è Roadmap

### Q1 2025
- [ ] Mobile App (iOS/Android)
- [ ] Synthetic Monitoring
- [ ] Cost Optimization Dashboard
- [ ] Service Level Objectives (SLOs)

### Q2 2025
- [ ] APM (Application Performance Monitoring)
- [ ] Real User Monitoring (RUM)
- [ ] Network Performance Monitoring
- [ ] Database Query Analyzer

### Q3 2025
- [ ] Multi-cloud Support
- [ ] Chaos Engineering
- [ ] Auto-remediation
- [ ] ChatOps Integration

---

## ÌøÜ Verificaci√≥n y Calidad

**Rhinometric v2.5.0** ha sido completamente validado:

- ‚úÖ Production Readiness Test (324 l√≠neas de verificaci√≥n)
- ‚úÖ Security Audit (sin credenciales hardcoded)
- ‚úÖ AI Metrics funcionando (6 dashboards, 14 m√©tricas)
- ‚úÖ Documentaci√≥n biling√ºe completa (ES/EN)
- ‚úÖ OVA appliance tested (VirtualBox + VMware)
- ‚úÖ License flow validated (trial + commercial)

**Fecha de cierre**: 2024-11-09  
**Build ID**: v2.5.0-prod-20241109  
**Automatizaci√≥n**: Packer + Docker Compose + Ansible

---

## Ì¥ù Contribuciones

Este es un proyecto propietario. Para solicitudes de features o reportar bugs:

1. Abrir issue en GitHub: https://github.com/Rafael2712/rhinometric-overview/issues
2. Contactar soporte: support@rhinometric.com
3. Unirse a la comunidad: https://community.rhinometric.com

---

## Ì≥Ñ Notas de Versi√≥n

### v2.5.0 (2024-11-09)

**Nuevas Caracter√≠sticas**:
- Enterprise Branding con landing page personalizable
- AI Anomaly Detection con ML (Isolation Forest + ARIMA)
- Dashboard Builder UI (interfaz no-code)
- OVA Demo Appliance (VirtualBox/VMware)
- License Server mejorado (trial 30 d√≠as)

**Mejoras**:
- Grafana datasource UID fijo ("prometheus")
- Dashboards auto-provisionados
- M√©tricas AI optimizadas (14 m√©tricas nativas)
- Documentaci√≥n completa biling√ºe

**Correcciones**:
- Fix: hardcoded emails en license server
- Fix: datasource UID mismatch en dashboards
- Fix: Packer systemd service path

**Componentes Verificados**:
- 14 servicios Docker funcionando
- 9 targets Prometheus UP
- 6 health checks pasando
- 3 dashboards provisioned

### Versiones Anteriores

- v2.4.0: Alta Disponibilidad (HA)
- v2.3.0: Distributed Tracing (Tempo)
- v2.2.0: Log Aggregation (Loki)
- v2.1.0: Basic Monitoring (Prometheus + Grafana)

---

## Ì≥ú Licencia y Copyright

¬© 2024 **Rhinometric Technologies**. Todos los derechos reservados.

Rhinometric Enterprise es software propietario. El uso de este software est√° sujeto a los t√©rminos de la licencia comercial. No est√° permitida la redistribuci√≥n, modificaci√≥n o uso comercial sin autorizaci√≥n expresa.

Para licencias comerciales, contactar: **licenses@rhinometric.com**

---

<p align="center">
  <strong>Ì∫Ä Desarrollado por el equipo Rhinometric</strong><br>
  <sub>Plataforma de observabilidad empresarial l√≠der en IA y automatizaci√≥n</sub><br><br>
  <a href="https://rhinometric.com">Website</a> ‚Ä¢
  <a href="https://docs.rhinometric.com">Documentaci√≥n</a> ‚Ä¢
  <a href="https://community.rhinometric.com">Comunidad</a> ‚Ä¢
  <a href="mailto:sales@rhinometric.com">Contacto Comercial</a>
</p>

---

**Ìºü ¬øTe gusta Rhinometric? Dale una estrella en GitHub y comp√°rtelo con tu equipo!**
