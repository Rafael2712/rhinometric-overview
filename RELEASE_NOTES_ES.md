# Rhinometric — Notas de Versión

**Mantenido por:** Rhinometric Team — info@rhinometric.com

---

## [2.7.0] — 2026-03-15

### Añadido
- **Módulo AI Insights**: Resúmenes de anomalías en lenguaje natural generados por el detector de IA, mostrados por grupo con puntuación de severidad y confianza.
- **Módulo de Análisis de Causa Raíz**: Recorrido automático de topología y clasificación de causas raíz cuando se crea un incidente desde alertas de anomalía.
- **Mapa de Servicios**: Grafo de dependencias en vivo mostrando interconexiones, estado de salud y rutas de propagación de anomalías.
- **Módulo SLO/SLA**: Objetivos de Nivel de Servicio configurables con seguimiento de presupuesto de error y alertas por violación.
- **Motor de Correlación**: Análisis de señales cruzadas que vincula métricas, logs y trazas con eventos de anomalía.
- **Gestión de Incidentes**: Gestión completa del ciclo de vida con línea de tiempo, comentarios (internos + sistema), asignación de etiquetas y máquina de estados (abierto → reconocido → investigando → resuelto → cerrado).
- **Historial de Alertas**: Registro persistente de todas las alertas con búsqueda, filtros y exportación CSV.
- **Motor de Reglas de Alerta**: Alertas basadas en reglas con condiciones de umbral, tasa de cambio y ausencia.
- **Pipeline de Notificaciones**: Notificaciones por Slack y email activadas por reglas de alerta. Canales configurables por regla con mapeo de severidad.
- **Sistema de Deep Links**: Links directos a Grafana generados por servicio/anomalía con contexto de rango temporal. Paneles para CPU, memoria, latencia, errores HTTP y saturación.
- **Sistema RBAC**: Control de acceso basado en roles con 4 roles (SuperAdmin, Admin, Operador, Visor) aplicado tanto a nivel de API como de interfaz.
- **Módulo de Licenciamiento**: Validación de licencias con huella de hardware y control por niveles (Community, Professional, Enterprise).
- **Filtro de Umbral MAD 30%**: El detector de anomalías rechaza grupos donde menos del 30% de los puntos superen el umbral de Desviación Absoluta de la Mediana.
- **Enfriamiento de Notificaciones**: Enfriamiento configurable por regla que previene notificaciones duplicadas durante eventos sostenidos.
- **Tiempo de Resolución Automática**: Resolución automática de alertas tras un período configurable sin nuevos datos de anomalía.

### Cambiado
- Los deep links de Grafana usan URLs directas de dashboard en lugar de redirecciones vía API.
- Las plantillas de notificación incluyen insignia de severidad, valores de métricas y enlaces directos.
- Manejo de errores en frontend: las respuestas 401 en páginas protegidas redirigen al login.
- Página de Anomalías IA: Manejo elegante de la expiración de autenticación con respaldo visual.
- Backend: Respuestas de error JSON estandarizadas para todos los routers.

### Corregido
- Pipeline de notificaciones: Eliminadas las duplicaciones de email cuando múltiples grupos de anomalías se resuelven simultáneamente dentro de la misma ventana de enfriamiento.
- Pipeline de notificaciones: Corregida condición de carrera donde la creación de incidente y la resolución de alerta podían disparar notificaciones conflictivas.
- Sistema de alertas: Corregida la lógica de reinicio del temporizador de enfriamiento que permitía re-notificación prematura en incidentes de larga duración.
- Página de Anomalías IA: Corregido error 401 cuando el token expira durante la sesión.
- Deep links de Grafana: Corregido cálculo incorrecto del rango temporal para URLs de paneles.

### Seguridad
- Validación de token JWT aplicada en todas las rutas API (excepto `/health` y `/auth/login`).
- Política CORS restringida al origen de frontend conocido.
- Limitación de tasa aplicada a endpoints de autenticación.

---

## [2.5.0] — 2024-11-15

### Añadido
- **Documentación Pública**: Primera documentación de producto orientada al público.
- **Matriz de Funcionalidades**: Comparación de capacidades publicada entre niveles de licencia.
- **Sistema de Branding**: Identidad de marca Rhinometric aplicada al frontend con logo, colores y tipografía.
- **Detección de Anomalías IA v1**: Despliegue inicial del detector basado en IsolationForest como servicio Python contenedorizado.
- **Integración VictoriaMetrics**: Almacenamiento de métricas a largo plazo reemplazando la retención de Prometheus.
- **Trazado Jaeger**: Recolección de trazas distribuidas vía OpenTelemetry Collector.
- **Agregación de Logs Loki**: Recolección centralizada de logs con agentes Promtail.

### Cambiado
- Frontend migrado de Create React App a Vite.
- Autenticación cambiada de basada en sesión a JWT.
- Prometheus reconfigurado como buffer a corto plazo (retención 15 días) con VictoriaMetrics como almacén a largo plazo.

---

## [2.1.0] — 2024-09-01

### Añadido
- Monitoreo básico de servicios con recolección de métricas Prometheus.
- Alertas básicas vía Alertmanager con notificación por email.
- Paneles de Grafana para métricas de infraestructura y servicios.
- Frontend inicial con React 18 + TypeScript.
- Base de datos PostgreSQL para estado de la plataforma.
- Capa de caché Redis.
- Despliegue con Docker Compose con 15 servicios.
- Proxy inverso Nginx con terminación SSL.

### Problemas Conocidos
- Sin sistema de migración de base de datos.
- Limitado a despliegue en un solo nodo.
- Sin instalador automatizado.

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
