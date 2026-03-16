# Ì≥ñ Manual de Usuario - Rhinometric Enterprise v2.5.0

**Fecha**: Noviembre 2024  
**Versi√≥n**: 2.5.0  
**Idioma**: Espa√±ol

---

## Ì≥ã √çndice

1. [Introducci√≥n](#introducci√≥n)
2. [Primeros Pasos](#primeros-pasos)
3. [Interfaz de Usuario](#interfaz-de-usuario)
4. [Dashboards y Visualizaci√≥n](#dashboards-y-visualizaci√≥n)
5. [Alertas y Notificaciones](#alertas-y-notificaciones)
6. [Detecci√≥n de Anomal√≠as con IA](#detecci√≥n-de-anomal√≠as-con-ia)
7. [Constructor de Dashboards](#constructor-de-dashboards)
8. [Gesti√≥n de Licencias](#gesti√≥n-de-licencias)
9. [Branding Empresarial](#branding-empresarial)
10. [Soluci√≥n de Problemas](#soluci√≥n-de-problemas)
11. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## ÌæØ Introducci√≥n

### ¬øQu√© es Rhinometric?

**Rhinometric Enterprise** es una plataforma integral de observabilidad empresarial que combina monitoreo de infraestructura, logs, trazas distribuidas y detecci√≥n de anomal√≠as con inteligencia artificial.

### Caracter√≠sticas Principales

- **Monitoreo Unificado**: M√©tricas, logs y trazas en una sola plataforma
- **IA Integrada**: Detecci√≥n autom√°tica de anomal√≠as con Machine Learning
- **Constructor Visual**: Crea dashboards sin c√≥digo
- **Branding Personalizado**: Adapta la interfaz a tu marca
- **Alertas Inteligentes**: Notificaciones multi-canal
- **Escalabilidad**: Desde 1 host hasta miles de servidores

---

## Ì∫Ä Primeros Pasos

### Requisitos del Sistema

#### Hardware M√≠nimo
- CPU: 4 cores
- RAM: 8 GB
- Disco: 50 GB SSD
- Red: 100 Mbps

#### Hardware Recomendado
- CPU: 8+ cores
- RAM: 16+ GB
- Disco: 200+ GB SSD
- Red: 1 Gbps

### Instalaci√≥n con Docker Compose

```bash
git clone https://github.com/Rafael2712/rhinometric-overview.git
cd rhinometric-overview/examples
docker compose up -d
```

### Primer Acceso

URL: http://localhost:3000
Usuario: admin
Password: rhinometric_v22

---

## Ì∂•Ô∏è Interfaz de Usuario

### Navegaci√≥n Principal

- **Home**: P√°gina principal
- **Explore**: Consultas ad-hoc
- **Dashboards**: Listado de dashboards
- **Alerting**: Gesti√≥n de alertas
- **Configuration**: Configuraci√≥n

---

## Ì≥ä Dashboards y Visualizaci√≥n

### Dashboards Pre-configurados

1. **System Metrics**: CPU, RAM, disco, red
2. **Application Metrics**: Request rate, latency, errores
3. **AI Anomaly Detection**: Detecci√≥n de anomal√≠as

### Consultas PromQL

```promql
# CPU total
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria disponible
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024
```

---

## Ì¥î Alertas y Notificaciones

### Canales Soportados

- Email (SMTP)
- Slack
- PagerDuty
- Webhooks

### Crear Alerta

1. Ir a Alerting ‚Üí Alert rules
2. New alert rule
3. Configurar query y condiciones
4. Seleccionar canal de notificaci√≥n

---

## Ì¥ñ Detecci√≥n de Anomal√≠as con IA

### C√≥mo Funciona

El motor de IA:
1. Aprende patrones normales (7 d√≠as)
2. Detecta desviaciones en tiempo real
3. Genera score de anomal√≠a (0-100)
4. Alerta cuando supera umbral

### Algoritmos

- Isolation Forest
- ARIMA
- Z-Score

---

## Ìæ® Constructor de Dashboards

### Crear Dashboard

1. Acceder a Dashboard Builder
2. Seleccionar plantilla
3. Agregar paneles
4. Configurar queries
5. Guardar

---

## Ì¥ê Gesti√≥n de Licencias

### Tipos de Licencia

- Trial: 30 d√≠as gratis
- Starter: 1-5 hosts
- Professional: 6-50 hosts
- Enterprise: Ilimitado

### Activar Licencia

```bash
docker cp license.lic rhinometric-license-server:/app/licenses/
docker exec rhinometric-license-server python /app/activate.py
```

---

## Ìæ® Branding Empresarial

### Personalizar Logo

```bash
cp logo.png infrastructure/nginx/landing/assets/
docker compose restart nginx
```

---

## Ì¥ß Soluci√≥n de Problemas

### Servicios No Inician

```bash
docker compose ps
docker compose logs [servicio]
```

### Dashboards Sin Datos

Verificar datasource en Grafana ‚Üí Configuration ‚Üí Data sources

---

## ‚ùì Preguntas Frecuentes

**P: ¬øPuedo usar en producci√≥n?**
R: S√≠, v2.5.0 est√° listo para producci√≥n.

**P: ¬øCu√°ntos hosts puedo monitorear?**
R: Depende de tu licencia (1-5, 6-50, ilimitado).

---

## Ì≥û Soporte

- Email: info@rhinometric.com
- Tel√©fono: +34 900 123 456
- GitHub: https://github.com/Rafael2712/rhinometric-overview

---

**Versi√≥n**: 2.5.0  
**Actualizaci√≥n**: Noviembre 2024
