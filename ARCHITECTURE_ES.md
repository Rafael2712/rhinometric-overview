# Rhinometric — Arquitectura

**Versión:** 2.7.0
**Mantenido por:** Equipo Rhinometric — info@rhinometric.com

---

## Arquitectura del Sistema

Rhinometric se despliega como un stack containerizado de 21 servicios Docker organizados en capas diferenciadas. Toda la comunicación entre servicios ocurre sobre una red Docker compartida con Nginx como único punto de entrada externo.

### Arquitectura de Alto Nivel

```mermaid
graph TB
    subgraph Externo
        User[Navegador del Usuario]
    end

    subgraph Capa Proxy
        Nginx[Nginx<br/>Proxy Inverso + SSL]
    end

    subgraph Capa de Aplicación
        Frontend[Frontend<br/>React 18 + Vite]
        Backend[Backend API<br/>FastAPI Python 3.11]
    end

    subgraph Capa de Inteligencia
        AI[Motor de Detección de Anomalías<br/>IsolationForest + LOF + MAD]
        License[License Server v2]
        LicenseUI[License UI]
    end

    subgraph Capa de Datos
        PG[(PostgreSQL 16)]
        Redis[(Redis 7)]
        VM[VictoriaMetrics<br/>Métricas Largo Plazo]
        Prom[Prometheus<br/>Buffer Corto Plazo]
    end

    subgraph Stack de Observabilidad
        Grafana[Grafana<br/>Dashboards]
        Loki[Loki<br/>Almacén de Logs]
        AM[Alertmanager]
        Promtail[Promtail<br/>Agente de Logs]
    end

    subgraph Capacidades Disponibles
        Jaeger[Jaeger<br/>Almacén de Trazas]
        OTel[OTel Collector]
    end

    subgraph Exportadores
        NodeExp[Node Exporter]
        cAdvisor[cAdvisor]
        PGExp[Postgres Exporter]
        RedisExp[Redis Exporter]
        BBExp[Blackbox Exporter]
    end

    User --> Nginx
    Nginx --> Frontend
    Nginx --> Backend
    Nginx --> Grafana

    Backend --> PG
    Backend --> Redis
    Backend --> VM
    Backend --> License

    AI --> VM
    AI --> PG

    Prom --> VM
    Prom --> AM
    Promtail --> Loki
    OTel --> Jaeger

    Prom --> NodeExp
    Prom --> cAdvisor
    Prom --> PGExp
    Prom --> RedisExp
    Prom --> BBExp
```

---

## Inventario de Contenedores

| # | Servicio | Tecnología | Puerto | Propósito |
|---|----------|-----------|--------|-----------|
| 1 | nginx | Nginx 1.25 | 80, 443 | Proxy inverso, terminación SSL, archivos estáticos |
| 2 | frontend | React 18 + Vite | 3000 | Aplicación de página única |
| 3 | backend | FastAPI + Python 3.11 | 8105 | API REST, lógica de negocio, acceso a datos |
| 4 | postgres | PostgreSQL 16 | 5432 | Base de datos principal para todo el estado de la aplicación |
| 5 | redis | Redis 7 | 6379 | Caché, datos de sesión, pub/sub en tiempo real |
| 6 | prometheus | Prometheus | 9090 | Buffer de métricas a corto plazo (retención 30 días) |
| 7 | victoriametrics | VictoriaMetrics | 8428 | Almacenamiento de métricas a largo plazo (retención 90 días) |
| 8 | loki | Grafana Loki | 3100 | Agregación y motor de consultas de logs |
| 9 | jaeger | Jaeger | 16686 | Trazado distribuido (disponible — requiere instrumentación de apps) |
| 10 | grafana | Grafana | 3001 | Visualización de métricas y dashboards |
| 11 | alertmanager | Alertmanager | 9093 | Enrutamiento y deduplicación de alertas |
| 12 | otel-collector | OpenTelemetry Collector | 4317, 4318 | Pipeline de telemetría (trazas) |
| 13 | node-exporter | Prometheus Node Exporter | 9100 | Métricas del sistema (CPU, memoria, disco, red) |
| 14 | cadvisor | Google cAdvisor | 8080 | Métricas de uso de recursos de contenedores |
| 15 | postgres-exporter | Prometheus PG Exporter | 9187 | Métricas de rendimiento de PostgreSQL |
| 16 | redis-exporter | Prometheus Redis Exporter | 9121 | Métricas de rendimiento de Redis |
| 17 | blackbox-exporter | Prometheus Blackbox Exporter | 9115 | Verificaciones de endpoints de servicios |
| 18 | promtail | Grafana Promtail | — | Agente de recolección de logs |
| 19 | ai-anomaly | Custom | 8085 | Motor de detección de anomalías (IsolationForest, LOF, MAD) |
| 20 | license-server-v2 | Custom Python | 8200 | Validación de claves de licencia |
| 21 | license-ui | React | 8201 | Interfaz de gestión de licencias |

