# Rhinometric — Módulos

**Versión:** 2.7.0  
**Mantenido por:** Rhinometric Team — info@rhinometric.com

---

## Resumen de Módulos

Rhinometric está organizado en 15 módulos funcionales. La tabla siguiente resume el propósito de cada módulo, su disponibilidad por nivel de licencia y su madurez actual.

| Módulo | Propósito | Community | Professional | Enterprise | Madurez |
|--------|-----------|:---------:|:------------:|:----------:|:-------:|
| Monitoreo de Servicios | Verificaciones de salud y seguimiento de disponibilidad | ✓ | ✓ | ✓ | Estable |
| Detección de Anomalías IA | Identificación automática de anomalías | — | ✓ | ✓ | Estable |
| Insights de IA | Resúmenes de anomalías en lenguaje natural | — | ✓ | ✓ | Estable |
| Reglas de Alerta | Condiciones de alerta configurables | Básico | Completo | Completo | Estable |
| Alertas | Gestión del ciclo de vida de alertas | ✓ | ✓ | ✓ | Estable |
| Historial de Alertas | Registro histórico de alertas y exportación | ✓ | ✓ | ✓ | Estable |
| Gestión de Incidentes | Seguimiento completo del ciclo de vida de incidentes | — | ✓ | ✓ | Estable |
| Análisis de Causa Raíz | Identificación automática del origen de fallas | — | — | ✓ | Beta |
| Mapa de Servicios | Visualización de topología de dependencias | — | ✓ | ✓ | Estable |
| SLO/SLA | Seguimiento de presupuesto de error y cumplimiento | — | — | ✓ | Estable |
| Motor de Correlación | Enriquecimiento de contexto con señales cruzadas | — | ✓ | ✓ | Beta |
| Notificaciones | Pipeline de entrega por Slack y Email | Email | Todos | Todos | Estable |
| Logs y Trazas | Acceso centralizado a logs y trazas | ✓ | ✓ | ✓ | Estable |
| RBAC | Control de acceso basado en roles | 2 roles | 3 roles | 4 roles | Estable |
| Licenciamiento | Validación de licencias y control por niveles | ✓ | ✓ | ✓ | Estable |

---

## Detalle de Módulos

### Monitoreo de Servicios
Registre endpoints con URL, protocolo e intervalo de verificación. Rhinometric utiliza Blackbox Exporter para realizar sondeos periódicos de salud, almacenando los resultados en Prometheus/VictoriaMetrics. El panel muestra estado en tiempo real, porcentajes de disponibilidad sobre ventanas configurables y enlaces a paneles de métricas en Grafana.

**Capacidades clave:**
- Sondeos de salud HTTP/HTTPS/TCP
- Cálculo de disponibilidad (1h, 24h, 7d, 30d)
- Agrupación de servicios con etiquetas
- Deep links a Grafana para exploración de métricas

---

### Detección de Anomalías con IA
Un modelo IsolationForest contenedorizado analiza series temporales de métricas desde VictoriaMetrics a intervalos regulares. Los puntos de datos que superan el umbral de anomalía se agrupan por servicio y ventana temporal. Un filtro de 30% MAD (Desviación Absoluta de la Mediana) reduce el ruido descartando grupos sin significancia estadística suficiente.

**Capacidades clave:**
- Detección automática de anomalías sin umbrales manuales
- Puntuación de severidad (Baja, Media, Alta, Crítica)
- Agrupación de anomalías por servicio y tiempo
- Filtrado de ruido con umbral MAD

---

### Insights de IA
Genera resúmenes legibles para grupos de anomalías detectadas, explicando qué cambió, en qué magnitud y el impacto operativo potencial. Los resúmenes incluyen puntuaciones de confianza y justificación de severidad.

**Capacidades clave:**
- Explicaciones de anomalías en lenguaje natural
- Puntuación de confianza
- Contexto de severidad

---

### Reglas de Alerta y Alertas
Los usuarios definen reglas con condiciones (umbral, basada en anomalía, ausencia), servicios objetivo, ventanas de evaluación y canales de notificación. Cuando las condiciones se cumplen, se crean alertas con un ciclo de vida: disparada → reconocida → resuelta. Los períodos de enfriamiento previenen notificaciones duplicadas; los tiempos de resolución automática permiten resolver alertas automáticamente.

**Capacidades clave:**
- Condiciones de umbral, anomalía y ausencia
- Asignación de canal de notificación por regla
- Enfriamiento y tiempo de resolución automática
- Gestión del ciclo de vida de alertas

---

### Gestión de Incidentes
Seguimiento completo del ciclo de vida de incidentes desde la detección hasta el cierre. Máquina de estados: abierto → reconocido → investigando → resuelto → cerrado. Cada incidente tiene una línea de tiempo con cambios de estado, comentarios de usuario y eventos del sistema. Etiquetas, alertas vinculadas, propietarios asignados y resúmenes de resolución obligatorios soportan una investigación estructurada.

**Capacidades clave:**
- Ciclo de vida de incidentes de 5 estados
- Línea de tiempo con comentarios de usuario y sistema
- Categorización basada en etiquetas
- Alertas y grupos de anomalías vinculados

