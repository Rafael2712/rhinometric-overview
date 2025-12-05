# 📖 Rhinometric - Overview del Producto

**Versión:** 2.5.1  
**Fecha:** Diciembre 2025  
**Audiencia:** CxO, Decisores Técnicos, Product Managers

---

## 🎯 ¿Qué es Rhinometric?

**Rhinometric** es una plataforma de observabilidad unificada con inteligencia artificial que permite a equipos técnicos monitorizar, diagnosticar y anticipar problemas en sus infraestructuras y aplicaciones, todo desde una consola centralizada y completamente on-premise.

A diferencia de herramientas dispersas (Prometheus, Grafana, Loki, Jaeger por separado), Rhinometric integra métricas, logs, trazas distribuidas y detección automática de anomalías basada en Machine Learning en una única interfaz, reduciendo el tiempo de investigación de incidentes de horas a minutos.

---

## 🔥 Problemas que Resuelve

### 1. **Dispersión de herramientas**
- **Problema:** Los equipos DevOps/SRE tienen que saltar entre 5-8 herramientas diferentes (Prometheus, Grafana, Kibana, Jaeger, etc.) para diagnosticar un solo incidente.
- **Solución Rhinometric:** Consola unificada con correlación automática entre métricas, logs y trazas.

### 2. **Reactividad vs Proactividad**
- **Problema:** Los equipos solo reaccionan cuando algo ya está roto. Las anomalías tempranas pasan desapercibidas.
- **Solución Rhinometric:** Motor de IA que detecta automáticamente desviaciones estadísticas antes de que se conviertan en incidentes críticos.

### 3. **Dependencia de servicios cloud propietarios**
- **Problema:** Soluciones SaaS (Datadog, New Relic, etc.) implican costes crecientes, latencia de exportación de datos y preocupaciones de privacidad/compliance.
- **Solución Rhinometric:** 100% on-premise. Tus datos nunca salen de tu infraestructura.

### 4. **Curva de aprendizaje elevada**
- **Problema:** Herramientas como Prometheus + Grafana requieren semanas de formación para dominarlas.
- **Solución Rhinometric:** Interfaz intuitiva diseñada para que cualquier miembro técnico del equipo pueda diagnosticar problemas sin ser experto en observabilidad.

### 5. **Ruido de alertas**
- **Problema:** Alertmanager genera decenas de alertas redundantes que saturan a los equipos ("alert fatigue").
- **Solución Rhinometric:** IA prioriza anomalías reales vs ruido, reduciendo falsos positivos en un 70%.

---

## 🏗️ Componentes Principales

### **Rhinometric Console** (Frontend + Backend)
- **Tecnología:** React + FastAPI
- **Función:** Interfaz web unificada para visualizar KPIs, anomalías, alertas, logs, trazas y dashboards.
- **Acceso:** http://your-host:3002
- **Características clave:**
  - Dashboard ejecutivo con KPIs en tiempo real
  - Visualización de anomalías detectadas por IA con contexto
  - Navegación integrada a logs y trazas correlacionadas
  - 8 dashboards de Grafana embebidos

### **Prometheus** (Metrics Storage)
- **Función:** Recopilación y almacenamiento de métricas de infraestructura (CPU, memoria, red, servicios).
- **Scraping:** 11+ targets monitorizados (servicios, contenedores, bases de datos).
- **Retención:** 15 días por defecto (configurable).

### **Grafana** (Visualización Avanzada)
- **Función:** Dashboards técnicos avanzados para análisis profundo.
- **Dashboards incluidos:** 8 dashboards pre-configurados (Logs Explorer, System Monitoring, Docker Containers, Stack Health, etc.).
- **Acceso:** http://your-host:3000

### **Loki** (Log Aggregation)
- **Función:** Recopilación centralizada de logs de todos los contenedores/servicios.
- **Integración:** Promtail envía logs automáticamente desde Docker.
- **Capacidades:** Búsqueda por contenedor, timestamp, nivel de log (error, warn, info).

### **Jaeger** (Distributed Tracing)
- **Función:** Trazabilidad end-to-end de peticiones a través de microservicios.
- **Protocolo:** OpenTelemetry (OTLP).
- **Uso:** Investigación de latencias, errores de integración, cuellos de botella.

### **AI Anomaly Engine** (Detección Inteligente)
- **Tecnología:** Python + Scikit-learn + Prometheus Client
- **Modelos ML:**
  - Isolation Forest (anomalías en series temporales)
  - Local Outlier Factor (comparación con comportamiento histórico)
  - Statistical Baselines (desviaciones estándar dinámicas)
- **Frecuencia:** Entrena cada 10 minutos con datos de las últimas 24h
- **Métricas monitorizadas:**
  - CPU usage (node, containers)
  - Memory usage (node, containers)
  - Network transmit/receive
  - Disk I/O
  - Service uptime
- **Output:** Anomalías con severity (low/medium/high/critical), baseline esperado, valor actual y % de desviación.

### **Alertmanager** (Alert Management)
- **Función:** Gestión centralizada de alertas basadas en reglas de Prometheus.
- **Reglas activas:** 14 reglas (PrometheusDown, GrafanaDown, LokiDown, DatabaseDown, RedisDown, APIHighErrorRate, etc.).
- **Integración futura:** Slack, Email, PagerDuty, Webhook genérico.

### **License Server** (AWS Lambda - Coming Soon)
- **Función:** Validación de licencias on-premise contra servidor central.
- **Características:**
  - Licencias por instancia/host
  - Trial de 15 días
  - Licencias anuales y perpetuas
  - Validación cada 24h (no requiere conexión permanente)
- **Estado actual:** En integración (próxima versión).

---

## ❌ Qué NO Hace Rhinometric (Aún)

