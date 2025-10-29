# Rhinometric – On-Premise Observability & Data Compliance Platform

**Guía Institucional para Administraciones Públicas y Empresas**  
**Institutional Guide for Public Administrations and Enterprises**

---

## 📋 Información del Documento / Document Information

| Campo / Field | Español | English |
|---------------|---------|---------|
| **Versión / Version** | v2.1.0 – Octubre 2025 | v2.1.0 – October 2025 |
| **Audiencia / Audience** | Ayuntamientos, Empresas Públicas, Instituciones | Municipalities, Public Companies, Institutions |
| **Cumplimiento / Compliance** | RGPD (UE 2016/679), ENS (España) | GDPR (EU 2016/679), ENS (Spain) |
| **Contacto / Contact** | rafael.canelon@rhinometric.com | rafael.canelon@rhinometric.com |
| **Web** | https://rhinometric.com | https://rhinometric.com |
| **Soporte / Support** | Lunes–Viernes 9:00–18:00 CET | Monday–Friday 9:00–18:00 CET |

---

## 1️⃣ ¿Qué es Rhinometric? / What is Rhinometric?

| Español | English |
|---------|---------|
| **Rhinometric** es una plataforma de observabilidad **on-premise** que permite monitorizar infraestructuras IT completas manteniendo **todos los datos dentro de las instalaciones del cliente**. | **Rhinometric** is an **on-premise** observability platform that enables monitoring of complete IT infrastructures while keeping **all data within the client's facilities**. |
| No hay dependencia de proveedores cloud externos ni transferencias de datos fuera de la organización. | There is no dependency on external cloud providers and no data transfers outside the organization. |
| Ideal para organizaciones con requisitos estrictos de **privacidad, soberanía de datos y cumplimiento normativo**. | Ideal for organizations with strict requirements for **privacy, data sovereignty, and regulatory compliance**. |

### Componentes Principales / Main Components

| Componente / Component | Descripción Español | English Description |
|------------------------|---------------------|---------------------|
| **Grafana** | Visualización de métricas y dashboards | Metrics visualization and dashboards |
| **Prometheus** | Almacenamiento de métricas time-series | Time-series metrics storage |
| **Loki** | Agregación y análisis de logs | Log aggregation and analysis |
| **Tempo** | Trazas distribuidas (tracing) | Distributed tracing |
| **PostgreSQL** | Base de datos para persistencia | Persistence database |
| **Redis** | Cache de alto rendimiento | High-performance cache |

---

## 2️⃣ Ventajas del Modelo On-Premise / Advantages of the On-Premise Model

| # | Español | English |
|---|---------|---------|
| **1** | 🔒 **Soberanía de Datos:** Toda la información permanece en servidores controlados por la organización. | 🔒 **Data Sovereignty:** All information remains on organization-controlled servers. |
| **2** | ✅ **Cumplimiento RGPD y ENS:** No hay transferencias internacionales de datos. Cumple automáticamente con regulaciones europeas. | ✅ **GDPR and ENS Compliance:** No international data transfers. Automatically complies with European regulations. |
| **3** | 🛡️ **Seguridad Total:** Sin exposición a internet público. Control completo del perímetro de seguridad. | 🛡️ **Total Security:** No public internet exposure. Complete control over security perimeter. |
| **4** | 🌍 **Independencia Tecnológica:** Sin dependencia de AWS, Azure, Google Cloud u otros proveedores externos. | 🌍 **Technological Independence:** No dependency on AWS, Azure, Google Cloud, or other external providers. |
| **5** | ⚙️ **Control y Personalización:** Configuración adaptada a las necesidades específicas de cada organización. | ⚙️ **Control and Customization:** Configuration adapted to each organization's specific needs. |
| **6** | 💰 **Costes Predecibles:** Sin cargos variables por tráfico o almacenamiento cloud. Inversión única de infraestructura. | 💰 **Predictable Costs:** No variable charges for traffic or cloud storage. Single infrastructure investment. |

---

## 3️⃣ Cumplimiento Normativo / Regulatory Compliance

