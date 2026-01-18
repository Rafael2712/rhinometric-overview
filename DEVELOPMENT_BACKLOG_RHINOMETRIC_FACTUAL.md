# RHINOMETRIC v2.5.0  
## Backlog de Desarrollo y Pendings

**Date:** 17 de Diciembre, 2025  
**Source:** PENDIENTES_DESARROLLO_RHINOMETRIC.md, ISSUES-PENDIENTES-v2.6.0.md, análisis de código  
**Estado del Proyecto:** Production operational with pending improvements

---

## Status Summary

**Completed:** ~75%  
**In Development:** ~15%  
**Planned/Pending:** ~10%

This document lists ONLY pending tasks documented in the repository, without inventing features.

---

## 🔴 PRIORIDAD CRÍTICA (Próximas 2 weeks)

### 1. Fix Annual Email Links ⏰ URGENTE
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 19-36  
**Status:** ❌ Pending  
**Estimated time:** 30 minutes  

**Documented problem:**
- Enlaces de descarga de instalador llevan a página incorrecta
- Enlaces de manuales no funcionan
- Solo el enlace de la web funciona

**Tasks:**
- [ ] Obtener URLs correctas de Google Drive (públicas)
- [ ] Actualizar template en `/home/ubuntu/license-server/app/main.py`
- [ ] Rebuild Docker container
- [ ] Probar envío de email de prueba
- [ ] Verificar todos los enlaces en email recibido

**Files to modify:**
- `main.py` lines 354, 360, 361

---

### 2. Implement Automatic Database Backup 🔒
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 38-57  
**Status:** ❌ Not implemented  
**Estimated time:** 4 hours  

**Tasks:**
- [ ] Crear script de backup diario de PostgreSQL
- [ ] Configurar cron job para ejecutar a las 3 AM
- [ ] Subir backups a AWS S3 o Google Cloud Storage
- [ ] Implementar retention policy (30 días hot, 1 año cold)
- [ ] Documentar procedimiento de restore
- [ ] Probar restore desde backup

**Deliverables:**
- Script `backup_postgres.sh`
- Documentación de DR (Disaster Recovery)
- Procedimiento de restore paso a paso

---

### 3. Migrate Legacy Stack and Remove Crashing Containers 🧹
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 59-72  
**Status:** ⚠️ rhinometric-license-server en loop de restart  
**Estimated time:** 3 hours  

**Tasks:**
- [ ] Exportar datos de rhinometric-postgres a license-server-postgres
- [ ] Verificar integridad de datos migrados
- [ ] Detener containers legacy: rhinometric-license-server, rhinometric-postgres, rhinometric-redis
- [ ] Eliminar containers y volúmenes legacy
- [ ] Actualizar Docker Compose para remover servicios deprecated
- [ ] Liberar recursos del servidor (expected: +100 MB RAM)

---

## 🟡 PRIORIDAD ALTA (Próximas 4 weeks)

### 4. Implement Complete Monitoring (Prometheus + Grafana + Loki) 📊
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 76-127  
**Status:** 🔄 Partially implemented  
**Estimated time:** 8 hours  

**Components:**

**A) Prometheus para Métricas**
- [ ] Instalar Prometheus container (✅ YA EXISTE en docker-compose-v2.5.0.yml)
- [ ] Configurar scraping de license-api, PostgreSQL, Redis
- [ ] Definir métricas custom:
  - `license_validations_total`
  - `license_creations_total`
  - `active_licenses_count`
  - `api_response_time_seconds`
- [ ] Configurar alertas en `prometheus.yml`

**B) Grafana para Visualización**
- [ ] Instalar Grafana container (✅ YA EXISTE)
- [ ] Conectar datasource Prometheus (✅ YA CONFIGURADO)
- [ ] Crear dashboards:
  1. Infrastructure Overview (CPU, RAM, Disk, Network)
  2. Application Metrics (Request rate, Response time, Error rate)
  3. License Analytics (Active licenses, by tier, expiring soon)
  4. Database Performance (Query duration, connections, deadlocks)
- [ ] Configurar alerting rules

**C) Loki para Logs**
- [ ] Instalar Loki container (✅ YA EXISTE)
- [ ] Configurar Docker logging driver
- [ ] Conectar Grafana a Loki datasource (✅ YA CONFIGURADO)
- [ ] Crear dashboards de logs centralizados

**Deliverables:**
- `docker-compose-monitoring.yml` (puede estar ya incluido en v2.5.0)
- 4 dashboards en Grafana
- Documentación de métricas
- Runbook de alertas

---

