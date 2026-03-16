# Rhinometric — Notas de Versión

**Mantenido por:** Equipo Rhinometric — info@rhinometric.com

---

## Versión 2.7.0 — Marzo 2026

### Destacados

La versión 2.7.0 representa una expansión importante de la plataforma, pasando de monitorización a observabilidad completa centrada en servicios y gestión de incidentes. Esta versión introduce análisis de anomalías con IA, ciclo de vida completo de incidentes, análisis de causa raíz, seguimiento de SLO y un pipeline de notificaciones — transformando Rhinometric en una plataforma de inteligencia operativa organizada alrededor de servicios monitorizados.

### Nuevos Módulos

| Módulo | Descripción |
|--------|-------------|
| **AI Insights** | Resúmenes de anomalías en lenguaje natural con puntuación de confianza y severidad |
| **Análisis de Causa Raíz** | Recorrido automatizado del grafo de dependencias para identificar el origen de fallos |
| **Mapa de Servicios** | Visualización de topología en tiempo real con superposición de estado de salud |
| **Gestión SLO/SLA** | Seguimiento de presupuesto de error con alertas proactivas de incumplimiento |
| **Motor de Correlación** | Vinculación de señales cruzadas de métricas y logs para enriquecimiento de contexto |
| **Gestión de Incidentes** | Ciclo de vida completo con línea temporal, comentarios, etiquetas y máquina de estados |
| **Historial de Alertas** | Registro persistente y buscable de todas las alertas con exportación CSV |
| **Reglas de Alerta** | Condiciones configurables con tipos de umbral, anomalía y ausencia |
| **Pipeline de Notificaciones** | Entrega por Slack y email con cooldown y deduplicación |
| **RBAC** | Sistema de permisos con cuatro roles aplicado a nivel de API e interfaz |

### Mejoras

- **Deep Links de Grafana**: URLs directas a dashboards con contexto de rango temporal para paneles de CPU, memoria, latencia, errores HTTP y saturación.
- **Detección de Anomalías IA**: Filtro de umbral MAD del 30% reduce falsos positivos filtrando grupos de anomalías estadísticamente insignificantes.
- **Manejo de Errores Frontend**: Gestión elegante de 401 con redirección a login en lugar de estados de UI rotos.
- **Plantillas de Notificación**: Plantillas enriquecidas con insignias de severidad, snapshots de métricas y enlaces de acción.
- **Backend API**: Respuestas de error JSON estandarizadas en los 20 routers.

### Correcciones

- Corregidas notificaciones de email duplicadas durante resolución simultánea de grupos de anomalías dentro de la misma ventana de cooldown.
- Corregida condición de carrera entre creación de incidentes y resolución de alertas causando notificaciones conflictivas.
- Corregida lógica de reinicio del temporizador de cooldown que permitía re-notificación prematura en incidentes de larga duración.
- Corregido error 401 en la página de Anomalías IA cuando el token de autenticación expira a mitad de sesión.
- Corregido cálculo incorrecto de rango temporal en URLs de deep links de Grafana.

### Infraestructura

- 21 contenedores Docker ejecutándose en configuración de producción.
- Motor de detección de anomalías desplegado como servicio containerizado dedicado.
- License Server v2 operativo con validación de niveles basada en servicios.
- Stack de observabilidad: Prometheus, VictoriaMetrics, Loki, Grafana, Alertmanager, con trazado distribuido opcional vía Jaeger/OTel Collector.

---

## Versión 2.5.0 — Noviembre 2024

### Destacados

Primera versión pública con documentación de producto y marca. Introdujo detección de anomalías con IA, almacenamiento de métricas a largo plazo y el stack principal de observabilidad.

### Nuevas Funcionalidades

- Detección de Anomalías IA v1 (basada en IsolationForest).
- Integración de VictoriaMetrics para retención de métricas a largo plazo.
- Agregación de logs Loki con agentes Promtail.
- Infraestructura de trazado distribuido desplegada (Jaeger + OTel Collector) — disponible para aplicaciones instrumentadas.
- Identidad de marca Rhinometric aplicada al frontend.
- Documentación pública del producto.

### Cambios

- Frontend migrado de Create React App a Vite.
- Autenticación cambiada de basada en sesión a JWT.
- Prometheus reconfigurado como buffer de corto plazo de 15 días con VictoriaMetrics como almacén de largo plazo.

---

## Versión 2.1.0 — Septiembre 2024

### Destacados

Lanzamiento inicial de la plataforma con capacidades de monitorización de servicios básicas.

### Funcionalidades

- Monitorización de servicios con recolección de métricas Prometheus.
- Alertas básicas vía Alertmanager con notificación por email.
- Dashboards de Grafana para métricas de infraestructura y servicios.
- Frontend React 18 + TypeScript.
- Base de datos PostgreSQL para estado de la plataforma.
- Capa de caché Redis.
- Despliegue Docker Compose con 15 servicios.
- Proxy inverso Nginx con terminación SSL.

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