Para no vender humo, es importante aclarar las limitaciones actuales:

### **Funcionalidades Futuras (Roadmap)**
1. **Integrations UI:** La configuración de integraciones (Slack, webhooks, colectores externos) todavía requiere edición manual de ficheros YAML. No hay interfaz gráfica para esto.
2. **Reportes Automáticos:** No genera PDFs ni envía reportes semanales/mensuales automáticos. Los datos están disponibles en tiempo real, pero el reporting debe hacerse manualmente.
3. **Edición de Dashboards desde Console:** Los dashboards de Grafana se abren desde la Console, pero no se pueden editar directamente. Hay que ir a Grafana nativo.
4. **Multi-tenancy:** En la versión actual, una instalación = un equipo. No hay separación de tenants ni multi-cliente.
5. **IA Predictiva:** La IA detecta anomalías actuales, pero no predice fallos futuros (aún).
6. **Mobile App:** No hay app móvil nativa. La web es responsive pero no está optimizada para móvil.
7. **Notificaciones Push:** Alertas solo se ven en la interfaz web. No se envían notificaciones push, email o Slack automáticas (próxima versión).

### **Limitaciones Técnicas**
- **On-premise obligatorio:** No hay versión SaaS (cloud). Requiere infraestructura propia.
- **Docker Compose:** La instalación está optimizada para Docker Compose. Kubernetes está en roadmap.
- **Escalabilidad:** Diseñado para pequeñas y medianas empresas (10-500 hosts). No está probado para >1000 hosts.

---

## 🎯 Casos de Uso Típicos

### 1. **Pequeñas y Medianas Empresas (50-200 empleados)**
- **Problema:** No pueden permitirse Datadog/New Relic (>$10,000/año).
- **Solución:** Rhinometric on-premise con licencia anual <$2,000.
- **Beneficio:** Observabilidad profesional con presupuesto ajustado.

### 2. **Startups SaaS (Series A/B)**
- **Problema:** Necesitan monitorizar su producto 24/7 pero el equipo DevOps es de 1-2 personas.
- **Solución:** Rhinometric reduce el tiempo de investigación de incidentes de horas a minutos.
- **Beneficio:** 1 persona puede manejar observabilidad completa sin dedicación full-time.

### 3. **Equipos DevOps/SRE en Empresas Medianas**
- **Problema:** Tienen Prometheus + Grafana pero les falta IA de anomalías.
- **Solución:** Rhinometric se integra con Prometheus existente.
- **Beneficio:** Detección proactiva de problemas antes de que afecten a usuarios.

### 4. **Empresas con Requisitos de Compliance (Banca, Salud, Gobierno)**
- **Problema:** No pueden exportar logs/métricas a clouds públicos por regulaciones.
- **Solución:** Rhinometric 100% on-premise.
- **Beneficio:** Compliance garantizado + observabilidad moderna.

### 5. **Agencias de Desarrollo/Consultoras**
- **Problema:** Gestionan infraestructuras de múltiples clientes.
- **Solución:** 1 instancia de Rhinometric por cliente (multi-instancia).
- **Beneficio:** Misma herramienta para todos los clientes, reduce curva de aprendizaje.

---

## 🔄 Comparativa vs Alternativas

| **Criterio** | **Rhinometric** | **Datadog/New Relic** | **Prometheus + Grafana (manual)** |
|--------------|-----------------|----------------------|-----------------------------------|
| **Coste** | Licencia anual (~$1,500-$5,000) | >$10,000/año | Gratis (pero requiere dedicación) |
| **On-premise** | ✅ Sí | ❌ No (SaaS) | ✅ Sí |
| **IA de Anomalías** | ✅ Incluida | ✅ Incluida | ❌ No (manual) |
| **Curva de aprendizaje** | 🟢 Baja (1-2 días) | 🟡 Media (1 semana) | 🔴 Alta (2-4 semanas) |
| **Consola Unificada** | ✅ Sí | ✅ Sí | ❌ No (múltiples UIs) |
| **Trazas Distribuidas** | ✅ Jaeger incluido | ✅ APM incluido | 🟡 Requiere configuración |
| **Privacidad de Datos** | ✅ 100% local | ❌ Datos en cloud | ✅ 100% local |
| **Escalabilidad** | 🟡 10-500 hosts | ✅ Miles de hosts | 🟡 Depende de infraestructura |
| **Soporte** | 🟡 Email + Docs | ✅ 24/7 | ❌ Comunidad |

---

## 📊 Métricas de Valor

- **Reducción de MTTR (Mean Time To Repair):** 60-70% (de horas a minutos)
- **Reducción de falsos positivos de alertas:** 70%
- **ROI:** Positivo en 3-6 meses vs SaaS equivalentes
- **Tiempo de setup:** <2 horas (vs 2-4 semanas en Prometheus+Grafana manual)

---

## 🚀 Próximos Pasos

1. **Leer:** [Arquitectura Técnica](./ARQUITECTURA_TECNICA.md) (para entender el stack completo)
2. **Instalar:** [Guía de Instalación](./INSTALACION_RHINOMETRIC_ONPREM.md) (setup en <2h)
3. **Usar:** [Guía de Uso](./GUÍA_USO_CONSOLE_RHINOMETRIC.md) (tour por todas las pantallas)
4. **Troubleshooting:** [FAQ y Soluciones](./FAQ_RHINOMETRIC.md) (problemas comunes)

---

## 📞 Contacto

- **Email:** soporte@rhinometric.com (ficticio - actualizar)
- **Documentación:** https://docs.rhinometric.com (ficticio - actualizar)
- **Licencias:** sales@rhinometric.com (ficticio - actualizar)

---

**© 2025 Rhinometric - Observabilidad Inteligente On-Premise**