### 5. Automatic License Expiration Notifications 📧
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 129-151  
**Status:** ❌ Not implemented  
**Estimated time:** 6 hours  

**Functionality:**
- [ ] Cron job diario que verifica licencias próximas a expirar
- [ ] Email 30 días antes de expiración: "Su licencia expira pronto"
- [ ] Email 7 días antes: "Última semana de su licencia"
- [ ] Email 1 día antes: "Su licencia expira mañana"
- [ ] Email al expirar: "Su licencia ha expirado - Renovar ahora"

**Templates:**
- [ ] `email_expiring_30days.html`
- [ ] `email_expiring_7days.html`
- [ ] `email_expiring_1day.html`
- [ ] `email_expired.html`

**Script:**
- [ ] `check_expiring_licenses.py`
- [ ] Agregar a crontab: `0 9 * * * python3 check_expiring_licenses.py`

---

### 6. Self-Service Client Portal 🌐
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 153-184  
**Status:** ❌ Not implemented  
**Estimated time:** 16 hours  

**Features:**
- [ ] Registro de nuevo cliente
- [ ] Login de cliente existente
- [ ] Dashboard de cliente:
  - Ver sus licencias activas
  - Descargar archivos .lic
  - Ver fecha de expiración
  - Ver uso actual de hosts
  - Histórico de activaciones
- [ ] Renovar licencia (con pago)
- [ ] Upgrade de plan (Trial → Annual)
- [ ] Soporte: Crear ticket de ayuda

**Endpoints nuevos:**
- `POST /api/client/register`
- `POST /api/client/login`
- `GET /api/client/licenses`
- `GET /api/client/licenses/{key}/download`
- `POST /api/client/licenses/{key}/renew`
- `POST /api/client/support/ticket`

**Frontend:**
- Nueva carpeta: `client-portal/`
- Framework: React o Vue.js (decidir)

---

### 7. Integrated Billing System 💳
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 186-211  
**Status:** ❌ Not implemented  
**Estimated time:** 20 hours  

**Integración con Stripe:**
- [ ] Crear cuenta Stripe
- [ ] Instalar SDK de Stripe
- [ ] Endpoints de pago:
  - `POST /api/payment/create-checkout-session`
  - `POST /api/payment/webhook` (Stripe webhook)
  - `GET /api/payment/invoices/{license_key}`
- [ ] Generar PDF de factura automáticamente
- [ ] Enviar factura por email
- [ ] Marcar licencia como "pagada" en DB

**Flujo:**
1. Cliente selecciona plan
2. Redirige a Stripe Checkout
3. Cliente paga
4. Webhook notifica a Rhinometric
5. Licencia se activa automáticamente
6. Email con factura y .lic enviado

---

## 🟢 MEDIUM PRIORITY (Next 2-3 months)

### 8. Documented Public API 📚
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 215-224  
**Status:** ⚠️ API existe pero sin documentación pública  
**Estimated time:** 8 hours

**Tasks:**
- [ ] Generar documentación Swagger/OpenAPI (✅ FastAPI ya genera auto-docs)
- [ ] Publicar en `rhinometric.com/docs/api`
- [ ] Crear API keys para clientes
- [ ] Rate limiting por API key
- [ ] Ejemplos de uso en múltiples lenguajes (Python, JavaScript, curl)

---

### 9. Smart Alerts and Webhooks 🔔
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 226-247  
**Status:** ❌ Not implemented  
**Estimated time:** 10 hours

**Features:**
- [ ] Webhooks configurables por cliente
- [ ] Integración con Slack (alertas en canal)
- [ ] Integración con Microsoft Teams
- [ ] Integración con PagerDuty
- [ ] SMS via Twilio (opcional, costo adicional)

**Triggers de alerta:**
- Host down
- CPU > 90% por 5 minutes
- RAM > 90% por 5 minutes
- Disk > 85%
- Licencia expirando en 7 días
- Alcanzado 80% de max_hosts

---

### 10. Multi-Region (EU Datacenter) 🌍
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 249-261  
**Status:** ❌ Not implemented  
**Estimated time:** 40 hours

**Architecture:**
- [ ] Desplegar réplica en AWS EU (Frankfurt o Irlanda)
- [ ] Load balancer geográfico (Route 53 o Cloudflare)
- [ ] Replicación de PostgreSQL master-slave
- [ ] Redis Cluster para cache distribuido
- [ ] CDN para assets estáticos
- [ ] Latencia < 50ms para clientes EU

---

### 11. Mobile App (iOS + Android) 📱
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 263-278  
**Status:** ❌ Not implemented  
**Estimated time:** 80 hours (outsourcing recomendado)

