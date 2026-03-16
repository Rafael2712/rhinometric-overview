# Rhinometric — Módulos

**Versión:** 2.7.0
**Mantenido por:** Equipo Rhinometric — info@rhinometric.com

---

## Resumen de Módulos

Rhinometric está organizado en 15 módulos funcionales. La siguiente tabla resume el propósito de cada módulo, su disponibilidad por nivel de licencia y su madurez actual.

| Módulo | Propósito | Community | Professional | Enterprise | Madurez |
|--------|-----------|:---------:|:------------:|:----------:|:-------:|
| Monitorización de Servicios | Verificaciones de salud y seguimiento de disponibilidad | ✓ | ✓ | ✓ | Estable |
| Detección de Anomalías IA | Identificación automática de anomalías | — | ✓ | ✓ | Estable |
| AI Insights | Resúmenes de anomalías en lenguaje natural | — | ✓ | ✓ | Estable |
| Reglas de Alerta | Condiciones de alerta configurables | Básicas | Completas | Completas | Estable |
| Alertas | Gestión del ciclo de vida de alertas | ✓ | ✓ | ✓ | Estable |
| Historial de Alertas | Registro histórico de alertas y exportación | ✓ | ✓ | ✓ | Estable |
| Gestión de Incidentes | Seguimiento completo del ciclo de vida | — | ✓ | ✓ | Estable |
| Análisis de Causa Raíz | Identificación automática del origen de fallos | — | — | ✓ | Beta |
| Mapa de Servicios | Visualización de topología de dependencias | — | ✓ | ✓ | Estable |
| SLO/SLA | Seguimiento de presupuesto de error y cumplimiento | — | — | ✓ | Estable |
| Motor de Correlación | Enriquecimiento de contexto con señales cruzadas | — | ✓ | ✓ | Beta |
| Notificaciones | Pipeline de entrega Slack y Email | Email | Todos | Todos | Estable |
| Logs | Agregación y búsqueda centralizada de logs | ✓ | ✓ | ✓ | Estable |
| Trazado Distribuido | Exploración de trazas (requiere instrumentación) | ✓ | ✓ | ✓ | Disponible |
| RBAC | Control de acceso basado en roles | 2 roles | 3 roles | 4 roles | Estable |
| Licenciamiento | Validación de licencias basada en servicios | ✓ | ✓ | ✓ | Estable |

---

## Detalle de Módulos

### Monitorización de Servicios
Registra endpoints con URL, protocolo e intervalo de verificación. Rhinometric utiliza Blackbox Exporter para realizar verificaciones periódicas de salud, almacenando resultados en Prometheus/VictoriaMetrics. El dashboard muestra estado en tiempo real, porcentajes de disponibilidad sobre ventanas configurables y enlaces a paneles de métricas de Grafana.

**Los servicios son la entidad principal** alrededor de la cual se organiza toda la plataforma. El modelo comercial, la detección de anomalías, las alertas, la gestión de incidentes y el seguimiento de SLO hacen referencia a los servicios monitorizados como su unidad central.

**Capacidades clave:**
- Verificaciones de salud HTTP/HTTPS/TCP
- Cálculo de disponibilidad (1h, 24h, 7d, 30d)
- Agrupación de servicios con etiquetas
- Deep links a Grafana para exploración detallada de métricas

---

### Detección de Anomalías con IA
Un motor de detección de anomalías dedicado analiza series temporales de métricas desde VictoriaMetrics a intervalos regulares. Los puntos de datos que superan el umbral de anomalía se agrupan por servicio y ventana temporal. Un filtro MAD (Desviación Absoluta de la Mediana) del 30% filtra el ruido descartando grupos sin significancia estadística suficiente.

**Capacidades clave:**
- Detección automática de anomalías sin umbrales manuales
- Múltiples modelos: IsolationForest, LOF, Estadístico basado en MAD
- Puntuación de severidad (Baja, Media, Alta, Crítica)
- Agrupación de anomalías por servicio y tiempo
- Filtrado de ruido con umbral MAD

---

### AI Insights
Genera resúmenes legibles para grupos de anomalías detectados, explicando qué cambió, cuánto y el impacto operativo potencial. Los resúmenes incluyen puntuaciones de confianza y justificación de severidad.

**Capacidades clave:**
- Explicaciones de anomalías en lenguaje natural
- Puntuación de confianza
- Contexto de severidad

---

### Reglas de Alerta y Alertas
Los usuarios definen reglas con condiciones (umbral, basadas en anomalías, ausencia), servicios objetivo, ventanas de evaluación y canales de notificación. Cuando se cumplen las condiciones, se crean alertas con un ciclo de vida: disparada → confirmada → resuelta. Los períodos de enfriamiento previenen notificaciones duplicadas; los tiempos de resolución permiten resolución automática.

**Capacidades clave:**
- Condiciones de umbral, anomalía y ausencia
- Asignación de canal de notificación por regla
- Cooldown y timeout de resolución
- Gestión del ciclo de vida de alertas

---

### Gestión de Incidentes
Seguimiento completo del ciclo de vida desde la detección hasta el cierre. Máquina de estados: abierto → confirmado → investigando → resuelto → cerrado. Cada incidente tiene una línea temporal con cambios de estado, comentarios de usuario y eventos del sistema. Etiquetas, alertas vinculadas, propietarios asignados y resúmenes de resolución obligatorios soportan investigación estructurada.

**Capacidades clave:**
- Ciclo de vida de incidentes de 5 estados
- Línea temporal con comentarios de usuario y sistema
- Categorización basada en etiquetas
- Alertas y grupos de anomalías vinculados

---

