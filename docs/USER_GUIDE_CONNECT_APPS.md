# Rhinometric – On-Premise Observability & Data Compliance Platform

**Guía Técnica para Conexión de Aplicaciones y Servicios**  
**Technical Guide for Connecting Applications and Services**

---

## 📋 Información del Documento / Document Information

| Campo / Field | Español | English |
|---------------|---------|---------|
| **Versión / Version** | v2.1.0 – Octubre 2025 | v2.1.0 – October 2025 |
| **Audiencia / Audience** | Equipos DevOps, Integradores, Administradores IT | DevOps Teams, Integrators, IT Administrators |
| **Cumplimiento / Compliance** | RGPD (UE 2016/679), ENS (España) | GDPR (EU 2016/679), ENS (Spain) |
| **Contacto / Contact** | info@rhinometric.com | info@rhinometric.com |
| **Web** | https://rhinometric.com | https://rhinometric.com |

---

## 1️⃣ Introducción / Introduction

| Español | English |
|---------|---------|
| Rhinometric es una plataforma de observabilidad **on-premise** diseñada para permitir monitoreo completo de infraestructuras, aplicaciones y servicios sin depender de la nube. | Rhinometric is an **on-premise** observability platform designed for complete monitoring of infrastructure, applications, and services without relying on the cloud. |
| Todos los datos permanecen dentro de la infraestructura del cliente, garantizando **soberanía de datos** y cumplimiento normativo. | All data remains within the client's infrastructure, ensuring **data sovereignty** and regulatory compliance. |
| Esta guía técnica explica cómo conectar servidores, aplicaciones, bases de datos y servicios a Rhinometric. | This technical guide explains how to connect servers, applications, databases, and services to Rhinometric. |

---

## 2️⃣ Requisitos Previos / Requirements

| Español | English |
|---------|---------|
| **Docker Engine 24+** instalado en todos los hosts | **Docker Engine 24+** installed on all hosts |
| **Recursos mínimos por nodo:** | **Minimum resources per node:** |
| • 4 CPU cores | • 4 CPU cores |
| • 8 GB RAM | • 8 GB RAM |
| • 30 GB espacio libre en disco | • 30 GB free disk space |
| **Conectividad de red** entre Rhinometric y los hosts a monitorizar | **Network connectivity** between Rhinometric and monitored hosts |
| **Permisos de administrador** en los sistemas objetivo | **Administrator permissions** on target systems |
| **Puertos abiertos según servicio** (detallados en cada sección) | **Open ports per service** (detailed in each section) |

---

## 3️⃣ Conectar un Servidor Linux / Connect a Linux Server

| Español | English |
|---------|---------|
| **Objetivo:** Monitorizar métricas del sistema operativo (CPU, RAM, disco, red). | **Objective:** Monitor operating system metrics (CPU, RAM, disk, network). |
| **Exporter:** Node Exporter | **Exporter:** Node Exporter |
| **Puerto:** 9100 | **Port:** 9100 |

### Paso 1: Instalar Node Exporter en el servidor objetivo / Step 1: Install Node Exporter on target server

```bash
# En el servidor Linux a monitorizar / On the Linux server to monitor
docker run -d \
  --name node_exporter \
  --restart always \
  -p 9100:9100 \
  prom/node-exporter:latest
```

### Paso 2: Configurar Prometheus / Step 2: Configure Prometheus

| Español | English |
|---------|---------|
| Editar el archivo `deploy/prometheus.yml` en el servidor Rhinometric: | Edit the `deploy/prometheus.yml` file on the Rhinometric server: |

```yaml
scrape_configs:
  - job_name: 'linux-server'
    static_configs:
      - targets: ['IP_DEL_SERVIDOR:9100']  # Reemplazar con IP real / Replace with actual IP
        labels:
          environment: 'production'
          hostname: 'server01'
```

### Paso 3: Reiniciar Prometheus / Step 3: Restart Prometheus

```bash
cd ~/rhinometric-overview
docker compose -f deploy/docker-compose.yml restart prometheus
```

### Paso 4: Verificar / Step 4: Verify

| Español | English |
|---------|---------|
| Acceder a Grafana → Dashboard "System Metrics" | Access Grafana → Dashboard "System Metrics" |
| Verificar que aparecen métricas del servidor | Verify that server metrics appear |

---

## 4️⃣ Conectar Aplicaciones (Logs) / Connect Applications (Logs)

| Español | English |
|---------|---------|
| **Objetivo:** Centralizar logs de aplicaciones en Loki. | **Objective:** Centralize application logs in Loki. |
| **Herramienta:** Promtail | **Tool:** Promtail |
| **Puerto:** 3100 (Loki) | **Port:** 3100 (Loki) |

### Paso 1: Instalar Promtail / Step 1: Install Promtail

```bash
# En el servidor con logs a recolectar / On the server with logs to collect
docker run -d \
  --name promtail \
  --restart always \
  -v /var/log:/var/log:ro \
  -v $(pwd)/promtail-config.yml:/etc/promtail/config.yml:ro \
  grafana/promtail:latest
```

### Paso 2: Crear promtail-config.yml / Step 2: Create promtail-config.yml

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

clients:
  - url: http://IP_RHINOMETRIC:3100/loki/api/v1/push  # Reemplazar / Replace

