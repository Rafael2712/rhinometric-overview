RhinoMetric SaaS Platform
Plataforma SaaS multi-tenant para servicios de medición y análisis rhinométrico.

🏗️ Arquitectura del Proyecto
mi-proyecto/
├── backend/                 # API Node.js + PostgreSQL
│   ├── src/
│   │   ├── config/         # Configuraciones (DB, Redis)
│   │   ├── routes/         # Endpoints de API
│   │   ├── middleware/     # Autenticación, validación
│   │   ├── utils/          # Utilidades y helpers
│   │   └── models/         # Modelos de datos
│   ├── migrations/         # Migraciones de BD
│   └── tests/             # Tests unitarios
├── frontend/              # React.js / Next.js
│   ├── src/
│   │   ├── components/    # Componentes reutilizables
│   │   ├── pages/         # Páginas de la aplicación
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API client
│   │   └── utils/         # Utilidades frontend
│   └── public/            # Assets estáticos
├── infrastructure/        # Docker, K8s, Terraform
│   ├── docker/           # Dockerfiles y compose
│   ├── kubernetes/       # Manifiestos K8s
│   └── terraform/        # Infrastructure as Code
├── docs/                 # Documentación
│   ├── api/              # Documentación API
│   ├── deployment/       # Guías de despliegue
│   └── architecture/     # Diagramas y arquitectura
└── .github/              # CI/CD workflows
    └── workflows/        # GitHub Actions
🚀 Inicio Rápido
Backend
cd backend
cp .env.example .env
# Configurar variables de entorno en .env
npm install
npm run migrate    # Crear tablas de BD
npm run dev       # Desarrollo
npm start         # Producción
Entornos de Desarrollo
Desarrollo: http://localhost:3001 (Puerto 3001)
Staging: http://localhost:3002 (Puerto 3002)
Producción: http://localhost:3000 (Puerto 3000)
🌐 Multi-Tenancy
La plataforma soporta múltiples inquilinos (tenants) con:

Aislamiento de datos por tenant
Subdominios personalizados (ej: cliente.rhinometric.com)
Planes de suscripción diferenciados
Configuración personalizada por tenant
📊 Stack Tecnológico
Backend
Node.js v10.24.0+ con Express.js
PostgreSQL para datos relacionales
Redis para caché y sesiones
JWT para autenticación
Winston para logging
Frontend (Próximamente)
React.js o Next.js
TypeScript
Tailwind CSS o Material-UI
React Query para gestión de estado
Infraestructura
Docker & Docker Compose
Oracle Cloud Infrastructure
Prometheus + Grafana para monitoreo
Loki para logs centralizados
🔐 Seguridad
Autenticación JWT
Rate limiting por IP
Validación de entrada con Joi
Headers de seguridad con Helmet
Hashing de contraseñas con bcrypt
📈 Monitoreo
Health checks en /api/v1/health
Métricas Prometheus en Puerto 9090
Dashboards Grafana en Puerto 3000
Logs centralizados con Loki
🚢 Despliegue
Ver documentación en /docs/deployment/ para instrucciones detalladas de despliegue en:

Oracle Cloud Infrastructure
Docker Compose
Kubernetes
🤝 Contribución
Fork del proyecto
Crear branch de feature: git checkout -b feature/nueva-funcionalidad
Commit cambios: git commit -m 'Añadir nueva funcionalidad'
Push al branch: git push origin feature/nueva-funcionalidad
Crear Pull Request
📝 Licencia
Este proyecto está bajo la licencia MIT. Ver LICENSE para más detalles.

📞 Soporte
Email: soporte@rhinometric.com
Documentación: https://docs.rhinometric.com
Issues: GitHub Issues en este repositorio – Observabilidad
Resumen
Traefik → NGINX (web). PgBouncer → PostgreSQL. Prometheus recolecta métricas (node-exporter, cAdvisor, nginx-exporter, postgres-exporter, pgbouncer-exporter, Traefik). Logs con Promtail → Loki. Grafana visualiza (dashboards provisionados).
