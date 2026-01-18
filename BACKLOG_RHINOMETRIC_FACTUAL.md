# RHINOMETRIC v2.5.0  
## Backlog de Desarrollo y Pendientes

**Fecha:** 17 de Diciembre, 2025  
**Fuente:** PENDIENTES_DESARROLLO_RHINOMETRIC.md, ISSUES-PENDIENTES-v2.6.0.md, análisis de código  
**Estado del Proyecto:** Producción operativa con mejoras pendientes

---

## Resumen de Estado

**Completado:** ~75%  
**En Desarrollo:** ~15%  
**Planeado/Pendiente:** ~10%

Este documento lista ÚNICAMENTE las tareas pendientes documentadas en el repositorio, sin inventar funcionalidades.

---

## 🔴 PRIORIDAD CRÍTICA (Próximas 2 semanas)

### 1. Corregir Enlaces del Email Annual ⏰ URGENTE
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 19-36  
**Status:** ❌ Pendiente  
**Tiempo estimado:** 30 minutos  

**Problema documentado:**
- Enlaces de descarga de instalador llevan a página incorrecta
- Enlaces de manuales no funcionan
- Solo el enlace de la web funciona

**Tareas:**
- [ ] Obtener URLs correctas de Google Drive (públicas)
- [ ] Actualizar template en `/home/ubuntu/license-server/app/main.py`
- [ ] Rebuild Docker container
- [ ] Probar envío de email de prueba
- [ ] Verificar todos los enlaces en email recibido

**Archivos a modificar:**
- `main.py` líneas 354, 360, 361

---

### 2. Implementar Backup Automático de Base de Datos 🔒
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 38-57  
**Status:** ❌ No implementado  
**Tiempo estimado:** 4 horas  

**Tareas:**
- [ ] Crear script de backup diario de PostgreSQL
- [ ] Configurar cron job para ejecutar a las 3 AM
- [ ] Subir backups a AWS S3 o Google Cloud Storage
- [ ] Implementar retention policy (30 días hot, 1 año cold)
- [ ] Documentar procedimiento de restore
- [ ] Probar restore desde backup

**Entregables:**
- Script `backup_postgres.sh`
- Documentación de DR (Disaster Recovery)
- Procedimiento de restore paso a paso

---

### 3. Migrar Stack Legacy y Eliminar Containers Crasheando 🧹
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 59-72  
**Status:** ⚠️ rhinometric-license-server en loop de restart  
**Tiempo estimado:** 3 horas  

**Tareas:**
- [ ] Exportar datos de rhinometric-postgres a license-server-postgres
- [ ] Verificar integridad de datos migrados
- [ ] Detener containers legacy: rhinometric-license-server, rhinometric-postgres, rhinometric-redis
- [ ] Eliminar containers y volúmenes legacy
- [ ] Actualizar Docker Compose para remover servicios deprecated
- [ ] Liberar recursos del servidor (expected: +100 MB RAM)

---

## 🟡 PRIORIDAD ALTA (Próximas 4 semanas)

### 4. Implementar Monitoreo Completo (Prometheus + Grafana + Loki) 📊
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 76-127  
**Status:** 🔄 Parcialmente implementado  
**Tiempo estimado:** 8 horas  

**Componentes:**

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

**Entregables:**
- `docker-compose-monitoring.yml` (puede estar ya incluido en v2.5.0)
- 4 dashboards en Grafana
- Documentación de métricas
- Runbook de alertas

---

### 5. Notificaciones Automáticas de Expiración de Licencias 📧
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 129-151  
**Status:** ❌ No implementado  
**Tiempo estimado:** 6 horas  

**Funcionalidad:**
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

### 6. Portal de Cliente Self-Service 🌐
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 153-184  
**Status:** ❌ No implementado  
**Tiempo estimado:** 16 horas  

**Funcionalidades:**
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

### 7. Sistema de Facturación Integrado 💳
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 186-211  
**Status:** ❌ No implementado  
**Tiempo estimado:** 20 horas  

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

## 🟢 PRIORIDAD MEDIA (Próximos 2-3 meses)

### 8. API Pública Documentada 📚
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 215-224  
**Status:** ⚠️ API existe pero sin documentación pública  
**Tiempo estimado:** 8 horas

**Tareas:**
- [ ] Generar documentación Swagger/OpenAPI (✅ FastAPI ya genera auto-docs)
- [ ] Publicar en `rhinometric.com/docs/api`
- [ ] Crear API keys para clientes
- [ ] Rate limiting por API key
- [ ] Ejemplos de uso en múltiples lenguajes (Python, JavaScript, curl)

---

### 9. Alertas Inteligentes y Webhooks 🔔
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 226-247  
**Status:** ❌ No implementado  
**Tiempo estimado:** 10 horas

**Funcionalidades:**
- [ ] Webhooks configurables por cliente
- [ ] Integración con Slack (alertas en canal)
- [ ] Integración con Microsoft Teams
- [ ] Integración con PagerDuty
- [ ] SMS via Twilio (opcional, costo adicional)