### RGPD (Reglamento General de Protección de Datos) / GDPR (General Data Protection Regulation)

| Requisito RGPD / GDPR Requirement | Cumplimiento Rhinometric / Rhinometric Compliance |
|-----------------------------------|---------------------------------------------------|
| **Español:** Toda la información sensible permanece local y bajo custodia directa del responsable del tratamiento. | **English:** All sensitive information remains local and under direct custody of the data controller. |
| **Español:** No hay transferencias internacionales de datos (Artículo 44-50). | **English:** No international data transfers (Articles 44-50). |
| **Español:** Derecho al olvido: los datos pueden ser eliminados físicamente en cualquier momento. | **English:** Right to erasure: data can be physically deleted at any time. |
| **Español:** Transparencia total: el cliente controla qué datos se recopilan y durante cuánto tiempo se conservan. | **English:** Total transparency: the client controls what data is collected and how long it's retained. |

### ENS (Esquema Nacional de Seguridad - España) / ENS (National Security Framework - Spain)

| Categoría ENS / ENS Category | Cumplimiento / Compliance |
|-----------------------------|---------------------------|
| **Español:** Sistemas de categoría MEDIA y ALTA pueden usar Rhinometric al estar completamente aislados. | **English:** MEDIUM and HIGH category systems can use Rhinometric as they are completely isolated. |
| **Español:** Cumple con medidas de seguridad organizativas, operacionales y de protección de datos. | **English:** Complies with organizational, operational, and data protection security measures. |
| **Español:** Apto para entornos air-gapped (sin conexión a internet). | **English:** Suitable for air-gapped environments (without internet connection). |

---

## 4️⃣ Seguridad y Soberanía de Datos / Data Security and Sovereignty

| Aspecto / Aspect | Español | English |
|------------------|---------|---------|
| **Aislamiento de Red** | Cada componente (Grafana, Prometheus, Loki, Tempo) se ejecuta en contenedores Docker aislados. No hay comunicación externa. | Each component (Grafana, Prometheus, Loki, Tempo) runs in isolated Docker containers. No external communications. |
| **Autenticación** | Acceso protegido por contraseñas configurables. Integración con LDAP/Active Directory disponible. | Access protected by configurable passwords. LDAP/Active Directory integration available. |
| **Cifrado** | Comunicaciones internas mediante TLS/SSL. Cifrado en reposo configurable. | Internal communications via TLS/SSL. Encryption at rest configurable. |
| **Auditoría** | Todos los accesos quedan registrados en logs auditables. | All access is recorded in auditable logs. |
| **Backup** | Copias de seguridad locales. Sin dependencia de servicios cloud. | Local backups. No dependency on cloud services. |

---

## 5️⃣ Instalación Asistida / Assisted Installation Process

### Opciones de Instalación / Installation Options

| Opción / Option | Español | English |
|-----------------|---------|---------|
| **1️⃣ Autogestionada** | El cliente ejecuta `install.sh` (Linux/macOS) o `install.ps1` (Windows) en su infraestructura. | Client runs `install.sh` (Linux/macOS) or `install.ps1` (Windows) on their infrastructure. |
| **2️⃣ Asistida** | Soporte remoto de Rhinometric durante la instalación. | Remote support from Rhinometric during installation. |
| **3️⃣ Presencial** | Instalación in-situ por técnicos Rhinometric (España y Portugal). | On-site installation by Rhinometric technicians (Spain and Portugal). |

### Proceso de Instalación / Installation Process

| Paso / Step | Español | English | Duración / Duration |
|-------------|---------|---------|---------------------|
| **1** | Validación de requisitos (Docker 24+, recursos) | Requirements validation (Docker 24+, resources) | 10 min |
| **2** | Configuración de credenciales (`.env`) | Credentials configuration (`.env`) | 10 min |
| **3** | Despliegue de servicios (`docker compose up`) | Services deployment (`docker compose up`) | 15 min |
| **4** | Verificación de salud de componentes | Component health verification | 10 min |
| **5** | Configuración de accesos y dashboards | Access and dashboard configuration | 15 min |
| **Total** | **Duración típica** | **Typical duration** | **< 1 hora / < 1 hour** |