### Análisis de Causa Raíz
Cuando se crea un incidente a partir de alertas de anomalías, la plataforma recorre el grafo de dependencias de servicios (del Mapa de Servicios) e identifica servicios upstream/downstream con anomalías concurrentes. Los candidatos se clasifican por precedencia temporal, profundidad de dependencia, severidad y patrón de propagación.

**Capacidades clave:**
- Recorrido del grafo de dependencias
- Clasificación temporal y basada en severidad
- Puntuación de confianza
- Activación automática al crear incidentes

---

### Mapa de Servicios
Grafo de dependencias interactivo mostrando servicios como nodos y sus relaciones como aristas dirigidas. Los colores de los nodos reflejan el estado de salud (verde/amarillo/rojo), y las anomalías activas se resaltan visualmente. Al seleccionar un nodo se muestran detalles incluyendo anomalías actuales, alertas y enlaces a Grafana.

**Capacidades clave:**
- Visualización interactiva de topología
- Superposición de estado de salud en tiempo real
- Resaltado de propagación de anomalías

---

### Seguimiento SLO/SLA
Define objetivos por servicio con métricas objetivo (disponibilidad, latencia, tasa de error), valores objetivo y ventanas de evaluación móviles. El motor calcula el cumplimiento actual y el consumo de presupuesto de error. Las alertas se disparan cuando el presupuesto cae por debajo de umbrales configurados.

**Capacidades clave:**
- Seguimiento de presupuesto de error con tasa de consumo
- Múltiples tipos de objetivos (disponibilidad, latencia, tasa de error)
- Alertas por agotamiento de presupuesto
- Soporte de metadatos SLA

---

### Motor de Correlación
Vincula métricas y logs alrededor de un evento de anomalía. Consulta VictoriaMetrics para desviaciones de métricas co-ocurrentes, Loki para entradas de logs de nivel error, y opcionalmente Jaeger para trazas cuando hay aplicaciones instrumentadas disponibles. Los resultados enriquecen las vistas de anomalías e incidentes.

**Capacidades clave:**
- Correlación de señales cruzadas (métricas + logs, opcionalmente trazas)
- Clasificación por proximidad temporal
- Enriquecimiento de anomalías e incidentes

---

### Notificaciones
Notificaciones activadas por alertas entregadas vía webhooks de Slack y email SMTP. Las plantillas incluyen insignias de severidad, valores de métricas, nombres de servicios y enlaces a la plataforma/Grafana. Los períodos de enfriamiento previenen tormentas de notificaciones durante eventos sostenidos.

**Capacidades clave:**
- Canales Slack y Email
- Asignación de canal por regla
- Cooldown y deduplicación
- Notificaciones de resolución

---

### Logs
Agregación y búsqueda centralizada de logs. Los agentes Promtail envían logs de contenedores a Loki. Los datos son accesibles a través de Grafana Explore y el Motor de Correlación.

**Capacidades clave:**
- Agregación de logs de contenedores
- Interfaz de consulta LogQL
- Integración con vistas de anomalías e incidentes

---

### Trazado Distribuido (Capacidad Disponible)
Jaeger y OpenTelemetry Collector están desplegados como parte del stack de la plataforma. La recolección de datos de trazas **requiere que las aplicaciones estén instrumentadas con SDKs de OpenTelemetry**. Actualmente, solo el backend de Rhinometric emite trazas. Para la mayoría de despliegues, las métricas y logs proporcionan las señales principales de observabilidad.

**Capacidades clave:**
- Búsqueda de trazas y visualización de cascada de spans
- Integración con Jaeger vía Grafana
- Disponible para servicios instrumentados con OTel

---

### RBAC
Sistema de permisos con cuatro roles aplicado a nivel de API (middleware FastAPI) e interfaz (guardas de rutas React). Owner gestiona usuarios y licencias. Admin gestiona funcionalidades de monitoreo. Operador maneja alertas e incidentes. Visor tiene acceso de solo lectura a la plataforma.

| Rol | Usuarios | Servicios | Alertas | Incidentes | Configuración |
|-----|:--------:|:---------:|:-------:|:----------:|:-------------:|
| Owner | Gestionar | Gestionar | Completo | Completo | Completo |
| Admin | Ver | Gestionar | Completo | Completo | Limitado |
| Operador | Ver | Ver | Crear | Gestionar | — |
| Visor | — | Ver | Ver | Ver | — |

---

### Licenciamiento
Validación de licencias basada en servicios con tres niveles. Cada nivel define el número máximo de servicios monitorizados y las funcionalidades disponibles. El License Server valida claves al inicio y periódicamente. La License UI proporciona una interfaz independiente para la entrada de claves y visualización de estado.

| Nivel | Máx. Servicios | Funciones IA | Módulos Avanzados |
|-------|:--------------:|:------------:|:-----------------:|
| Community | 10 | — | — |
| Professional | 50 | ✓ | Parcial |
| Enterprise | Ilimitados | ✓ | Completo |

---

## Mapa de Interacción de Módulos

```
Servicios ──▶ Anomalías IA ──▶ AI Insights
                │
                ├──▶ Reglas de Alerta ──▶ Alertas ──▶ Notificaciones
                │                           │
                │                           ▼
                │                  Gestión de Incidentes ──▶ Causa Raíz
                │
                ├──▶ Motor de Correlación
                │         │
                │         ├── Logs (Loki)
                │         └── Trazas (Jaeger, cuando disponible)
                │
                └──▶ Mapa de Servicios
                          │
                          └──▶ Causa Raíz

SLO/SLA ◀── Servicios + Reglas de Alerta
RBAC ──▶ Todos los módulos (aplicación de permisos)
Licenciamiento ──▶ Todos los módulos (gating de funcionalidades + límites de servicios)
```

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
