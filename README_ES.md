> **[Español]** | [English](README.md)

# Rhinometric

**Plataforma de Observabilidad Centrada en Servicios**

[![Versión](https://img.shields.io/badge/versión-2.7.0-blue.svg)]()
[![Licencia](https://img.shields.io/badge/licencia-Propietaria-red.svg)]()

---

## ¿Qué es Rhinometric?

Rhinometric es una **plataforma de observabilidad centrada en servicios** que organiza todos los datos operativos — métricas, logs y detección de anomalías con IA — alrededor de los **servicios monitorizados** como entidad principal. Está diseñada para equipos de infraestructura y DevOps que necesitan monitorizar servicios, detectar problemas antes de que causen interrupciones y gestionar incidentes con soporte completo de ciclo de vida.

A diferencia de las herramientas de monitoreo tradicionales que dependen exclusivamente de umbrales estáticos, Rhinometric añade una capa de detección de anomalías con IA que identifica automáticamente comportamientos anormales en todos los servicios monitorizados, sin necesidad de configurar reglas manuales para cada métrica.

El modelo comercial de la plataforma se basa en el número de **servicios monitorizados**, con tres niveles de licencia que ofrecen progresivamente más capacidades.

---

## Capacidades Principales

### Monitorización de Servicios
Registra y monitoriza servicios con verificaciones periódicas de salud. Visualiza el estado en tiempo real, disponibilidad histórica y métricas detalladas a través de dashboards integrados de Grafana. Los servicios son la entidad central alrededor de la cual se organizan todos los módulos de la plataforma.

### Detección de Anomalías con IA
Un motor de detección de anomalías dedicado analiza series temporales de métricas e identifica anomalías estadísticas usando modelos IsolationForest, LOF y MAD. Las desviaciones relacionadas se agrupan por servicio y ventana temporal. Un filtro de umbral MAD del 30% reduce los falsos positivos.

### AI Insights
Resúmenes en lenguaje natural explican las anomalías detectadas en términos claros — describiendo qué cambió, cuánto y el impacto potencial — para que los operadores puedan entender los problemas sin análisis manual de métricas.

### Reglas de Alerta y Alertas
Define reglas de alerta basadas en umbrales, severidad de anomalías o ausencia de métricas. Las alertas se disparan cuando se cumplen las condiciones y siguen un ciclo de vida (disparada → confirmada → resuelta) con canales de notificación configurables.

### Gestión de Incidentes
Gestión completa del ciclo de vida de incidentes con máquina de estados (abierto → confirmado → investigando → resuelto → cerrado), línea temporal, comentarios, etiquetas, alertas vinculadas y propietarios asignados.

### Análisis de Causa Raíz
Cuando se crean incidentes a partir de alertas de anomalías, la plataforma recorre el grafo de dependencias de servicios para identificar y clasificar el origen más probable del fallo.

### Mapa de Servicios
Grafo de dependencias en tiempo real mostrando interconexiones entre servicios, estado de salud y rutas de propagación de anomalías.

### Seguimiento SLO/SLA
Define Objetivos de Nivel de Servicio con seguimiento de presupuesto de error y alertas ante el agotamiento del presupuesto antes de que ocurran incumplimientos de SLA.

### Motor de Correlación
Análisis de señales cruzadas vinculando métricas y logs (y opcionalmente trazas, cuando estén disponibles) con eventos de anomalías para enriquecimiento del contexto.

### Pipeline de Notificaciones
Notificaciones por Slack y email con canales configurables, períodos de enfriamiento, tiempos de resolución y plantillas adaptadas a la severidad.

### Logs Centralizados
Agregación de logs vía Loki/Promtail integrada en las vistas de anomalías e incidentes.

### Trazado Distribuido (Disponible)
La infraestructura de trazado Jaeger/OpenTelemetry está desplegada y lista. La recolección de datos de trazas requiere que las aplicaciones estén instrumentadas con SDKs de OpenTelemetry. Para la mayoría de despliegues, las métricas y logs proporcionan las señales principales de observabilidad.

### Control de Acceso Basado en Roles
Sistema de permisos con cuatro roles (SuperAdmin, Admin, Operador, Visor) aplicado tanto a nivel de API como de interfaz.

### Licenciamiento
Niveles de licencia basados en servicios: Community, Professional, Enterprise. Cada nivel define el número máximo de servicios monitorizados y las funcionalidades disponibles.

---

## Arquitectura General

Rhinometric se ejecuta como un stack containerizado de 21 servicios Docker:

```
┌─────────────────────────────────────────────────────┐
│                      NGINX                          │
│              (Proxy Inverso + SSL)                  │
├───────────────────────┬─────────────────────────────┤
│     Frontend          │         Backend API         │
│  React 18 + Vite      │      FastAPI (Python)       │
├───────────────────────┴─────────────────────────────┤
│                  Capa de Datos                       │
│  PostgreSQL │ Redis │ VictoriaMetrics │ Prometheus   │
├─────────────────────────────────────────────────────┤
│           Observabilidad e Inteligencia              │
│  Loki │ Grafana │ Alertmanager │ Promtail           │
│  Motor de Detección de Anomalías │ License Server   │
├─────────────────────────────────────────────────────┤
│          Capacidades Disponibles                    │
│  Jaeger │ OTel Collector (trazado)                  │
├─────────────────────────────────────────────────────┤
│           Exportadores de Infraestructura           │
│  Node Exporter │ cAdvisor │ Postgres Exporter       │
│  Redis Exporter │ Blackbox Exporter                 │
└─────────────────────────────────────────────────────┘
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18, TypeScript, Vite, TanStack Query, Zustand |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Base de Datos | PostgreSQL 16, Redis 7 |
| Métricas | Prometheus, VictoriaMetrics |
| Logs | Loki, Promtail |
| Visualización | Grafana |
| Detección de Anomalías | IsolationForest, LOF, MAD — motor de detección dedicado |
| Alertas | Alertmanager, pipeline de notificaciones personalizado |
| Trazado (disponible) | Jaeger, OpenTelemetry Collector |
| Proxy | Nginx |
| Despliegue | Docker Compose |

---

## Requisitos de Despliegue

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 16 GB | 32 GB |
| Almacenamiento | 100 GB SSD | 250 GB SSD |
| SO | Ubuntu 22.04+ / Rocky Linux 8+ | Ubuntu 24.04 |
| Docker | 24.0+ | Última estable |
| Docker Compose | v2.20+ | Última estable |

---

## Niveles de Licencia

| Funcionalidad | Community | Professional | Enterprise |
|---------------|:---------:|:------------:|:----------:|
| Servicios Monitorizados | Hasta 10 | Hasta 50 | Ilimitados |
| Dashboards de Salud | ✓ | ✓ | ✓ |
| Detección de Anomalías IA | — | ✓ | ✓ |
| AI Insights | — | ✓ | ✓ |
| Reglas de Alerta | Básicas | Completas | Completas |
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
| [Arquitectura](ARCHITECTURE_ES.md) | Arquitectura detallada con diagramas de flujo |
| [Módulos](MODULES_ES.md) | Matriz de funcionalidades y descripción de módulos |
| [Notas de Versión](RELEASE_NOTES_ES.md) | Historial de versiones y cambios |
| [Hoja de Ruta](ROADMAP_ES.md) | Hoja de ruta pública y próximas funcionalidades |

---

## Contacto

**Equipo Rhinometric**
Web: [rhinometric.com](https://rhinometric.com)
Email: info@rhinometric.com

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