---

## Flujo de Datos

### Flujo de Recolección de Métricas y Detección de Anomalías
```mermaid
sequenceDiagram
    participant BBE as Blackbox Exporter
    participant NE as Node Exporter
    participant CA as cAdvisor
    participant P as Prometheus
    participant VM as VictoriaMetrics
    participant AI as Motor de Detección
    participant BE as Backend API
    participant FE as Frontend

    BBE->>P: probe_success, probe_duration
    NE->>P: cpu, memoria, disco, red
    CA->>P: métricas de contenedores
    P->>VM: remote_write (todas las métricas)
    P->>P: Evaluar reglas de alerta
    AI->>VM: Consultas PromQL (análisis de métricas)
    AI->>AI: Scoring IsolationForest + LOF + MAD
    AI->>BE: Grupos de anomalías vía PostgreSQL
    FE->>BE: GET /api/anomalies
    BE->>FE: Datos de anomalías + deep links Grafana
```

### Flujo de Alertas y Notificaciones
```mermaid
sequenceDiagram
    participant AI as Motor de Detección
    participant BE as Backend API
    participant AM as Alertmanager
    participant Slack as Slack
    participant Email as Email

    AI->>BE: Nuevo grupo de anomalías detectado
    BE->>BE: Evaluar reglas de alerta
    BE->>BE: Verificar cooldown y dedup
    BE->>Slack: Notificación webhook
    BE->>Email: Notificación SMTP
    AM->>BE: Alertas del lado Prometheus
    BE->>BE: Crear/actualizar incidente
```

### Flujo de Recolección de Logs
```mermaid
sequenceDiagram
    participant App as Contenedores
    participant PT as Promtail
    participant Loki as Loki
    participant G as Grafana

    App->>PT: stdout/stderr logs
    PT->>Loki: Push de flujos de logs
    G->>Loki: Consultas LogQL
```

> **Nota:** El trazado distribuido vía Jaeger/OpenTelemetry está disponible cuando las aplicaciones están instrumentadas con SDKs de OTel. La infraestructura (OTel Collector → Jaeger) está desplegada y lista. Actualmente, solo el backend de Rhinometric emite trazas.

---

## Arquitectura de Red

Todos los servicios se comunican a través de una red Docker bridge compartida. Solo Nginx está expuesto a la red externa.

| Puerto Externo | Servicio Interno | Protocolo |
|---------------|-----------------|-----------|
| 80 | nginx | HTTP (redirección a 443) |
| 443 | nginx | HTTPS |

Todos los demás servicios son accesibles solo a través de la red interna de Docker, con Nginx redirigiendo solicitudes según la ruta URL:
- `/` → Frontend
- `/api/` → Backend
- `/grafana/` → Grafana

---

## Arquitectura de Seguridad

- **Terminación TLS**: Nginx gestiona SSL con certificados Let's Encrypt.
- **Autenticación**: Basada en JWT con hashing de contraseñas bcrypt.
- **Autorización**: Control de acceso basado en roles con 4 roles aplicados a nivel de API e interfaz.
- **CORS**: Restringido al origen del frontend configurado.
- **Limitación de Tasa**: Aplicada a endpoints de autenticación.
- **Gestión de Secretos**: Variables de entorno vía archivo `.env` (integración con vault planificada).
- **Aislamiento de Red**: Solo Nginx está expuesto externamente.

---

## Consideraciones de Escalabilidad

La arquitectura actual está diseñada para despliegue en un solo nodo. Para escalar en producción:

| Componente | Estrategia de Escalado |
|-----------|----------------------|
| Backend API | Horizontal — múltiples contenedores detrás del balanceo de Nginx |
| PostgreSQL | Escalado vertical o réplicas de lectura |
| VictoriaMetrics | Soporte nativo de clustering disponible |
| Prometheus | Federación o Thanos para multi-nodo |
| Motor de Detección | Horizontal — particionado por grupos de servicios |

---

*Copyright 2024–2026 Rhinometric. Todos los derechos reservados.*