**Funcionalidades MVP:**
- Ver dashboards principales
- Recibir push notifications de alertas
- Ver licencias activas
- Responder a alertas críticas
- Chat de soporte

**Tech Stack:**
- React Native o Flutter
- API REST de Rhinometric

---

### 12. Improvements to Existing Anomaly Detection Engine 🤖
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 280-293  
**Status:** 🔄 Basic engine implemented in v2.5.0 (puerto 8085), improvements planned for Q2 2026  
**Estimated time:** 60 hours

**Functionality:**
- ML model que aprende patrones normales de uso
- Detecta anomalías automáticamente
- Alertas predictivas: "CPU subirá >90% en próximos 10 minutes"
- Recomendaciones: "Servidor X necesita más RAM"

**Tech Stack:**
- Python scikit-learn o TensorFlow
- Time-series analysis
- Integración con Prometheus metrics

---

### 13. Native Kubernetes Monitoring ☸️
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 295-305  
**Status:** ❌ Not implemented  
**Estimated time:** 30 hours

**Features:**
- Descubrimiento automático de pods, services, nodes
- Dashboards específicos de K8s
- Health checks de deployments
- Resource limits monitoring
- Eventos de K8s centralizados

---

### 14. Custom Plugins Marketplace 🔌
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 307-315  
**Status:** 📋 Concepto  
**Estimated time:** 100 hours

**Vision:**
- Clientes pueden crear y vender plugins
- Rhinometric toma comisión (ej: 30%)
- Plugins para: integraciones, dashboards custom, alertas custom
- Instalación one-click desde Admin UI

---

## 🔵 LOW PRIORITY (Backlog - 6+ months)

### 15. White-Label Solution 🏷️
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 319-328  
**Status:** 📋 Concepto  
**Estimated time:** 60 hours

Permitir que partners revendan Rhinometric con su propia marca:
- Logo personalizable
- Colores de marca
- Dominio custom (monitoring.clienteempresa.com)
- Emails con branding del partner

---

### 16. Enterprise SSO (SAML, OAuth) 🔐
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 330-340  
**Status:** ❌ Not implemented  
**Estimated time:** 30 hours

Integración con:
- Active Directory
- Okta
- Auth0
- Google Workspace
- Azure AD

---

### 17. Cloud Cost Optimization 💸
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 342-351  
**Status:** 📋 Concepto  
**Estimated time:** 40 hours

Dashboard que muestra:
- Costos de AWS, GCP, Azure
- Recursos subutilizados
- Recomendaciones de ahorro
- Proyecciones de gasto

---

### 18. Compliance Automation (SOC 2, ISO 27001) 📋
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 353-365  
**Status:** 🔄 Parcialmente conforme  
**Estimated time:** 80 hours (con consultoría)

**Tasks:**
- Logs de auditoría completos
- Reportes de compliance automáticos
- Políticas de retención documentadas
- Encriptación end-to-end
- Penetration testing anual
- Certificación SOC 2 Type II

---

### 19. On-Premise Installer (Air-Gapped) 🏢
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 367-376  
**Status:** ⚠️ Requiere Docker, internet  
**Estimated time:** 30 hours

Para clientes que no pueden tener conexión a internet:
- Instalador offline completo
- Todas las imágenes Docker incluidas
- Base de datos pre-configurada
- Updates manuales via USB

---

### 20. Complete Multi-Tenancy 🏘️
**Source file:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 378-388  
**Status:** ⚠️ Parcial (una instancia por cliente actualmente)  
**Estimated time:** 50 hours

Permitir múltiples clientes en una sola instancia:
- Aislamiento total de datos
- Quotas por tenant
- Billing por tenant
- Admin por tenant
- Escalabilidad horizontal

---

## 📊 Effort Summary

### Breakdown by Priority

| Prioridad | Tareas | Total Hours | Equivalent in Weeks (1 dev) |
|-----------|--------|---------------|--------------------------------|
| **Critical** | 3 | ~8 hours | 1 semana |
| **High** | 7 | ~124 hours | 3-4 weeks |
| **Medium** | 7 | ~328 hours | 8-10 weeks |
| **Low** | 10 | ~440 hours | 11-13 weeks |
| **TOTAL** | **27 tareas** | **~900 hours** | **22-26 weeks** |

---

## 🎯 Proposed Roadmap

