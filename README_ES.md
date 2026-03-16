> [English](README.md) | **[Español]**

# Rhinometric

**Observabilidad Inteligente para Infraestructura Moderna**

[![Versión](https://img.shields.io/badge/versión-2.7.0-blue.svg)]()
[![Licencia](https://img.shields.io/badge/licencia-Propietaria-red.svg)]()

---

## ¿Qué es Rhinometric?

Rhinometric es una plataforma de observabilidad empresarial que unifica métricas, logs, trazas y detección de anomalías basada en inteligencia artificial en una sola consola operativa. Está diseñada para equipos de infraestructura y DevOps que necesitan monitorear servicios, detectar problemas antes de que causen interrupciones y gestionar incidentes con soporte de ciclo de vida completo.

A diferencia de las herramientas de monitoreo tradicionales que dependen exclusivamente de umbrales estáticos, Rhinometric añade una capa de detección de anomalías con IA que identifica automáticamente comportamientos anormales en todos los servicios monitoreados, sin necesidad de configurar reglas manuales para cada métrica.

---

## Capacidades Principales

### Monitoreo de Servicios
Registre y monitoree servicios con verificaciones de salud periódicas. Visualice estado en tiempo real, disponibilidad histórica y métricas detalladas a través de paneles de Grafana integrados.

### Detección de Anomalías con IA
Un detector basado en IsolationForest analiza series temporales de métricas e identifica anomalías estadísticas, agrupando desviaciones relacionadas por servicio y ventana temporal. Un filtro de umbral MAD reduce los falsos positivos.

### Insights de IA
Resúmenes en lenguaje natural que explican las anomalías detectadas en términos claros — describiendo qué cambió, en qué magnitud y el impacto potencial — para que los operadores comprendan los problemas sin análisis manual de métricas.

### Reglas de Alerta y Alertas
Defina reglas de alerta basadas en umbrales, severidad de anomalía o ausencia de métricas. Las alertas se disparan cuando las condiciones se cumplen y siguen un ciclo de vida (disparada → reconocida → resuelta) con canales de notificación configurables.

### Gestión de Incidentes
Gestión completa del ciclo de vida de incidentes con máquina de estados (abierto → reconocido → investigando → resuelto → cerrado), línea de tiempo, comentarios, etiquetas, alertas vinculadas y propietarios asignados.

### Análisis de Causa Raíz
Cuando se crean incidentes a partir de alertas de anomalía, la plataforma recorre el grafo de dependencias de servicios para identificar y clasificar el origen más probable de la falla.

### Mapa de Servicios
Grafo de dependencias en vivo que muestra interconexiones entre servicios, estado de salud y rutas de propagación de anomalías.

### Seguimiento de SLO/SLA
Defina Objetivos de Nivel de Servicio con seguimiento de presupuesto de error y alertas por agotamiento antes de que ocurran violaciones de SLA.

### Motor de Correlación
Análisis de señales cruzadas que vincula métricas, logs y trazas con eventos de anomalía para enriquecimiento de contexto.

### Pipeline de Notificaciones
Notificaciones por Slack y correo electrónico con canales configurables, períodos de enfriamiento, tiempos de resolución automática y plantillas apropiadas por severidad.

### Logs y Trazas Centralizados
Agregación de logs vía Loki/Promtail y trazado distribuido vía Jaeger/OpenTelemetry, integrados en las vistas de anomalías e incidentes.

### Control de Acceso Basado en Roles
Sistema de permisos con cuatro roles (SuperAdmin, Admin, Operador, Visor) aplicado tanto a nivel de API como de interfaz de usuario.

### Licenciamiento
Validación de licencias con huella de hardware y tres niveles: Community, Professional, Enterprise.

---

## Resumen de Arquitectura

Rhinometric se ejecuta como un stack contenedorizado de 21 servicios Docker:

```
┌─────────────────────────────────────────────────────┐
│                      NGINX                          │
│            (Proxy Inverso + SSL)                    │
├───────────────────────┬─────────────────────────────┤
│     Frontend          │       Backend API           │
│  React 18 + Vite      │    FastAPI (Python)         │
├───────────────────────┴─────────────────────────────┤
│                  Capa de Datos                      │
│  PostgreSQL │ Redis │ VictoriaMetrics │ Prometheus   │
├─────────────────────────────────────────────────────┤
│             Stack de Observabilidad                 │
│  Loki │ Jaeger │ OTel Collector │ Grafana           │
│  Alertmanager │ Promtail                            │
├─────────────────────────────────────────────────────┤
│              Capa de Inteligencia                   │
│  Detector de Anomalías IA │ Servidor de Licencias   │
├─────────────────────────────────────────────────────┤
│            Exportadores de Infraestructura          │
│  Node Exporter │ cAdvisor │ Postgres Exporter       │
│  Redis Exporter │ Blackbox Exporter                 │
└─────────────────────────────────────────────────────┘
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18, TypeScript, Vite, TanStack Query, Zustand |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Base de Datos | PostgreSQL 15, Redis 7 |
| Métricas | Prometheus, VictoriaMetrics |
| Logs | Loki, Promtail |
| Trazas | Jaeger, OpenTelemetry Collector |
| Visualización | Grafana |
| Detección IA | IsolationForest (scikit-learn), servicio Python personalizado |
| Alertas | Alertmanager, pipeline de notificaciones propio |
| Proxy | Nginx |
| Despliegue | Docker Compose |

---

## Requisitos de Despliegue

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 16 GB | 32 GB |
| Almacenamiento | 100 GB SSD | 250 GB SSD |
| Sistema Operativo | Ubuntu 22.04+ / Rocky Linux 8+ | Ubuntu 24.04 |
| Docker | 24.0+ | Última versión estable |
| Docker Compose | v2.20+ | Última versión estable |

---

## Niveles de Licencia

| Funcionalidad | Community | Professional | Enterprise |
|---------------|:---------:|:------------:|:----------:|
| Monitoreo de Servicios | ✓ (10 máx) | ✓ (50 máx) | ✓ (Ilimitado) |
| Paneles de Salud | ✓ | ✓ | ✓ |
| Detección de Anomalías IA | — | ✓ | ✓ |
| Insights de IA | — | ✓ | ✓ |
| Reglas de Alerta | Básico | Completo | Completo |
| Gestión de Incidentes | — | ✓ | ✓ |
| Análisis de Causa Raíz | — | — | ✓ |
| Mapa de Servicios | — | ✓ | ✓ |
| SLO/SLA | — | — | ✓ |
| Motor de Correlación | — | ✓ | ✓ |
| RBAC | 2 roles | 3 roles | 4 roles |
| Canales de Notificación | Email | Email + Slack | Todos |
| Soporte | Comunidad | Email | Prioritario |

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](ARCHITECTURE_ES.md) | Arquitectura detallada con diagramas de flujo de datos |
| [Módulos](MODULES_ES.md) | Matriz de funcionalidades y descripciones de módulos |
| [Notas de Versión](RELEASE_NOTES_ES.md) | Historial de versiones y cambios |
| [Hoja de Ruta](ROADMAP_ES.md) | Hoja de ruta pública y próximas funcionalidades |

---

## Contacto

**Rhinometric Team**  
Sitio web: [rhinometric.com](https://rhinometric.com)  
Email: info@rhinometric.com

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