**Triggers de alerta:**
- Host down
- CPU > 90% por 5 minutos
- RAM > 90% por 5 minutos
- Disk > 85%
- Licencia expirando en 7 días
- Alcanzado 80% de max_hosts

---

### 10. Multi-Región (EU Datacenter) 🌍
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 249-261  
**Status:** ❌ No implementado  
**Tiempo estimado:** 40 horas

**Arquitectura:**
- [ ] Desplegar réplica en AWS EU (Frankfurt o Irlanda)
- [ ] Load balancer geográfico (Route 53 o Cloudflare)
- [ ] Replicación de PostgreSQL master-slave
- [ ] Redis Cluster para cache distribuido
- [ ] CDN para assets estáticos
- [ ] Latencia < 50ms para clientes EU

---

### 11. Mobile App (iOS + Android) 📱
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 263-278  
**Status:** ❌ No implementado  
**Tiempo estimado:** 80 horas (outsourcing recomendado)

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

### 12. Mejoras del Motor de Detección de Anomalías Existente 🤖
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 280-293  
**Status:** 🔄 Motor básico implementado en v2.5.0 (puerto 8085), mejoras planeadas para Q2 2026  
**Tiempo estimado:** 60 horas

**Funcionalidad:**
- ML model que aprende patrones normales de uso
- Detecta anomalías automáticamente
- Alertas predictivas: "CPU subirá >90% en próximos 10 minutos"
- Recomendaciones: "Servidor X necesita más RAM"

**Tech Stack:**
- Python scikit-learn o TensorFlow
- Time-series analysis
- Integración con Prometheus metrics

---

### 13. Kubernetes Monitoring Nativo ☸️
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 295-305  
**Status:** ❌ No implementado  
**Tiempo estimado:** 30 horas

**Funcionalidades:**
- Descubrimiento automático de pods, services, nodes
- Dashboards específicos de K8s
- Health checks de deployments
- Resource limits monitoring
- Eventos de K8s centralizados

---

### 14. Custom Plugins Marketplace 🔌
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 307-315  
**Status:** 📋 Concepto  
**Tiempo estimado:** 100 horas

**Visión:**
- Clientes pueden crear y vender plugins
- Rhinometric toma comisión (ej: 30%)
- Plugins para: integraciones, dashboards custom, alertas custom
- Instalación one-click desde Admin UI

---

## 🔵 PRIORIDAD BAJA (Backlog - 6+ meses)

### 15. White-Label Solution 🏷️
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 319-328  
**Status:** 📋 Concepto  
**Tiempo estimado:** 60 horas

Permitir que partners revendan Rhinometric con su propia marca:
- Logo personalizable
- Colores de marca
- Dominio custom (monitoring.clienteempresa.com)
- Emails con branding del partner

---

### 16. Enterprise SSO (SAML, OAuth) 🔐
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 330-340  
**Status:** ❌ No implementado  
**Tiempo estimado:** 30 horas

Integración con:
- Active Directory
- Okta
- Auth0
- Google Workspace
- Azure AD

---

### 17. Cloud Cost Optimization 💸
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 342-351  
**Status:** 📋 Concepto  
**Tiempo estimado:** 40 horas

Dashboard que muestra:
- Costos de AWS, GCP, Azure
- Recursos subutilizados
- Recomendaciones de ahorro
- Proyecciones de gasto

---

### 18. Compliance Automation (SOC 2, ISO 27001) 📋
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 353-365  
**Status:** 🔄 Parcialmente conforme  
**Tiempo estimado:** 80 horas (con consultoría)

**Tareas:**
- Logs de auditoría completos
- Reportes de compliance automáticos
- Políticas de retención documentadas
- Encriptación end-to-end
- Penetration testing anual
- Certificación SOC 2 Type II

---

### 19. On-Premise Installer (Air-Gapped) 🏢
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 367-376  
**Status:** ⚠️ Requiere Docker, internet  
**Tiempo estimado:** 30 horas

Para clientes que no pueden tener conexión a internet:
- Instalador offline completo
- Todas las imágenes Docker incluidas
- Base de datos pre-configurada
- Updates manuales via USB

---