According to `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 401-483:

### Q1 2026 (Ene-Mar)
**Focus:** Stabilization and operational improvements

**Goals Q1 2026:**
- Corregir enlaces del email
- Implementar backup automático
- Migrar stack legacy
- Monitoreo completo (Prometheus + Grafana + Loki)
- Notificaciones de expiración
- Portal de cliente self-service (inicio)

**Expected result:** Platform 100% production-ready

### Q2 2026 (Abr-Jun)
**Focus:** Feature expansion

**Goals Q2 2026:**
- Sistema de facturación integrado
- API pública documentada
- Alertas inteligentes y webhooks
- Multi-región (EU datacenter)
- Mejoras del motor de anomalías (aprendizaje avanzado)

**Expected result:** Enterprise functionality

### Q3 2026 (Jul-Sep)
**Focus:** Scalability and new channels

**Goals Q3 2026:**
- Mobile app (iOS + Android)
- Kubernetes monitoring nativo
- Custom plugins marketplace
- Cloud cost optimization

**Expected result:** Multi-platform platform

### Q4 2026 (Oct-Dic)
**Focus:** Enterprise and compliance

**Goals Q4 2026:**
- White-label solution
- Enterprise SSO
- Compliance automation (SOC 2)
- On-premise installer air-gapped
- Multi-tenancy completo

**Expected result:** Enterprise-grade platform

---

## 💰 Investment Estimate

According to `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 485-518:

### Required Resources

**Development:**
- 1 Full-Stack Developer: $60K/año
- 1 DevOps Engineer: $70K/año
- 1 Frontend Developer (part-time): $30K/año
- **Total Dev:** $160K/año

**Infrastructure:**
- AWS Lightsail (actual): $120/año
- AWS Lightsail upgrade (2GB RAM): $240/año
- AWS S3 backups: $60/año
- AWS Route 53: $50/año
- Monitoring tools: $100/año
- **Total Infra:** $570/año

**Other:**
- SMTP (Zoho): $240/año
- SSL certificates: $100/año
- Testing tools: $200/año
- **Total Other:** $540/año

**TOTAL YEAR 1:** ~$161K

---

## ✅ Immediate Next Steps

According to `PENDIENTES_DESARROLLO_RHINOMETRIC.md` lines 545-571:

**This Week:**
1. [ ] Obtener URLs correctas de instalador y manuales
2. [ ] Corregir enlaces del email
3. [ ] Probar flujo completo de creación de licencia

**Next Week:**
1. [ ] Implementar backup automático
2. [ ] Migrar stack legacy
3. [ ] Liberar recursos del servidor

**This Month:**
1. [ ] Implementar Prometheus + Grafana + Loki (parcialmente hecho)
2. [ ] Crear 4 dashboards principales
3. [ ] Configurar alertas básicas
4. [ ] Implementar notificaciones de expiración

---

## Known Technical Issues

According to `ISSUES-PENDIENTES-v2.6.0.md`:

### Issue #1: Stack Legacy en Loop de Restart
**Severity:** High  
**Affected containers:** rhinometric-license-server, rhinometric-postgres, rhinometric-redis  
**Status:** ⚠️ En análisis  
**Proposed solution:** Migración a stack v2 (License Server v2)

### Issue #2: Enlaces del Email Rotos
**Severity:** Critical  
**Afecta a:** Todos los emails de licencias annual  
**Status:** ❌ Pending  
**Proposed solution:** Actualizar URLs en template HTML

### Issue #3: Capacidad del Servidor Limitada
**Severity:** Medium  
**Problem:** Servidor actual tiene 914 MB RAM, stack requiere ~6-7 GB  
**Status:** ⚠️ Funciona con limitaciones  
**Proposed solution:** Upgrade a instancia con 8 GB RAM mínimo

---

## Implementation Notes

### Tests Automatizados
**Status:** ❌ Not implementeds  
**Coverage:** 0%  
**Prioridad:** Medium (según archivos de análisis)

Pending:
- Unit tests para License Server
- Integration tests para flujos de licencias
- E2E tests para UI
- Load tests para capacidad

### Documentación
**Status:** ⚠️ 90% completa  
**Missing:**
- API pública (Swagger existe pero no publicado)
- Guías de troubleshooting avanzado
- Runbooks de operaciones
- Guías de desarrollo para contributors

---

**Document generated from verifiable repository files.**  
**Last update:** 17 de Diciembre, 2025  
**Document version:** 1.0  

---

**References:**
- `PENDIENTES_DESARROLLO_RHINOMETRIC.md` (fuente principal)
- `ISSUES-PENDIENTES-v2.6.0.md` (issues conocidos)
- `docker-compose-v2.5.0.yml` (capacidades actuales)
- `docs/v2.5.0/RELEASE_NOTES.md` (features implementadas)
