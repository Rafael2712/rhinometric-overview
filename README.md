# 🧭 Rhinometric Platform Overview

Plataforma de observabilidad empresarial con arquitectura **cloud-native**, **multi-tenant** y monitoreo distribuido. Este repositorio documenta la estructura técnica, el stack tecnológico y las capacidades clave del proyecto.

---

## 📚 Tabla de Contenido

- [🏗️ Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [⚙️ Stack Tecnológico](#stack-tecnológico)
- [🌐 Multi-Tenancy](#multi-tenancy)
- [📈 Observabilidad](#observabilidad)
- [🔐 Seguridad](#seguridad)
- [🚢 Despliegue](#despliegue)
- [🤝 Contribución](#contribución)
- [📝 Licencia](#licencia)

---

## 🏗️ Arquitectura del Proyecto

---

## ⚙️ Stack Tecnológico

**Backend**
- Node.js + Express
- PostgreSQL (persistencia relacional)
- Redis (caché y sesiones)
- JWT para autenticación
- Winston para logging estructurado

**Frontend (en desarrollo)**
- React.js / Next.js
- TypeScript
- Tailwind CSS / Material-UI
- React Query para gestión de estado

**Infraestructura**
- Docker & Docker Compose
- Kubernetes (manifiestos listos)
- Terraform & Ansible
- Oracle Cloud Infrastructure

**Observabilidad**
- Prometheus + Pushgateway
- Grafana (dashboards provisionados)
- Loki + Promtail
- Tempo (tracing distribuido)

**CI/CD**
- GitHub Actions
- Workflows para test, build y despliegue

---

## 🌐 Multi-Tenancy

La plataforma soporta múltiples inquilinos (tenants) con:

- Aislamiento de datos por cliente
- Subdominios personalizados (`cliente.rhinometric.com`)
- Configuración individual por tenant
- Planes de suscripción diferenciados
- Roles y permisos (RBAC avanzado)

---

## 📈 Observabilidad

- Health checks en `/api/v1/health`
- Métricas Prometheus en puerto `9090`
- Logs centralizados con Loki
- Dashboards Grafana en puerto `3000`
- Exporters: node, nginx, postgres, pgbouncer, traefik
- Trazas distribuidas con Tempo

---

## 🔐 Seguridad

- Autenticación JWT
- Rate limiting por IP
- Validación de entrada con Joi
- Headers seguros con Helmet
- Hashing de contraseñas con bcrypt

---

## 🚢 Despliegue

**Entornos disponibles:**

- Desarrollo: `http://localhost:3000` (backend), `http://localhost:5173` (frontend)
- Staging: `http://localhost:3002`
- Producción: `http://localhost:3001`

**Inicio rápido:**

```bash
cd backend
cp .env.example .env
npm install
npm run db       # Crear tablas de base de datos
npm run dev      # Ejecutar entorno de desarrollo

Infraestructura lista para escalar a cloud:
- Oracle Cloud Infrastructure
- AWS / Azure (compatible)
- Docker Compose, Kubernetes y Terraform

🤝 Contribución
- Fork del proyecto
- Crear branch: git checkout -b feature/nueva-funcionalidad
- Commit: git commit -m 'Añadir nueva funcionalidad'
- Push: git push origin feature/nueva-funcionalidad
- Crear Pull Request


Licencia
Este proyecto está bajo la licencia MIT. Ver archivo LICENSE para más detalles.