scrape_configs:
  - job_name: 'varlogs'
    static_configs:
      - targets: ['localhost']
        labels:
          job: 'varlogs'
          __path__: /var/log/*.log

  - job_name: 'application'
    static_configs:
      - targets: ['localhost']
        labels:
          job: 'myapp'
          __path__: /var/log/myapp/*.log
```

### Paso 3: Verificar en Grafana / Step 3: Verify in Grafana

| Español | English |
|---------|---------|
| Ir a **Explore** → Seleccionar **Loki** | Go to **Explore** → Select **Loki** |
| Ejecutar query: `{job="varlogs"}` | Run query: `{job="varlogs"}` |
| Deberían aparecer los logs | Logs should appear |

---

## 5️⃣ Conectar Bases de Datos y Servicios / Connect Databases and Services

| Base de Datos / Database | Exporter | Puerto / Port | Target Example |
|---------------------------|----------|---------------|----------------|
| **PostgreSQL** | `wrouesnel/postgres_exporter` | 9187 | `postgres-db:9187` |
| **MySQL** | `prom/mysqld-exporter` | 9104 | `mysql-db:9104` |
| **MongoDB** | `percona/mongodb_exporter` | 9216 | `mongo-db:9216` |
| **Redis** | `oliver006/redis_exporter` | 9121 | `redis-cache:9121` |
| **Nginx** | `nginx/nginx-prometheus-exporter` | 9113 | `nginx-lb:9113` |
| **Apache** | `lusitaniae/apache_exporter` | 9117 | `apache-web:9117` |

### Ejemplo: PostgreSQL / Example: PostgreSQL

```bash
# En el servidor de base de datos / On the database server
docker run -d \
  --name postgres_exporter \
  --restart always \
  -p 9187:9187 \
  -e DATA_SOURCE_NAME="postgresql://user:pass@localhost:5432/dbname?sslmode=disable" \
  wrouesnel/postgres_exporter:latest
```

### Añadir a Prometheus / Add to Prometheus

```yaml
scrape_configs:
  - job_name: 'postgresql'
    static_configs:
      - targets: ['IP_POSTGRES_SERVER:9187']
        labels:
          database: 'production'
```

---

## 6️⃣ Validar Conexión / Validate Connection

| Método / Method | Español | English |
|-----------------|---------|---------|
| **1. Logs de Prometheus** | Verificar scraping exitoso | Verify successful scraping |

```bash
docker logs prometheus | grep 'Scrape succeeded'
```

| **2. Targets en Prometheus UI** | Acceder a http://localhost:9090/targets | Access http://localhost:9090/targets |
| | Todos los endpoints deben estar en **UP** | All endpoints should be **UP** |

| **3. Grafana Dashboards** | Verificar que aparecen métricas en: | Verify metrics appear in: |
| | • System Metrics | • System Metrics |
| | • Database Overview | • Database Overview |
| | • Application Logs | • Application Logs |

---

## 7️⃣ Buenas Prácticas / Best Practices

| Español | English |
|---------|---------|
| **1. Nomenclatura de Jobs** | **1. Job Naming** |
| Usar nombres descriptivos: `postgresql-prod`, `nginx-frontend` | Use descriptive names: `postgresql-prod`, `nginx-frontend` |
| | |
| **2. Labels Consistentes** | **2. Consistent Labels** |
| Añadir labels de entorno, datacenter, aplicación | Add environment, datacenter, application labels |
| | |
| **3. Límites de Targets** | **3. Target Limits** |
| Un "host" = un endpoint monitorizado | One "host" = one monitored endpoint |
| Máximo recomendado: <100 targets por nodo Prometheus | Recommended maximum: <100 targets per Prometheus node |
| | |
| **4. DNS Estáticos** | **4. Static DNS** |
| Preferir IPs fijas o DNS internos estables | Prefer fixed IPs or stable internal DNS |
| | |
| **5. Retención de Datos** | **5. Data Retention** |
| Ajustar según recursos disponibles (default: 15 días) | Adjust according to available resources (default: 15 days) |
| Modificar en `prometheus.yml`: `--storage.tsdb.retention.time=30d` | Modify in `prometheus.yml`: `--storage.tsdb.retention.time=30d` |
| | |
| **6. Seguridad** | **6. Security** |
| Cambiar contraseñas por defecto en `.env` | Change default passwords in `.env` |
| Limitar acceso con firewall (solo IPs autorizadas) | Restrict access with firewall (authorized IPs only) |
| Activar TLS/SSL en producción | Enable TLS/SSL in production |

---

## 8️⃣ Soporte Técnico / Technical Support

| Español | English |
|---------|---------|
| **Email:** info@rhinometric.com | **Email:** info@rhinometric.com |
| **Horario:** Lunes–Viernes 9:00–18:00 CET | **Schedule:** Monday–Friday 9:00–18:00 CET |
| **Issues:** https://github.com/Rafael2712/rhinometric-overview/issues | **Issues:** https://github.com/Rafael2712/rhinometric-overview/issues |
| **Documentación:** https://github.com/Rafael2712/rhinometric-overview | **Documentation:** https://github.com/Rafael2712/rhinometric-overview |

---

## 📚 Recursos Adicionales / Additional Resources

| Español | English |
|---------|---------|
| • [Guía de Instalación](../README.md) | • [Installation Guide](../README.md) |
| • [Guía Cloud Deployment](../CLOUD_DEPLOYMENT_GUIDE.md) | • [Cloud Deployment Guide](../CLOUD_DEPLOYMENT_GUIDE.md) |
| • [Arquitectura Híbrida](../HYBRID_ARCHITECTURE_GUIDE.md) | • [Hybrid Architecture](../HYBRID_ARCHITECTURE_GUIDE.md) |
| • [Sistema de Licencias](../LICENSE_SERVER_CLARIFICATION.md) | • [License System](../LICENSE_SERVER_CLARIFICATION.md) |

---

**© 2025 Rhinometric® – Todos los derechos reservados / All rights reserved**  
**Cumplimiento / Compliance:** RGPD (UE 2016/679) | ENS (España) | GDPR (EU 2016/679) | ENS (Spain)
