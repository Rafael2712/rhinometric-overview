# Rhinometric — Hoja de Ruta Pública

**Versión:** 2.7.0
**Mantenido por:** Equipo Rhinometric — info@rhinometric.com

---

## Estado Actual

Rhinometric 2.7.0 es la última versión, ofreciendo una plataforma de observabilidad centrada en servicios con detección de anomalías con IA, gestión de incidentes, análisis de causa raíz e inteligencia operativa a través de 21 servicios containerizados.

---

## Planificado para v2.8.0 (Q2 2026)

### Estabilidad de la Plataforma
- **Dashboard de Inicio Configurable**: Widgets seleccionables por el usuario con persistencia de layout basada en roles.
- **Monitorización de Servicios Escalable**: Paginación, búsqueda y operaciones masivas para 100–200 servicios monitorizados.
- **Migraciones de Base de Datos**: Versionado de esquema gestionado con Alembic para actualizaciones seguras.

### Distribución
- **Instalador Ansible**: Despliegue empresarial automatizado con validación previa, verificación de compatibilidad de SO y capacidad de rollback.
- **Validador de Licencias Compilado**: Binario Rust con validación basada en servicios y resistencia a manipulación (reemplaza implementación Python).

### Calidad
- **Suite de Tests**: Tests unitarios (objetivo 80% cobertura), tests de integración, tests E2E para flujos de usuario críticos.
- **Tests de Carga**: Operación validada con 100+ servicios, 1000+ flujos de métricas, 50+ grupos de anomalías, 10+ usuarios concurrentes.

### Documentación
- **Sitio de Documentación**: Portal de documentación versionado, con búsqueda y soporte multiidioma (EN/ES).

---

## Planificado para v2.9.0 (Q3 2026)

### Seguridad
- **Pista de Auditoría**: Registro completo de todas las operaciones administrativas.
- **Autenticación por API Key**: Acceso programático para automatización e integraciones.
- **Gestión de Secretos**: Integración con vault cifrado para credenciales y claves.

### Expansión de la Plataforma
- **Notificaciones Microsoft Teams**: Soporte nativo de canal Teams.
- **Integración PagerDuty**: Enrutamiento de alertas a servicios PagerDuty.

---

## Planificado para v3.0.0 (Q4 2026)

### Funcionalidades Enterprise
- **SSO/LDAP/SAML**: Integración con proveedores de identidad externos.
- **Constructor de Dashboards Nativo**: Creación de dashboards drag-and-drop sin dependencia de Grafana.
- **Arquitectura Multi-Tenant**: Aislamiento de tenants con marca por tenant, vistas de administración cross-tenant.
- **Canales de Notificación Avanzados**: OpsGenie, SMS (Twilio), webhooks personalizados.

### Mejoras de IA
- **Analítica Predictiva**: Pronósticos basados en tendencias para planificación de capacidad.
- **Ajuste de Modelos Personalizado**: Parámetros de detección de anomalías por servicio.
- **Bucle de Retroalimentación de Falsos Positivos**: Aprendizaje de falsos positivos marcados por el usuario para mejorar la precisión.

---

## Completado (v2.7.0)

| Funcionalidad | Estado |
|---------------|--------|
| Detección de Anomalías IA con Filtro MAD | ✅ Entregado |
| AI Insights (Lenguaje Natural) | ✅ Entregado |
| Motor de Reglas de Alerta | ✅ Entregado |
| Ciclo de Vida de Alertas e Historial | ✅ Entregado |
| Gestión de Incidentes (Línea Temporal/Comentarios/Etiquetas) | ✅ Entregado |
| Análisis de Causa Raíz | ✅ Entregado |
| Mapa de Servicios | ✅ Entregado |
| SLO/SLA con Presupuesto de Error | ✅ Entregado |
| Motor de Correlación (Métricas/Logs) | ✅ Entregado |
| Pipeline de Notificaciones (Slack/Email) | ✅ Entregado |
| RBAC (4 Roles) | ✅ Entregado |
| Niveles de Licencia Basados en Servicios | ✅ Entregado |
| Deep Links de Grafana | ✅ Entregado |
| Stack Docker de 21 Contenedores | ✅ Entregado |
| Infraestructura de Trazado Distribuido (Disponible) | ✅ Desplegado |

---

## Cómo Priorizamos

Los elementos se priorizan usando un framework P0–P2:

- **P0 (Imprescindible)**: Requerido para viabilidad comercial y despliegue en cliente.
- **P1 (Debería tener)**: Mejora significativamente el valor del producto y la preparación operativa.
- **P2 (Deseable)**: Mejora el posicionamiento competitivo y la experiencia del cliente.

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