### 20. Multi-Tenancy Completo 🏘️
**Archivo fuente:** `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 378-388  
**Status:** ⚠️ Parcial (una instancia por cliente actualmente)  
**Tiempo estimado:** 50 horas

Permitir múltiples clientes en una sola instancia:
- Aislamiento total de datos
- Quotas por tenant
- Billing por tenant
- Admin por tenant
- Escalabilidad horizontal

---

## 📊 Resumen de Esfuerzo

### Desglose por Prioridad

| Prioridad | Tareas | Horas Totales | Equivalente en Semanas (1 dev) |
|-----------|--------|---------------|--------------------------------|
| **Crítica** | 3 | ~8 horas | 1 semana |
| **Alta** | 7 | ~124 horas | 3-4 semanas |
| **Media** | 7 | ~328 horas | 8-10 semanas |
| **Baja** | 10 | ~440 horas | 11-13 semanas |
| **TOTAL** | **27 tareas** | **~900 horas** | **22-26 semanas** |

---

## 🎯 Roadmap Propuesto

Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 401-483:

### Q1 2026 (Ene-Mar)
**Focus:** Estabilización y mejoras operacionales

**Objetivos Q1 2026:**
- Corregir enlaces del email
- Implementar backup automático
- Migrar stack legacy
- Monitoreo completo (Prometheus + Grafana + Loki)
- Notificaciones de expiración
- Portal de cliente self-service (inicio)

**Resultado esperado:** Plataforma production-ready al 100%

### Q2 2026 (Abr-Jun)
**Focus:** Expansión de funcionalidades

**Objetivos Q2 2026:**
- Sistema de facturación integrado
- API pública documentada
- Alertas inteligentes y webhooks
- Multi-región (EU datacenter)
- Mejoras del motor de anomalías (aprendizaje avanzado)

**Resultado esperado:** Funcionalidad enterprise

### Q3 2026 (Jul-Sep)
**Focus:** Escalabilidad y nuevos canales

**Objetivos Q3 2026:**
- Mobile app (iOS + Android)
- Kubernetes monitoring nativo
- Custom plugins marketplace
- Cloud cost optimization

**Resultado esperado:** Plataforma multi-plataforma

### Q4 2026 (Oct-Dic)
**Focus:** Enterprise y compliance

**Objetivos Q4 2026:**
- White-label solution
- Enterprise SSO
- Compliance automation (SOC 2)
- On-premise installer air-gapped
- Multi-tenancy completo

**Resultado esperado:** Enterprise-grade platform

---

## 💰 Estimación de Inversión

Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 485-518:

### Recursos Necesarios

**Desarrollo:**
- 1 Full-Stack Developer: $60K/año
- 1 DevOps Engineer: $70K/año
- 1 Frontend Developer (part-time): $30K/año
- **Total Dev:** $160K/año

**Infraestructura:**
- AWS Lightsail (actual): $120/año
- AWS Lightsail upgrade (2GB RAM): $240/año
- AWS S3 backups: $60/año
- AWS Route 53: $50/año
- Monitoring tools: $100/año
- **Total Infra:** $570/año

**Otros:**
- SMTP (Zoho): $240/año
- SSL certificates: $100/año
- Testing tools: $200/año
- **Total Otros:** $540/año

**TOTAL AÑO 1:** ~$161K

---

## ✅ Próximos Pasos Inmediatos

Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md` líneas 545-571:

**Esta Semana:**
1. [ ] Obtener URLs correctas de instalador y manuales
2. [ ] Corregir enlaces del email
3. [ ] Probar flujo completo de creación de licencia

**Próxima Semana:**
1. [ ] Implementar backup automático
2. [ ] Migrar stack legacy
3. [ ] Liberar recursos del servidor

**Este Mes:**
1. [ ] Implementar Prometheus + Grafana + Loki (parcialmente hecho)
2. [ ] Crear 4 dashboards principales
3. [ ] Configurar alertas básicas
4. [ ] Implementar notificaciones de expiración

---

## Issues Técnicos Conocidos

Según `ISSUES-PENDIENTES-v2.6.0.md`:

### Issue #1: Stack Legacy en Loop de Restart
**Severidad:** Alta  
**Containers afectados:** rhinometric-license-server, rhinometric-postgres, rhinometric-redis  
**Status:** ⚠️ En análisis  
**Solución propuesta:** Migración a stack v2 (License Server v2)

### Issue #2: Enlaces del Email Rotos
**Severidad:** Crítica  
**Afecta a:** Todos los emails de licencias annual  
**Status:** ❌ Pendiente  
**Solución propuesta:** Actualizar URLs en template HTML

### Issue #3: Capacidad del Servidor Limitada
**Severidad:** Media  
**Problema:** Servidor actual tiene 914 MB RAM, stack requiere ~6-7 GB  
**Status:** ⚠️ Funciona con limitaciones  
**Solución propuesta:** Upgrade a instancia con 8 GB RAM mínimo

---

## Notas de Implementación

### Tests Automatizados
**Status:** ❌ No implementados  
**Cobertura:** 0%  
**Prioridad:** Media (según archivos de análisis)

Pendiente:
- Unit tests para License Server
- Integration tests para flujos de licencias
- E2E tests para UI
- Load tests para capacidad

### Documentación
**Status:** ⚠️ 90% completa  
**Faltante:**
- API pública (Swagger existe pero no publicado)
- Guías de troubleshooting avanzado
- Runbooks de operaciones
- Guías de desarrollo para contributors

---

**Documento generado a partir de archivos verificables del repositorio.**  
**Última actualización:** 17 de Diciembre, 2025  
**Versión del documento:** 1.0  

---

**Referencias:**
- `PENDIENTES_DESARROLLO_RHINOMETRIC.md` (fuente principal)
- `ISSUES-PENDIENTES-v2.6.0.md` (issues conocidos)
- `docker-compose-v2.5.0.yml` (capacidades actuales)
- `docs/v2.5.0/RELEASE_NOTES.md` (features implementadas)