---

### Análisis de Causa Raíz
Cuando se crean incidentes a partir de alertas de anomalía, la plataforma recorre el grafo de dependencias de servicios (del Mapa de Servicios) e identifica servicios upstream/downstream con anomalías concurrentes. Los candidatos se clasifican por precedencia temporal, profundidad de dependencia, severidad y patrón de propagación.

**Capacidades clave:**
- Recorrido del grafo de dependencias
- Clasificación basada en tiempo y severidad
- Puntuación de confianza
- Activación automática al crear incidentes

---

### Mapa de Servicios
Grafo de dependencias interactivo que muestra servicios como nodos y sus relaciones como aristas dirigidas. Los colores de los nodos reflejan el estado de salud (verde/amarillo/rojo), y las anomalías activas se resaltan visualmente. Seleccionar un nodo muestra detalles incluyendo anomalías actuales, alertas y enlaces a Grafana.

**Capacidades clave:**
- Visualización de topología interactiva
- Superposición de estado de salud en tiempo real
- Resaltado de propagación de anomalías

---

### Seguimiento de SLO/SLA
Defina objetivos por servicio con métricas objetivo (disponibilidad, latencia, tasa de error), valores objetivo y ventanas de evaluación móviles. El motor calcula el cumplimiento actual y el consumo del presupuesto de error. Las alertas se disparan cuando el presupuesto cae por debajo de los umbrales configurados.

**Capacidades clave:**
- Seguimiento de presupuesto de error con tasa de consumo
- Múltiples tipos de objetivos (disponibilidad, latencia, tasa de error)
- Alertas por agotamiento de presupuesto
- Soporte de metadatos SLA

---

### Motor de Correlación
Vincula métricas, logs y trazas alrededor de un evento de anomalía. Consulta VictoriaMetrics para desviaciones de métricas co-ocurrentes, Loki para entradas de logs de nivel error, y Jaeger para trazas de alta latencia o con errores dentro de la ventana temporal del evento. Los resultados enriquecen las vistas de anomalías e incidentes.

**Capacidades clave:**
- Correlación de señales cruzadas (métricas + logs + trazas)
- Clasificación por proximidad temporal
- Enriquecimiento de anomalías e incidentes

---

### Notificaciones
Notificaciones activadas por alertas entregadas vía webhooks de Slack y correo SMTP. Las plantillas incluyen insignias de severidad, valores de métricas, nombres de servicios y enlaces a la plataforma/Grafana. Los períodos de enfriamiento previenen tormentas de notificaciones durante eventos sostenidos.

**Capacidades clave:**
- Canales Slack y Email
- Asignación de canal por regla
- Enfriamiento y deduplicación
- Notificaciones de resolución

---

### Logs y Trazas
Recolección centralizada y acceso a datos de logs y trazas. Los agentes Promtail envían logs de contenedores a Loki; los servicios instrumentados con OpenTelemetry exportan trazas a Jaeger a través del OTel Collector. Los datos son accesibles a través de Grafana Explore y el Motor de Correlación.

**Capacidades clave:**
- Agregación de logs de contenedores
- Trazado distribuido
- Integración con fuentes de datos de Grafana

---

### RBAC
Sistema de permisos con cuatro roles aplicado a nivel de API (middleware FastAPI) y UI (guardas de ruta React). SuperAdmin gestiona usuarios y licencias. Admin gestiona funcionalidades de monitoreo. Operador maneja alertas e incidentes. Visor tiene acceso de solo lectura a la plataforma.

| Rol | Usuarios | Servicios | Alertas | Incidentes | Configuración |
|-----|:--------:|:---------:|:-------:|:----------:|:-------------:|
| SuperAdmin | Gestionar | Gestionar | Completo | Completo | Completo |
| Admin | Ver | Gestionar | Completo | Completo | Limitado |
| Operador | Ver | Ver | Crear | Gestionar | — |
| Visor | — | Ver | Ver | Ver | — |

---

### Licenciamiento
Validación de licencias con huella de hardware y tres niveles. El Servidor de Licencias valida llaves al inicio y periódicamente. La disponibilidad de funcionalidades se controla por el nivel activo. La UI de Licencias proporciona una interfaz independiente para ingreso de llaves y visualización de estado.

---

## Mapa de Interacción de Módulos

```
Servicios ──▶ Anomalías IA ──▶ Insights IA
                  │
                  ├──▶ Reglas de Alerta ──▶ Alertas ──▶ Notificaciones
                  │                            │
                  │                            ▼
                  │                   Gestión de Incidentes ──▶ Causa Raíz
                  │
                  ├──▶ Motor de Correlación
                  │         │
                  │         ├── Logs (Loki)
                  │         └── Trazas (Jaeger)
                  │
                  └──▶ Mapa de Servicios
                            │
                            └──▶ Causa Raíz

SLO/SLA ◀── Servicios + Reglas de Alerta
RBAC ──▶ Todos los módulos (aplicación de permisos)
Licenciamiento ──▶ Todos los módulos (control de funcionalidades)
```

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