---

## 6️⃣ Soporte y Mantenimiento / Support and Maintenance

### Soporte Técnico Incluido / Included Technical Support

| Español | English |
|---------|---------|
| **Canal:** Correo electrónico (rafael.canelon@rhinometric.com) | **Channel:** Email (rafael.canelon@rhinometric.com) |
| **Horario:** Lunes–Viernes 9:00–18:00 CET | **Schedule:** Monday–Friday 9:00–18:00 CET |
| **Respuesta:** < 24 horas en días laborables | **Response:** < 24 hours on business days |
| **Cobertura:** Consultas técnicas, resolución de incidencias, actualizaciones | **Coverage:** Technical inquiries, incident resolution, updates |

### Mantenimiento Anual Opcional / Optional Annual Maintenance

| Servicio / Service | Español | English |
|--------------------|---------|---------|
| **Actualizaciones** | Nuevas versiones y parches de seguridad | New versions and security patches |
| **Ampliaciones** | Nuevos exporters y dashboards personalizados | New exporters and custom dashboards |
| **Soporte Prioritario** | Respuesta < 4 horas | Response < 4 hours |
| **Revisión Anual** | Auditoría de configuración y optimización | Configuration audit and optimization |

---

## 7️⃣ Preguntas Frecuentes / Frequently Asked Questions (FAQ)

### Técnicas / Technical

| Pregunta / Question | Español | English |
|---------------------|---------|---------|
| **¿Requiere conexión a Internet?** | No. Rhinometric funciona completamente offline en entornos air-gapped. | No. Rhinometric works completely offline in air-gapped environments. |
| **¿Qué datos recopila?** | Solo los definidos por el cliente: métricas de sistema, logs de aplicación, trazas distribuidas. | Only client-defined data: system metrics, application logs, distributed traces. |
| **¿Es compatible con mi infraestructura?** | Sí. Compatible con Linux, Windows Server, VMware, Proxmox, Oracle Cloud, AWS, Azure, GCP. | Yes. Compatible with Linux, Windows Server, VMware, Proxmox, Oracle Cloud, AWS, Azure, GCP. |
| **¿Cuántos servidores puedo monitorizar?** | Sin límites técnicos. Dimensionado según recursos (CPU/RAM). | No technical limits. Sized according to resources (CPU/RAM). |
| **¿Puedo integrarlo con Active Directory?** | Sí. Grafana soporta autenticación LDAP/AD. | Yes. Grafana supports LDAP/AD authentication. |

### Comerciales / Commercial

| Pregunta / Question | Español | English |
|---------------------|---------|---------|
| **¿Cuál es el modelo de licenciamiento?** | Trial 30 días gratuito. Licencias perpetuas o anuales disponibles. | 30-day free trial. Perpetual or annual licenses available. |
| **¿Hay costes recurrentes obligatorios?** | No. Solo mantenimiento opcional. Sin cargos por uso o almacenamiento. | No. Only optional maintenance. No usage or storage charges. |
| **¿Puedo usar Rhinometric en la nube pública?** | Sí. Puedes desplegarlo en AWS/Azure/GCP manteniendo control local. | Yes. You can deploy it on AWS/Azure/GCP while maintaining local control. |
| **¿Ofrecen servicios profesionales?** | Sí. Consultoría, migración, integración personalizada. | Yes. Consulting, migration, custom integration. |

### Cumplimiento / Compliance

| Pregunta / Question | Español | English |
|---------------------|---------|---------|
| **¿Cumple con el ENS español?** | Sí. Apto para sistemas de categoría MEDIA y ALTA. | Yes. Suitable for MEDIUM and HIGH category systems. |
| **¿Y con el RGPD europeo?** | Sí. Todos los datos permanecen en la UE bajo control del cliente. | Yes. All data remains in the EU under client control. |
| **¿Puede usarse en sector sanitario?** | Sí. Cumple con requisitos de protección de datos sensibles. | Yes. Complies with sensitive data protection requirements. |
| **¿Es auditable?** | Sí. Logs completos de accesos, cambios y operaciones. | Yes. Complete logs of access, changes, and operations. |

