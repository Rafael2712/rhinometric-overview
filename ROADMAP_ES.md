# Rhinometric — Hoja de Ruta Pública

**Versión:** 2.7.0  
**Mantenido por:** Rhinometric Team — info@rhinometric.com

---

## Estado Actual

Rhinometric 2.7.0 es la versión más reciente, proporcionando detección de anomalías con IA, gestión de incidentes, análisis de causa raíz y un stack de observabilidad completo con 21 servicios contenedorizados.

---

## Planificado para v2.8.0 (Q2 2026)

### Estabilidad de la Plataforma
- **Monitoreo de Servicios Escalable**: Paginación, búsqueda y operaciones masivas para 100+ servicios.
- **Panel de Inicio Configurable**: Widgets seleccionables por usuario con persistencia de diseño por rol.
- **Migraciones de Base de Datos**: Versionado de esquema gestionado con Alembic para actualizaciones seguras.

### Distribución
- **Instalador Ansible**: Despliegue empresarial automatizado con validación previa, verificaciones de compatibilidad de SO y capacidad de rollback.
- **Validador de Licencias Compilado**: Binario de validación de licencias en Rust con huella de hardware (reemplaza implementación en Python).

### Calidad
- **Suite de Tests**: Tests unitarios (objetivo 80% cobertura), tests de integración, tests E2E para flujos críticos de usuario.
- **Tests de Carga**: Operación validada con 100+ servicios, 1000+ flujos de métricas, 50+ grupos de anomalías, 10+ usuarios concurrentes.

---

## Planificado para v2.9.0 (Q3 2026)

### Seguridad
- **Registro de Auditoría**: Log completo de todas las operaciones administrativas.
- **Autenticación por API Key**: Acceso programático para automatización e integraciones.
- **Gestión de Secretos**: Integración con vault cifrado para credenciales y llaves.

### Expansión de la Plataforma
- **Notificaciones Microsoft Teams**: Soporte nativo de canal Teams.
- **Integración PagerDuty**: Enrutamiento de alertas a servicios PagerDuty.

---

## Planificado para v3.0.0 (Q4 2026)

### Funcionalidades Enterprise
- **SSO/LDAP/SAML**: Integración con proveedores de identidad externos.
- **Constructor de Paneles Nativo**: Creación de paneles con arrastrar y soltar sin dependencia de Grafana.
- **Arquitectura Multi-Tenant**: Aislamiento por tenant con branding personalizado y vistas de administración cruzada.
- **Canales de Notificación Avanzados**: OpsGenie, SMS (Twilio), webhooks personalizados.

### Mejoras de IA
- **Analítica Predictiva**: Pronósticos basados en tendencias para planificación de capacidad.
- **Ajuste de Modelo Personalizado**: Parámetros de detección de anomalías por servicio.
- **Bucle de Retroalimentación de Falsos Positivos**: Aprendizaje de falsos positivos marcados por el usuario para mejorar precisión.

---

## Completado (v2.7.0)

| Funcionalidad | Estado |
|---------------|--------|
| Detección de Anomalías IA con Filtro MAD | ✅ Entregado |
| AI Insights (Lenguaje Natural) | ✅ Entregado |
| Motor de Reglas de Alerta | ✅ Entregado |
| Ciclo de Vida de Alertas e Historial | ✅ Entregado |
| Gestión de Incidentes (Timeline/Comentarios/Tags) | ✅ Entregado |
| Análisis de Causa Raíz | ✅ Entregado |
| Mapa de Servicios | ✅ Entregado |
| SLO/SLA con Presupuesto de Error | ✅ Entregado |
| Motor de Correlación (Métricas/Logs/Trazas) | ✅ Entregado |
| Pipeline de Notificaciones (Slack/Email) | ✅ Entregado |
| RBAC (4 Roles) | ✅ Entregado |
| Licenciamiento con Huella de Hardware | ✅ Entregado |
| Deep Links de Grafana | ✅ Entregado |
| Stack Docker de 21 Contenedores | ✅ Entregado |

---

## Cómo Priorizamos

Los elementos se priorizan usando un marco P0–P2:

- **P0 (Debe Tener)**: Requerido para viabilidad comercial y despliegue en clientes.
- **P1 (Debería Tener)**: Mejora significativamente el valor del producto y la preparación operativa.
- **P2 (Deseable)**: Mejora el posicionamiento competitivo y la experiencia del cliente.

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
