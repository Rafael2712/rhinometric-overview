# RHINOMETRIC v2.5.0 "Rhino Radar"  
## Resumen Ejecutivo para Leads y Partners

**Fecha:** 17 de Diciembre, 2025  
**Versión:** 2.5.0  
**Estado:** Producción Operativa

---

## ¿Qué es Rhinometric?

Rhinometric es una **plataforma de observabilidad on-premise** que permite monitorizar infraestructuras IT completas manteniendo todos los datos dentro de las instalaciones del cliente. A diferencia de soluciones cloud como Datadog o New Relic, Rhinometric permite mantener todos los datos dentro de la infraestructura del cliente, facilitando la **soberanía de datos** y el cumplimiento normativo (por ejemplo, RGPD).

---

## Problemas que Resuelve

### 1. Falta de Visibilidad Operativa
- Métricas en tiempo real de servidores, contenedores y aplicaciones
- 15+ dashboards precargados para análisis inmediato
- Logs centralizados de todos los servicios
- Trazas distribuidas con Jaeger

### 2. Dependencia de Proveedores Cloud
- Se posiciona como alternativa on-premise a las principales soluciones de observabilidad SaaS (Datadog, New Relic, Splunk), para organizaciones que no pueden o no quieren enviar sus datos fuera
- Modelo de licenciamiento por número de hosts, sin cargos variables por volumen de datos ingeridos
- Control total de la información (RGPD, ENS, datos sensibles)

### 3. Complejidad de Despliegue
- 3 formatos de distribución:
  - **Demo OVA:** Máquina virtual lista en 5 minutos (4 horas de prueba)
  - **Trial Installer:** Script automático para Linux (14 días, hasta 5 hosts)
  - **Annual License:** Producción completa (1 año, hosts configurables)

### 4. Falta de Detección Proactiva
- Motor de detección de anomalías basado en modelos de IA (Prophet + IsolationForest), ya disponible en la plataforma y con mejoras previstas en el roadmap
- Base de alertas con Prometheus (integración con Alertmanager en roadmap)
- Monitoreo de licencias con expiración anticipada

---

## Stack Tecnológico (Verificado)

Basado en `docker-compose-v2.5.0.yml`:

### Almacenamiento
- **PostgreSQL 15.10:** Base de datos de licencias y configuración
- **Redis 7.2:** Caché de sesiones y rate limiting

### Observabilidad
- **Prometheus 2.53.0:** Métricas (30 días de retención)
- **Loki 3.0.0:** Logs centralizados
- **Jaeger (all-in-one):** Trazas distribuidas
- **Grafana 10.4.0:** Visualización y dashboards

### Recolección de Telemetría
- **OpenTelemetry Collector 0.91.0:** Ingesta estándar de trazas/métricas
- **cAdvisor:** Métricas de contenedores Docker
- **Node Exporter:** Métricas del sistema operativo

### Aplicación
- **License Server v2:** API FastAPI (migrada desde Flask, rendimiento 10x superior)
- **Console v3:** Interfaz web Vue.js + FastAPI
- **AI Anomaly Engine:** Detección predictiva con Python

---

## Público Objetivo

### Sectores Ideales
- **Sector Público:** Administraciones que requieren datos on-premise (ENS)
- **Salud:** Hospitales con datos médicos sensibles (LOPD)
- **Banca:** Cumplimiento normativo estricto
- **SMEs:** Empresas que buscan alternativa económica a SaaS
- **MSPs:** Proveedores de servicios gestionados que revenden monitoreo

### Perfil del Cliente
- 10-200 hosts monitorizados
- Infraestructura híbrida (on-premise + cloud)
- Requisitos de cumplimiento normativo
- Preferencia por control total de datos

---

## Modelos de Distribución

Según `RELEASE_NOTES.md` v2.5.0:

### 1. Demo Cloud (4 horas)
- **Formato:** Archivo OVA (máquina virtual)
- **Compatibilidad:** VirtualBox, VMware
- **Contenido:** Stack completo pre-configurado
- **Uso:** Pruebas rápidas, demos comerciales
- **Limitaciones:** 4 horas de uso, luego expira

### 2. Trial Installer (14 días)
- **Formato:** Script de instalación Linux
- **Plataformas:** Ubuntu, Debian, CentOS, RHEL
- **Hosts:** Hasta 5 hosts
- **Contenido:** Instalación completa con Docker Compose
- **Limitaciones:** 14 días, luego expira

### 3. Annual License (1 año)
- **Formato:** Instalador + archivo .lic
- **Hosts:** Configurable (sin límite técnico)
- **Duración:** 1 año renovable
- **Soporte:** Email incluido
- **Actualizaciones:** Incluidas durante vigencia

---

## Capacidades Técnicas (Documentadas)