---

## 8️⃣ Casos de Uso en Sector Público / Public Sector Use Cases

| Organización / Organization | Español | English |
|-----------------------------|---------|---------|
| **Ayuntamientos** | Monitoreo de servicios municipales, portales ciudadanos, sistemas de gestión interna | Monitoring of municipal services, citizen portals, internal management systems |
| **Diputaciones / Consejos Comarcales** | Supervisión de infraestructuras compartidas entre municipios | Supervision of shared infrastructure between municipalities |
| **Empresas Públicas** | Monitoreo de servicios críticos (agua, transporte, energía) | Monitoring of critical services (water, transport, energy) |
| **Universidades Públicas** | Observabilidad de campus virtuales, sistemas académicos | Observability of virtual campuses, academic systems |
| **Hospitales y Centros de Salud** | Monitoreo de sistemas sanitarios respetando privacidad de datos clínicos | Healthcare systems monitoring respecting clinical data privacy |

---

## 9️⃣ Contacto / Contact

| Español | English |
|---------|---------|
| **Email Comercial:** rafael.canelon@rhinometric.com | **Commercial Email:** rafael.canelon@rhinometric.com |
| **Email Soporte:** rafael.canelon@rhinometric.com | **Support Email:** rafael.canelon@rhinometric.com |
| **Web Oficial:** https://rhinometric.com | **Official Website:** https://rhinometric.com |
| **GitHub:** https://github.com/Rafael2712/rhinometric-overview | **GitHub:** https://github.com/Rafael2712/rhinometric-overview |
| **Horario:** Lunes–Viernes 9:00–18:00 CET | **Schedule:** Monday–Friday 9:00–18:00 CET |

---

## 🇪🇺 Declaración Final / Final Statement

| Español | English |
|---------|---------|
| **Rhinometric promueve la transparencia, soberanía tecnológica y seguridad digital en Europa.** | **Rhinometric promotes transparency, technological sovereignty, and digital security in Europe.** |
| Creemos que las organizaciones públicas y privadas tienen derecho a controlar completamente sus datos sin depender de grandes proveedores cloud estadounidenses. | We believe public and private organizations have the right to completely control their data without depending on large US cloud providers. |
| Nuestra plataforma on-premise garantiza que los datos sensibles permanezcan dentro de las fronteras de la Unión Europea, cumpliendo con las normativas más estrictas de privacidad y seguridad. | Our on-premise platform ensures sensitive data remains within European Union borders, complying with the strictest privacy and security regulations. |

---

## 📚 Recursos Adicionales / Additional Resources

| Español | English |
|---------|---------|
| • [Guía de Instalación](../README.md) | • [Installation Guide](../README.md) |
| • [Guía Técnica de Conexión](USER_GUIDE_CONNECT_APPS.md) | • [Technical Connection Guide](USER_GUIDE_CONNECT_APPS.md) |
| • [Guía Cloud Deployment](../CLOUD_DEPLOYMENT_GUIDE.md) | • [Cloud Deployment Guide](../CLOUD_DEPLOYMENT_GUIDE.md) |
| • [Arquitectura Híbrida](../HYBRID_ARCHITECTURE_GUIDE.md) | • [Hybrid Architecture](../HYBRID_ARCHITECTURE_GUIDE.md) |
| • [Sistema de Licencias](../LICENSE_SERVER_CLARIFICATION.md) | • [License System](../LICENSE_SERVER_CLARIFICATION.md) |

---

**© 2025 Rhinometric® – Todos los derechos reservados / All rights reserved**  
**Cumplimiento Normativo / Regulatory Compliance:**  
✅ RGPD (UE 2016/679) | ✅ ENS (España) | ✅ GDPR (EU 2016/679) | ✅ ENS (Spain)

**Soberanía de Datos Europea / European Data Sovereignty** 🇪🇺