### Recolección de Datos
- Métricas de sistema (CPU, RAM, disco, red)
- Métricas de aplicaciones (HTTP, response time, errores)
- Logs de contenedores Docker
- Trazas de transacciones distribuidas

### Dashboards Disponibles
Según archivos de configuración:
- Overview del sistema
- Docker Containers
- Prometheus Metrics
- Loki Logs Explorer
- Jaeger Traces
- (15+ dashboards en total - número exacto en archivos de Grafana)

### Integraciones
- Docker (nativo)
- Kubernetes (documentado como roadmap)
- APIs REST (vía OpenTelemetry)
- Exportadores Prometheus (Node, cAdvisor, Blackbox, PostgreSQL)

---

## Requisitos de Hardware

Basado en configuración de `docker-compose-v2.5.0.yml`:

### Mínimo (Trial - 5 hosts)
- **CPU:** 2 vCPUs
- **RAM:** 4 GB
- **Disco:** 20 GB SSD

### Recomendado (30 hosts)
- **CPU:** 4 vCPUs
- **RAM:** 8 GB
- **Disco:** 50 GB SSD

### Producción (100+ hosts)
- **CPU:** 8 vCPUs
- **RAM:** 16 GB
- **Disco:** 100 GB SSD (datos recolectados crecen con el tiempo)

*Nota: Números aproximados basados en configuración de límites de memoria en docker-compose.*

---

## Ventajas Competitivas

### 1. On-Premise Total
- Sin envío de datos a terceros
- Facilita el cumplimiento del RGPD al evitar que los datos salgan a terceros proveedores cloud, siempre que el cliente configure su entorno de acuerdo a la normativa aplicable
- Ideal para sectores regulados

### 2. Stack Open-Source
- Basado en Prometheus, Grafana, Loki (proyectos CNCF)
- Sin vendor lock-in
- Comunidad activa

### 3. Despliegue Simplificado
- Instalación automática en 10 minutos
- Docker Compose (sin Kubernetes necesario)
- Dashboards precargados (listos para usar)

### 4. Detección de Anomalías
- Motor de IA local (no cloud)
- Algoritmos Prophet + IsolationForest
- Predicciones sin salida de datos

### 5. Sistema de Licencias Flexible
- Demo gratuito (4h) para pruebas
- Trial de 14 días sin compromiso
- Annual license con renovación simple

---

## Limitaciones Conocidas

### Capacidad Actual
- Actualmente la plataforma se utiliza en entornos reales de prueba y despliegues internos
- Está diseñada para crecer con el cliente desde escenarios pequeños (10-30 hosts) hasta infraestructuras mayores, ajustando el dimensionamiento de hardware según necesidades

### Funcionalidades Pendientes
Según `PENDIENTES_DESARROLLO_RHINOMETRIC.md`:

**Prioridad Alta (próximos 3 meses):**
- Sistema de facturación integrado (Stripe)
- Portal de cliente self-service
- Notificaciones automáticas de expiración
- API pública documentada

**Prioridad Media (6 meses):**
- Multi-región (datacenter EU)
- Mobile app (iOS/Android)
- Kubernetes monitoring nativo

**Prioridad Baja (12+ meses):**
- White-label para partners
- Enterprise SSO (SAML, OAuth)
- Multi-tenancy completo

---

## Casos de Uso Reales

*Nota: No se dispone de casos de uso de clientes documentados en el repositorio. Esta sección se completará cuando existan referencias verificables.*

---

## Soporte y Documentación

### Canales de Soporte
- Email: rafael.canelon@rhinometric.com (verificado en configuración SMTP)
- Documentación técnica: Archivos markdown en `/docs/v2.5.0/`

### Documentación Disponible
Según estructura de archivos:
- Guía de instalación (EN/ES)
- Manual de usuario (EN/ES)
- Guía de deployment
- Endpoints de descarga
- Testing de emails
- Guía de publicación

---

## Información de Contacto

**Empresa:** Rhinometric  
**Email Comercial:** rafael.canelon@rhinometric.com  
**Servidor SMTP:** smtp.zoho.eu:465 (verificado en configuración)  
**Servidor de Licencias:** licensing.rhinometric.com:5000 (según documentación de deployment)

---

## Próximos Pasos

### Para Leads Interesados
1. Solicitar demo OVA (4 horas de prueba)
2. Instalar en VirtualBox/VMware local
3. Explorar dashboards precargados
4. Si es viable, solicitar trial de 14 días

### Para Partners Potenciales
1. Contacto inicial por email
2. Reunión técnica (arquitectura, capacidades)
3. Prueba de concepto (POC) de 30 días
4. Evaluación de modelo de distribución/reventa

---

**Documento generado a partir de archivos verificables del repositorio.**  
**Última actualización:** 17 de Diciembre, 2025  
**Versión del documento:** 1.0
